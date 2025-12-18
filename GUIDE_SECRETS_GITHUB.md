# 📧 Guide Complet : Configuration des Secrets GitHub pour les Notifications Email

## 🎯 Objectif

Configurer les secrets GitHub pour que votre workflow CI/CD puisse envoyer des emails d'alerte automatiquement lorsque les tests échouent.

---

## 📋 Liste des 5 Secrets à Configurer

| N° | Nom du Secret | Description | Exemple de Valeur |
|----|---------------|-------------|-------------------|
| 1 | `MAIL_SERVER` | Adresse du serveur SMTP | `smtp.gmail.com` |
| 2 | `MAIL_PORT` | Port du serveur SMTP | `587` |
| 3 | `MAIL_USERNAME` | Votre adresse email complète | `votre.email@gmail.com` |
| 4 | `MAIL_PASSWORD` | Mot de passe d'application (pas votre mot de passe Gmail) | `abcd efgh ijkl mnop` |
| 5 | `RECIPIENT_EMAIL` | Email qui recevra les alertes | `votre.email@gmail.com` |

---

## 🔧 Étape 1 : Créer un Mot de Passe d'Application Gmail

> [!IMPORTANT]
> **Ne JAMAIS utiliser votre mot de passe Gmail principal !** Vous devez créer un "mot de passe d'application" spécifique.

### Prérequis
- Avoir un compte Gmail
- Activer la validation en deux étapes (2FA) sur votre compte Google

### Instructions détaillées

#### A. Activer la validation en deux étapes (si pas déjà fait)

