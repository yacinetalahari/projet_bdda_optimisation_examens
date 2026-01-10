import random
from datetime import datetime, timedelta
from db import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT id FROM modules")
modules = [x[0] for x in cur.fetchall()]

cur.execute("SELECT id FROM professeurs")
profs = [x[0] for x in cur.fetchall()]

cur.execute("SELECT id FROM salles")
salles = [x[0] for x in cur.fetchall()]

start = datetime(2026,1,10,8,0)

for m in modules:
    try:
        cur.execute("""
        INSERT INTO examens (module_id, prof_id, salle_id, date_heure, duree_minutes)
        VALUES (%s,%s,%s,%s,%s)
        """, (
            m,
            random.choice(profs),
            random.choice(salles),
            start + timedelta(days=random.randint(0,12)),
            random.choice([60,90,120])
        ))
    except:
        conn.rollback()

conn.commit()
cur.close()
conn.close()
