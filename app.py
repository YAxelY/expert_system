import os
import sqlite3
import pandas as pd
import numpy as np
import json
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DB_PATH = 'data/raw/medical_data.db'

# Template HTML intégré
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Système Expert Médical</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding-top: 2rem;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .container {
            max-width: 900px;
        }
        .card {
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px 20px 0 0 !important;
            padding: 1.5rem;
        }
        .diagnosis-card {
            transition: all 0.3s ease;
            border-radius: 15px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
        }
        .diagnosis-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
        }
        .select2-container {
            width: 100% !important;
        }
        .select2-selection {
            border-radius: 10px !important;
            border: 2px solid #e9ecef !important;
            min-height: 45px !important;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        .loading {
            display: none;
            text-align: center;
            margin: 30px 0;
        }
        .loading-spinner {
            width: 4rem;
            height: 4rem;
            border: 4px solid rgba(102, 126, 234, 0.3);
            border-left-color: #667eea;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        #error-message {
            display: none;
            margin-top: 1rem;
            border-radius: 10px;
        }
        #results {
            display: none;
        }
        .progress {
            height: 8px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.3);
        }
        .progress-bar {
            background: linear-gradient(90deg, #00d4ff, #090979);
            border-radius: 10px;
        }
        .symptom-badge {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            color: #333;
            padding: 5px 12px;
            border-radius: 20px;
            margin: 3px;
            display: inline-block;
            font-size: 0.85rem;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card mb-4">
            <div class="card-header text-center">
                <h1 class="mb-0">🏥 Système Expert Médical</h1>
                <p class="mb-0 mt-2 opacity-75">Diagnostic intelligent basé sur vos symptômes</p>
            </div>
            <div class="card-body p-4">
                <form id="diagnosis-form">
                    <div class="mb-4">
                        <label for="symptoms" class="form-label h5">
                            <i class="bi bi-clipboard2-pulse-fill"></i> Sélectionnez vos symptômes :
                        </label>
                        <select class="form-control" id="symptoms" multiple="multiple">
                            <!-- Les options seront ajoutées dynamiquement -->
                        </select>
                        <div class="form-text">Vous pouvez sélectionner plusieurs symptômes pour un diagnostic plus précis.</div>
                    </div>
                    <div class="text-center">
                        <button type="submit" class="btn btn-primary btn-lg">
                            🔍 Obtenir un diagnostic
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <div id="loading" class="loading">
            <div class="spinner-border loading-spinner" role="status">
                <span class="visually-hidden">Chargement...</span>
            </div>
            <p class="mt-3 h5">🤖 Analyse des symptômes en cours...</p>
            <p class="text-muted">Notre IA analyse vos symptômes pour vous proposer des diagnostics possibles</p>
        </div>

        <div id="error-message" class="alert alert-danger" role="alert">
            <!-- Le message d'erreur sera inséré ici -->
        </div>

        <div id="results">
            <div class="card">
                <div class="card-header">
                    <h2 class="mb-0">📋 Diagnostics possibles</h2>
                </div>
                <div class="card-body">
                    <div id="selected-symptoms" class="mb-3">
                        <strong>Symptômes analysés :</strong>
                        <div id="symptoms-display"></div>
                    </div>
                    <div id="diagnoses" class="row">
                        <!-- Les résultats seront insérés ici -->
                    </div>
                    <div class="alert alert-warning mt-3" role="alert">
                        <strong>⚠️ Avertissement :</strong> Ce système est à des fins éducatives uniquement. 
                        Consultez toujours un professionnel de santé pour un diagnostic médical approprié.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
    <script>
        $(document).ready(function() {
            // Initialisation de Select2
            $('#symptoms').select2({
                placeholder: 'Choisissez un ou plusieurs symptômes',
                allowClear: true,
                theme: 'bootstrap-5'
            });

            // Chargement des symptômes
            $.get('/api/symptoms')
                .done(function(symptoms) {
                    symptoms.forEach(function(symptom) {
                        $('#symptoms').append(new Option(symptom.replace('_', ' '), symptom));
                    });
                })
                .fail(function(error) {
                    showError("Erreur lors du chargement des symptômes");
                });

            // Gestion du formulaire
            $('#diagnosis-form').on('submit', function(e) {
                e.preventDefault();
                
                const symptoms = $('#symptoms').val();
                if (!symptoms || symptoms.length === 0) {
                    showError("Veuillez sélectionner au moins un symptôme");
                    return;
                }

                // Réinitialisation et affichage du chargement
                $('#results').hide();
                $('#error-message').hide();
                $('#loading').show();

                // Envoi de la requête
                $.ajax({
                    url: '/api/diagnose',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ symptoms: symptoms }),
                    success: function(response) {
                        $('#loading').hide();
                        displayResults(response);
                    },
                    error: function(xhr) {
                        $('#loading').hide();
                        const error = xhr.responseJSON ? xhr.responseJSON.error : "Erreur lors du diagnostic";
                        showError(error);
                    }
                });
            });

            function displayResults(response) {
                const diagnosesContainer = $('#diagnoses');
                const symptomsDisplay = $('#symptoms-display');
                
                diagnosesContainer.empty();
                symptomsDisplay.empty();

                // Affichage des symptômes sélectionnés
                response.symptoms.forEach(function(symptom) {
                    symptomsDisplay.append(`<span class="symptom-badge">${symptom.replace('_', ' ')}</span>`);
                });

                // Affichage des diagnostics
                if (response.diagnoses && response.diagnoses.length > 0) {
                    response.diagnoses.forEach(function(diagnosis, index) {
                        const confidenceColor = diagnosis.probability > 70 ? 'success' : 
                                              diagnosis.probability > 40 ? 'warning' : 'info';
                        
                        const card = $(`
                            <div class="col-md-4 mb-3">
                                <div class="card diagnosis-card h-100">
                                    <div class="card-body text-center">
                                        <h5 class="card-title mb-3">
                                            ${index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'} 
                                            ${diagnosis.diagnostic.replace('_', ' ').toUpperCase()}
                                        </h5>
                                        <div class="progress mb-3">
                                            <div class="progress-bar" role="progressbar" 
                                                 style="width: ${diagnosis.probability}%" 
                                                 aria-valuenow="${diagnosis.probability}" 
                                                 aria-valuemin="0" 
                                                 aria-valuemax="100">
                                            </div>
                                        </div>
                                        <h4 class="text-white mb-2">${diagnosis.probability}%</h4>
                                        <p class="card-text opacity-75">
                                            Probabilité de correspondance
                                        </p>
                                    </div>
                                </div>
                            </div>
                        `);
                        diagnosesContainer.append(card);
                    });
                } else {
                    diagnosesContainer.append(`
                        <div class="col-12">
                            <div class="alert alert-info text-center">
                                <h5>🤔 Aucun diagnostic trouvé</h5>
                                <p>Désolé, nous n'avons pas pu établir de diagnostic avec ces symptômes. 
                                Veuillez consulter un professionnel de santé.</p>
                            </div>
                        </div>
                    `);
                }

                $('#results').show();
            }

            function showError(message) {
                $('#error-message')
                    .html(`<strong>❌ Erreur :</strong> ${message}`)
                    .show();
            }
        });
    </script>
