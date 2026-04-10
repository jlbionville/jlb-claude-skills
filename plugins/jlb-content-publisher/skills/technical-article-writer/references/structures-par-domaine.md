# Structures par domaine

Ossatures spécifiques à utiliser selon le domaine de l'article.
Adapter les titres au sujet concret, garder l'ordre des sections.

---

## AWS / Cloud

```markdown
## [Titre : le problème AWS concret, ex: "Pourquoi tes S3 buckets coûtent une fortune"]

### La situation : quand tu reçois la facture AWS du mois
*(Hook storytelling + persona)*

### Prérequis
- Compte AWS (free tier OK)
- AWS CLI configuré
- [Autres selon le sujet]

### Ce qu'on comprend mal sur [concept AWS]
*(Analogie du monde réel ici — AVANT l'explication technique)*

### Architecture : comment ça fonctionne vraiment
*(Diagramme Mermaid obligatoire pour les architectures)*

### Mise en pratique pas à pas
*(Blocs de code commentés ✅/❌)*

### Sécurité & bonnes pratiques IAM
*(Section obligatoire pour tout article AWS)*

### Optimisation des coûts
*(Si pertinent)*

### Pièges classiques
*(3-5 erreurs fréquentes avec la solution)*

### Ce qu'on retient
*(Conclusion narrative + leçon)*

### Pour aller plus loin
*(Liens AWS docs, articles connexes)*
```

**Prompts image typiques AWS :**
```
HERO: "A developer in a dark office looking at multiple screens with AWS cloud architecture 
diagrams, blue and orange light, cinematic, realistic"

SECTION (architecture): Diagramme Mermaid avec les services AWS impliqués
```

---

## Git / GitHub / GitLab

```markdown
## [Titre : le scénario Git catastrophique, ex: "J'ai pushé sur main par accident"]

### C'était un vendredi après-midi
*(Hook storytelling + persona — les vendredi sont magiques pour Git)*

### Prérequis
- Git installé (version X+)
- Notions de base (commit, push, branch)

### Comment Git pense (pas comme toi)
*(Analogie : Git comme un arbre généalogique, un journal de bord, etc.)*

### La commande / le workflow expliqué
*(Progression simple → complexe)*

### Cas pratique : reproduire et résoudre
*(Blocs de code avec le scénario complet)*
\```bash
# 🎬 Reproduire le problème
git ...  # Ce qui a mal tourné

# 🔧 La solution
git ...  # Explication de chaque option
\```

### Ce qui se passe sous le capot
*(Optionnel pour articles avancés — graphe de commits)*

### Les variantes selon ton cas
*(Tableau comparatif des options)*

### Pièges et commandes dangereuses
*(--force, reset --hard, etc. — avec les gardes-fous)*

### Ce qu'on retient
*(Conclusion narrative)*
```

**Prompts image typiques Git :**
```
HERO: "A tangled tree of branches slowly becoming organized, digital art, 
dark background, green terminal colors, metaphorical"

SECTION: Diagramme Mermaid gitGraph si le flow est complexe
```

---

## Python

```markdown
## [Titre : le problème Python courant, ex: "Arrête d'écrire du Python de 2015"]

### Ce script qui tourne depuis 3 ans
*(Hook storytelling + persona)*

### Prérequis
- Python 3.x+
- [Librairies nécessaires]
- Niveau : [Débutant / Intermédiaire]

### L'analogie : Python comme [métaphore]

### Le problème en détail
*(Code "avant" — ce qu'on fait mal et pourquoi)*
\```python
# ❌ Ce qu'on voit souvent (et pourquoi c'est problématique)
def ma_fonction():
    ...  # Explication du problème ici
\```

### La solution
*(Code "après" — progression pas à pas)*
\```python
# ✅ La version propre — expliquons chaque décision
def ma_fonction():
    ...  # Pourquoi ce choix
\```

### Aller plus loin : cas avancés
*(Optionnel selon le niveau cible)*

### Tests : comment vérifier que ça marche
*(Mini-section testing si pertinent)*

### Pièges et gotchas Python
*(Spécificités du langage liées au sujet)*

### Ce qu'on retient
*(Conclusion narrative)*
```

