import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psycopg2
from contextlib import contextmanager

st.set_page_config(
    page_title="Plateforme d'Optimisation des Examens",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    
    .top-navbar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px 40px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }  
   
    
    
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stats-header {
        font-size: 2rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 2.5rem 0 1.5rem 0;
        padding-bottom: 0.8rem;
        border-bottom: 4px solid #667eea;
    }
    
    [data-testid="stMetricValue"] {
        color: #667eea !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 14px 32px;
        align-items:center;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
    
    .info-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 2rem 0;
    }
    
    .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
    </style>
""", unsafe_allow_html=True)

@contextmanager
def get_connection():
    conn = None
    try:
        # Try Streamlit secrets first (for cloud deployment)
        try:
            if 'database' in st.secrets:
                conn = psycopg2.connect(
                    host=st.secrets["database"]["host"],
                    port=st.secrets["database"]["port"],
                    database=st.secrets["database"]["name"],
                    user=st.secrets["database"]["user"],
                    password=st.secrets["database"]["password"]
                )
        except:
            # Fall back to local connection
            conn = psycopg2.connect(
                dbname="exam_scheduler",
                user="postgres",
                password="yassinopostgresql",
                host="localhost",
                port="5432"
            )
        yield conn
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        st.info("Vérifiez que PostgreSQL est démarré et que les identifiants sont corrects")
        yield None
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=300)
def get_global_kpis():
    with get_connection() as conn:
        if not conn:
            return {}
        try:
            kpis = {}
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM etudiants")
            kpis['total_etudiants'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM professeurs")
            kpis['total_professeurs'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM modules")
            kpis['total_modules'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM inscriptions")
            kpis['total_inscriptions'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM departements")
            kpis['total_departements'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM formations")
            kpis['total_formations'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM salles")
            kpis['total_salles'] = cur.fetchone()[0]
            
            cur.execute("SELECT SUM(capacite) FROM salles")
            kpis['capacite_totale'] = cur.fetchone()[0] or 0
            
            cur.execute("SELECT COUNT(*) FROM examens")
            kpis['total_examens'] = cur.fetchone()[0]
            
            cur.close()
            return kpis
        except Exception as e:
            st.error(f"Erreur KPIs : {e}")
            return {}

@st.cache_data(ttl=300)
def get_department_stats():
    with get_connection() as conn:
        if not conn:
            return pd.DataFrame()
        try:
            query = """
                SELECT 
                    d.nom as departement,
                    COUNT(DISTINCT e.id) as nb_etudiants,
                    COUNT(DISTINCT p.id) as nb_professeurs,
                    COUNT(DISTINCT f.id) as nb_formations
                FROM departements d
                LEFT JOIN formations f ON f.dept_id = d.id
                LEFT JOIN etudiants e ON e.formation_id = f.id
                LEFT JOIN professeurs p ON p.dept_id = d.id
                GROUP BY d.nom
                ORDER BY nb_etudiants DESC
            """
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Erreur stats département : {e}")
            return pd.DataFrame()

@st.cache_data(ttl=300)
def get_conflicts():
    with get_connection() as conn:
        if not conn:
            return {}
        try:
            conflicts = {}
            cur = conn.cursor()
            
            # Conflits étudiants (>1 examen/jour)
            cur.execute("""
                SELECT COUNT(DISTINCT e.id)
                FROM etudiants e
                JOIN inscriptions i ON i.etudiant_id = e.id
                JOIN examens ex ON ex.module_id = i.module_id
                GROUP BY e.id, DATE(ex.date_heure)
                HAVING COUNT(*) > 1
            """)
            conflicts['etudiants'] = len(cur.fetchall())
            
            # Conflits professeurs (>3 examens/jour)
            cur.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT prof_id, DATE(date_heure)
                    FROM examens
                    GROUP BY prof_id, DATE(date_heure)
                    HAVING COUNT(*) > 3
                ) t
            """)
            conflicts['professeurs'] = cur.fetchone()[0]
            
            # Conflits capacité salles
            cur.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT ex.id
                    FROM examens ex
                    JOIN salles s ON s.id = ex.salle_id
                    JOIN inscriptions i ON i.module_id = ex.module_id
                    GROUP BY ex.id, s.capacite
                    HAVING COUNT(i.etudiant_id) > s.capacite
                ) t
            """)
            conflicts['capacite'] = cur.fetchone()[0]
            
            cur.close()
            return conflicts
        except Exception as e:
            st.error(f"Erreur détection conflits : {e}")
            return {}

@st.cache_data(ttl=300)
def get_exam_list():
    with get_connection() as conn:
        if not conn:
            return pd.DataFrame()
        try:
            query = """
                SELECT 
                    ex.id,
                    m.nom as module,
                    p.nom as professeur,
                    s.nom as salle,
                    ex.date_heure,
                    ex.duree_minutes,
                    COUNT(i.etudiant_id) as nb_inscrits,
                    s.capacite
                FROM examens ex
                JOIN modules m ON m.id = ex.module_id
                JOIN professeurs p ON p.id = ex.prof_id
                JOIN salles s ON s.id = ex.salle_id
                LEFT JOIN inscriptions i ON i.module_id = ex.module_id
                GROUP BY ex.id, m.nom, p.nom, s.nom, ex.date_heure, ex.duree_minutes, s.capacite
                ORDER BY ex.date_heure
            """
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Erreur liste examens : {e}")
            return pd.DataFrame()

@st.cache_data(ttl=300)
def get_prof_workload():
    with get_connection() as conn:
        if not conn:
            return pd.DataFrame()
        try:
            query = """
                SELECT 
                    p.nom,
                    COUNT(ex.id) as nb_examens,
                    d.nom as departement
                FROM professeurs p
                LEFT JOIN examens ex ON ex.prof_id = p.id
                JOIN departements d ON d.id = p.dept_id
                GROUP BY p.nom, d.nom
                ORDER BY nb_examens DESC
                LIMIT 20
            """
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Erreur charge professeurs : {e}")
            return pd.DataFrame()

@st.cache_data(ttl=300)
def get_salle_occupation():
    with get_connection() as conn:
        if not conn:
            return pd.DataFrame()
        try:
            query = """
                SELECT 
                    s.nom,
                    s.type,
                    s.capacite,
                    COUNT(ex.id) as nb_examens,
                    ROUND(AVG(inscr_count.nb_inscrits * 100.0 / s.capacite), 2) as taux_occupation
                FROM salles s
                LEFT JOIN examens ex ON ex.salle_id = s.id
                LEFT JOIN (
                    SELECT ex.id, COUNT(i.etudiant_id) as nb_inscrits
                    FROM examens ex
                    JOIN inscriptions i ON i.module_id = ex.module_id
                    GROUP BY ex.id
                ) inscr_count ON inscr_count.id = ex.id
                GROUP BY s.nom, s.type, s.capacite
                ORDER BY taux_occupation DESC NULLS LAST
                LIMIT 15
            """
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Erreur occupation salles : {e}")
            return pd.DataFrame()

def render_navbar(current_page):
    cols = st.columns([1, 1, 1, 1, 1, 1])
    
    # Laisse cols[0] vide pour centrer
    with cols[1]:
        if st.button("Accueil", use_container_width=True, type="primary" if current_page == "Accueil" else "secondary"):
            st.session_state.page = "Accueil"
            st.rerun()
    
    with cols[2]:
        if st.button("Administration", use_container_width=True, type="primary" if current_page == "Administration" else "secondary"):
            st.session_state.page = "Administration"
            st.rerun()
    
    with cols[3]:
        if st.button("Statistiques", use_container_width=True, type="primary" if current_page == "Statistiques" else "secondary"):
            st.session_state.page = "Statistiques"
            st.rerun()
    
    with cols[4]:
        if st.button("Consultation", use_container_width=True, type="primary" if current_page == "Consultation" else "secondary"):
            st.session_state.page = "Consultation"
            st.rerun()
    # cols[5] reste vide aussi
    
    st.markdown("---")

def show_accueil():
    st.markdown('<div class="main-header">Plateforme d\'Optimisation des Emplois du Temps d\'Examens</div>', unsafe_allow_html=True)
    
    kpis = get_global_kpis()
    
    st.markdown('<div class="stats-header">Vue d\'ensemble</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Étudiants", f"{kpis.get('total_etudiants', 0):,}")
    with col2:
        st.metric("Professeurs", f"{kpis.get('total_professeurs', 0):,}")
    with col3:
        st.metric("Modules", f"{kpis.get('total_modules', 0):,}")
    with col4:
        st.metric("Inscriptions", f"{kpis.get('total_inscriptions', 0):,}")
    
    st.markdown("---")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Départements", kpis.get('total_departements', 0))
    with col6:
        st.metric("Formations", kpis.get('total_formations', 0))
    with col7:
        st.metric("Salles", kpis.get('total_salles', 0))
    with col8:
        st.metric("Examens planifiés", kpis.get('total_examens', 0))
    
    st.markdown("---")
    
    st.markdown('<div class="stats-header">Statistiques par Département</div>', unsafe_allow_html=True)
    
    dept_stats = get_department_stats()
    
    if not dept_stats.empty:
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig = px.bar(
                dept_stats,
                x='departement',
                y='nb_etudiants',
                title='Étudiants par Département',
                color='nb_etudiants',
                color_continuous_scale='Purples'
            )
            fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            fig = px.bar(
                dept_stats,
                x='departement',
                y='nb_professeurs',
                title='Professeurs par Département',
                color='nb_professeurs',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(dept_stats, use_container_width=True, hide_index=True)

def show_administration():
    st.markdown('<div class="main-header">Administration des Examens</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3 style="color: #2c3e50; margin-bottom: 1rem;">Génération Automatique des Examens</h3>
        <p style="color: #6c757d; font-size: 1.1rem;">
            Ici vous pouvez générer automatiquement les emplois du temps d'examens pour tous les départements.
            Le système optimisera l'allocation des salles et la répartition des horaires en respectant toutes les contraintes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button(" Générer les Emplois du Temps", use_container_width=True, type="primary"):
            with st.spinner("Génération en cours... Optimisation des ressources"):
                from scheduler import ExamScheduler
                try:
                    scheduler = ExamScheduler()
                    success, message = scheduler.generate()
                    if success:
                        st.success(f" Succès ! {message}")
                        st.cache_data.clear() # Invalider le cache pour rafraîchir les vues
                        st.rerun()
                    else:
                        st.error(f"Échec de l'optimisation : {message}")
                except Exception as e:
                    st.error(f"Erreur inattendue : {e}")
    
    st.markdown("---")
    
    st.markdown('<div class="stats-header">Détection de Conflits</div>', unsafe_allow_html=True)
    
    conflicts = get_conflicts()
    
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        st.metric("Conflits Étudiants", conflicts.get('etudiants', 0), 
                 delta="Examens multiples/jour", delta_color="inverse")
    
    with col_c2:
        st.metric("Conflits Professeurs", conflicts.get('professeurs', 0),
                 delta=">3 examens/jour", delta_color="inverse")
    
    with col_c3:
        st.metric("Conflits Capacité", conflicts.get('capacite', 0),
                 delta="Salles surchargées", delta_color="inverse")
    
    total_conflicts = sum(conflicts.values())
    if total_conflicts == 0:
        st.success("✅ Aucun conflit détecté dans le planning actuel !")
    else:
        st.warning(f"⚠️ {total_conflicts} conflit(s) détecté(s). Optimisation recommandée.")
    
    st.markdown("---")
    
    st.markdown('<div class="stats-header">Liste des Examens Planifiés</div>', unsafe_allow_html=True)
    
    df_exams = get_exam_list()
    
    if not df_exams.empty:
        st.dataframe(df_exams, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun examen planifié pour le moment")

def show_statistiques():
    st.markdown('<div class="main-header">Statistiques Avancées</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="stats-header">Statistiques par Département</div>', unsafe_allow_html=True)
    
    dept_stats = get_department_stats()
    
    if not dept_stats.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                dept_stats,
                x='departement',
                y='nb_etudiants',
                title='Répartition des Étudiants',
                color='nb_etudiants',
                color_continuous_scale='Purples'
            )
            fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                dept_stats,
                names='departement',
                values='nb_formations',
                title='Répartition des Formations'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown('<div class="stats-header">Charge de Travail des Professeurs</div>', unsafe_allow_html=True)
    
    df_prof = get_prof_workload()
    
    if not df_prof.empty:
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            fig = px.bar(
                df_prof,
                x='nom',
                y='nb_examens',
                color='departement',
                title='Top 20 Professeurs - Nombre d\'examens',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_b:
            st.dataframe(df_prof, use_container_width=True, hide_index=True)
            st.metric("Moyenne examens/prof", f"{df_prof['nb_examens'].mean():.1f}")
    
    st.markdown("---")
    
    st.markdown('<div class="stats-header">Occupation des Salles</div>', unsafe_allow_html=True)
    
    df_salles = get_salle_occupation()
    
    if not df_salles.empty:
        fig = px.bar(
            df_salles,
            x='nom',
            y='taux_occupation',
            color='type',
            title='Taux d\'occupation des salles (%)',
            color_discrete_map={'salle': '#667eea', 'amphi': '#764ba2'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_salles, use_container_width=True, hide_index=True)

def show_consultation():
    st.markdown('<div class="main-header">Consultation des Plannings</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3 style="color: #2c3e50;">Consultation Personnalisée</h3>
        <p style="color: #6c757d;">
            Les étudiants et professeurs peuvent consulter leurs plannings d'examens personnalisés.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    role = st.selectbox("Sélectionnez votre rôle", ["Étudiant", "Professeur"])
    
    selected_id = None
    
    with get_connection() as conn:
        if not conn:
            st.error("Erreur connexion BDD")
            return

        if role == "Étudiant":
            df_students = pd.read_sql("SELECT id, nom, prenom FROM etudiants ORDER BY nom LIMIT 200", conn)
            if not df_students.empty:
                student_options = {f"{r['nom']} {r['prenom']} (ID: {r['id']})": r['id'] for _, r in df_students.iterrows()}
                selected_label = st.selectbox("Sélectionnez un étudiant", list(student_options.keys()))
                selected_id = student_options[selected_label]
        else:
            df_profs = pd.read_sql("SELECT id, nom FROM professeurs ORDER BY nom", conn)
            if not df_profs.empty:
                prof_options = {f"{r['nom']} (ID: {r['id']})": r['id'] for _, r in df_profs.iterrows()}
                selected_label = st.selectbox("Sélectionnez un professeur", list(prof_options.keys()))
                selected_id = prof_options[selected_label]
    
        if st.button("Afficher mon planning", type="primary") and selected_id:
            st.markdown("### Votre Planning")
            
            if role == "Étudiant":
                query = """
                    SELECT 
                        m.nom as Module,
                        ex.date_heure as "Date & Heure",
                        ex.duree_minutes as "Durée (min)",
                        s.nom as Salle,
                        s.batiment as Bâtiment
                    FROM inscriptions i
                    JOIN examens ex ON ex.module_id = i.module_id
                    JOIN modules m ON m.id = ex.module_id
                    JOIN salles s ON s.id = ex.salle_id
                    WHERE i.etudiant_id = %s
                    ORDER BY ex.date_heure
                """
            else:
                query = """
                    SELECT 
                        m.nom as Module,
                        ex.date_heure as "Date & Heure",
                        ex.duree_minutes as "Durée (min)",
                        s.nom as Salle,
                        s.batiment as Bâtiment,
                        (SELECT COUNT(*) FROM inscriptions i WHERE i.module_id = m.id) as "Nombre Étudiants"
                    FROM examens ex
                    JOIN modules m ON m.id = ex.module_id
                    JOIN salles s ON s.id = ex.salle_id
                    WHERE ex.prof_id = %s
                    ORDER BY ex.date_heure
                """
            
            df_res = pd.read_sql(query, conn, params=(selected_id,))
            
            if not df_res.empty:
                st.dataframe(df_res, use_container_width=True, hide_index=True)
            else:
                st.warning("Aucun examen trouvé pour ce profil.")


def main():
    if 'page' not in st.session_state:
        st.session_state.page = "Accueil"
    
    render_navbar(st.session_state.page)
    
    with get_connection() as conn:
        if not conn:
            st.error("Impossible de se connecter à la base de données")
            st.stop()
    
    if st.session_state.page == "Accueil":
        show_accueil()
    elif st.session_state.page == "Administration":
        show_administration()
    elif st.session_state.page == "Statistiques":
        show_statistiques()
    elif st.session_state.page == "Consultation":
        show_consultation()

if __name__ == "__main__":
    main()