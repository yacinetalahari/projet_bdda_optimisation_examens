import psycopg2

def get_connection():
    try:
        conn = psycopg2.connect(
           dbname="exam_scheduler",
            user="postgres",
            password="yassinopostgresql",
            host="localhost",
            port="5432"
        )
        print("Connexion PostgreSQL OK")
        return conn

    except Exception as e:
        print("Erreur connexion PostgreSQL :", e)
        raise