</body>
</html>
'''

def generate_medical_data():
    """Génère des données médicales d'exemple pour le système expert"""
    logger.info("Génération des données médicales...")
    
    # Définition des diagnostics et leurs symptômes associés
    medical_data = {
        'grippe': ['fievre', 'toux', 'fatigue', 'courbatures', 'mal_de_tete', 'frissons'],
        'rhume': ['toux', 'nez_bouche', 'eternuements', 'mal_de_gorge', 'fatigue_legere'],
        'angine': ['mal_de_gorge', 'fievre', 'difficulte_deglutition', 'ganglions_gonfles'],
        'bronchite': ['toux_persistante', 'expectorations', 'essoufflement', 'douleur_thoracique'],
        'pneumonie': ['fievre_elevee', 'toux', 'essoufflement', 'douleur_thoracique', 'fatigue'],
        'gastro_enterite': ['nausees', 'vomissements', 'diarrhee', 'douleur_abdominale', 'fievre'],
        'migraine': ['mal_de_tete_intense', 'nausees', 'sensibilite_lumiere', 'vomissements'],
        'allergie': ['eternuements', 'yeux_rouges', 'nez_bouche', 'demangeaisons', 'toux_seche'],
        'hypertension': ['mal_de_tete', 'vertiges', 'vision_floue', 'fatigue', 'essoufflement'],
        'diabete': ['soif_excessive', 'urination_frequente', 'fatigue', 'vision_floue', 'cicatrisation_lente']
    }
    
    # Génération des patients
    patients = []
    symptoms_records = []
    
    for i in range(1000):  # 1000 patients d'exemple
        # Sélection aléatoire d'un diagnostic
        diagnostic = random.choice(list(medical_data.keys()))
        symptoms_list = medical_data[diagnostic]
        
        # Sélection de 2-5 symptômes pour ce patient
        num_symptoms = random.randint(2, min(5, len(symptoms_list)))
        patient_symptoms = random.sample(symptoms_list, num_symptoms)
        
        # Ajout de quelques symptômes "parasites" parfois
        if random.random() < 0.2:  # 20% de chance
            all_symptoms = set()
            for symp_list in medical_data.values():
                all_symptoms.update(symp_list)
            other_symptoms = list(all_symptoms - set(symptoms_list))
            if other_symptoms:
                patient_symptoms.append(random.choice(other_symptoms))
        
        # Création du patient
        patient = {
            'id': i + 1,
            'age': random.randint(18, 80),
            'diagnostic': diagnostic,
            'symptoms_list': patient_symptoms
        }
        patients.append(patient)
        
        # Création des enregistrements de symptômes pour SQLite
        for symptom in patient_symptoms:
            symptoms_records.append({
                'patient_id': i + 1,
                'symptom': symptom
            })
    
    return patients, symptoms_records

def create_sqlite_database():
    """Crée et remplit la base de données SQLite"""
    try:
        logger.info("Création de la base de données SQLite...")
        
        # Création du répertoire si nécessaire
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Génération des données
        patients, symptoms_records = generate_medical_data()
        
        # Connexion à SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Création des tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY,
                age INTEGER NOT NULL,
                diagnostic TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptoms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                symptom TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Insertion des patients
        for patient in patients:
            cursor.execute(
                'INSERT INTO patients (id, age, diagnostic) VALUES (?, ?, ?)',
                (patient['id'], patient['age'], patient['diagnostic'])
            )
        
        # Insertion des symptômes
        for symptom_record in symptoms_records:
            cursor.execute(
                'INSERT INTO symptoms (patient_id, symptom) VALUES (?, ?)',
                (symptom_record['patient_id'], symptom_record['symptom'])
            )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Base de données SQLite créée avec {len(patients)} patients")
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de la base SQLite: {str(e)}")
        raise

def create_json_data():
    """Crée un fichier JSON avec des données supplémentaires"""
    try:
        logger.info("Création des données JSON...")
        
        # Génération de données supplémentaires
        patients, _ = generate_medical_data()
        
        # Formatage pour JSON
        json_data = {
            "patients": [
                {
                    "id": patient['id'],
                    "age": patient['age'],
                    "diagnostic": patient['diagnostic'],
                    "symptoms": patient['symptoms_list']
                }
                for patient in patients[:500]  # Seulement 500 pour le JSON
            ],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_patients": 500,
                "data_source": "generated"
            }
        }
        
        # Sauvegarde
        json_path = 'data/raw/medical_data.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Fichier JSON créé: {json_path}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du JSON: {str(e)}")
        raise

def load_data():
    """Charge les données depuis SQLite et JSON"""
    try:
        # Vérification de l'existence du fichier de base de données
        if not os.path.exists(DB_PATH):
            logger.warning("Base de données non trouvée, génération des données...")
            create_sqlite_database()
            create_json_data()
        
        # Connexion SQLite
        conn = sqlite3.connect(DB_PATH)
        
        # Chargement des données SQLite
        patients_df = pd.read_sql_query("""
            SELECT p.*, GROUP_CONCAT(s.symptom) as symptoms_list
            FROM patients p
            LEFT JOIN symptoms s ON p.id = s.patient_id
            GROUP BY p.id
        """, conn)
        
        # Conversion des symptômes en liste
        patients_df['symptoms_list'] = patients_df['symptoms_list'].apply(
            lambda x: x.split(',') if isinstance(x, str) else []
        )
        
        conn.close()
        
        # Chargement des données JSON si disponible
        json_path = 'data/raw/medical_data.json'
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            json_df = pd.json_normalize(json_data['patients'])
            json_df = json_df.rename(columns={'symptoms': 'symptoms_list'})
            
            # Fusion des données
            combined_data = pd.concat([
                patients_df[['age', 'diagnostic', 'symptoms_list']],
                json_df[['age', 'diagnostic', 'symptoms_list']]
            ], ignore_index=True)
        else:
            combined_data = patients_df
        
        logger.info(f"Données chargées avec succès: {len(combined_data)} entrées")
        return combined_data
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données: {str(e)}")
        return None

def calculate_diagnosis(symptoms, data):
    """Calcule le diagnostic le plus probable basé sur les symptômes"""
    try:
        # Filtrage des cas avec des symptômes similaires
        matching_cases = data[data['symptoms_list'].apply(
            lambda x: any(symptom in x for symptom in symptoms) if isinstance(x, list) else False
        )]
        
        if len(matching_cases) == 0:
            logger.warning(f"Aucun cas trouvé pour les symptômes: {symptoms}")
            return None
        
        # Calcul des scores pour chaque diagnostic
        diagnosis_scores = {}
        for _, case in matching_cases.iterrows():
            diagnosis = case['diagnostic']
            case_symptoms = set(case['symptoms_list']) if isinstance(case['symptoms_list'], list) else set()
            input_symptoms = set(symptoms)
            
            # Calcul de la similarité (coefficient de Jaccard)
            intersection = len(case_symptoms.intersection(input_symptoms))
            union = len(case_symptoms.union(input_symptoms))
            similarity = intersection / union if union > 0 else 0
            
            if diagnosis not in diagnosis_scores:
                diagnosis_scores[diagnosis] = []
            diagnosis_scores[diagnosis].append(similarity)
        
        # Calcul des scores moyens
        average_scores = {
            diagnosis: sum(scores) / len(scores)
            for diagnosis, scores in diagnosis_scores.items()
        }
        
        # Tri des diagnostics par score
        sorted_diagnoses = sorted(
            average_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Retourne les 3 meilleurs diagnostics avec leurs scores
        results = [
            {"diagnostic": diag, "probability": round(score * 100, 2)}
            for diag, score in sorted_diagnoses[:3]
            if score > 0.1  # Seuil minimal de 10%
        ]
        
        logger.info(f"Diagnostic calculé avec succès: {results}")
        return results
    
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic: {str(e)}")
        return None

# Initialisation des données
data = None
try:
    logger.info("Initialisation du système expert médical...")
    data = load_data()
    if data is None:
        raise RuntimeError("Échec du chargement initial des données")
    logger.info("✅ Système expert initialisé avec succès.")
except Exception as e:
    logger.error(f"Erreur critique lors du démarrage: {str(e)}")

# Routes
@app.route('/')
def home():
    """Page d'accueil"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Endpoint de santé pour le monitoring"""
    try:
        # Vérification de la connexion à la base de données
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            conn.close()
            return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
        else:
            return jsonify({"status": "unhealthy", "error": "Database not found"}), 500
    except Exception as e:
        logger.error(f"Échec du health check: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    """Retourne la liste des symptômes possibles"""
    try:
        if data is None:
            raise ValueError("Données non disponibles")
        
        # Extraction de tous les symptômes uniques
        all_symptoms = set()
        for symptoms in data['symptoms_list']:
            if isinstance(symptoms, list):
                all_symptoms.update(symptoms)
        
        return jsonify(sorted(list(all_symptoms)))
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des symptômes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    """Endpoint de diagnostic"""
    try:
        if data is None:
            return jsonify({"error": "Système non initialisé"}), 500
        
        # Vérification des données d'entrée
        request_data = request.get_json()
        if not request_data or 'symptoms' not in request_data:
            return jsonify({"error": "Symptoms are required"}), 400
        
        symptoms = request_data['symptoms']
        if not isinstance(symptoms, list) or len(symptoms) == 0:
            return jsonify({"error": "Symptoms must be a non-empty list"}), 400
        
        # Calcul du diagnostic
        diagnosis = calculate_diagnosis(symptoms, data)
        
        return jsonify({
            "symptoms": symptoms,
            "diagnoses": diagnosis if diagnosis else [],
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)