**Prompts image typiques Python :**
```
HERO: "A python snake coiled around a laptop keyboard, digital illustration, 
minimalist, dark background, purple and yellow accents"

SECTION: Schéma de flux si le code a une logique complexe
```

---

## Linux / WSL / Terminal

```markdown
## [Titre : le blocage Linux classique, ex: "Comprendre les permissions Unix en 10 minutes"]

### Première connexion SSH à 22h
*(Hook storytelling + persona — souvent quelqu'un qui découvre Linux)*

### Ce dont tu as besoin
- Linux / WSL2 / macOS terminal
- [Autres prérequis]

### Linux comme [analogie concrète]
*(Ex: permissions = clés d'appartement avec différents niveaux d'accès)*

### Comprendre avant de copier-coller
*(Section théorie courte mais indispensable)*

### En pratique : les commandes
\```bash
# 🔍 D'abord observer la situation
ls -la  # Que veulent dire ces symboles ?
#  → drwxr-xr-x = répertoire (d) + droits proprio + groupe + autres

# ✅ Modifier avec intention
chmod 755 mon-script.sh  # Pourquoi 755 et pas 777 ?
\```

### Automatiser avec un script
*(Si pertinent — script bash commenté)*

### WSL2 : spécificités Windows↔Linux
*(Section obligatoire si l'article concerne WSL)*

### Pièges courants
*(rm -rf, sudo, paths, etc.)*

### Ce qu'on retient
*(Conclusion narrative)*
```

**Prompts image typiques Linux :**
```
HERO: "A terminal screen with green text on black background in a dark room, 
cinematic, moody, hacker aesthetic but professional"

SECTION: ASCII diagram si l'architecture filesystem est importante
```

---

## DevOps / CI-CD / Infrastructure

```markdown
## [Titre : le dysfonctionnement DevOps, ex: "Ton pipeline CI/CD ment depuis des mois"]

### Le build qui passe en local mais plante en prod
*(Hook storytelling + persona)*

### Stack utilisée dans cet article
*(GitHub Actions / GitLab CI / Jenkins / etc.)*

### La philosophie DevOps en une image
*(Analogie : chaîne de montage, cuisine de restaurant, etc.)*

### Architecture du pipeline
*(Diagramme Mermaid obligatoire)*

### Configuration pas à pas
*(YAML commenté ligne par ligne)*
\```yaml
# pipeline.yml — Expliquons chaque bloc
name: CI Pipeline

on:
  push:
    branches: [main]  # ← Pourquoi main uniquement ?

jobs:
  test:
    runs-on: ubuntu-latest  # ← Ubuntu, pas Windows — voici pourquoi
\```

### Monitoring et alertes
*(Ce qu'on observe pour savoir si ça marche)*

### Pièges et anti-patterns
*(Ce qu'on voit trop souvent)*

### Ce qu'on retient
*(Conclusion narrative)*
```

**Prompts image typiques DevOps :**
```
HERO: "A factory assembly line with code snippets floating through each station, 
digital art, isometric view, blue and green colors"

SECTION: Diagramme Mermaid du pipeline
```

---

## AI/ML / LLM / MLOps

```markdown
## [Titre : le défi IA concret, ex: "Intégrer Claude dans ton app sans exploser la facture"]

### Le prototype qui coûtait 800€/mois
*(Hook storytelling + persona)*

### Ce qu'on suppose (souvent faux) sur les LLM / ML
*(Démystification — analogie humaine du concept)*

### Architecture : comment ça fonctionne réellement
*(Diagramme Mermaid pour le flux de données)*

### Implémentation progressive
*(Code Python/API commenté ✅/❌)*

### Évaluation et métriques
*(Comment mesurer que ça marche vraiment)*

### Coûts et optimisation
*(Section obligatoire pour tout article LLM/cloud AI)*

### Pièges : hallucinations, drift, latence
*(Problèmes spécifiques à l'IA avec les solutions)*

### Ce qu'on retient
*(Conclusion narrative)*
```

**Prompts image typiques AI/ML :**
```
HERO: "Neural network nodes connecting with golden light threads, dark background, 
abstract and elegant, professional tech illustration"

SECTION: Diagramme de flux de données si pipeline ML complexe
```
