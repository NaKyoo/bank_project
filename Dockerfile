# on utilise une image de base Python alléger
FROM python:3.13-slim AS build-stage

# on définit le dossier de travail
WORKDIR /app

# empêche Python d'écrire des fichiers .pyc inutiles dans le conteneur
ENV PYTHONDONTWRITEBYTECODE=1

# force Python à afficher les logs en temps réel
ENV PYTHONUNBUFFERED=1
# indique à Python où chercher tes modules (ton code) pour éviter les erreurs d'importation
ENV PYTHONPATH=/app

# installe les outils système nécessaires à la compilation de certaines bibliothèques Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# copie la listes des dépendances Python et les installe
COPY requirements.txt ../
RUN pip install --no-cache-dir -r ../requirements.txt

# copie l'intégralité de ton code source dans le conteneur
COPY . .

# Docs stage

FROM build-stage AS doc-stage
# Installation de l'outil de documentation
RUN pip install --no-cache-dir pdoc
# On s'assure que src est un package Python (crée __init__.py si absent)
RUN touch src/__init__.py
# On génère la doc du dossier 'src' vers '/app/docs/out'
RUN pdoc src -o /app/docs/out

FROM build-stage AS final
# expose le port sur lequel l'application va tourner
EXPOSE 8000

# commande pour lancer l'application avec Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]