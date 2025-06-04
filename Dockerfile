# Étape 1 : image de base
FROM python:3.10-slim

# Étape 2 : répertoire de travail
WORKDIR /app

# Étape 3 : copier l'app
COPY . /app

# Étape 4 : dépendances système
RUN apt-get update && \
    apt-get install -y build-essential libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Étape 5 : dépendances Python
RUN pip install --no-cache-dir \
    flask flask-cors pandas mlxtend faker

# Étape 6 : créer la base SQLite à la build
RUN python setup_db.py

# Étape 7 : exposer le port
EXPOSE 5000

# Étape 8 : démarrer l'app Flask
CMD ["python", "app.py"]
