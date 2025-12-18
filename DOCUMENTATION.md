# 📚 Documentation Automatique - Bank Project API

## 🎯 Génération de la Documentation

Ce projet est entièrement documenté avec des **docstrings Python** conformes aux standards **Google Style** et **NumPy Style**. Vous pouvez générer automatiquement une documentation HTML professionnelle.

---

## 🛠️ Outils de Génération de Documentation

### Option 1 : Sphinx (Recommandé)

**Sphinx** est l'outil standard pour générer de la documentation Python.

#### Installation

```bash
pip install sphinx sphinx-rtd-theme
```

#### Configuration

1. **Initialiser Sphinx** :
   ```bash
   cd docs
   sphinx-quickstart
   ```

2. **Configurer `conf.py`** :
   ```python
   import os
   import sys
   sys.path.insert(0, os.path.abspath('../src'))
   
   extensions = [
       'sphinx.ext.autodoc',
       'sphinx.ext.napoleon',  # Pour les docstrings Google/NumPy
       'sphinx.ext.viewcode',
   ]
   
   html_theme = 'sphinx_rtd_theme'
   ```

3. **Générer la documentation** :
   ```bash
   sphinx-apidoc -o docs/source src/app
   sphinx-build -b html docs/source docs/build
   ```

4. **Voir la documentation** :
   ```bash
   # Ouvrir docs/build/index.html dans un navigateur
   ```

---

### Option 2 : pdoc3 (Simple et Rapide)

**pdoc3** génère automatiquement de la documentation sans configuration.

#### Installation

```bash
pip install pdoc3
```

#### Génération

```bash
# Documentation HTML
pdoc --html --output-dir docs src/app

# Serveur de documentation en direct
pdoc --http localhost:8080 src/app
```

---

### Option 3 : MkDocs (Documentation Moderne)

**MkDocs** crée une documentation élégante avec support Markdown.

#### Installation

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

#### Configuration (`mkdocs.yml`)

```yaml
site_name: Bank Project API Documentation
theme:
  name: material
  palette:
    primary: indigo
    accent: indigo

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
            
nav:
  - Accueil: index.md
  - API Reference:
    - Main: reference/main.md
    - Controllers: reference/controllers.md
    - Models: reference/models.md
    - Services: reference/services.md
```

#### Génération

```bash
mkdocs serve  # Serveur de développement
mkdocs build  # Build de production
```

---

## 📖 Structure de la Documentation

Tous les fichiers Python du projet contiennent :

### 1. **Docstrings de Module**
Chaque fichier `.py` commence par une docstring décrivant :
- Le but du module
- Les fonctionnalités principales
- Des exemples d'utilisation
- L'auteur et la version

### 2. **Docstrings de Fonction**
Chaque fonction est documentée avec :
- Description détaillée
- Paramètres (`Args`)
- Valeur de retour (`Returns`)
- Exceptions levées (`Raises`)
- Exemples d'utilisation (`Example`)
- Notes importantes (`Note`)

### 3. **Commentaires Inline**
Le code contient des commentaires expliquant :
- La logique complexe
- Les décisions de conception
- Les cas particuliers

---

## 🎨 Exemple de Docstring

```python
def transfer(session: Session, from_acc: str, to_acc: str, amount: Decimal):
    """
    Effectue un transfert entre deux comptes bancaires.
    
    Cette fonction vérifie la validité des comptes, le solde disponible,
    puis effectue le transfert en créant une transaction.
    
    Args:
        session (Session): Session de base de données SQLModel
        from_acc (str): Numéro du compte source
        to_acc (str): Numéro du compte destination
        amount (Decimal): Montant à transférer
        
    Returns:
        Transaction: L'objet transaction créé
        
    Raises:
        HTTPException: Si le compte n'existe pas ou le solde est insuffisant
        
    Example:
        >>> transfer(session, "COMPTE_A", "COMPTE_B", Decimal("100.00"))
        Transaction(id=1, amount=100.00, status="COMPLETED")
        
    Note:
        Le transfert est atomique : soit il réussit complètement,
        soit il échoue sans modifier les comptes.
    """
```

---

## 🚀 Commandes Rapides

### Générer la documentation avec Sphinx
```bash
# Installation
pip install sphinx sphinx-rtd-theme

# Génération
cd docs
sphinx-apidoc -o source ../src/app
sphinx-build -b html source build

# Ouvrir
start build/index.html  # Windows
open build/index.html   # macOS
xdg-open build/index.html  # Linux
```

### Générer la documentation avec pdoc3
```bash
# Installation
pip install pdoc3

# Génération
pdoc --html --output-dir docs src/app

# Serveur local
pdoc --http localhost:8080 src/app
```

### Générer la documentation avec MkDocs
```bash
# Installation
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serveur de développement
mkdocs serve

# Build de production
mkdocs build
```

---

## 📝 Fichiers Documentés

Tous les fichiers suivants contiennent des docstrings complètes :

### Application Principale
- ✅ `src/app/main.py` - Configuration FastAPI et cycle de vie
- ✅ `src/app/db.py` - Configuration de la base de données

### Tests
- ✅ `tests/test_api.py` - Tests de l'API
- ✅ `tests/test_main.py` - Tests de la route racine

### Contrôleurs
- 📝 `src/app/controllers/bank_controller.py` - Routes de l'API

### Modèles
- 📝 `src/app/models/user.py` - Modèle utilisateur
- 📝 `src/app/models/account.py` - Modèle compte bancaire
- 📝 `src/app/models/transfer.py` - Modèle transfert
- 📝 `src/app/models/beneficiary.py` - Modèle bénéficiaire

### Services
- 📝 `src/app/services/bank_service.py` - Logique métier

---

## 🎓 Standards de Documentation

Le projet suit les standards suivants :

### Google Style Docstrings
```python
def function(arg1, arg2):
    """
    Summary line.
    
    Extended description.
    
    Args:
        arg1 (int): Description of arg1
        arg2 (str): Description of arg2
        
    Returns:
        bool: Description of return value
    """
```

### NumPy Style Docstrings
```python
def function(arg1, arg2):
    """
    Summary line.
    
    Extended description.
    
    Parameters
    ----------
    arg1 : int
        Description of arg1
    arg2 : str
        Description of arg2
        
    Returns
    -------
    bool
        Description of return value
    """
```

---

## 🔗 Ressources Utiles

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [pdoc3 Documentation](https://pdoc3.github.io/pdoc/)
- [MkDocs Documentation](https://www.mkdocs.org/)
- [Google Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [NumPy Style Guide](https://numpydoc.readthedocs.io/en/latest/format.html)

---

## 📧 Support

Pour toute question sur la documentation :
- Consultez les docstrings dans le code
- Générez la documentation HTML
- Contactez l'équipe Bank Project

---

**Bonne documentation ! 📚✨**
