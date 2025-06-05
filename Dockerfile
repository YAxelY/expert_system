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

# Étape 6 : vérifier les versions installées
RUN pip freeze

# Étape 7 : créer dossier db (si manquant)
RUN mkdir -p data/raw

# Étape 8 : générer les données initiales
RUN python data_generator.py

# Étape 9 : variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Étape 10 : exposer le port
EXPOSE 8000

# Étape 11 : healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Étape 12 : lancer Flask
CMD gunicorn --bind 0.0.0.0:$PORT \
    --workers=2 \
    --timeout=120 \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=- \
    app:app
