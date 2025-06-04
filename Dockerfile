# Étape 1 : image de base
FROM python:3.10-slim

# Étape 2 : répertoire de travail
WORKDIR /app

# Étape 3 : copier les fichiers
COPY . /app

# Étape 4 : installer dépendances système
RUN apt-get update && \
    apt-get install -y build-essential libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Étape 5 : installer les paquets Python
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    pandas \
    mlxtend

# Étape 6 : exposer le port Flask
EXPOSE 5000

# Étape 7 : lancer l'application
CMD ["python", "app.py"]
