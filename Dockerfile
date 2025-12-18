FROM python:3.11-slim

# On se place directement dans le dossier src
# Comme ça, le dossier 'app' est juste sous nos yeux
WORKDIR /app/src

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# PYTHONPATH pointant sur le dossier actuel (.)
ENV PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# On remonte d'un cran pour copier le requirements qui est à la racine
COPY requirements.txt ../
RUN pip install --no-cache-dir -r ../requirements.txt

# On copie tout le projet
COPY . ../

EXPOSE 8000

# On lance uvicorn depuis /app/src
# Donc le chemin devient simplement app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]