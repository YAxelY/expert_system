import os
import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta

os.makedirs("data/raw", exist_ok=True)
db_path = "data/raw/medical_data.db"

fake = Faker('fr_FR')
diagnosisSymptomsMap = {
    "grippe": ["fièvre", "toux", "fatigue", "courbatures"],
    "COVID-19": ["fièvre", "toux sèche", "perte d’odorat", "fatigue"],
    "migraine": ["maux de tête", "nausées", "sensibilité à la lumière"],
    "angine": ["gorge irritée", "fièvre", "douleur en avalant"],
    "varicelle": ["éruption cutanée", "fièvre", "démangeaisons"],
    "asthme": ["essoufflement", "sifflements", "toux"],
    "allergie": ["éternuements", "yeux rouges", "démangeaisons"],
    "gastro-entérite": ["nausées", "vomissements", "diarrhée", "crampes"],
    "hypertension": ["maux de tête", "vertiges", "saignement de nez"]
}
medicationsList = ["paracétamol", "ibuprofène", "doliprane", "amoxicilline", "ventoline"]

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    age INTEGER,
    diagnostic TEXT,
    date_consultation TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS symptoms (
    patient_id TEXT,
    symptom TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS medications (
    patient_id TEXT,
    medication TEXT
)
""")

for i in range(1, 51):
    pid = f"P{str(i).zfill(3)}"
    age = random.randint(18, 90)
    diagnosis = random.choice(list(diagnosisSymptomsMap.keys()))
    date = (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat()
    cur.execute("INSERT INTO patients VALUES (?, ?, ?, ?)", (pid, age, diagnosis, date))

    symptoms = random.sample(diagnosisSymptomsMap[diagnosis], k=random.randint(2, 4))
    for s in symptoms:
        cur.execute("INSERT INTO symptoms VALUES (?, ?)", (pid, s))

    meds = random.sample(medicationsList, k=random.randint(1, 3))
    for m in meds:
        cur.execute("INSERT INTO medications VALUES (?, ?)", (pid, m))

conn.commit()
conn.close()

print("✅ Base de données SQLite générée dans data/raw/medical_data.db")
