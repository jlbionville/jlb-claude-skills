# Templates de code commentés par domaine

Chaque bloc de code doit être pédagogique. Utiliser ces patterns comme base.

## Convention universelle

```
# ❌ [Ce qu'on faisait avant / l'anti-pattern]
# ✅ [Ce qu'on fait maintenant / pourquoi]
# 🔍 [Observation / diagnostic]
# ⚠️  [Attention / piège potentiel]
# 💡 [Astuce / alternative]
# →   [Résultat attendu en commentaire inline]
```

---

## AWS CLI / Boto3

```bash
# 🔍 D'abord, toujours observer avant de modifier
aws s3 ls s3://mon-bucket/ --recursive --human-readable
# → Liste les fichiers avec leur taille lisible

# ❌ Ce qu'on voit souvent : credentials hardcodés
AWS_ACCESS_KEY_ID="AKIA..." python script.py  # ⚠️ Jamais en prod !

# ✅ La bonne approche : IAM Role ou profil nommé
aws configure --profile mon-projet   # Profil dédié par projet
export AWS_PROFILE=mon-projet        # Activer pour la session
python script.py                     # Boto3 le détecte automatiquement
```

```python
import boto3

# ✅ Toujours spécifier la région explicitement
session = boto3.Session(region_name='eu-west-1')  # Paris — pas de suprise
s3 = session.client('s3')

# ❌ Anti-pattern : attraper Exception générique
try:
    s3.download_file(bucket, key, destination)
except Exception as e:
    print(e)  # On perd toute l'info de débogage

# ✅ Attraper les erreurs boto3 précisément
from botocore.exceptions import ClientError, NoCredentialsError

try:
    s3.download_file(bucket, key, destination)
except NoCredentialsError:
    raise SystemExit("❌ Credentials AWS manquants — vérifie aws configure")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        raise FileNotFoundError(f"Fichier introuvable : {key}")
    raise  # Re-raise les autres erreurs inconnues
```

---

## Git / Bash

```bash
# 🔍 Toujours vérifier l'état avant une opération destructive
git status          # Quoi de nouveau ?
git log --oneline -5  # Où en est-on ?

# ❌ La commande dangereuse sans filet
git reset --hard HEAD~3  # ⚠️ Irréversible sans reflog !

# ✅ Avec filet de sécurité
git stash           # Sauvegarder le travail en cours
git log --oneline   # Noter le hash du commit cible
git reset --hard abc1234  # Reset vers un commit précis (pas relatif)
# → En cas de regret : git reflog pour retrouver l'état précédent

# 💡 Alias utile à ajouter dans ~/.gitconfig
git config --global alias.undo 'reset HEAD~1 --mixed'  # Annuler sans perdre les modifs
```

```bash
# ✅ Pattern de commit conventionnel (Conventional Commits)
git commit -m "feat(auth): ajouter authentification JWT

- Implémenter la génération de token RS256
- Ajouter middleware de validation
- Tests unitaires inclus

Closes #42"
# Format : type(scope): description courte
# Types : feat, fix, docs, refactor, test, chore
```

---

## Python

```python
# ❌ Anti-pattern : tout dans un seul script
import requests, json, os

data = requests.get("https://api.exemple.com/data").json()
with open("output.json", "w") as f:
    json.dump(data, f)
# Problèmes : pas de gestion d'erreur, pas de config, pas de logs

# ✅ Version structurée et robuste
import logging
import os
from pathlib import Path
from typing import Optional
import requests
from requests.exceptions import RequestException, Timeout

# Configuration centralisée
API_URL = os.getenv("API_URL", "https://api.exemple.com")  # Variable d'env avec défaut
TIMEOUT_SEC = 10  # Toujours un timeout explicite
OUTPUT_DIR = Path("output")  # Pathlib plutôt que os.path

logger = logging.getLogger(__name__)  # Logger par module, pas global


def fetch_data(endpoint: str, timeout: int = TIMEOUT_SEC) -> Optional[dict]:
    """Récupère les données depuis l'API.
    
    Args:
        endpoint: Chemin relatif de l'endpoint (ex: '/data')
        timeout: Délai max en secondes
        
    Returns:
        Les données JSON ou None si erreur
    """
    url = f"{API_URL}{endpoint}"
    
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Lève une exception si 4xx/5xx
        return response.json()
        
    except Timeout:
        logger.error("⏱️ Timeout après %ds sur %s", timeout, url)
        return None
    except RequestException as e:
        logger.error("❌ Erreur réseau : %s", e)
        return None
```

