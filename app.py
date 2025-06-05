import os
import sqlite3
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from mlxtend.frequent_patterns import apriori, association_rules
import json
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

DB_PATH = 'data/raw/medical_data.db'

def load_data():
    """Charge les données depuis SQLite et JSON"""
    try:
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
        
        # Chargement des données JSON
        with open('data/raw/medical_data.json', 'r') as f:
            json_data = json.load(f)
        
        # Création d'un DataFrame à partir des données JSON
        json_df = pd.json_normalize(json_data['patients'])
        
        # Fusion des données
        combined_data = pd.concat([
            patients_df[['age', 'diagnostic', 'symptoms_list']],
            json_df[['age', 'diagnostic', 'symptoms']]
        ], ignore_index=True)
        
        # Uniformisation des noms de colonnes
        combined_data = combined_data.rename(columns={'symptoms': 'symptoms_list'})
        
        logger.info(f"Données chargées avec succès: {len(combined_data)} entrées")
        return combined_data
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données: {str(e)}")
        return None

def extract_rules(data, min_support=0.05):
    features = [col for col in data.columns if col not in ['id', 'age', 'diagnostic', 'date_consultation']]
    frequent_itemsets = apriori(data[features], min_support=min_support, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)
    print(f"🔢 Règles extraites : {len(rules)}")
    return rules

class ExpertSystem:
    def __init__(self, rules_df):
        self.rules_df = rules_df if rules_df is not None else pd.DataFrame()

    def diagnose(self, symptoms_list):
        if self.rules_df.empty:
            raise ValueError("Aucune règle disponible pour diagnostiquer.")

        input_set = set(symptoms_list)
        try:
            matches = self.rules_df[
                self.rules_df['antecedents'].apply(lambda ant: isinstance(ant, frozenset) and ant.issubset(input_set))
            ]
            return matches.sort_values(by='confidence', ascending=False).head(5).to_dict(orient='records')
        except Exception as e:
            raise RuntimeError(f"Erreur pendant le diagnostic : {e}")

# Initialisation du système expert
expert = None
try:
    logger.info("Chargement initial des données...")
    data = load_data()
    if data is None:
        raise RuntimeError("Échec du chargement initial des données")
    rules = extract_rules(data)
    expert = ExpertSystem(rules)
    print("✅ Système expert initialisé avec succès.")
except Exception as e:
    logger.error(f"Erreur critique lors du démarrage: {str(e)}")
    raise

# Routes
@app.route('/')
def home():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Endpoint de santé pour le monitoring"""
    try:
        # Vérification de la connexion à la base de données
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Échec du health check: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    """Retourne la liste des symptômes possibles"""
    try:
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
        # Vérification des données d'entrée
        request_data = request.get_json()
        if not request_data or 'symptoms' not in request_data:
            return jsonify({"error": "Symptoms are required"}), 400
        
        symptoms = request_data['symptoms']
        if not isinstance(symptoms, list) or len(symptoms) == 0:
            return jsonify({"error": "Symptoms must be a non-empty list"}), 400
        
        # Calcul du diagnostic
        diagnosis = calculate_diagnosis(symptoms, data)
        if diagnosis is None:
            return jsonify({
                "error": "Unable to make a diagnosis with the given symptoms"
            }), 400
        
        return jsonify({
            "symptoms": symptoms,
            "diagnoses": diagnosis,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic: {str(e)}")
        return jsonify({"error": str(e)}), 500

def calculate_diagnosis(symptoms, data):
    """Calcule le diagnostic le plus probable basé sur les symptômes"""
    try:
        # Filtrage des cas avec des symptômes similaires
        matching_cases = data[data['symptoms_list'].apply(
            lambda x: any(symptom in x for symptom in symptoms)
        )]
        
        if len(matching_cases) == 0:
            logger.warning(f"Aucun cas trouvé pour les symptômes: {symptoms}")
            return None
        
        # Calcul des scores pour chaque diagnostic
        diagnosis_scores = {}
        for _, case in matching_cases.iterrows():
            diagnosis = case['diagnostic']
            case_symptoms = set(case['symptoms_list'])
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
