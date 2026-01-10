from faker import Faker
import random
from db import get_connection
import time

fake = Faker("fr_FR")

# Début du chronomètre
start_time = time.time()

print("🚀 Début de l'insertion de 13,250 étudiants...")

conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT id FROM formations")
formations = [x[0] for x in cur.fetchall()]

for i in range(13250):
    cur.execute("""
    INSERT INTO etudiants (nom, prenom, formation_id, promo)
    VALUES (%s,%s,%s,%s)
    """, (
        fake.last_name(),
        fake.first_name(),
        random.choice(formations),
        random.randint(2022,2025)
    ))
    
    # Afficher progression tous les 1000 étudiants
    if (i + 1) % 1000 == 0:
        print(f"✅ {i + 1} étudiants insérés...")

conn.commit()
cur.close()
conn.close()

# Fin du chronomètre
end_time = time.time()
execution_time = end_time - start_time

print(f"\n✅ TERMINÉ !")
print(f"⏱  Temps d'exécution : {execution_time:.2f} secondes")
print(f" {13250} étudiants insérés avec succès")
print(f" Vitesse : {13250/execution_time:.0f} étudiants/seconde")