```python
# ✅ Context managers pour les ressources (fichiers, connexions DB)
# ❌ Anti-pattern
f = open("fichier.txt")
data = f.read()
f.close()  # Oublié si une exception se lève avant

# ✅ Toujours utiliser with
with open("fichier.txt", encoding="utf-8") as f:
    data = f.read()
# → Le fichier est fermé automatiquement, même en cas d'exception

# 💡 Pour plusieurs ressources
with open("input.txt") as src, open("output.txt", "w") as dst:
    dst.write(src.read())
```

---

## Bash / Linux / WSL

```bash
#!/usr/bin/env bash
# ✅ Shebang portable — fonctionne sur Linux, macOS, WSL

# ✅ En-tête de script robuste (toujours en début de script)
set -euo pipefail
# -e : arrêt si une commande échoue
# -u : erreur si variable non définie (évite les surprises)
# -o pipefail : erreur si n'importe quelle commande dans un pipe échoue

# ✅ Variables en MAJUSCULES pour les constantes
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${SCRIPT_DIR}/deploy.log"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# ✅ Fonction de logging
log() {
    echo "[${TIMESTAMP}] $*" | tee -a "${LOG_FILE}"
}

log "🚀 Démarrage du déploiement..."

# ❌ Anti-pattern : ne pas vérifier les prérequis
docker compose up  # Plante si Docker n'est pas installé

# ✅ Vérifier les dépendances en début de script
check_requirements() {
    local -a required_tools=("docker" "aws" "jq")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "${tool}" &>/dev/null; then
            log "❌ Outil manquant : ${tool}"
            exit 1
        fi
    done
    log "✅ Tous les outils requis sont disponibles"
}

check_requirements
```

---

## YAML (GitHub Actions / Docker Compose / K8s)

```yaml
# ✅ GitHub Actions — pipeline commenté pour article DevOps
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]  # Déclenche sur ces branches uniquement
  pull_request:
    branches: [main]           # Et sur les PR vers main

env:
  PYTHON_VERSION: '3.11'       # ✅ Version fixée — pas "latest" (imprévisible)
  REGISTRY: ghcr.io            # GitHub Container Registry

jobs:
  test:
    name: Tests & Qualité
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout du code
        uses: actions/checkout@v4  # ✅ Version épinglée (pas @latest)
      
      - name: Setup Python ${{ env.PYTHON_VERSION }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'           # ✅ Cache des dépendances — build 2x plus rapide
      
      - name: Installation des dépendances
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      # ❌ Anti-pattern : lancer les tests sans rapport
      # - run: pytest
      
      # ✅ Avec rapport de couverture et format JUnit pour GitHub
      - name: Lancer les tests
        run: |
          pytest \
            --cov=src \              # Couverture sur le dossier src/
            --cov-report=xml \      # Format lisible par GitHub
            --junitxml=results.xml \ # Résultats intégrés dans l'UI GitHub
            -v                       # Verbose pour voir chaque test

  deploy:
    name: Déploiement
    needs: test              # ✅ Condition : deploy uniquement si tests OK
    if: github.ref == 'refs/heads/main'  # ✅ Uniquement sur main
    runs-on: ubuntu-latest
    
    environment:
      name: production       # ✅ Environment GitHub avec protection rules
      url: https://mon-app.com
```
