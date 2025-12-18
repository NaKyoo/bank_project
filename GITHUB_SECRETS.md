# Configuration des Secrets GitHub pour CI/CD

## Secrets requis pour le workflow `ci-backend.yml`

Pour que le workflow GitHub Actions puisse envoyer des emails d'alerte en cas d'échec des tests, vous devez configurer les secrets suivants dans votre dépôt GitHub.

### Liste des secrets

| Secret | Description | Exemple |
|--------|-------------|---------|
| `MAIL_SERVER` | Serveur SMTP pour l'envoi d'emails | `smtp.gmail.com` |
| `MAIL_PORT` | Port SMTP (587 pour TLS, 465 pour SSL) | `587` |
| `MAIL_USERNAME` | Adresse email d'envoi | `notifications@example.com` |
| `MAIL_PASSWORD` | Mot de passe ou token d'application | `votre_mot_de_passe_app` |
| `RECIPIENT_EMAIL` | Adresse email du destinataire des alertes | `votre.email@example.com` |

### Comment configurer les secrets dans GitHub

1. **Accédez aux paramètres du dépôt** :
   - Allez sur votre dépôt GitHub
   - Cliquez sur **Settings** (Paramètres)

2. **Naviguez vers les secrets** :
   - Dans le menu de gauche, cliquez sur **Secrets and variables**
   - Puis cliquez sur **Actions**

3. **Ajoutez chaque secret** :
   - Cliquez sur **New repository secret**
   - Entrez le nom du secret (ex: `MAIL_SERVER`)
   - Entrez la valeur correspondante
   - Cliquez sur **Add secret**
   - Répétez pour chaque secret de la liste

### Configuration Gmail (exemple)

Si vous utilisez Gmail, voici les étapes spécifiques :

1. **Activer l'authentification à deux facteurs** sur votre compte Gmail

2. **Créer un mot de passe d'application** :
   - Allez sur [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Sélectionnez "Autre (nom personnalisé)"
   - Nommez-le "GitHub Actions CI"
   - Copiez le mot de passe généré (16 caractères)

3. **Configurez les secrets avec ces valeurs** :
   ```
   MAIL_SERVER: smtp.gmail.com
   MAIL_PORT: 587
   MAIL_USERNAME: votre.email@gmail.com
   MAIL_PASSWORD: [mot de passe d'application de 16 caractères]
   RECIPIENT_EMAIL: votre.email@gmail.com
   ```

### Vérification

Une fois les secrets configurés :

1. Faites un push sur la branche `github-action`
2. Vérifiez que le workflow se déclenche dans l'onglet **Actions**
3. Si les tests échouent, vous devriez recevoir un email d'alerte

### Sécurité

> [!CAUTION]
> - Ne commitez **JAMAIS** vos mots de passe ou tokens dans le code
> - Utilisez toujours des **mots de passe d'application** plutôt que votre mot de passe principal
> - Les secrets GitHub sont chiffrés et ne sont jamais exposés dans les logs

### Dépannage

Si vous ne recevez pas d'email :

1. Vérifiez que tous les secrets sont correctement configurés
2. Consultez les logs du workflow dans l'onglet Actions
3. Vérifiez que votre serveur SMTP autorise les connexions depuis GitHub Actions
4. Pour Gmail, assurez-vous que "Accès moins sécurisé" n'est pas requis (utilisez un mot de passe d'application)
