# Référence CI/CD Python

---

## Variables d'environnement et secrets dans les pipelines

```python
import os
import sys

def get_env(key: str, required: bool = True) -> str:
    """Récupère une variable d'environnement avec validation."""
    value = os.environ.get(key)
    if required and not value:
        logger.error("Variable d'environnement manquante : %s", key)
        sys.exit(1)
    return value or ""

# Usage dans un script CI
github_token = get_env("GITHUB_TOKEN")
deploy_env   = get_env("DEPLOY_ENV", required=False) or "staging"
```

Jamais de secrets dans le code source. Utiliser :
- GitHub Actions : `${{ secrets.MY_SECRET }}`
- GitLab CI : `$MY_SECRET` (variables protégées)
- Doc GitHub : https://docs.github.com/en/actions/security-guides/encrypted-secrets
- Doc GitLab : https://docs.gitlab.com/ee/ci/variables/

---

## Notifications Slack depuis un script CI

```python
import requests

def notify_slack(webhook_url: str, message: str, success: bool = True) -> None:
    """Envoie une notification Slack via webhook."""
    color = "#36a64f" if success else "#ff0000"
    payload = {
        "attachments": [{
            "color": color,
            "text": message,
            "footer": "CI/CD Pipeline",
        }]
    }
    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
    logger.info("Notification Slack envoyée")
```

Alternative : `slack-sdk` pour des messages plus riches (blocs, fichiers).
Doc webhook : https://api.slack.com/messaging/webhooks

---

## Gestion du code de retour (exit codes)

```python
import sys

# ✅ Exit codes explicites pour que le pipeline sache ce qui s'est passé
EXIT_SUCCESS = 0
EXIT_ERROR   = 1
EXIT_PARTIAL = 2  # succès partiel (certaines ressources ont échoué)

try:
    result = deploy()
    if result.failed_resources:
        logger.warning("%d ressources ont échoué", len(result.failed_resources))
        sys.exit(EXIT_PARTIAL)
    sys.exit(EXIT_SUCCESS)
except Exception as e:
    logger.error("Déploiement échoué : %s", e)
    sys.exit(EXIT_ERROR)
```

---

## Idempotence des scripts de déploiement

Principe : le script doit pouvoir être rejoué sans effet de bord.

```python
def create_resource_if_not_exists(name: str) -> bool:
    """Crée la ressource uniquement si elle n'existe pas déjà. Retourne True si créée."""
    if resource_exists(name):
        logger.info("Ressource '%s' déjà existante, skip.", name)
        return False
    create_resource(name)
    logger.info("Ressource '%s' créée.", name)
    return True
```

---

## Dry-run mode

Toujours proposer un mode `--dry-run` pour les scripts destructifs :

```python
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Simule les actions sans les exécuter"
)

def delete_old_artifacts(path: str, dry_run: bool = False) -> None:
    if dry_run:
        logger.info("[DRY-RUN] Supprimerait : %s", path)
        return
    os.remove(path)
    logger.info("Supprimé : %s", path)
```

---

## Liens utiles CI/CD

- GitHub Actions Python : https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
- GitLab CI Python : https://docs.gitlab.com/ee/ci/examples/python.html
- `python-semantic-release` (versioning automatique) : https://python-semantic-release.readthedocs.io/
