# Text Processing — Référence sed / awk / grep

## Table des matières
1. [grep — Filtrage et recherche](#1-grep--filtrage-et-recherche)
2. [sed — Stream editor](#2-sed--stream-editor)
3. [awk — Traitement structuré](#3-awk--traitement-structuré)
4. [Pipelines combinés](#4-pipelines-combinés)
5. [Patterns courants par cas d'usage](#5-patterns-courants-par-cas-dusage)

---

## 1. grep — Filtrage et recherche

### Options essentielles
```bash
grep "pattern" file         # basique
grep -E "pat1|pat2" file    # ERE (Extended Regex) — préférer à egrep
grep -P "(?<=prefix)\w+"   # PCRE (Perl — puissant mais non POSIX)
grep -F "chaine.exacte"    # Fixed string — pas de regex, plus rapide
grep -i "pattern"          # case insensitive
grep -v "pattern"          # invert match (exclure)
grep -c "pattern"          # compter les lignes
grep -n "pattern"          # numéroter les lignes
grep -l "pattern" *.log    # lister les fichiers qui matchent
grep -L "pattern" *.log    # lister les fichiers qui NE matchent PAS
grep -r "pattern" dir/     # récursif
grep -rl "pattern" dir/    # récursif — fichiers seulement
grep -w "mot"              # mot entier uniquement
grep -x "ligne entière"    # ligne entière uniquement
grep -A 3 "pattern"        # 3 lignes après
grep -B 3 "pattern"        # 3 lignes avant
grep -C 3 "pattern"        # 3 lignes avant ET après (contexte)
grep -o "pattern"          # afficher uniquement la partie qui matche
grep -m 5 "pattern"        # stopper après 5 correspondances
grep -q "pattern"          # silencieux — code retour seulement
grep --include="*.py"      # filtrer par extension (avec -r)
grep --exclude="*.min.js"  # exclure des fichiers (avec -r)
```

### Regex utiles
```bash
# Ancres et quantificateurs
grep -E "^ERROR"           # début de ligne
grep -E "\.log$"           # fin de ligne
grep -E "colou?r"          # 0 ou 1 occurrence (color/colour)
grep -E "zo{2,4}m"         # 2 à 4 'o'
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"  # IP basique

# Groupes et alternance
grep -E "(ERROR|WARN|CRIT)"  # plusieurs niveaux de log
grep -E "^(GET|POST|PUT|DELETE) /"  # méthodes HTTP

# Lookahead / lookbehind (PCRE)
grep -P "(?<=port=)\d+"    # extraire le numéro de port
grep -P "password=\K\S+"   # \K = reset le début du match

# Exclusions combinées
grep -v "^#" config.conf | grep -v "^$"   # sans commentaires ni lignes vides
```

---

## 2. sed — Stream editor

### Syntaxe de base
```
sed [options] 'commande' fichier
sed [options] -e 'cmd1' -e 'cmd2' fichier
sed [options] -f script.sed fichier
```

Options globales :
```bash
-n          # supprime l'affichage automatique (avec p explicite)
-i          # in-place (modifie le fichier)
-i.bak      # in-place avec backup .bak
-E ou -r    # ERE (évite les escapes excessifs)
```

### Commande de substitution `s`
```bash
# Forme : s/pattern/remplacement/flags
sed 's/foo/bar/'           # 1ère occurrence par ligne
sed 's/foo/bar/g'          # toutes les occurrences (global)
sed 's/foo/bar/2'          # 2ème occurrence uniquement
sed 's/foo/bar/gi'         # toutes, case insensitive
sed 's/foo/bar/p'          # afficher si substitution (avec -n)
sed 's/foo/bar/w out.txt'  # écrire les lignes modifiées dans un fichier

# Délimiteurs alternatifs (évite d'échapper les /)
sed 's|/usr/local|/opt|g'
sed 's#/home/user#/tmp#g'

# Groupes de capture
sed -E 's/(foo)(bar)/\2\1/'          # inverser → barfoo
sed -E 's/([0-9]{4})-([0-9]{2})-([0-9]{2})/\3\/\2\/\1/'  # YYYY-MM-DD → DD/MM/YYYY
sed -E 's/^([^:]+):.*/\1/'          # extraire avant le premier :

# & — référence au match entier
sed 's/[0-9]*/[&]/'                  # entourer les nombres de []
sed 's/ERROR/>>> & <<</'             # encadrer les ERRORs

# Multilignes (GNU sed)
sed -z 's/\n/,/g'                    # remplacer newlines par virgules (-z = null-separated)
sed ':a;N;$!ba;s/\n/ /g'            # version POSIX — joindre toutes les lignes
```

### Adressage — cibler des lignes
```bash
sed '3s/foo/bar/'          # ligne 3 uniquement
sed '2,5s/foo/bar/'        # lignes 2 à 5
sed '2,+3s/foo/bar/'       # ligne 2 + les 3 suivantes (GNU)
sed '$s/foo/bar/'          # dernière ligne
sed '/pattern/s/foo/bar/'  # lignes contenant "pattern"
sed '/start/,/end/s/foo/bar/'  # entre deux patterns
sed '0,/pattern/s/foo/bar/'    # de début jusqu'au premier pattern (GNU)
sed '/pattern/!s/foo/bar/'     # lignes NE contenant PAS "pattern"
sed -n '10,20p'            # afficher lignes 10-20
sed '5q'                   # quitter après ligne 5
```

### Autres commandes sed
```bash
# d — delete
sed '/^#/d'                # supprimer les commentaires
sed '/^$/d'                # supprimer les lignes vides
sed '2,4d'                 # supprimer lignes 2-4

# p — print (avec -n)
sed -n '/ERROR/p'          # afficher uniquement les lignes ERROR
sed -n '5,10p'             # afficher lignes 5-10

# a — append (après la ligne)
sed '/pattern/a\Ligne ajoutée après'
sed '3a\Nouveau texte'

# i — insert (avant la ligne)
sed '/pattern/i\Ligne insérée avant'

# c — change (remplacer la ligne entière)
sed '/pattern/c\Nouvelle ligne complète'

# y — transliteration (comme tr)
sed 'y/abc/ABC/'           # a→A, b→B, c→C

# q — quit
sed '10q'                  # afficher les 10 premières lignes et quitter

# = — numéro de ligne
sed -n '/pattern/='        # afficher les numéros de lignes qui matchent

# r — read file (insérer contenu d'un fichier)
sed '/marker/r footer.txt' # insérer footer.txt après "marker"

# w — write to file
sed -n '/ERROR/w errors.txt' fichier.log

# Script multi-commandes
sed -e '/^#/d' -e '/^$/d' -e 's/  */ /g' fichier  # chaîner
```

### sed avancé — labels et branches
```bash
# Boucle pour traitement multi-lignes
sed ':loop; N; /pattern/!b loop; s/\n/ /g'

# Suppression des espaces de début/fin (trim)
sed 's/^[[:space:]]*//' <<< "  hello  "   # ltrim
sed 's/[[:space:]]*$//' <<< "  hello  "   # rtrim
sed 's/^[[:space:]]*//; s/[[:space:]]*$//' <<< "  hello  "  # trim complet

# Supprimer les lignes dupliquées consécutives
sed '$!N; /^\(.*\)\n\1$/!P; D'
```

---

## 3. awk — Traitement structuré

### Modèle d'exécution
```
awk 'BEGIN { init } /pattern/ { action } END { finale }' fichier
```

- `BEGIN` : exécuté une fois avant la lecture
- `END` : exécuté une fois après la lecture
- Pattern vide = toutes les lignes
- `NR` : numéro de ligne courante (toutes sources)
- `NF` : nombre de champs de la ligne courante
- `$0` : ligne entière, `$1` à `$NF` : champs

### Variables prédéfinies
```bash
FS   # séparateur de champs en entrée (défaut: espace/tab)
OFS  # séparateur de champs en sortie (défaut: espace)
RS   # séparateur de lignes en entrée (défaut: newline)
ORS  # séparateur de lignes en sortie (défaut: newline)
NR   # numéro de ligne courant
NF   # nombre de champs
FILENAME  # nom du fichier en cours
ARGV / ARGC  # arguments
```

### Syntaxe courante
```bash
# Sélection de champs
awk '{print $1, $3}' file            # champs 1 et 3
awk '{print $NF}' file               # dernier champ
awk '{print $(NF-1)}' file           # avant-dernier
awk -F: '{print $1}' /etc/passwd     # avec séparateur :
awk -F'[,;]' '{print $2}' file       # regex comme séparateur
awk 'BEGIN{FS=","} {print $1}' file  # via BEGIN

# Filtrage
awk 'NR>5'                           # à partir de la ligne 6
awk 'NR>=10 && NR<=20'              # lignes 10-20
awk '/pattern/'                      # lignes contenant pattern
awk '!/pattern/'                     # lignes ne contenant PAS pattern
awk '$3 > 100'                       # champ 3 > 100
awk 'NF > 3'                         # lignes avec plus de 3 champs
awk 'length($0) > 80'               # lignes > 80 caractères

# Calculs et agrégations
awk '{sum += $2} END {print sum}'                      # somme colonne 2
awk '{sum += $2; count++} END {print sum/count}'       # moyenne
awk 'BEGIN{max=0} $1>max{max=$1} END{print max}'       # maximum
awk '{if($2>max) max=$2} END{print max}'               # idem

# Comptage
awk '/ERROR/{count++} END{print count}' app.log
awk '{counts[$1]++} END{for(k in counts) print k, counts[k]}' file  # fréquence

# Reformatage
awk 'BEGIN{OFS=","} {print $1,$3,$5}'       # CSV avec champs sélectionnés
awk '{printf "%-20s %5d\n", $1, $2}'        # colonnes alignées
awk '{printf "%s=%s\n", $1, $2}'            # clé=valeur
```

### awk avancé
```bash
# Tableaux associatifs
awk '{
  count[$1]++
  total[$1] += $2
} END {
  for (svc in count)
    printf "%-20s calls=%-5d avg=%.2f\n", svc, count[svc], total[svc]/count[svc]
}' access.log

# Traitement multi-fichiers — NR vs FNR
awk 'FNR==1{print "==> " FILENAME}' *.log   # FNR repart à 1 par fichier

# Join de deux fichiers (awk comme SQL JOIN)
awk 'NR==FNR{map[$1]=$2; next} {print $0, map[$1]}' ref.csv data.csv

# Fonctions
awk '
function ltrim(s) { sub(/^[[:space:]]+/, "", s); return s }
function rtrim(s) { sub(/[[:space:]]+$/, "", s); return s }
function trim(s)  { return rtrim(ltrim(s)) }
{ print trim($0) }
'

# Blocs conditionnels
awk '{
  if ($1 ~ /^ERROR/) {
    print "CRITICAL:", $0 > "/dev/stderr"
  } else if ($1 ~ /^WARN/) {
    print "WARNING:", $0
  } else {
    next
  }
}' app.log

# Traitement CSV avec guillemets (basique — pour CSV simple)
awk -F'","' '{gsub(/^"|"$/, ""); print $2}' data.csv

# Pagination — afficher N lignes puis pause
awk 'NR%25==0{system("read")} {print}' big-file.txt

# In-place avec awk (via fichier temporaire)
awk '{gsub(/old/, "new"); print}' file > /tmp/tmp$$ && mv /tmp/tmp$$ file
```

---

## 4. Pipelines combinés

### Patterns classiques
```bash
# Extraire → filtrer → transformer → agréger
cat access.log \
  | grep "POST /api" \
  | grep -v "200" \
  | awk '{print $7}' \
  | sort | uniq -c | sort -rn \
  | head -20

# Traitement de logs structurés
grep "ERROR" app.log \
  | sed 's/.*\[ERROR\] //' \
  | awk -F: '{print $1}' \
  | sort | uniq -c | sort -rn

# Extraction de config
grep -E "^\s*[^#]" nginx.conf \
  | sed 's/;$//' \
  | awk '{key=$1; $1=""; print key "=" $0}' \
  | sed 's/= /=/'

# Comparaison de deux fichiers (colonnes)
join -t: -1 1 -2 1 \
  <(sort /etc/passwd) \
  <(sort /etc/shadow) \
  | awk -F: '{print $1, $3}'

# Remplacement dans de nombreux fichiers
grep -rl "ancien_pattern" src/ \
  | xargs sed -i 's/ancien_pattern/nouveau_pattern/g'

# Stats de performances
awk '/duration/{sum+=$NF; n++} END{printf "avg=%.0fms n=%d\n",sum/n,n}' perf.log

# Transformer JSON lines avec awk (sans jq)
awk -F'"' '/"error":/{print $4}' events.ndjson | sort | uniq -c
```

### Optimisations de performance
```bash
# Préférer grep pour filtrer AVANT awk (grep est plus rapide)
grep "ERROR" big.log | awk '{print $5}'    # ✅
awk '/ERROR/{print $5}' big.log            # OK mais grep + rapide en amont

# -F string vs regex — string est plus rapide
awk -F: '{print $1}' file     # ✅ séparateur string
awk -F'[:]' '{print $1}' file # ✅ même résultat mais regex (légèrement moins rapide)

# Éviter fork dans les boucles
# ❌ Lent : fork pour chaque ligne
while read line; do
  echo "$line" | sed 's/foo/bar/'
done < file

# ✅ Rapide : sed traite tout le fichier
sed 's/foo/bar/' file
```

---

## 5. Patterns courants par cas d'usage

### Fichiers de configuration
```bash
# Lire une valeur de config clé=valeur
get_config() {
  local key="$1" file="${2:-config.conf}"
  grep -E "^\s*${key}\s*=" "$file" \
    | sed -E "s/^\s*${key}\s*=\s*//" \
    | sed 's/[[:space:]]*#.*//' \
    | sed 's/[[:space:]]*$//' \
    | tail -1
}

# Modifier une valeur in-place
set_config() {
  local key="$1" value="$2" file="${3:-config.conf}"
  if grep -qE "^\s*${key}\s*=" "$file"; then
    sed -i -E "s|^\s*${key}\s*=.*|${key}=${value}|" "$file"
  else
    echo "${key}=${value}" >> "$file"
  fi
}

# Supprimer commentaires et lignes vides
clean_config() {
  grep -vE '^\s*#|^\s*$' "$1"
}
```

### Logs
```bash
# Extraire une plage temporelle
awk '/2024-01-15 10:00/,/2024-01-15 11:00/' app.log

# Compter les erreurs par heure
grep "ERROR" app.log \
  | awk '{print substr($2,1,5)}' \
  | sort | uniq -c

# Top N endpoints les plus lents
awk '$NF>1000 {print $7, $NF}' access.log \
  | sort -t' ' -k2 -rn \
  | head -20

# Surveiller un log en temps réel avec filtre
tail -f app.log | grep --line-buffered "ERROR\|WARN"
```

### Données CSV / TSV
```bash
# Sélectionner colonnes d'un CSV (sans guillemets imbriqués)
awk -F, 'NR>1{print $1","$3}' data.csv   # skip header, cols 1 et 3

# Filtrer sur une valeur
awk -F, '$3=="active" {print $1}' users.csv

# Additionner une colonne
awk -F, 'NR>1{sum+=$4} END{printf "Total: %.2f\n", sum}' sales.csv

# Convertir TSV → CSV
sed 's/\t/,/g' data.tsv > data.csv

# Trier un CSV par colonne (hors header)
{ head -1 data.csv; tail -n +2 data.csv | sort -t, -k3 -rn; } > sorted.csv
```

### Code source
```bash
# Compter les lignes de code (hors blancs et commentaires)
find src/ -name "*.py" \
  | xargs grep -vE '^\s*(#|$)' \
  | wc -l

# Trouver tous les TODO/FIXME avec contexte
grep -rn "TODO\|FIXME\|HACK\|XXX" src/ \
  | grep -v "node_modules\|.git" \
  | awk -F: '{printf "%s:%s\t%s\n", $1, $2, substr($0, index($0,$3))}'

# Extraire toutes les fonctions Python
grep -n "^def \|^    def " src/*.py \
  | sed -E 's/: *def /:def /' \
  | awk -F: '{printf "%s %-30s (ligne %s)\n", $1, $3, $2}'

# Remplacer un import dans tout un projet
grep -rl "from old_module import" src/ \
  | xargs sed -i 's/from old_module import/from new_module import/g'
```
