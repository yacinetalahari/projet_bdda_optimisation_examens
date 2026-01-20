import pandas as pd
import networkx as nx
import psycopg2
from db import get_connection
from datetime import datetime, timedelta
import random

class ExamScheduler:
    def __init__(self):
        self.conn = get_connection()
        self.start_date = datetime.now().replace(hour=8, minute=30, second=0, microsecond=0) + timedelta(days=7)
        # Sauts les weekends
        while self.start_date.weekday() > 4:
            self.start_date += timedelta(days=1)
            
    def load_data(self):
        """Charge les données nécessaires depuis la BDD"""
        # Récupérer les modules et leur durée
        self.modules = pd.read_sql("""
            SELECT m.id, m.nom, m.credits, m.formation_id, f.dept_id,
                   COUNT(i.etudiant_id) as nb_inscrits
            FROM modules m
            JOIN formations f ON f.id = m.formation_id
            LEFT JOIN inscriptions i ON i.module_id = m.id
            GROUP BY m.id, m.nom, m.credits, f.dept_id
            ORDER BY nb_inscrits DESC
        """, self.conn)
        
        # Récupérer les inscriptions pour le graphe de conflit
        self.inscriptions = pd.read_sql("SELECT etudiant_id, module_id FROM inscriptions", self.conn)
        
        # Récupérer les salles
        self.salles = pd.read_sql("SELECT id, nom, capacite, type FROM salles ORDER BY capacite ASC", self.conn)
        
        # Récupérer les profs
        self.profs = pd.read_sql("SELECT id, nom, dept_id FROM professeurs", self.conn)
        
    def build_conflict_graph(self):
        """Construit le graphe de conflits entre modules (basé sur les étudiants communs)"""
        G = nx.Graph()
        G.add_nodes_from(self.modules['id'].tolist())
        
        # Group par étudiant pour trouver les modules conflictuels
        student_modules = self.inscriptions.groupby('etudiant_id')['module_id'].apply(list)
        
        # Ajouter les arêtes
        for modules in student_modules:
            for i in range(len(modules)):
                for j in range(i + 1, len(modules)):
                    G.add_edge(modules[i], modules[j])
                    
        return G

    def assign_resources(self, module_id, date_slot, time_slot_minutes, assigned_profs_count):
        """Assigne une salle et un prof pour un créneau donné"""
        module = self.modules[self.modules['id'] == module_id].iloc[0]
        nb_etudiants = module['nb_inscrits']
        
        # 1. Trouver une salle
        # On cherche la plus petite salle qui peut contenir les étudiants (Best Fit)
        possible_salles = self.salles[self.salles['capacite'] >= nb_etudiants]
        
        if possible_salles.empty:
            print(f"ALERTE: Aucune salle suffisante pour module {module_id} ({nb_etudiants} étudiants)")
            # Fallback: prendre la plus grande
            salle = self.salles.iloc[-1]
        else:
            salle = possible_salles.iloc[0]
            
        # 2. Trouver un prof
        # Priorité: Département du module
        # Contrainte: Max 3 examens par jour (vérifié via assigned_profs_count)
        
        dept_match_profs = self.profs[self.profs['dept_id'] == module['dept_id']]
        other_profs = self.profs[self.profs['dept_id'] != module['dept_id']]
        
        # Mélanger pour équité
        candidates = pd.concat([dept_match_profs.sample(frac=1), other_profs.sample(frac=1)])
        
        chosen_prof = None
        current_day_str = date_slot.strftime('%Y-%m-%d')
        
        for _, prof in candidates.iterrows():
            pid = prof['id']
            # Vérifier charge journalière (max 3)
            if assigned_profs_count.get((pid, current_day_str), 0) < 3:
                chosen_prof = prof
                assigned_profs_count[(pid, current_day_str)] = assigned_profs_count.get((pid, current_day_str), 0) + 1
                break
                
        if chosen_prof is None:
            # Cas rare : tous les profs sont occupés ce jour là ?
            # On prend un au hasard (le trigger sql bloquera si > 3, mais on essaie d'éviter)
            chosen_prof = self.profs.sample(1).iloc[0]
            
        return salle['id'], chosen_prof['id']

    def generate(self):
        try:
            print("Début optimisation...")
            self.load_data()
            
            # Nettoyer avant
            cur = self.conn.cursor()
            try:
                cur.execute("CALL clear_planning()")
            except psycopg2.errors.UndefinedFunction:
                # Fallback si la procédure n'existe pas encore
                self.conn.rollback()
                cur = self.conn.cursor() # Re-cursor after rollback
                cur.execute("TRUNCATE TABLE examens RESTART IDENTITY CASCADE")
            
            self.conn.commit()
            
            # Graphe de conflits (Coloration pour les jours)
            G = self.build_conflict_graph()
            
            # Greedy coloring : stratégie 'largest_first' pour traiter les gros noeuds d'abord
            coloring = nx.coloring.greedy_color(G, strategy='largest_first')
            
            # Group modules by color (day)
            days = {}
            for node, color in coloring.items():
                if color not in days:
                    days[color] = []
                days[color].append(node)
                
            # Assign Slots
            exam_records = []
            current_date = self.start_date
            
            # Tracking pour Profs (ProfID, Date) -> Count
            prof_daily_load = {}
            
            # Trier les jours pour l'ordre chrono
            sorted_colors = sorted(days.keys())
            
            for color in sorted_colors:
                day_modules = days[color]
                
                # Gestion Weekend
                if current_date.weekday() >= 5: # Samedi/Dimanche
                    current_date += timedelta(days=(7 - current_date.weekday()))
                
                # Créneaux horaires disponibles par jour (ex: 08:30, 10:30, 13:30, 15:30)
                # On met max 4 examens séquentiels dans la même salle, mais ici on simplifie
                # On répartit les modules du jour sur les créneaux.
                # Simplification: Tous les modules de ce "Jour couleur" peuvent être en parallèle 
                # SI ils n'ont pas de conflit. Mais la coloration garantit pas de conflit étudiant.
                # Donc tous les modules de 'days[color]' peuvent avoir lieu LE MEME JOUR.
                # Ils peuvent être à la MEME HEURE ? 
                # OUI, car s'ils ont la même couleur, ils ne partagent AUCUN étudiant.
                # Donc on peut paralléliser max.
                
                # Assignation Horaire: Tout le monde à 09:00 sauf si manque de salles
                # Si manque de salles, on décale à 14:00.
                
                morning_slots = []
                afternoon_slots = []
                
                for mod_id in day_modules:
                    # Alternance basique pour répartir la charge salles
                    if len(morning_slots) <= len(afternoon_slots):
                        morning_slots.append(mod_id)
                    else:
                        afternoon_slots.append(mod_id)
                        
                # Traitement Matin (09:00)
                for mod_id in morning_slots:
                    salle_id, prof_id = self.assign_resources(mod_id, current_date, 9*60, prof_daily_load)
                    exam_records.append((
                        int(mod_id), int(prof_id), int(salle_id), 
                        current_date.replace(hour=9, minute=0), 
                        90 # Durée par défaut
                    ))
                    
                # Traitement Aprèm (14:00)
                for mod_id in afternoon_slots:
                    salle_id, prof_id = self.assign_resources(mod_id, current_date, 14*60, prof_daily_load)
                    exam_records.append((
                        int(mod_id), int(prof_id), int(salle_id), 
                        current_date.replace(hour=14, minute=0), 
                        90
                    ))
                
                current_date += timedelta(days=1)
            
            # Insertion Batch
            print(f"Insertion de {len(exam_records)} examens...")
            args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s)", x).decode('utf-8') for x in exam_records)
            cur.execute("INSERT INTO examens (module_id, prof_id, salle_id, date_heure, duree_minutes) VALUES " + args_str)
            
            self.conn.commit()
            print("Planification terminée avec succès.")
            return True, f"Généré {len(exam_records)} examens sur {len(sorted_colors)} jours."
            
        except Exception as e:
            self.conn.rollback()
            print(f"Erreur scheduler : {e}")
            return False, str(e)
            
        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    scheduler = ExamScheduler()
    scheduler.generate()
