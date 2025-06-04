# Utilisation de Python 3.8 comme base
FROM python:3.8-slim

# Définition du répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Création du dossier data/raw avant la copie
RUN mkdir -p data/raw
# Copie des fichiers nécessaires
COPY requirements.txt .
COPY app.py .
COPY data/raw/medical_data.db ./data/raw/

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Variables d'environnement (optionnel)
ENV FLASK_ENV=production

# Exposition du port
EXPOSE 8000

# Commande de démarrage
CMD ["python", "app.py"]