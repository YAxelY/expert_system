import sqlite3
import json
import random
from datetime import datetime, timedelta
import os

# Symptômes généraux + tropicaux
SYMPTOMS = [
    "fièvre", "toux", "fatigue", "maux_de_tete", "douleurs_musculaires",
    "nausees", "diarrhee", "essoufflement", "perte_gout_odorat",
    "eruption_cutanee", "maux_de_gorge", "congestion_nasale",
    "frissons", "vomissements", "douleurs_abdominales", "saignement",
    "jaunisse", "maux_de_ventre"
]

# Maladies incluant celles tropicales
DISEASES = [
    "covid19", "grippe", "rhume", "angine", "gastro_enterite",
    "bronchite", "allergie", "migraine", "infection_urinaire",
    "paludisme", "typhoide", "dengue", "chikungunya", "fievre_jaune"
]

# Médicaments usuels + tropicaux
MEDICATIONS = [
    "paracetamol", "ibuprofene", "amoxicilline", "omeprazole",
    "loratadine", "azithromycine", "doliprane", "aspirine",
    "artemether", "quinine", "chloroquine", "ciprofloxacine"
]

# Associations simples maladie → symptômes → médicaments
DISEASE_PROFILE = {
    "paludisme": {
        "symptoms": ["fièvre", "frissons", "maux_de_tete", "douleurs_musculaires", "vomissements"],
        "medications": ["artemether", "quinine"]
    },
    "typhoide": {
        "symptoms": ["fièvre", "diarrhee", "douleurs_abdominales", "jaunisse"],
        "medications": ["ciprofloxacine", "paracetamol"]
    },
    "dengue": {
        "symptoms": ["fièvre", "maux_de_tete", "saignement", "eruption_cutanee", "douleurs_musculaires"],
        "medications": ["paracetamol"]
    },
    "chikungunya": {
        "symptoms": ["fièvre", "douleurs_musculaires", "fatigue", "maux_de_tete"],
        "medications": ["paracetamol", "ibuprofene"]
    },
    "fievre_jaune": {
        "symptoms": ["fièvre", "jaunisse", "vomissements", "maux_de_ventre"],
        "medications": ["paracetamol"]
    }
}

def generate_patient():
    age = random.randint(1, 85)
    disease = random.choice(DISEASES)

    # Utilisation du profil si maladie tropicale
    if disease in DISEASE_PROFILE:
        base_symptoms = DISEASE_PROFILE[disease]["symptoms"]
        base_meds = DISEASE_PROFILE[disease]["medications"]
        symptoms = base_symptoms + random.sample([s for s in SYMPTOMS if s not in base_symptoms], random.randint(0, 2))
        medications = base_meds + random.sample([m for m in MEDICATIONS if m not in base_meds], random.randint(0, 1))
    else:
        symptoms = random.sample(SYMPTOMS, random.randint(2, 5))
        medications = random.sample(MEDICATIONS, random.randint(1, 3))

    date = datetime.now() - timedelta(days=random.randint(0, 365))

    return {
        "age": age,
        "symptoms": symptoms,
        "diagnostic": disease,
        "medications": medications,
        "date_consultation": date.strftime("%Y-%m-%d")
    }

def create_sqlite_database(num_patients=1000):
    conn = sqlite3.connect('data/raw/medical_data.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS patients
                 (id INTEGER PRIMARY KEY, age INTEGER, diagnostic TEXT, date_consultation TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS symptoms
                 (patient_id INTEGER, symptom TEXT,
                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS medications
                 (patient_id INTEGER, medication TEXT,
                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')

    for _ in range(num_patients):
        patient = generate_patient()
        c.execute('''INSERT INTO patients (age, diagnostic, date_consultation)
                     VALUES (?, ?, ?)''',
                  (patient['age'], patient['diagnostic'], patient['date_consultation']))
        patient_id = c.lastrowid

        for symptom in patient['symptoms']:
            c.execute('INSERT INTO symptoms VALUES (?, ?)', (patient_id, symptom))
        
        for medication in patient['medications']:
            c.execute('INSERT INTO medications VALUES (?, ?)', (patient_id, medication))
    
    conn.commit()
    conn.close()

def create_json_data(num_patients=200):
    patients = [generate_patient() for _ in range(num_patients)]
    with open('data/raw/medical_data.json', 'w', encoding='utf-8') as f:
        json.dump({"patients": patients}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    os.makedirs('data/raw', exist_ok=True)
    create_sqlite_database()
    create_json_data()
    print("✅ Données enrichies pour maladies tropicales générées avec succès !")
