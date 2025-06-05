# Utilisation d'une image Python légère
FROM python:3.9-slim

# Définition du répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY app.py .
COPY data_generator.py .

# Création du répertoire pour les données
RUN mkdir -p data/raw

# Variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Génération des données initiales
RUN python data_generator.py

# Exposition du port
EXPOSE $PORT

# Healthcheck pour vérifier la santé de l'application
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Commande de démarrage avec Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT \
    --workers=2 \
    --timeout=120 \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=- \
    app:app