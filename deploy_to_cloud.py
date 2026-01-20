import psycopg2
import os
from faker import Faker
import random

# Configuration Supabase (Données fournies)
DB_CONFIG = {
    "host": "aws-1-eu-central-2.pooler.supabase.com",
    "port": "6543",
    "database": "postgres",
    "user": "postgres.texawjwdgphhdgtrxsya"
}

def run_sql_file(cur, filename):
    print(f"Executing {filename}...")
    with open(filename, 'r', encoding='utf-8') as f:
        cur.execute(f.read())

def main():
    print("=== DÉPLOIEMENT VERS SUPABASE ===")
    print(f"Cible : {DB_CONFIG['host']}")
    
    # Demander le mot de passe
    password = input("Entrez le mot de passe de la base de données Supabase : ")
    
    try:
        conn = psycopg2.connect(
            **DB_CONFIG,
            password=password
        )
        conn.autocommit = True
        cur = conn.cursor()
        print("✅ Connexion réussie !")
        
        # 1. Création des tables
        print("\n--- 1. CRÉATION DU SCHÉMA ---")
        # On drop tout avant pour être propre
        cur.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
        run_sql_file(cur, 'creation.sql')
        run_sql_file(cur, 'contrainte.sql')
        run_sql_file(cur, 'optimization.sql')
        
        # 2. Génération des données
        print("\n--- 2. GÉNÉRATION DES DONNÉES ---")
        fake = Faker("fr_FR")
        
        # Départements
        print("Génération départements...")
        for i in range(1, 8):
            cur.execute("INSERT INTO departements (nom) VALUES (%s)", (f"Departement {i}",))
            
        cur.execute("SELECT id FROM departements")
        dept_ids = [x[0] for x in cur.fetchall()]

        # Formations
        print("Génération formations...")
        formations_ids = []
        for d in dept_ids:
            for _ in range(30):
                cur.execute("""
                INSERT INTO formations (nom, dept_id, nb_modules)
                VALUES (%s,%s,%s) RETURNING id
                """, (f"Licence {fake.word()}", d, random.randint(6,9)))
                formations_ids.append(cur.fetchone()[0])

        # Professeurs
        print("Génération professeurs...")
        for _ in range(120):
            cur.execute("""
            INSERT INTO professeurs (nom, dept_id, specialite)
            VALUES (%s,%s,%s)
            """, (fake.last_name(), random.choice(dept_ids), fake.job()))

        # Salles
        print("Génération salles...")
        for i in range(60):
            cur.execute("INSERT INTO salles VALUES (DEFAULT,%s,20,'salle','Bloc A')",(f"S{i}",))
        for i in range(15):
            cur.execute("INSERT INTO salles VALUES (DEFAULT,%s,%s,'amphi','Bloc B')",
                        (f"A{i}", random.randint(100,300)))
                        
        # Etudiants & Modules & Inscriptions
        print("Génération étudiants, modules et inscriptions (ça peut prendre un peu de temps)...")
        # Pour simplifier et ne pas implémenter toute la logique complexe de data.py si elle n'y est pas,
        # je reprends la logique standard :
        
        # Création modules pour chaque formation
        modules_map = {} # formation_id -> list[module_id]
        for f_id in formations_ids:
            modules_map[f_id] = []
            for k in range(random.randint(6,9)):
                cur.execute("INSERT INTO modules (nom, credits, formation_id) VALUES (%s, %s, %s) RETURNING id",
                           (f"Module {fake.word()} {k}", random.randint(2,6), f_id))
                modules_map[f_id].append(cur.fetchone()[0])
        
        # Création étudiants et inscriptions
        for f_id in formations_ids:
            # 5 à 10 étudiants par formation
            for _ in range(random.randint(5, 10)):
                cur.execute("INSERT INTO etudiants (nom, prenom, formation_id, promo) VALUES (%s, %s, %s, %s) RETURNING id",
                           (fake.last_name(), fake.first_name(), f_id, 2024))
                etudiant_id = cur.fetchone()[0]
                
                # Inscription à tous les modules de la formation
                for m_id in modules_map[f_id]:
                    cur.execute("INSERT INTO inscriptions (etudiant_id, module_id, note) VALUES (%s, %s, %s)",
                               (etudiant_id, m_id, random.randint(0,20)))

        print("\n✅ Déploiement terminé avec succès !")
        print("Vous pouvez maintenant utiliser l'application Streamlit connectée au Cloud.")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ ERREUR : {e}")

if __name__ == "__main__":
    main()
