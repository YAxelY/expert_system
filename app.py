import os
import pandas as pd
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from mlxtend.frequent_patterns import apriori, association_rules

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)


def load_data():
    db_path = 'data/raw/medical_data.db'
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    
    conn = sqlite3.connect(db_path)

    try:
        patients = pd.read_sql("SELECT * FROM patients", conn)
        symptoms = pd.read_sql("SELECT * FROM symptoms", conn)
        medications = pd.read_sql("SELECT * FROM medications", conn)
    except Exception as e:
        conn.close()
        raise RuntimeError(f"Erreur lors de la lecture des tables : {e}")
    
    conn.close()

    # One-hot encoding
    symptoms_pivot = pd.crosstab(symptoms['patient_id'], symptoms['symptom'])
    medications_pivot = pd.crosstab(medications['patient_id'], medications['medication'])

    data = patients.merge(symptoms_pivot, left_on='id', right_index=True, how='left')
    data = data.merge(medications_pivot, left_on='id', right_index=True, how='left')
    data.fillna(0, inplace=True)
    data.iloc[:, 4:] = data.iloc[:, 4:].astype(int)

    return data


def extract_rules(data, min_support=0.1):
    features = [col for col in data.columns if col not in ['id', 'age', 'diagnostic', 'date_consultation']]
    frequent_itemsets = apriori(data[features], min_support=min_support, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)
    return rules


class ExpertSystem:
    def __init__(self, rules_df):
        self.rules_df = rules_df

    def diagnose(self, input_symptoms):
        input_set = set(input_symptoms)
        matches = self.rules_df[self.rules_df['antecedents'].apply(lambda ant: ant.issubset(input_set))]
        return matches.sort_values(by='confidence', ascending=False).head(5).to_dict(orient='records')


# Chargement des règles
try:
    data = load_data()
    rules = extract_rules(data)
    expert = ExpertSystem(rules)
    print("✅ Données chargées et règles extraites.")
except Exception as e:
    expert = None
    print("❌ Échec du chargement :", e)


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


@app.route('/diagnose', methods=['POST'])
def diagnose():
    if expert is None:
        return jsonify({"error": "Le système expert n'est pas prêt."}), 500

    content = request.get_json()
    if not content or 'symptoms' not in content:
        return jsonify({"error": "Liste de symptômes non fournie."}), 400

    try:
        symptoms = content['symptoms']
        if not isinstance(symptoms, list):
            raise ValueError("Le champ 'symptoms' doit être une liste.")
        result = expert.diagnose(symptoms)
        return jsonify({"input": symptoms, "results": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
