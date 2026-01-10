from faker import Faker
import random
from db import get_connection

fake = Faker("fr_FR")
conn = get_connection()
cur = conn.cursor()

for i in range(1,8):
    cur.execute("INSERT INTO departements (nom) VALUES (%s)", (f"Departement {i}",))

cur.execute("SELECT id FROM departements")
dept_ids = [x[0] for x in cur.fetchall()]

for d in dept_ids:
    for _ in range(30):
        cur.execute("""
        INSERT INTO formations (nom, dept_id, nb_modules)
        VALUES (%s,%s,%s)
        """, (f"Licence {fake.word()}", d, random.randint(6,9)))

for _ in range(120):
    cur.execute("""
    INSERT INTO professeurs (nom, dept_id, specialite)
    VALUES (%s,%s,%s)
    """, (fake.last_name(), random.choice(dept_ids), fake.job()))

for i in range(60):
    cur.execute("INSERT INTO salles VALUES (DEFAULT,%s,20,'salle','Bloc A')",(f"S{i}",))
for i in range(15):
    cur.execute("INSERT INTO salles VALUES (DEFAULT,%s,%s,'amphi','Bloc B')",
                (f"A{i}", random.randint(100,300)))

conn.commit()
cur.close()
conn.close()
