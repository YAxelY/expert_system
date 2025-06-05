import sqlite3
import json
import random
from datetime import datetime, timedelta
import os

# Définition des données médicales
SYMPTOMS = {
    "respiratoires": [
        "toux", "essoufflement", "congestion_nasale", "maux_de_gorge", "eternuements"
    ],
    "digestifs": [
        "nausees", "diarrhee", "vomissements", "douleurs_abdominales", "perte_appetit"
    ],
    "généraux": [
        "fièvre", "fatigue", "maux_de_tete", "douleurs_musculaires",
        "perte_gout_odorat", "frissons", "sueurs_nocturnes"
    ],
    "cutanés": [
        "eruption_cutanee", "demangeaisons", "rougeurs", "urticaire"
    ],
    "neurologiques": [
        "vertiges", "confusion", "troubles_vision", "engourdissements"
    ]
}

SYMPTOMS_FLAT = [item for sublist in SYMPTOMS.values() for item in sublist]

DISEASES = {
    "covid19": {
        "principaux": ["fièvre", "toux", "fatigue", "perte_gout_odorat"],
        "secondaires": ["maux_de_tete", "douleurs_musculaires", "maux_de_gorge"],
        "probabilite": 0.25
    },
    "grippe": {
        "principaux": ["fièvre", "toux", "fatigue", "douleurs_musculaires"],
        "secondaires": ["maux_de_tete", "congestion_nasale", "frissons"],
        "probabilite": 0.20
    },
    "rhume": {
        "principaux": ["congestion_nasale", "maux_de_gorge", "toux", "eternuements"],
        "secondaires": ["fatigue", "maux_de_tete"],
        "probabilite": 0.15
    },
    "gastro_enterite": {
        "principaux": ["nausees", "diarrhee", "vomissements"],
        "secondaires": ["fièvre", "douleurs_abdominales", "fatigue"],
        "probabilite": 0.12
    },
    "allergie": {
        "principaux": ["congestion_nasale", "demangeaisons", "eternuements"],
        "secondaires": ["toux", "rougeurs", "urticaire"],
        "probabilite": 0.10
    },
    "migraine": {
        "principaux": ["maux_de_tete", "nausees"],
        "secondaires": ["troubles_vision", "fatigue", "vertiges"],
        "probabilite": 0.08
    },
    "angine": {
        "principaux": ["maux_de_gorge", "fièvre"],
        "secondaires": ["fatigue", "douleurs_musculaires", "maux_de_tete"],
        "probabilite": 0.10
    }
}

MEDICATIONS = {
    "covid19": ["paracetamol", "ibuprofene", "vitamine_d"],
    "grippe": ["paracetamol", "ibuprofene", "oseltamivir"],
    "rhume": ["paracetamol", "phenylephrine", "chlorpheniramine"],
    "gastro_enterite": ["loperamide", "diosmectite", "paracetamol"],
    "allergie": ["cetirizine", "loratadine", "desloratadine"],
    "migraine": ["paracetamol", "ibuprofene", "sumatriptan"],
    "angine": ["paracetamol", "amoxicilline", "ibuprofene"]
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
        if random.random() < 0.85:  # 85% de chance
            symptoms.append(symptom)
    
    # Ajout des symptômes secondaires avec probabilité moyenne
    for symptom in DISEASES[disease]["secondaires"]:
        if random.random() < 0.45:  # 45% de chance
            symptoms.append(symptom)
    
    # Ajout possible de symptômes aléatoires (bruit dans les données)
    if random.random() < 0.15:  # 15% de chance d'avoir un symptôme supplémentaire
        other_symptoms = [s for s in SYMPTOMS_FLAT if s not in symptoms]
        if other_symptoms:
            symptoms.append(random.choice(other_symptoms))
    
    # S'assurer qu'il y a au moins un symptôme
    if not symptoms and disease in DISEASES:
        symptoms.append(random.choice(DISEASES[disease]["principaux"]))
    
    # Sélection des médicaments appropriés
    medications = MEDICATIONS.get(disease, ["paracetamol"]).copy()
    if len(medications) > 2:
        medications = random.sample(medications, random.randint(1, min(3, len(medications))))
    
    date = datetime.now() - timedelta(days=random.randint(0, 365))
    
    return {
        "age": age,
        "symptoms": symptoms,
        "diagnostic": disease,
        "medications": medications,
        "date_consultation": date.strftime("%Y-%m-%d")
    }

def create_sqlite_database(num_patients=1500):
    """Crée la base de données SQLite avec des patients structurés"""
    try:
        os.makedirs('data/raw', exist_ok=True)
        conn = sqlite3.connect('data/raw/medical_data.db')
        c = conn.cursor()
        
        # Suppression des tables existantes pour un redémarrage propre
        c.execute('DROP TABLE IF EXISTS medications')
        c.execute('DROP TABLE IF EXISTS symptoms')
        c.execute('DROP TABLE IF EXISTS patients')
        
        # Création des tables
        c.execute('''CREATE TABLE patients
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      age INTEGER NOT NULL,
                      diagnostic TEXT NOT NULL,
                      date_consultation TEXT NOT NULL)''')
        
        c.execute('''CREATE TABLE symptoms
                     (patient_id INTEGER NOT NULL,
                      symptom TEXT NOT NULL,
                      FOREIGN KEY(patient_id) REFERENCES patients(id))''')
        
        c.execute('''CREATE TABLE medications
                     (patient_id INTEGER NOT NULL,
                      medication TEXT NOT NULL,
                      FOREIGN KEY(patient_id) REFERENCES patients(id))''')