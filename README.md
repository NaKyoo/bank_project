# Bank Project — Mini FastAPI template

##################################################

BIEN UTILISEZ CMD ET PAS POWERSHELL

##################################################

Avant de commencer (une seule fois par poste)

1. Créer l'environnement virtuel et l'activer (cmd) :

```
python -m venv env
env\Scripts\activate.bat
```

2. Installer les dépendances (verrouillées pour reproductibilité) :

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Lancer le projet

```
run.bat        # lance sur le port 8000
run.bat 5000   # lance sur le port 5000
```

Règles simples pour le travail en équipe

- Ne commitez jamais `env/` (il est listé dans `.gitignore`).

Reproductibilité

- Les versions des dépendances sont verrouillées dans `requirements.txt`. Si quelqu'un doit mettre à jour une dépendance, ouvrez une PR et documentez le changement dans la description.

Dépannage rapide

- ModuleNotFoundError: `app.main` — lance `run.bat` depuis la racine du repo et vérifie que `src\app` existe.
- fastapi / uvicorn absents — activez le venv et réinstallez `pip install -r requirements.txt`.
- Port occupé — changez de port : `run.bat 5001`.

