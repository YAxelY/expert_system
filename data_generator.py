import sqlite3
import json
import random
from datetime import datetime, timedelta

# Définition des données médicales
SYMPTOMS = [
    "fièvre", "toux", "fatigue", "maux_de_tete", "douleurs_musculaires",
    "nausees", "diarrhee", "essoufflement", "perte_gout_odorat",
    "eruption_cutanee", "maux_de_gorge", "congestion_nasale"
]

DISEASES = [
    "covid19", "grippe", "rhume", "angine", "gastro_enterite",
    "bronchite", "allergie", "migraine", "infection_urinaire"
]

MEDICATIONS = [
    "paracetamol", "ibuprofene", "amoxicilline", "omeprazole",
    "loratadine", "azithromycine", "doliprane", "aspirine"
]

def generate_patient():
    """Génère des données aléatoires pour un patient"""
    age = random.randint(18, 85)
    num_symptoms = random.randint(2, 5)
    symptoms = random.sample(SYMPTOMS, num_symptoms)
    disease = random.choice(DISEASES)
    num_medications = random.randint(1, 3)
    medications = random.sample(MEDICATIONS, num_medications)
    
    date = datetime.now() - timedelta(days=random.randint(0, 365))
    
    return {
        "age": age,
        "symptoms": symptoms,
        "diagnostic": disease,
        "medications": medications,
        "date_consultation": date.strftime("%Y-%m-%d")
    }

def create_sqlite_database(num_patients=1000):
    """Crée la base de données SQLite avec des patients structurés"""
    conn = sqlite3.connect('data/raw/medical_data.db')
    c = conn.cursor()
    
    # Création des tables
    c.execute('''CREATE TABLE IF NOT EXISTS patients
                 (id INTEGER PRIMARY KEY, age INTEGER, diagnostic TEXT, date_consultation TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS symptoms
                 (patient_id INTEGER, symptom TEXT,
                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS medications
                 (patient_id INTEGER, medication TEXT,
                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')
    
    # Génération des données
    for i in range(num_patients):
        patient = generate_patient()
        
        # Insertion patient
        c.execute('''INSERT INTO patients (age, diagnostic, date_consultation)
                     VALUES (?, ?, ?)''',
                  (patient['age'], patient['diagnostic'], patient['date_consultation']))
        patient_id = c.lastrowid
        
        # Insertion symptômes
        for symptom in patient['symptoms']:
            c.execute('INSERT INTO symptoms VALUES (?, ?)', (patient_id, symptom))
        
        # Insertion médicaments
        for medication in patient['medications']:
            c.execute('INSERT INTO medications VALUES (?, ?)', (patient_id, medication))
    
    conn.commit()
    conn.close()

def create_json_data(num_patients=200):
    """Crée un fichier JSON avec des patients non structurés"""
    patients = [generate_patient() for _ in range(num_patients)]
    
    with open('data/raw/medical_data.json', 'w', encoding='utf-8') as f:
        json.dump({"patients": patients}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Création du dossier data/raw s'il n'existe pas
    import os
    os.makedirs('data/raw', exist_ok=True)
    
    # Génération des données
    create_sqlite_database()
    create_json_data()
    print("Données générées avec succès!") 