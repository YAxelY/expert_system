import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import fpgrowth, apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sqlite3

app = Flask(__name__)
CORS(app)

def load_data():
    conn = sqlite3.connect('data/raw/medical_data.db')
    
    # Chargement des données
    patients_df = pd.read_sql_query("SELECT * FROM patients", conn)
    symptoms_df = pd.read_sql_query("SELECT * FROM symptoms", conn)
    medications_df = pd.read_sql_query("SELECT * FROM medications", conn)
    
    conn.close()
    
    # Préparation des données
    symptoms_pivot = pd.crosstab(symptoms_df['patient_id'], symptoms_df['symptom'])
    medications_pivot = pd.crosstab(medications_df['patient_id'], medications_df['medication'])
    
    final_df = patients_df.merge(symptoms_pivot, left_on='id', right_index=True)
    final_df = final_df.merge(medications_pivot, left_on='id', right_index=True)
    
    return final_df

def get_rules(data, min_support=0.1):
    symptom_cols = [col for col in data.columns if col not in ['id', 'age', 'diagnostic', 'date_consultation']]
    frequent_itemsets = apriori(data[symptom_cols], min_support=min_support, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)
    return rules

class ExpertSystem:
    def __init__(self, rules):
        self.rules = rules
    
    def diagnose(self, symptoms):
        relevant_rules = self.rules[self.rules['antecedents'].apply(
            lambda x: all(symptom in symptoms for symptom in x))]
        
        if len(relevant_rules) == 0:
            return []
        
        relevant_rules = relevant_rules.sort_values('confidence', ascending=False)
        return relevant_rules.head().to_dict('records')

# Initialisation du système
data = load_data()
rules = get_rules(data)
expert_system = ExpertSystem(rules)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/diagnose', methods=['POST'])
def diagnose():
    try:
        data = request.get_json()
        if not data or 'symptoms' not in data:
            return jsonify({"error": "Symptoms are required"}), 400
        
        symptoms = data['symptoms']
        if not isinstance(symptoms, list):
            return jsonify({"error": "Symptoms must be a list"}), 400
        
        diagnosis = expert_system.diagnose(symptoms)
        return jsonify({
            "symptoms": symptoms,
            "diagnosis": diagnosis
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)