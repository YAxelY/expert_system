# Étape 1 : image de base avec Python
FROM python:3.10-slim

# Étape 2 : définir le répertoire de travail
WORKDIR /app

# Étape 3 : copier les fichiers de l'application
COPY . /app

# Étape 4 : installer les dépendances système (SQLite + pip utils)
RUN apt-get update && \
    apt-get install -y build-essential libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Étape 5 : installer les dépendances Python
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    pandas \
    mlxtend

# Étape 6 : exposer le port Flask
EXPOSE 5000

# Étape 7 : commande de démarrage
CMD ["python", "app.py"]
