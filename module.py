from faker import Faker
import random
from db import get_connection

fake = Faker()
conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT id, nb_modules FROM formations")
for fid, nb in cur.fetchall():
    for _ in range(nb):
        cur.execute("""
        INSERT INTO modules (nom, credits, formation_id)
        VALUES (%s,%s,%s)
        """, (fake.word(), random.randint(2,6), fid))

conn.commit()
cur.close()
conn.close()
