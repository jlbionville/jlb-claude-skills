---
name: linux-shell
description: >
  Skill experte pour écrire des scripts shell professionnels (sh/bash/zsh), des pipelines
  de traitement de texte (sed/awk/grep), automatiser vim/vi depuis la ligne de commande,
  et créer des Makefile comme task runner DevOps/Python. Utilise cette skill dès que
  l'utilisateur mentionne : script shell, bash, zsh, sed, awk, grep, vi, vim, Makefile,
  pipeline texte, one-liner, automatisation système, traitement de fichiers. Déclencher
  aussi pour : "écris-moi un script qui...", "comment parser ce fichier avec awk",
  "remplace dans tous mes fichiers avec sed", "crée un Makefile pour mon projet Python",
  "automatise vi pour modifier en masse", "one-liner pour extraire...", "je veux un
  pipeline shell qui...", "comment déboguer mon script bash", ou toute demande mêlant
  shell + DevOps/infra/automatisation. Ne jamais livrer un script sans shebang, gestion
  d'erreurs et commentaires explicatifs.
---

# Linux Shell Skill

Skill pour écrire des scripts shell professionnels, pipelines texte et Makefile.
Couvre : sh/bash/zsh avancé, sed/awk/grep, automatisation vi/vim, Makefile task runner.

---

## Étape 0 — Collecte d'informations (si absentes)

Avant de générer, s'assurer d'avoir :

| Info | Exemple |
|------|---------|
| **Shell cible** | sh (POSIX), bash, zsh |
| **Domaine** | Script shell, pipeline texte, Makefile, vim automation |
| **Objectif précis** | "renommer 500 fichiers en masse", "build Python avec venv" |
| **Contexte d'exécution** | Local, CI/CD, Docker, cron |
| **Livrable** | Fichier téléchargeable ou snippet inline |

Si des infos manquent, poser **une seule question groupée**. Faire une hypothèse raisonnable et l'expliciter plutôt que de bloquer.

---

## Étape 1 — Identifier le domaine et charger la référence

| Domaine détecté | Référence à lire |
|-----------------|-----------------|
| Scripts sh/bash/zsh | `references/shell-scripting.md` |
| sed / awk / grep | `references/text-processing.md` |
| Automatisation vi/vim | `references/vim-automation.md` |
| Makefile task runner | `references/makefile.md` |

Si la demande croise plusieurs domaines (ex : script bash qui appelle sed + make), lire **tous** les fichiers concernés.

---

## Étape 2 — Structure standard obligatoire

### 2.1 Scripts shell (sh/bash/zsh)

**Tout script généré doit suivre ce squelette**, sauf snippet one-liner explicitement demandé :

```bash
#!/usr/bin/env bash
# =============================================================================
# nom-du-script.sh — Description courte
#
# Usage   : ./nom-du-script.sh [OPTIONS] <arg>
# Exemple : ./nom-du-script.sh --env prod deploy
# Auteur  : [auteur]
# =============================================================================
set -euo pipefail
IFS=$'\n\t'

# ── Constantes ────────────────────────────────────────────────────────────────
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"

# ── Couleurs (optionnel selon contexte) ───────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# ── Fonctions utilitaires ─────────────────────────────────────────────────────
log()   { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*" >&2; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <arg>
  -h, --help     Affiche cette aide
  -v, --verbose  Mode verbeux
  -e, --env ENV  Environnement cible (default: dev)
EOF
  exit 0
}

# ── Parsing des arguments ─────────────────────────────────────────────────────
VERBOSE=false
ENV="dev"

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)    usage ;;
    -v|--verbose) VERBOSE=true; shift ;;
    -e|--env)     ENV="$2"; shift 2 ;;
    --)           shift; break ;;
    -*)           error "Option inconnue : $1" ;;
    *)            break ;;
  esac
done

# ── Logique principale ────────────────────────────────────────────────────────
main() {
  log "Démarrage — env=$ENV"
  # ... logique ici
}

main "$@"
```

