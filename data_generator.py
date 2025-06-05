import sqlite3
import json
import random
from datetime import datetime, timedelta
import os

# Définition des données médicales
SYMPTOMS = {
    "respiratoires": [
        "toux", "essoufflement", "congestion_nasale", "maux_de_gorge"
    ],
    "digestifs": [
        "nausees", "diarrhee", "vomissements", "douleurs_abdominales"
    ],
    "généraux": [
        "fièvre", "fatigue", "maux_de_tete", "douleurs_musculaires",
        "perte_gout_odorat", "frissons"
    ],
    "cutanés": [
        "eruption_cutanee", "demangeaisons", "rougeurs"
    ]
}

SYMPTOMS_FLAT = [item for sublist in SYMPTOMS.values() for item in sublist]

DISEASES = {
    "covid19": {
        "principaux": ["fièvre", "toux", "fatigue", "perte_gout_odorat"],
        "secondaires": ["maux_de_tete", "douleurs_musculaires"],
        "probabilite": 0.3
    },
    "grippe": {
        "principaux": ["fièvre", "toux", "fatigue", "douleurs_musculaires"],
        "secondaires": ["maux_de_tete", "congestion_nasale"],
        "probabilite": 0.25
    },
    "rhume": {
        "principaux": ["congestion_nasale", "maux_de_gorge", "toux"],
        "secondaires": ["fatigue", "maux_de_tete"],
        "probabilite": 0.2
    },
    "gastro_enterite": {
        "principaux": ["nausees", "diarrhee", "vomissements"],
        "secondaires": ["fièvre", "douleurs_abdominales"],
        "probabilite": 0.15
    },
    "allergie": {
        "principaux": ["congestion_nasale", "demangeaisons", "rougeurs"],
        "secondaires": ["toux", "fatigue"],
        "probabilite": 0.1
    }
}

MEDICATIONS = {
    "covid19": ["paracetamol", "ibuprofene", "azithromycine"],
    "grippe": ["paracetamol", "ibuprofene", "oseltamivir"],
    "rhume": ["paracetamol", "phenylephrine", "chlorpheniramine"],
    "gastro_enterite": ["loperamide", "diosmectite", "paracetamol"],
    "allergie": ["cetirizine", "loratadine", "desloratadine"]
}

def generate_patient():
    """Génère des données réalistes pour un patient"""
    age = random.randint(18, 85)
    
    # Sélection de la maladie basée sur les probabilités
    disease = random.choices(
        list(DISEASES.keys()),
        weights=[d["probabilite"] for d in DISEASES.values()]
    )[0]
    
    # Sélection des symptômes
    symptoms = []
    # Ajout des symptômes principaux avec forte probabilité
    for symptom in DISEASES[disease]["principaux"]:
        if random.random() < 0.8:  # 80% de chance
            symptoms.append(symptom)
    
    # Ajout des symptômes secondaires avec probabilité moyenne
    for symptom in DISEASES[disease]["secondaires"]:
        if random.random() < 0.4:  # 40% de chance
            symptoms.append(symptom)
    
    # Ajout possible de symptômes aléatoires
    if random.random() < 0.2:  # 20% de chance d'avoir un symptôme supplémentaire
        other_symptoms = [s for s in SYMPTOMS_FLAT if s not in symptoms]
        symptoms.append(random.choice(other_symptoms))
    
    # Sélection des médicaments appropriés
    medications = MEDICATIONS[disease].copy()
    if len(medications) > 2:
        medications = random.sample(medications, random.randint(1, len(medications)))
    
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
    os.makedirs('data/raw', exist_ok=True)
    conn = sqlite3.connect('data/raw/medical_data.db')
    c = conn.cursor()
    
    # Création des tables
    c.execute('''CREATE TABLE IF NOT EXISTS patients
                 (id INTEGER PRIMARY KEY,
                  age INTEGER,
                  diagnostic TEXT,
                  date_consultation TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS symptoms
                 (patient_id INTEGER,
                  symptom TEXT,
                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS medications
                 (patient_id INTEGER,
                  medication TEXT,
                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')
    
    # Génération des données
    for _ in range(num_patients):
        patient = generate_patient()
        
        c.execute('''INSERT INTO patients (age, diagnostic, date_consultation)
                     VALUES (?, ?, ?)''',
                  (patient['age'], patient['diagnostic'], patient['date_consultation']))
        patient_id = c.lastrowid
        
        for symptom in patient['symptoms']:
            c.execute('INSERT INTO symptoms VALUES (?, ?)',
                     (patient_id, symptom))
        
        for medication in patient['medications']:
            c.execute('INSERT INTO medications VALUES (?, ?)',
                     (patient_id, medication))
    
    conn.commit()
    conn.close()

def create_json_data(num_patients=200):
    """Crée un fichier JSON avec des patients non structurés"""
    os.makedirs('data/raw', exist_ok=True)
    patients = [generate_patient() for _ in range(num_patients)]
    
    with open('data/raw/medical_data.json', 'w', encoding='utf-8') as f:
        json.dump({"patients": patients}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("Génération des données...")
    create_sqlite_database()
    create_json_data()
    print("Données générées avec succès!")
