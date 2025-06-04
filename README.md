# Système Expert Médical

Ce projet implémente un système expert médical sophistiqué utilisant des techniques de fouille de données et d'apprentissage automatique pour :
1. Analyser les symptômes des patients
2. Établir des diagnostics
3. Recommander des traitements
4. Apprendre en continu à partir des nouveaux cas

## Structure du projet

```
expert_system/
├── data/
│   ├── raw/          # Données brutes
│   └── processed/    # Données traitées et base SQLite
├── medical_expert.py # Classe principale du système expert
├── requirements.txt  # Dépendances Python
└── systeme_expert_medical.ipynb  # Notebook de démonstration
```

## Fonctionnalités

### 1. Gestion des données
- Base de données SQLite pour le stockage persistant
- Tables pour les patients, médicaments et règles d'association
- Support pour les données structurées et non structurées

### 2. Moteur d'inférence
- Utilisation de l'algorithme FP-Growth pour la découverte de motifs fréquents
- Génération de règles d'association avec support et confiance configurables
- Système de pondération des règles basé sur la fréquence et la récence

### 3. Apprentissage continu
- Mise à jour automatique des règles à chaque nouveau cas
- Adaptation dynamique des seuils de support et de confiance
- Conservation de l'historique des diagnostics pour l'amélioration continue

### 4. Visualisation
- Graphiques de distribution des règles d'association
- Statistiques sur la base de connaissances
- Interface utilisateur interactive dans le notebook

## Installation

1. Créer un environnement virtuel Python :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

1. Lancer Jupyter Notebook :
```bash
jupyter notebook
```

2. Ouvrir `systeme_expert_medical.ipynb`

3. Suivre les exemples dans le notebook pour :
   - Initialiser le système expert
   - Ajouter des cas d'exemple
   - Tester le diagnostic
   - Visualiser les règles d'association
   - Utiliser l'interface interactive

## Structure des données

### Table patients
- id : Identifiant unique
- age : Âge du patient
- gender : Genre du patient
- symptoms : Liste des symptômes (JSON)
- diagnosis : Diagnostic établi
- treatment : Traitement prescrit
- timestamp : Date et heure

### Table medications
- id : Identifiant unique
- name : Nom du médicament
- indications : Conditions traitées
- contraindications : Contre-indications
- side_effects : Effets secondaires

### Table rules
- id : Identifiant unique
- antecedents : Conditions préalables (symptômes)
- consequents : Conséquences (diagnostic)
- support : Support statistique
- confidence : Niveau de confiance
- lift : Mesure de l'intérêt de la règle
- timestamp : Date et heure de création

## Exemple d'utilisation

```python
from medical_expert import MedicalExpertSystem

# Création d'une instance
expert = MedicalExpertSystem()

# Diagnostic
symptoms = ['fièvre', 'toux', 'fatigue']
diagnosis, confidence = expert.diagnose(symptoms)

# Recommandation de traitement
if diagnosis:
    treatment = expert.recommend_treatment(diagnosis)
    print(f"Traitement recommandé : {treatment}")

# Apprentissage d'un nouveau cas
expert.learn(
    symptoms=['maux de tête', 'nausées'],
    diagnosis='migraine',
    treatment='ibuprofène',
    age=35,
    gender='F'
)
```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Forker le projet
2. Créer une branche pour votre fonctionnalité
3. Soumettre une pull request

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