**Éléments toujours présents :**
- Shebang + en-tête documenté
- `set -euo pipefail` + `IFS=$'\n\t'` (robustesse obligatoire)
- Fonctions `log/warn/error` avec stderr pour les erreurs
- `usage()` avec heredoc
- Parsing d'arguments avec `while/case`
- Fonction `main()` appelée en fin de script

### 2.2 POSIX sh (portabilité maximale)

Quand `sh` est requis, remplacer :
- `[[ ]]` → `[ ]`
- `${BASH_SOURCE[0]}` → `$0`
- `local` → variables globales préfixées
- Pas de tableaux bash, pas de `<<<`, pas de `{a..z}`

### 2.3 zsh

Ajouter en tête : `emulate -L zsh` pour un comportement prévisible.
Utiliser `zparseopts` pour le parsing d'options avancé si nécessaire.

---

## Étape 3 — Mode Génération

### 3.1 Appliquer les patterns de la référence chargée

Charger `references/shell-scripting.md` pour : fonctions avancées, arrays, process substitution, trap, here-docs, subshells, getopts, redirections.

Charger `references/text-processing.md` pour : sed one-liners, awk programs, grep pipelines, chaînage.

Charger `references/vim-automation.md` pour : commandes ex headless, macros, vimscript inline, `-c` et `+cmd`.

Charger `references/makefile.md` pour : targets, variables, règles implicites, `.PHONY`, patterns DevOps/Python.

### 3.2 Expliquer les choix (obligatoire)

Après chaque livrable, fournir un bloc **"Pourquoi ces choix ?"** :

```
## Pourquoi ces choix ?

- **set -euo pipefail** : `-e` stoppe sur erreur, `-u` refuse les variables non définies,
  `-o pipefail` propage l'échec dans les pipes. Sans ça, un script peut continuer
  silencieusement après une erreur critique.

- **[choix spécifique]** : [explication] → [lien man page ou référence]
```

### 3.3 Décider du livrable

- One-liner / snippet < 20 lignes → **code inline**
- Script autonome / production-ready → **fichier téléchargeable** via `bash_tool` + `present_files`
- Makefile → **toujours** fichier téléchargeable (indentation tabs critique)

---

## Étape 4 — Mode Debug / Analyse

Format de réponse :

```
## Problème identifié
[Cause racine — ex: "quoting non protégé sur variable avec espaces"]

## Code corrigé
[bloc avec commentaires sur les changements]

## Pourquoi cette correction ?
[Explication + man page ou référence si pertinent]

## À vérifier aussi
[Problèmes connexes détectés dans le script]
```

**Signaler en priorité :**
- `rm -rf` sans vérification de variable (`rm -rf $DIR/` → danger si `$DIR` vide)
- Absence de `set -euo pipefail`
- Variables non quotées dans des contextes à risque
- Pipes vers `sudo` ou élévation de privilèges non justifiée

---

## Étape 5 — Checklist avant livraison

- [ ] Shebang correct pour le shell cible
- [ ] `set -euo pipefail` + `IFS` (bash) ou équivalent POSIX
- [ ] `usage()` documenté
- [ ] Toutes les variables quotées (`"$var"`, `"${array[@]}"`)
- [ ] `trap` pour nettoyage si fichiers temporaires créés
- [ ] Gestion d'erreurs explicite (pas de `|| true` sans raison)
- [ ] Commentaires sur les one-liners sed/awk complexes
- [ ] Makefile : indentation tabs (jamais espaces)
- [ ] Bloc "Pourquoi ces choix ?" fourni
- [ ] Livrable adapté (inline vs fichier)

---

## Références

- `references/shell-scripting.md` — sh/bash/zsh avancé : arrays, trap, process substitution, getopts, here-docs, redirections, subshells, best practices
- `references/text-processing.md` — sed/awk/grep : one-liners, programs multi-lignes, chaînage, patterns courants
- `references/vim-automation.md` — vi/vim headless : commandes ex, `-c`, vimscript, macros, batch editing
- `references/makefile.md` — Makefile task runner : targets, variables, patterns DevOps/Python, .PHONY, includes
