import pandas as pd
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from mlxtend.frequent_patterns import apriori, association_rules
from flask import Flask, request, jsonify


app = Flask(__name__)
CORS(app)

def load_data():
    conn = sqlite3.connect('data/raw/medical_data.db')
    patients = pd.read_sql("SELECT * FROM patients", conn)
    symptoms = pd.read_sql("SELECT * FROM symptoms", conn)
    medications = pd.read_sql("SELECT * FROM medications", conn)
    conn.close()

    symptoms_pivot = pd.crosstab(symptoms['patient_id'], symptoms['symptom'])
    medications_pivot = pd.crosstab(medications['patient_id'], medications['medication'])

    data = patients.merge(symptoms_pivot, left_on='id', right_index=True)
    data = data.merge(medications_pivot, left_on='id', right_index=True)
    return data

def extract_rules(data, min_support=0.1):
    cols = [col for col in data.columns if col not in ['id', 'age', 'diagnostic', 'date_consultation']]
    frequent_itemsets = apriori(data[cols], min_support=min_support, use_colnames=True)
    return association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)

class ExpertSystem:
    def __init__(self, rules):
        self.rules = rules

    def diagnose(self, input_symptoms):
        matching = self.rules[self.rules['antecedents'].apply(
            lambda ant: all(sym in input_symptoms for sym in ant))]
        return matching.sort_values(by='confidence', ascending=False).head().to_dict(orient='records')

data = load_data()
rules = extract_rules(data)
expert = ExpertSystem(rules)


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/diagnose', methods=['POST'])
def diagnose():
    content = request.get_json()
    if not content or 'symptoms' not in content:
        return jsonify({"error": "No symptoms provided"}), 400
    result = expert.diagnose(content['symptoms'])
    return jsonify({"input": content['symptoms'], "results": result})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
