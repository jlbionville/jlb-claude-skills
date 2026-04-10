---
name: devops-python
description: >
  Génère, analyse et améliore des scripts Python DevOps professionnels couvrant AWS/Cloud,
  CI/CD, automatisation d'infrastructure et monitoring/logging. Utilise cette skill dès que
  l'utilisateur veut écrire un script Python lié à du DevOps, de l'infra, du cloud ou de
  l'automatisation — même s'il ne le formule pas explicitement. Déclencher aussi pour :
  "écris-moi un script qui déploie...", "automatise cette tâche AWS...", "comment monitorer X
  en Python", "debug ce script boto3", "j'ai une erreur dans mon pipeline Python",
  "bonnes pratiques pour scripts d'infra", ou toute demande mêlant Python + ops/cloud/infra.
  Impose systématiquement la structure standard (argparse, logging, main guard) et adopte une
  pédagogie explicative avec alternatives et liens vers la documentation officielle.
---

# DevOps Python Skill

Skill pour générer, analyser et guider des scripts Python DevOps professionnels.
Couvre : AWS/Cloud, CI/CD, automatisation d'infra, monitoring/logging.

---

## Étape 0 — Collecte d'informations (si absentes)

Avant de générer ou analyser, s'assurer d'avoir :

| Info | Exemple |
|------|---------|
| **Domaine** | AWS, CI/CD, Docker, monitoring, scripting générique |
| **Objectif précis** | "lister les buckets S3 non chiffrés", "notifier Slack si CPU > 80%" |
| **Mode** | Génération / Analyse-debug / Bonnes pratiques |
| **Niveau** | Débutant / Intermédiaire / Senior |
| **Livrable** | Fichier `.py` téléchargeable ou code inline |

Si des infos manquent, poser **une seule question groupée**. Ne jamais bloquer sur une ambiguïté mineure — faire une hypothèse raisonnable et l'expliciter.

---

## Étape 1 — Identifier le domaine et charger la référence

Selon le domaine détecté, lire le fichier de référence correspondant **avant** de générer :

| Domaine | Référence à lire |
|---------|-----------------|
| AWS / Cloud (boto3, S3, EC2, Lambda, IAM…) | `references/aws.md` |
| CI/CD (GitHub Actions, GitLab CI, scripts de pipeline) | `references/cicd.md` |
| Monitoring / Logging (métriques, alertes, observabilité) | `references/monitoring.md` |
| Automatisation infra / scripting générique | `references/scripting.md` |

Si le script touche plusieurs domaines (ex : script AWS avec logging avancé), lire les deux fichiers.

---

## Étape 2 — Structure standard obligatoire

**Tout script généré doit suivre ce squelette**, sauf si l'utilisateur demande explicitement du code minimal :

```python
#!/usr/bin/env python3
"""
Description courte du script.

Usage:
    python script.py --param valeur

Domaine: AWS / CI/CD / Monitoring / Scripting
Doc officielle: [lien pertinent]
"""

import argparse
import logging
import sys
# imports spécifiques au domaine

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Logique métier ────────────────────────────────────────────────────────────
def main_function(param: str) -> None:
    """Docstring décrivant ce que fait la fonction."""
    logger.info("Démarrage avec param=%s", param)
    # ... logique ici


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--param", required=True, help="Description du paramètre")
    parser.add_argument("--verbose", action="store_true", help="Mode verbeux")
    return parser.parse_args()


# ── Entrée principale ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    main_function(args.param)
```

**Éléments toujours présents :**
- Shebang + docstring de module avec usage et lien doc
- `logging` configuré (jamais de `print()` bruts en prod)
- `argparse` pour tous les paramètres CLI
- Type hints sur les fonctions principales
- `if __name__ == "__main__"` guard

---

## Étape 3 — Mode Génération

### 3.1 Générer le script
Suivre la structure de l'Étape 2 + les patterns spécifiques au domaine (depuis la référence chargée à l'Étape 1).

### 3.2 Expliquer les choix (pédagogie obligatoire)
Après le code, toujours fournir un bloc **"Pourquoi ces choix ?"** :

```
## Pourquoi ces choix ?

- **logging vs print** : `logging` permet de filtrer par niveau (DEBUG/INFO/WARNING),
  de rediriger vers fichier/CloudWatch, et d'avoir les timestamps automatiques.
  Alternative : `structlog` pour du logging JSON structuré en prod → [lien]

- **argparse vs sys.argv** : `argparse` génère automatiquement l'aide `--help`,
  valide les types et rend le script auto-documenté.
  Alternative : `click` ou `typer` si tu préfères une API déclarative → [lien]

- [Choix spécifique au domaine] : [explication] → [lien doc officielle]
```

### 3.3 Décider du livrable
- Script court (< 80 lignes) ou snippet d'illustration → **code inline**
- Script complet autonome / production-ready → **fichier `.py` téléchargeable** via `bash_tool` + `present_files`

---

## Étape 4 — Mode Analyse / Debug

### 4.1 Diagnostiquer
1. Identifier la nature du problème : erreur runtime, logique, performance, sécurité
2. Localiser la ligne ou le pattern en cause
3. Expliquer **pourquoi** c'est un problème (pas juste "c'est faux")

### 4.2 Corriger avec explication
Format de réponse pour un debug :

```
## Problème identifié
[Explication claire de la cause racine]

## Code corrigé
[bloc de code avec commentaires sur les changements]

## Pourquoi cette correction ?
[Explication pédagogique + lien doc si pertinent]

## Alternative à considérer
[Si une meilleure approche existe pour le cas d'usage]
```

### 4.3 Signaler les problèmes de sécurité en priorité
Si le code contient des secrets hardcodés, des permissions trop larges, ou des injections potentielles → **le signaler en premier**, avant les bugs fonctionnels.

---

## Étape 5 — Mode Bonnes Pratiques

Quand l'utilisateur demande des conseils ou une review, structurer la réponse en niveaux :

### Niveau 1 — Critique (à corriger maintenant)
Sécurité, secrets exposés, gestion d'erreurs absente, ressources non fermées.

### Niveau 2 — Important (à corriger prochainement)
Logging insuffisant, pas de retry sur les appels réseau, couplage fort.

### Niveau 3 — Améliorations (nice-to-have)
Type hints, docstrings, tests unitaires, configuration externalisée.

Pour chaque point :
- ✅ **Ce qu'on veut** : [pattern recommandé]
- ❌ **Ce qu'on évite** : [anti-pattern]
- 📖 **Pourquoi** : [explication courte]
- 🔗 **Doc** : [lien officiel pertinent]

---

## Étape 6 — Checklist avant livraison

Vérifier avant de livrer tout script :

- [ ] Shebang + docstring avec usage et lien doc officielle
- [ ] `logging` configuré (pas de `print()` nus)
- [ ] `argparse` pour tous les paramètres
- [ ] Type hints sur les fonctions principales
- [ ] `if __name__ == "__main__"` guard
- [ ] Gestion d'exceptions explicite (pas de `except Exception: pass`)
- [ ] Bloc "Pourquoi ces choix ?" fourni
- [ ] Alternatives mentionnées pour les choix non triviaux
- [ ] Livrable adapté au contexte (inline vs fichier)

---

## Références

- `references/aws.md` — Patterns boto3, gestion credentials, pagination, retry
- `references/cicd.md` — Scripts GitHub Actions / GitLab CI, gestion artifacts, notifications
- `references/monitoring.md` — Métriques, alertes, CloudWatch, Prometheus, Slack webhooks
- `references/scripting.md` — Patterns génériques : retry, config, secrets, file I/O, subprocess
