# Étape 1 : base Python légère
FROM python:3.8-slim

# Étape 2 : dossier de travail
WORKDIR /app

# Étape 3 : copier les fichiers
COPY requirements.txt .
COPY app.py .
COPY data_generator.py .
COPY static/ static/

# Étape 4 : dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Étape 5 : installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Étape 6 : créer dossier db (si manquant)
RUN mkdir -p data/raw

# Étape 7 : générer les données initiales
RUN python data_generator.py

# Étape 8 : variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8000

# Étape 9 : exposer le port
EXPOSE 8000

# Étape 10 : lancer Flask
CMD gunicorn --bind 0.0.0.0:$PORT app:app
