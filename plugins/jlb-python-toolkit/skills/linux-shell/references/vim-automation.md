# Vim / vi — Automatisation et Scripting

## Table des matières
1. [Vim headless — principes](#1-vim-headless--principes)
2. [Commandes ex depuis la ligne de commande](#2-commandes-ex-depuis-la-ligne-de-commande)
3. [Scripts ex multi-commandes](#3-scripts-ex-multi-commandes)
4. [Vimscript inline](#4-vimscript-inline)
5. [Macros et registres](#5-macros-et-registres)
6. [Patterns batch editing](#6-patterns-batch-editing)
7. [Vim comme filtre dans des pipelines](#7-vim-comme-filtre-dans-des-pipelines)

---

## 1. Vim headless — principes

Vim peut fonctionner entièrement sans interface graphique pour l'automatisation :

```bash
# Modes d'invocation
vim -es file.txt            # ex mode silencieux (ex mode + silent)
vim --headless file.txt     # headless (nvim compatible)
vim -c "cmd" file.txt       # exécuter une commande ex après ouverture
vim +"cmd" file.txt         # identique à -c (syntaxe alternative)
vim -S script.vim file.txt  # exécuter un fichier vimscript
vim -u NONE file.txt        # sans .vimrc (plus rapide, prévisible)

# Sortir proprement (obligatoire en mode script)
vim -es -c "..." -c "wqa"  file.txt   # wqa : write all + quit all
vim +"cmd | wq" file.txt               # + pour commande en ligne
```

**Règle d'or** : toujours terminer avec `:wq`, `:wqa`, `:qa!` ou `:q!` sinon vim restera suspendu.

```bash
# Template de base pour modification in-place
vim -u NONE -es \
  -c "set nobackup noswapfile" \
  -c "COMMANDES_ICI" \
  -c "wq" \
  fichier.txt
```

---

## 2. Commandes ex depuis la ligne de commande

### Substitution (`:s`)
```bash
# Syntaxe : :[range]s/pattern/remplacement/[flags]
vim -u NONE -es -c '%s/foo/bar/g' -c 'wq' file.txt

# Flags courants
# g = global (toutes occurrences sur la ligne)
# i = case insensitive
# I = case sensitive (override ignorecase)
# c = confirmation interactive (éviter en mode headless)
# e = pas d'erreur si aucun match

# Ranges
# %       = tout le fichier
# 1,10    = lignes 1 à 10
# /pat/   = ligne contenant pat
# /p1/,/p2/ = de p1 à p2

# Avec regex avancée
vim -u NONE -es \
  -c 'set magic' \
  -c '%s/\v(\d{4})-(\d{2})-(\d{2})/\3\/\2\/\1/g' \
  -c 'wq' dates.txt
# \v = very magic (ERE-like, moins d'escapes)

# Groupes de capture
vim -es -c '%s/\(foo\)\(bar\)/\2\1/g' -c 'wq' file.txt  # sans \v
vim -es -c '%s/\v(foo)(bar)/\2\1/g'   -c 'wq' file.txt  # avec \v

# Multilignes
vim -es -c '%s/ligne1\nligné2/remplacé/g' -c 'wq' file.txt
```

### Suppression, insertion, filtrage
```bash
# Supprimer des lignes
vim -es -c 'g/^#/d'   -c 'wq' file.txt    # supprimer commentaires
vim -es -c 'g/^$/d'   -c 'wq' file.txt    # supprimer lignes vides
vim -es -c 'v/error/d' -c 'wq' file.txt   # garder UNIQUEMENT les lignes avec "error"

# g/pattern/commande — global
vim -es -c 'g/TODO/m$'    -c 'wq' file.txt   # déplacer TODOs en fin de fichier
vim -es -c 'g/^$/d'       -c 'wq' file.txt   # supprimer lignes vides
vim -es -c 'g/debug/p'    -c 'q!'  file.txt  # afficher lignes debug (sans modifier)

# Insertion de lignes
vim -es -c '1i\#!/usr/bin/env bash' -c 'wq' script.sh  # shebang en tête
vim -es -c '$a\# End of file'       -c 'wq' file.txt   # ligne en fin
vim -es -c '/marker/a\nouvelle ligne après marker' -c 'wq' file.txt

# Lecture/insertion d'un fichier
vim -es -c 'r header.txt'  -c 'wq' file.txt     # insérer header.txt après ligne 1
vim -es -c '0r header.txt' -c 'wq' file.txt     # insérer avant ligne 1
vim -es -c '$r footer.txt' -c 'wq' file.txt     # insérer à la fin

# Tri
vim -es -c '%!sort'         -c 'wq' file.txt    # trier tout le fichier
vim -es -c '2,$!sort -k2'   -c 'wq' file.txt    # trier à partir de la ligne 2
vim -es -c '%!sort | uniq'  -c 'wq' file.txt    # trier + dédupliquer
```

### Navigation et sélection
```bash
# Aller à une ligne spécifique et opérer
vim -es -c '42d'            -c 'wq' file.txt    # supprimer ligne 42
vim -es -c '10,20j'         -c 'wq' file.txt    # joindre lignes 10-20
vim -es -c '5,10d'          -c 'wq' file.txt    # supprimer lignes 5-10
vim -es -c '1,5m$'          -c 'wq' file.txt    # déplacer lignes 1-5 à la fin
vim -es -c '1,5co$'         -c 'wq' file.txt    # copier lignes 1-5 à la fin
```

---

## 3. Scripts ex multi-commandes

Pour des opérations complexes, écrire un script ex dédié :

```bash
# script.ex
%s/foo/bar/g
%s/\s\+$//g
g/^$/d
1i\#!/usr/bin/env bash
$a\# Generated
wq
```

```bash
# Exécution
vim -u NONE -es -S script.ex fichier.txt
# ou
ex -s < script.ex fichier.txt
```

### Script ex généré dynamiquement
```bash
apply_vim_transforms() {
  local file="$1"
  local old="$2"
  local new="$3"

  vim -u NONE -es \
    -c "set nobackup noswapfile" \
    -c "%s/${old}/${new}/ge" \
    -c "%s/\s\+$//ge" \
    -c "g/^$/d" \
    -c "wq" \
    "$file"
}

# Usage
apply_vim_transforms config.yml "staging" "production"
```

### Traitement de plusieurs fichiers
```bash
# Modifier plusieurs fichiers avec une seule invocation
vim -u NONE -es \
  -c 'bufdo %s/version = "1.0"/version = "2.0"/ge | update' \
  -c 'qa' \
  pyproject.toml setup.cfg *.spec

# Avec glob
vim -u NONE -es \
  -c 'argdo %s/old_api/new_api/ge | update' \
  -c 'qa' \
  $(find src/ -name "*.py")
```

---

## 4. Vimscript inline

```bash
# Exécuter du vimscript arbitraire
vim -u NONE -es \
  -c 'let @a = ""' \
  -c 'execute "normal! gg"' \
  -c 'call feedkeys("qa")' \
  -c 'wq' \
  file.txt

# Script vimscript complet dans un fichier
cat > /tmp/transform.vim << 'EOF'
" Supprimer trailing whitespace
%s/\s\+$//e

" Normaliser les fins de ligne
set ff=unix

" Remplacements conditionnels
if search('deprecated', 'n')
  %s/deprecated_func(\(.*\))/new_func(\1)/ge
endif

" Rapport
echo "Traitement terminé : " . expand('%')
wq
EOF

vim -u NONE -es -S /tmp/transform.vim fichier.py

# Vimscript avec fonctions
cat > /tmp/batch.vim << 'EOF'
function! ProcessFile()
  " Supprimer commentaires et lignes vides
  g/^\s*#/d
  g/^\s*$/d

  " Trim trailing whitespace
  %s/\s\+$//e

  " Reformater les imports (Python)
  %s/^import \(.*\), \(.*\)$/import \1\rimport \2/e

  update
endfunction

argdo call ProcessFile()
qa
EOF

vim -u NONE -es -S /tmp/batch.vim $(find . -name "*.py")
```

---

## 5. Macros et registres

### Enregistrement et replay via commandes ex
```bash
# Simuler une macro avec feedkeys (utile pour automatiser des actions complexes)
vim -es \
  -c 'call feedkeys("gg")' \
  -c 'g/^def /normal! A:  # TODO: add docstring' \
  -c 'wq' \
  module.py

# Utiliser un registre comme macro
vim -es \
  -c 'let @q = "I# \<Esc>j"' \
  -c 'normal! 1G' \
  -c 'normal! 10@q' \
  -c 'wq' \
  file.txt

# Exécuter une commande normale sur des lignes matchées
vim -es \
  -c 'g/pattern/normal! >>>' \
  -c 'wq' \
  file.txt
```

---

## 6. Patterns batch editing

### Refactoring en masse
```bash
# Renommer une fonction dans tout un projet
refactor_function() {
  local old_name="$1" new_name="$2"
  local files
  files=$(grep -rl "def ${old_name}\|${old_name}(" src/ --include="*.py")

  if [[ -z "$files" ]]; then
    echo "Aucun fichier à modifier"
    return 0
  fi

  echo "Fichiers à modifier :"
  echo "$files"
  echo ""
  read -rp "Confirmer ? [y/N] " confirm
  [[ "${confirm,,}" != "y" ]] && return 0

  # shellcheck disable=SC2086
  vim -u NONE -es \
    -c "argdo %s/\\b${old_name}\\b/${new_name}/ge | update" \
    -c 'qa' \
    $files

  echo "Refactoring terminé"
}

# Mettre à jour des numéros de version
bump_version() {
  local old_ver="$1" new_ver="$2"
  vim -u NONE -es \
    -c "argdo %s/${old_ver//./\\.}/${new_ver}/ge | update" \
    -c 'qa' \
    pyproject.toml setup.cfg CHANGELOG.md
}

# Ajouter un header de licence à des fichiers sans header
add_license_header() {
  local license_file="$1"
  shift
  for f in "$@"; do
    # Ne modifier que si le header est absent
    if ! grep -q "Copyright" "$f"; then
      vim -u NONE -es \
        -c "0r ${license_file}" \
        -c 'wq' \
        "$f"
    fi
  done
}
```

### Normalisation de fichiers
```bash
# Normaliser les fins de ligne (CRLF → LF)
fix_line_endings() {
  local file="$1"
  vim -u NONE -es \
    -c 'set ff=unix' \
    -c 'wq' \
    "$file"
}

# Convertir tabs → espaces
convert_tabs() {
  local file="$1" spaces="${2:-4}"
  vim -u NONE -es \
    -c "set expandtab tabstop=${spaces}" \
    -c '%retab' \
    -c 'wq' \
    "$file"
}

# Convertir espaces → tabs
convert_spaces_to_tabs() {
  local file="$1" spaces="${2:-4}"
  vim -u NONE -es \
    -c "set noexpandtab tabstop=${spaces}" \
    -c '%retab!' \
    -c 'wq' \
    "$file"
}
```

---

## 7. Vim comme filtre dans des pipelines

```bash
# Vim peut lire stdin et écrire stdout
echo "hello world" | vim - -es -c '%s/world/vim/g' -c 'p' -c 'q!'

# Plus pratique : utiliser vim pour des opérations complexes dans un pipeline
process_with_vim() {
  vim -u NONE -es \
    -c '%s/pattern/replacement/g' \
    -c '%p' \
    -c 'q!' \
    /dev/stdin 2>/dev/null
}
cat input.txt | process_with_vim > output.txt

# Filtrer des lignes avec global/print
grep_with_vim() {
  local pattern="$1"
  vim -u NONE -es \
    -c "g/${pattern}/p" \
    -c 'q!' \
    "$2" 2>/dev/null
}

# Préférer sed/awk pour les cas simples
# Utiliser vim quand :
# - Besoin de regex vim (\v, \ze, \zs, look-around)
# - Opérations multi-étapes avec état
# - Conversion d'encodage / fin de ligne
# - Indent/retab

# \zs et \ze — start/end du match (vim-specific)
vim -es -c '%s/prefix\zs.*\ze suffix/REMPLACÉ/g' -c 'wq' file.txt
# Remplace uniquement ce qui est entre "prefix" et "suffix"
```

### Quand choisir vim vs sed vs awk
| Besoin | Outil recommandé |
|--------|-----------------|
| Substitution simple | `sed` |
| Traitement de colonnes | `awk` |
| Filtrage de lignes | `grep` + `sed` |
| Regex multi-lignes complexe | `vim` |
| Conversion CRLF/tabs | `vim` ou `dos2unix` |
| Opérations multi-étapes avec état | `vim` script |
| Traitement de code avec indentation | `vim` |
| Performance sur gros fichiers | `awk` |