1. Allez sur [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Cherchez la section **"Validation en deux étapes"**
3. Cliquez sur **"Validation en deux étapes"**
4. Suivez les instructions pour l'activer (vous aurez besoin de votre téléphone)

#### B. Créer un mot de passe d'application

1. **Allez sur la page des mots de passe d'application** :
   - URL directe : [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - OU : Compte Google → Sécurité → Validation en deux étapes → Mots de passe des applications

2. **Connectez-vous** si demandé

3. **Créez un nouveau mot de passe** :
   - Dans le champ "Sélectionner l'application", choisissez **"Autre (nom personnalisé)"**
   - Tapez un nom descriptif : `GitHub Actions CI Bank Project`
   - Cliquez sur **"Générer"**

4. **Copiez le mot de passe généré** :
   - Google affichera un mot de passe de 16 caractères (format : `abcd efgh ijkl mnop`)
   - **COPIEZ-LE IMMÉDIATEMENT** (vous ne pourrez plus le voir après)
   - Gardez-le dans un endroit sûr temporairement (vous allez le coller dans GitHub)

> [!CAUTION]
> **Ce mot de passe ne sera affiché qu'une seule fois !** Si vous le perdez, vous devrez en générer un nouveau.

---

## 🔐 Étape 2 : Configurer les Secrets dans GitHub

### Navigation vers les Secrets

1. **Ouvrez votre dépôt GitHub** dans un navigateur
   - Exemple : `https://github.com/votre-username/bank_project`

2. **Allez dans les paramètres** :
   - Cliquez sur l'onglet **"Settings"** (en haut à droite)

3. **Naviguez vers les secrets** :
   - Dans le menu de gauche, cherchez **"Secrets and variables"**
   - Cliquez dessus pour déplier le menu
   - Cliquez sur **"Actions"**

4. Vous êtes maintenant sur la page : **"Actions secrets and variables"**

### Ajouter chaque secret (répétez 5 fois)

Pour chacun des 5 secrets, suivez ces étapes :

#### Secret 1 : MAIL_SERVER

1. Cliquez sur le bouton vert **"New repository secret"**
2. Dans le champ **"Name"**, tapez exactement : `MAIL_SERVER`
3. Dans le champ **"Secret"**, tapez : `smtp.gmail.com`
4. Cliquez sur **"Add secret"**

#### Secret 2 : MAIL_PORT

1. Cliquez sur **"New repository secret"**
2. **Name** : `MAIL_PORT`
3. **Secret** : `587`
4. Cliquez sur **"Add secret"**

#### Secret 3 : MAIL_USERNAME

1. Cliquez sur **"New repository secret"**
2. **Name** : `MAIL_USERNAME`
3. **Secret** : Votre adresse email complète (ex: `jean.dupont@gmail.com`)
4. Cliquez sur **"Add secret"**

#### Secret 4 : MAIL_PASSWORD

1. Cliquez sur **"New repository secret"**
2. **Name** : `MAIL_PASSWORD`
3. **Secret** : Collez le mot de passe d'application de 16 caractères que vous avez copié à l'Étape 1
   - Format : `abcdefghijklmnop` (sans espaces) ou `abcd efgh ijkl mnop` (avec espaces, les deux fonctionnent)
4. Cliquez sur **"Add secret"**

#### Secret 5 : RECIPIENT_EMAIL

1. Cliquez sur **"New repository secret"**
2. **Name** : `RECIPIENT_EMAIL`
3. **Secret** : L'adresse email qui recevra les alertes (généralement la même que MAIL_USERNAME)
4. Cliquez sur **"Add secret"**

---

## ✅ Étape 3 : Vérifier la Configuration

Après avoir ajouté les 5 secrets, vous devriez voir une liste comme celle-ci :

```
Repository secrets
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAIL_PASSWORD          Updated now by you
MAIL_PORT              Updated now by you
MAIL_SERVER            Updated now by you
MAIL_USERNAME          Updated now by you
RECIPIENT_EMAIL        Updated now by you
```

> [!NOTE]
> Les valeurs des secrets ne sont **jamais affichées** pour des raisons de sécurité. Vous ne verrez que les noms.

---

## 🧪 Étape 4 : Tester le Workflow

### Test 1 : Vérifier que le workflow fonctionne

1. **Faites un commit et push sur la branche `github-action`** :
   ```bash
   git add .
   git commit -m "test: Verify CI workflow"
   git push origin github-action
   ```

2. **Vérifiez l'exécution** :
   - Allez dans l'onglet **"Actions"** de votre dépôt GitHub
   - Vous devriez voir un workflow en cours : **"CI Backend - Tests Automatisés"**
   - Cliquez dessus pour voir les détails
   - Attendez que le workflow se termine (normalement, les tests devraient **passer** ✅)

### Test 2 : Tester l'envoi d'email en cas d'échec

1. **Modifiez temporairement le test pour le faire échouer** :
   
   Ouvrez `tests/test_main.py` et changez la ligne 42 :
   ```python
   # Avant :
   assert response.json() == {"message": "Hello, FastAPI!"}
   
   # Après (pour faire échouer) :
   assert response.json() == {"message": "TEST VOLONTAIRE D'ÉCHEC"}
   ```

2. **Commitez et poussez** :
   ```bash
   git add tests/test_main.py
   git commit -m "test: Force test failure to verify email notification"
   git push origin github-action
   ```

3. **Vérifiez** :
   - Le workflow devrait **échouer** ❌
   - Vous devriez recevoir un **email d'alerte** à l'adresse configurée dans `RECIPIENT_EMAIL`
   - L'email contiendra les détails de l'échec et un lien vers les logs

4. **Remettez le test en état** :
   ```python
   # Remettre la bonne assertion
   assert response.json() == {"message": "Hello, FastAPI!"}
   ```
   
   Puis commitez et poussez à nouveau.

---

## 📧 Exemple d'Email Reçu

Lorsque les tests échouent, vous recevrez un email qui ressemble à ceci :

```
De : votre.email@gmail.com
À : votre.email@gmail.com
Sujet : ❌ Échec des tests CI - Bank Project

Bonjour,

Les tests unitaires du projet Bank Project ont échoué lors du dernier push.

📋 Détails :
- Branche : github-action
- Commit : abc123def456...
- Auteur : votre-username
- Workflow : CI Backend - Tests Automatisés
- Run ID : 1234567890

🔗 Voir les détails de l'exécution :
https://github.com/votre-username/bank_project/actions/runs/1234567890

Veuillez corriger les erreurs et relancer les tests.

Cordialement,
GitHub Actions CI/CD
```

---

## 🔍 Dépannage

### Problème : Je ne reçois pas d'email

**Solutions possibles** :

1. **Vérifiez vos spams/courrier indésirable**
   - L'email peut être filtré comme spam

2. **Vérifiez les secrets** :
   - Allez dans Settings → Secrets and variables → Actions
   - Vérifiez que les 5 secrets sont bien présents
   - Si vous avez un doute, supprimez et recréez-les

3. **Vérifiez les logs du workflow** :
   - Allez dans Actions → Cliquez sur le workflow échoué
   - Cliquez sur l'étape "Send email notification on failure"
   - Lisez les erreurs éventuelles

4. **Vérifiez le mot de passe d'application** :
   - Assurez-vous d'avoir utilisé un mot de passe d'application, pas votre mot de passe Gmail
   - Générez un nouveau mot de passe d'application si nécessaire

5. **Vérifiez que la validation en deux étapes est activée** :
   - Sans 2FA, vous ne pouvez pas créer de mots de passe d'application

### Problème : "Invalid credentials" dans les logs

- Votre mot de passe d'application est incorrect
- Régénérez un nouveau mot de passe d'application et mettez à jour le secret `MAIL_PASSWORD`

### Problème : Le workflow ne se déclenche pas

- Vérifiez que vous poussez bien sur la branche `github-action`
- Vérifiez que le fichier `.github/workflows/ci-backend.yml` existe bien

---

## 🎓 Récapitulatif des Valeurs

Voici un tableau récapitulatif avec **VOS** valeurs à utiliser :

| Secret | Valeur à mettre |
|--------|-----------------|
| `MAIL_SERVER` | `smtp.gmail.com` |
| `MAIL_PORT` | `587` |
| `MAIL_USERNAME` | **Votre email Gmail complet** (ex: `jean.dupont@gmail.com`) |
| `MAIL_PASSWORD` | **Le mot de passe d'application de 16 caractères** généré par Google |
| `RECIPIENT_EMAIL` | **L'email qui recevra les alertes** (souvent le même que MAIL_USERNAME) |

---

## 🔒 Sécurité - Points Importants

> [!CAUTION]
> **À NE JAMAIS FAIRE** :
> - ❌ Commiter vos mots de passe dans le code
> - ❌ Utiliser votre mot de passe Gmail principal
> - ❌ Partager vos mots de passe d'application
> - ❌ Publier vos secrets dans les issues ou discussions GitHub

> [!TIP]
> **Bonnes pratiques** :
> - ✅ Toujours utiliser des mots de passe d'application
> - ✅ Révoquer les mots de passe d'application non utilisés
> - ✅ Utiliser les secrets GitHub pour toutes les informations sensibles
> - ✅ Activer la validation en deux étapes sur tous vos comptes

---

## 📞 Besoin d'Aide ?

Si vous rencontrez des difficultés :

1. Vérifiez les logs du workflow dans l'onglet Actions
2. Consultez la section Dépannage ci-dessus
3. Vérifiez que tous les secrets sont correctement orthographiés (sensible à la casse)
4. Assurez-vous que la validation en deux étapes est activée sur votre compte Google

---

**Bonne chance ! 🚀**
