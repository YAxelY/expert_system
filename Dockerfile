# Étape 1 : image de base
FROM python:3.10-slim

# Étape 2 : répertoire de travail
WORKDIR /app

# Étape 3 : copier les fichiers de l'application
COPY . .

# Étape 4 : dépendances système
RUN apt-get update && apt-get install -y build-essential libsqlite3-dev && rm -rf /var/lib/apt/lists/*

# Étape 5 : installer les packages Python
RUN pip install --no-cache-dir flask flask-cors pandas mlxtend

# Étape 6 : créer le dossier pour la DB si manquant
RUN mkdir -p data/raw

# Étape 7 : exposer le port Flask
EXPOSE 5000

# Étape 8 : lancer l'application
CMD ["python", "app.py"]
