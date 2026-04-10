# Shell Scripting — Référence Avancée (sh/bash/zsh)

## Table des matières
1. [Robustesse et sécurité](#1-robustesse-et-sécurité)
2. [Variables et types](#2-variables-et-types)
3. [Arrays et structures](#3-arrays-et-structures)
4. [Fonctions avancées](#4-fonctions-avancées)
5. [Redirections et process substitution](#5-redirections-et-process-substitution)
6. [Here-docs et here-strings](#6-here-docs-et-here-strings)
7. [Parsing d'arguments : getopts vs case](#7-parsing-darguments--getopts-vs-case)
8. [Trap et nettoyage](#8-trap-et-nettoyage)
9. [Subshells et groupes de commandes](#9-subshells-et-groupes-de-commandes)
10. [Patterns de contrôle de flux](#10-patterns-de-contrôle-de-flux)
11. [Gestion des erreurs](#11-gestion-des-erreurs)
12. [Portabilité POSIX vs bash vs zsh](#12-portabilité-posix-vs-bash-vs-zsh)
13. [Patterns DevOps courants](#13-patterns-devops-courants)

---

## 1. Robustesse et sécurité

```bash
# Toujours en tête de script bash
set -euo pipefail
IFS=$'\n\t'

# -e  : stop sur erreur non gérée
# -u  : stop sur variable non définie
# -o pipefail : propage l'échec dans les pipes
# IFS : évite le word splitting sur espaces
```

**ShellCheck** — linter incontournable :
```bash
shellcheck mon-script.sh          # analyse statique
shellcheck -s sh mon-script.sh    # forcer mode POSIX
```

**Quoting rules** :
```bash
# Toujours quoter les variables
cp "$src" "$dst"                  # ✅
cp $src $dst                      # ❌ risque avec espaces

# Arrays : quoter avec [@]
for f in "${files[@]}"; do ...    # ✅
for f in ${files[@]}; do ...      # ❌

# Chemins avec espaces
find . -name "*.log" -print0 | xargs -0 rm   # ✅ null-separated
```

---

## 2. Variables et types

```bash
# Déclaration et portée
local var="valeur"                # locale à une fonction (bash)
readonly CONST="immuable"         # constante
declare -i nb=42                  # entier (bash)
declare -l lower="HELLO"          # force lowercase → "hello"
declare -u upper="hello"          # force UPPERCASE → "HELLO"
declare -A map                    # tableau associatif (bash 4+)

# Expansion avancée
${var:-défaut}        # valeur si var vide/non définie
${var:=défaut}        # assigne si vide ET retourne la valeur
${var:?message}       # stop avec message si vide/non définie
${var:+autre}         # retourne 'autre' si var définie et non vide

# Manipulation de chaînes
${var#pattern}        # supprime préfixe (le plus court)
${var##pattern}       # supprime préfixe (le plus long)
${var%pattern}        # supprime suffixe (le plus court)
${var%%pattern}       # supprime suffixe (le plus long)
${var/old/new}        # remplace première occurrence
${var//old/new}       # remplace toutes les occurrences
${var^}               # première lettre en majuscule (bash 4+)
${var^^}              # tout en majuscule (bash 4+)
${#var}               # longueur de la chaîne

# Sous-chaînes
${var:offset}         # depuis offset
${var:offset:length}  # offset + longueur

# Exemple pratique
filename="/path/to/archive.tar.gz"
echo "${filename##*/}"    # archive.tar.gz  (basename)
echo "${filename%/*}"     # /path/to        (dirname)
echo "${filename%%.*}"    # /path/to/archive (sans extensions)
ext="${filename##*.}"     # gz
```

---

## 3. Arrays et structures

```bash
# Arrays indexés (bash)
files=("a.txt" "b.txt" "c.txt")
files+=("d.txt")                  # append
echo "${files[0]}"                # premier élément
echo "${files[-1]}"               # dernier élément (bash 4.3+)
echo "${files[@]}"                # tous les éléments
echo "${#files[@]}"               # nombre d'éléments
echo "${!files[@]}"               # indices
unset 'files[1]'                  # supprime l'élément 1

# Itération sûre
for f in "${files[@]}"; do
  echo "$f"
done

# Slicing
echo "${files[@]:1:2}"            # éléments 1 et 2

# Tableaux associatifs (bash 4+)
declare -A config
config[host]="localhost"
config[port]="5432"
config[db]="mydb"

for key in "${!config[@]}"; do
  echo "$key = ${config[$key]}"
done

# Construire un array depuis une commande
readarray -t lines < fichier.txt           # lire fichier ligne par ligne
mapfile -t results < <(find . -name "*.py") # process substitution

# zsh : arrays 1-indexed par défaut
# setopt KSH_ARRAYS pour comportement bash
```

---

## 4. Fonctions avancées

```bash
# Fonction avec valeur de retour via stdout
get_version() {
  local file="$1"
  grep -oP '(?<=version=)\S+' "$file"
}
version=$(get_version "setup.py")

# Fonction avec code de retour
is_running() {
  local service="$1"
  pgrep -x "$service" > /dev/null 2>&1
}
is_running "nginx" && echo "running" || echo "stopped"

# Passage d'array en argument (bash)
process_files() {
  local -n arr=$1   # nameref (bash 4.3+)
  for f in "${arr[@]}"; do
    echo "Processing: $f"
  done
}
process_files files

# Fonction récursive
factorial() {
  local n=$1
  (( n <= 1 )) && echo 1 && return
  echo $(( n * $(factorial $((n-1))) ))
}

# Retry pattern
retry() {
  local max=$1; local delay=$2; shift 2
  local i=1
  until "$@"; do
    (( i++ > max )) && { echo "Échec après $max tentatives" >&2; return 1; }
    echo "Tentative $i/$max — retry dans ${delay}s..." >&2
    sleep "$delay"
  done
}
retry 3 5 curl -sf "https://api.example.com/health"
```

---

## 5. Redirections et process substitution

```bash
# Redirections classiques
cmd > out.txt           # stdout → fichier (écrase)
cmd >> out.txt          # stdout → fichier (append)
cmd 2> err.txt          # stderr → fichier
cmd 2>&1                # stderr → stdout
cmd &> out.txt          # stdout + stderr → fichier (bash)
cmd > /dev/null 2>&1    # silencer tout (POSIX)
cmd < input.txt         # stdin depuis fichier

# Redirection multi-flux
{
  echo "stdout line"
  echo "stderr line" >&2
} > stdout.log 2> stderr.log

# Process substitution (bash/zsh — pas POSIX)
diff <(sort file1) <(sort file2)              # compare deux sorties triées
while read line; do ...; done < <(cmd)       # évite le subshell du pipe

# Tee — dupliquer un flux
cmd | tee output.txt | grep "ERROR"          # écrire ET filtrer

# Pipe avec gestion d'erreurs
if ! output=$(cmd 2>&1); then
  echo "Erreur : $output" >&2
  exit 1
fi

# Named pipe (FIFO)
mkfifo /tmp/mypipe
producer > /tmp/mypipe &
consumer < /tmp/mypipe
```

---

## 6. Here-docs et here-strings

```bash
# Here-doc standard
cat <<EOF
  Ligne 1
  Ligne 2 avec $variable interpolée
EOF

# Here-doc sans interpolation (quoted delimiter)
cat <<'EOF'
  Ligne avec $variable littérale (pas interpolée)
  Et des `backticks` non exécutés
EOF

# Here-doc avec indentation (tiret)
cat <<-EOF
	Indentation par tabs supprimée
	(tabs de début retirés automatiquement)
EOF

# Here-doc vers fichier
cat > /etc/app.conf <<EOF
host=localhost
port=${PORT:-8080}
EOF

# Here-string (bash/zsh)
grep "pattern" <<< "$variable"
base64 --decode <<< "SGVsbG8="

# Here-doc vers commande SSH
ssh user@host <<'ENDSSH'
  cd /app
  git pull
  systemctl restart app
ENDSSH

# Here-doc pour générer du SQL
psql -U postgres <<SQL
  SELECT * FROM users WHERE active = true;
  UPDATE sessions SET expired = true WHERE created < NOW() - INTERVAL '24h';
SQL
```

---

## 7. Parsing d'arguments : getopts vs case

### getopts (POSIX — options courtes uniquement)
```bash
usage() { echo "Usage: $0 [-v] [-e env] [-n name] <arg>"; exit 0; }

VERBOSE=false; ENV="dev"; NAME=""

while getopts ":ve:n:h" opt; do
  case $opt in
    v) VERBOSE=true ;;
    e) ENV="$OPTARG" ;;
    n) NAME="$OPTARG" ;;
    h) usage ;;
    :) echo "Option -$OPTARG nécessite un argument" >&2; exit 1 ;;
    \?) echo "Option inconnue : -$OPTARG" >&2; exit 1 ;;
  esac
done
shift $((OPTIND - 1))
# $@ contient maintenant les arguments positionnels restants
```

### while/case (bash — options longues)
```bash
VERBOSE=false; ENV="dev"; DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose)   VERBOSE=true; shift ;;
    -e|--env)       ENV="${2:?'--env nécessite une valeur'}"; shift 2 ;;
    --dry-run)      DRY_RUN=true; shift ;;
    -h|--help)      usage ;;
    --)             shift; break ;;          # fin des options
    -*)             error "Option inconnue : $1" ;;
    *)              break ;;                 # premier arg positionnel
  esac
done
```

### zsh : zparseopts
```zsh
emulate -L zsh
zparseopts -D -E -- \
  v=verbose -verbose=verbose \
  e:=env_opt -env:=env_opt \
  h=help -help=help

[[ -n $help ]] && usage
ENV="${env_opt[-1]:-dev}"
```

---

## 8. Trap et nettoyage

```bash
# Nettoyage automatique sur sortie
TMPDIR=$(mktemp -d)
cleanup() {
  local exit_code=$?
  rm -rf "$TMPDIR"
  [[ $exit_code -ne 0 ]] && echo "Script terminé avec erreur $exit_code" >&2
  exit $exit_code
}
trap cleanup EXIT

# Signaux spécifiques
trap 'echo "Interruption reçue"; cleanup' INT TERM

# Trap pour debug (affiche chaque commande)
trap 'echo "Ligne $LINENO : $BASH_COMMAND"' DEBUG   # bash uniquement

# ERR trap (bash) — appelé sur chaque erreur
trap 'error "Erreur ligne $LINENO : $BASH_COMMAND"' ERR

# Désactiver le trap temporairement
trap - EXIT    # désactive
trap cleanup EXIT  # réactive

# Lockfile pattern
LOCKFILE="/tmp/$(basename "$0").lock"
acquire_lock() {
  if ! mkdir "$LOCKFILE" 2>/dev/null; then
    error "Script déjà en cours (lock: $LOCKFILE)"
  fi
  trap 'rm -rf "$LOCKFILE"' EXIT
}
```

---

## 9. Subshells et groupes de commandes

```bash
# Subshell — modifications locales (cd, variables, set)
(
  cd /tmp
  set +e          # désactive -e localement
  risky_command
)
# répertoire courant inchangé après le subshell

# Groupe de commandes (même shell, pas de fork)
{
  cmd1
  cmd2
  cmd3
} | tee output.txt

# Exécution parallèle avec wait
{
  task1 &
  task2 &
  task3 &
  wait    # attend toutes les tâches background
}

# Parallèle avec capture d'erreur (bash 4.2+)
declare -A pids
for service in nginx redis postgres; do
  restart_service "$service" & pids[$service]=$!
done
for service in "${!pids[@]}"; do
  if ! wait "${pids[$service]}"; then
    error "Échec restart $service"
  fi
done

# Éviter le subshell dans un pipe (problème classique)
count=0
# ❌ count ne sera pas modifié hors du pipe
cat file | while read line; do (( count++ )); done

# ✅ Avec process substitution
while read line; do (( count++ )); done < <(cat file)
echo "Total : $count"
```

---

## 10. Patterns de contrôle de flux

```bash
# Test arithmétique (bash) — plus rapide que [ ]
(( x > 5 )) && echo "grand"
(( x++, y-- ))                     # incrément/décrément
result=$(( a * b + c ))

# Conditions avancées avec [[ ]]
[[ "$str" == *pattern* ]]           # glob matching
[[ "$str" =~ ^[0-9]+$ ]]           # regex matching
[[ -v varname ]]                    # variable définie (bash 4.2+)
[[ -f "$file" && -r "$file" ]]      # fichier lisible

# Boucle avec index (bash)
for (( i=0; i<${#array[@]}; i++ )); do
  echo "$i : ${array[$i]}"
done

# Boucle sur plage avec seq (POSIX-friendly)
for i in $(seq 1 10); do echo "$i"; done

# Boucle sur plage bash (expansion)
for i in {1..10}; do echo "$i"; done
for i in {0..100..5}; do echo "$i"; done   # pas de 5

# While avec timeout
TIMEOUT=30; START=$SECONDS
while ! check_ready; do
  (( SECONDS - START > TIMEOUT )) && error "Timeout après ${TIMEOUT}s"
  sleep 2
done

# Case avec patterns multiples
case "$input" in
  start|up)     start_service ;;
  stop|down)    stop_service ;;
  restart|r)    stop_service; start_service ;;
  status|s)     check_status ;;
  [0-9]*)       echo "Nombre détecté" ;;
  *)            error "Commande inconnue : $input" ;;
esac

# select — menu interactif
PS3="Choisir l'environnement : "
select env in dev staging prod quit; do
  case $env in
    quit) break ;;
    "")   echo "Choix invalide" ;;
    *)    deploy_to "$env"; break ;;
  esac
done
```

---

## 11. Gestion des erreurs

```bash
# Fonctions d'erreur avec contexte
error() {
  local msg="$1"
  local code="${2:-1}"
  echo "[ERROR] $(date '+%H:%M:%S') ${FUNCNAME[1]:-main}:${BASH_LINENO[0]} — $msg" >&2
  exit "$code"
}

# Gestion fine avec || et &&
rm "$file" || warn "Impossible de supprimer $file, on continue"
mkdir -p "$dir" || error "Impossible de créer $dir"

# Bloc try/catch simulé
{
  risky_operation
} || {
  warn "risky_operation a échoué, fallback..."
  fallback_operation || error "fallback aussi échoué"
}

# Vérification de dépendances
require_commands() {
  local missing=()
  for cmd in "$@"; do
    command -v "$cmd" &>/dev/null || missing+=("$cmd")
  done
  (( ${#missing[@]} > 0 )) && error "Commandes manquantes : ${missing[*]}"
}
require_commands curl jq docker aws

# Vérification de version minimale
require_bash_version() {
  local major=$1 minor=$2
  if (( BASH_VERSINFO[0] < major || (BASH_VERSINFO[0] == major && BASH_VERSINFO[1] < minor) )); then
    error "Bash >= $major.$minor requis (actuel : $BASH_VERSION)"
  fi
}
require_bash_version 4 3
```

---

## 12. Portabilité POSIX vs bash vs zsh

| Fonctionnalité | sh (POSIX) | bash | zsh |
|----------------|-----------|------|-----|
| Arrays indexés | ❌ | ✅ | ✅ (1-indexed) |
| Arrays associatifs | ❌ | ✅ 4+ | ✅ |
| `[[ ]]` | ❌ | ✅ | ✅ |
| `(( ))` | ❌ | ✅ | ✅ |
| Process substitution `<()` | ❌ | ✅ | ✅ |
| Here-string `<<<` | ❌ | ✅ | ✅ |
| `local` | ❌ (mksh: ✅) | ✅ | ✅ |
| `${var^^}` case | ❌ | ✅ 4+ | ✅ (différent) |
| `readarray/mapfile` | ❌ | ✅ | ❌ |
| `$BASH_SOURCE` | ❌ | ✅ | `$0` |
| Globs étendus | ❌ | `shopt -s extglob` | `setopt EXTENDED_GLOB` |
| Regex `=~` | ❌ | ✅ | ✅ |

**Détecter le shell à l'exécution :**
```bash
detect_shell() {
  case "$SHELL" in
    */bash) echo "bash ${BASH_VERSION}" ;;
    */zsh)  echo "zsh ${ZSH_VERSION}" ;;
    */sh)   echo "POSIX sh" ;;
    *)      echo "Inconnu : $SHELL" ;;
  esac
}
```

---

## 13. Patterns DevOps courants

```bash
# Chargement de .env
load_env() {
  local env_file="${1:-.env}"
  [[ -f "$env_file" ]] || return 0
  set -a    # auto-export toutes les variables
  # shellcheck source=/dev/null
  source "$env_file"
  set +a
}

# Spinner pour les opérations longues
spinner() {
  local pid=$1 msg="${2:-En cours...}"
  local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
  local i=0
  while kill -0 "$pid" 2>/dev/null; do
    printf "\r${spin:$((i++ % ${#spin})):1} $msg"
    sleep 0.1
  done
  printf "\r✓ $msg\n"
}
long_task & spinner $! "Déploiement..."

# Confirmation interactive
confirm() {
  local msg="${1:-Confirmer ?}"
  read -rp "$msg [y/N] " answer
  [[ "${answer,,}" == "y" ]]
}
confirm "Supprimer la base ?" || exit 0

# Logging vers fichier + stdout
setup_logging() {
  local logfile="${1:-/tmp/$(basename "$0").log}"
  exec > >(tee -a "$logfile")
  exec 2>&1
  log "Logs → $logfile"
}

# Check droits root
require_root() {
  [[ $EUID -eq 0 ]] || error "Ce script nécessite les droits root (sudo $0 $*)"
}

# Version semver compare
version_gte() {
  printf '%s\n%s' "$2" "$1" | sort -C -V
}
version_gte "$(python3 --version | cut -d' ' -f2)" "3.9.0" || error "Python 3.9+ requis"
```
