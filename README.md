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

##################################################

Sécurité : Générer un SBOM (Software Bill of Materials)

Pour générer un inventaire complet des composants (utile pour la sécurité et la conformité) :

1.  Activer l'environnement virtuel.
2.  Lancer la commande :
    ```bash
    cyclonedx-py environment --output-file sbom.xml
    ```
    Cela crée `sbom.xml` à la racine.

##################################################

Comprendre le CI/CD (.github/workflows/ci-backend.yml)

Ce projet utilise GitHub Actions pour l'intégration continue.

- **`actions/checkout@v4`** : Cette action "clone" votre code dans l'environnement de test de GitHub. Le `@v4` spécifie la version de l'action à utiliser. Il est crucial de fixer une version (ex: v4) pour éviter que votre pipeline ne casse si l'action change radicalement dans une version future (v5, v6...).
- **`actions/setup-python@v5`** : Prépare Python dans l'environnement CI.
- **Workflow** : À chaque `push`, GitHub installe les dépendances, lance les tests (`pytest`), et crée une Issue si ça échoue.

