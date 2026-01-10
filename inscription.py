import random
from db import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
SELECT e.id, m.id
FROM etudiants e
JOIN modules m ON m.formation_id = e.formation_id
""")

mapping = {}
for e,m in cur.fetchall():
    mapping.setdefault(e, []).append(m)

for e, mods in mapping.items():
    for m in random.sample(mods, min(6,len(mods))):
        cur.execute("INSERT INTO inscriptions VALUES (%s,%s)", (e,m))

conn.commit()
cur.close()
conn.close()
