import os
import sqlite3
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from mlxtend.frequent_patterns import apriori, association_rules

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

DB_PATH = 'data/raw/medical_data.db'

def load_data():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError("❌ Base de données introuvable.")
    
    conn = sqlite3.connect(DB_PATH)
    patients = pd.read_sql("SELECT * FROM patients", conn)
    symptoms = pd.read_sql("SELECT * FROM symptoms", conn)
    medications = pd.read_sql("SELECT * FROM medications", conn)
    conn.close()

    symptoms_pivot = pd.crosstab(symptoms['patient_id'], symptoms['symptom'])
    medications_pivot = pd.crosstab(medications['patient_id'], medications['medication'])

    data = patients.merge(symptoms_pivot, left_on='id', right_index=True, how='left')
    data = data.merge(medications_pivot, left_on='id', right_index=True, how='left')
    data.fillna(0, inplace=True)
    data.iloc[:, 4:] = data.iloc[:, 4:].astype(int)
    return data

def extract_rules(data, min_support=0.05):
    features = [col for col in data.columns if col not in ['id', 'age', 'diagnostic', 'date_consultation']]
    frequent_itemsets = apriori(data[features], min_support=min_support, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)
    return rules

class ExpertSystem:
    def __init__(self, rules_df):
        self.rules_df = rules_df

    def diagnose(self, symptoms_list):
        input_set = set(symptoms_list)
        matches = self.rules_df[self.rules_df['antecedents'].apply(lambda ant: ant.issubset(input_set))]
        return matches.sort_values(by='confidence', ascending=False).head(5).to_dict(orient='records')

# Initialisation
expert = None
try:
    data = load_data()
    rules = extract_rules(data)
    expert = ExpertSystem(rules)
    print("✅ Système expert initialisé.")
except Exception as e:
    print("❌ Erreur à l'initialisation :", e)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/diagnose', methods=['POST'])
def diagnose():
    global expert
    if expert is None:
        return jsonify({"error": "Système non prêt"}), 500
    try:
        symptoms = request.json.get("symptoms", [])
        result = expert.diagnose(symptoms)
        return jsonify({"input": symptoms, "results": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add', methods=['POST'])
def add_case():
    data = request.json
    age = data.get("age")
    symptoms = data.get("symptoms", [])
    diagnosis = data.get("diagnostic")
    medications = data.get("medications", [])
    date_consult = data.get("date_consultation")

    if not (age and diagnosis and date_consult):
        return jsonify({"error": "Champs obligatoires manquants"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO patients (age, diagnostic, date_consultation) VALUES (?, ?, ?)", (age, diagnosis, date_consult))
    patient_id = c.lastrowid

    for s in symptoms:
        c.execute("INSERT INTO symptoms (patient_id, symptom) VALUES (?, ?)", (patient_id, s))
    for m in medications:
        c.execute("INSERT INTO medications (patient_id, medication) VALUES (?, ?)", (patient_id, m))

    conn.commit()
    conn.close()

    # Recharger les règles après ajout
    try:
        df = load_data()
        rules = extract_rules(df)
        global expert
        expert = ExpertSystem(rules)
    except Exception as e:
        return jsonify({"warning": f"Patient ajouté, mais erreur mise à jour des règles : {e}"}), 200

    return jsonify({"message": "✅ Cas ajouté avec succès."})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
