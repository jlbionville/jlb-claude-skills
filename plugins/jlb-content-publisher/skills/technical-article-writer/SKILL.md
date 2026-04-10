---
name: technical-article-writer
description: >
  Rédige des articles techniques en français sur des sujets DevOps, AWS, Git, Python, Linux/WSL, IA/ML.
  Utilise cette skill dès que l'utilisateur veut écrire, structurer, rédiger ou améliorer un article,
  un post de blog, un tutoriel ou un guide technique. La skill impose une structure éditoriale cohérente
  avec storytelling, persona fictif, analogies, illustrations (code commenté + image évocatrice),
  et optimisation SEO. Déclencher aussi si l'utilisateur dit "rédige un article sur X", "aide-moi à
  écrire un tuto sur Y", "je veux publier un post sur Z", ou demande un plan d'article.
---

# Technical Article Writer

Skill pour rédiger des articles techniques en français, cohérents, engageants et bien structurés,
ciblant un public junior → senior selon le sujet. Chaque article suit la même ossature éditoriale
avec storytelling, illustrations et SEO intégré.

---

## Étape 0 — Collecte d'informations (si absentes)

Avant de rédiger, s'assurer d'avoir :

| Info | Exemple |
|------|---------|
| **Sujet précis** | "Configurer un VPN site-à-site sur AWS" |
| **Domaine** | AWS / Git / Python / Linux-WSL / DevOps / AI-ML |
| **Niveau cible** | Débutant / Junior→Intermédiaire / Intermédiaire→Senior |
| **Longueur** | Court (800-1200 mots) / Standard (1500-2500) / Long (3000+) |
| **Angle storytelling** | Anecdote perso, bug en prod, découverte, migration, etc. |

Si des éléments manquent, poser **une seule question groupée** avant de démarrer.

---

## Étape 1 — Persona & Hook storytelling

### 1.1 Choisir un persona adapté au domaine
Consulter `references/personas.md` pour choisir ou créer un persona cohérent.
Le persona doit correspondre au niveau cible de l'article.

### 1.2 Rédiger le Hook (150-250 mots)
Structure obligatoire du hook :
```
[Situation concrète] → [Problème/tension] → [Promesse de résolution]
```

**Règles du hook :**
- Commencer par une scène vivante, pas par une définition
- Nommer le persona dès le 1er ou 2e paragraphe
- La douleur doit être reconnaissable par le lecteur cible
- Terminer sur une phrase d'accroche qui annonce le "avant/après"

**Exemple de hook réussi :**
> Il est 23h47. Thomas, dev backend chez une scale-up parisienne, fixe son terminal.
> Le pipeline CI/CD vient de péter en prod pour la 3ème fois cette semaine.
> La cause ? Un simple secret AWS hardcodé dans le code. Ce soir, il va tout refactoriser —
> et découvrir que la solution tenait en 3 commandes.

---

## Étape 2 — Structure de l'article

Utiliser systématiquement cette ossature (adapter les titres au sujet) :

```
## [Titre accrocheur avec le problème, pas la solution]

### Le contexte : quand ça arrive et pourquoi ça compte
### Prérequis
### [Titre section technique 1] — L'analogie
### [Titre section technique 2] — La mise en pratique
### [Titre section technique 3] — Aller plus loin
### Pièges classiques à éviter
### Ce qu'on retient (leçon narrative)
### Pour aller plus loin (liens, ressources)
```

Pour les structures détaillées par domaine, voir `references/structures-par-domaine.md`.

---

## Étape 3 — Analogie du monde réel

Chaque concept technique complexe doit être accompagné d'une **analogie concrète**.

**Règle de l'analogie :**
- Elle doit être compréhensible sans connaissance technique
- Elle précède toujours l'explication technique (pas après)
- Elle doit fonctionner à deux niveaux : surface ET profondeur

**Exemples par domaine :**
- AWS IAM → "Le badge d'accès à un immeuble de bureaux"
- Git rebase → "Réécrire un brouillon avant de l'envoyer"
- Docker → "Une boîte de livraison standardisée"
- CI/CD pipeline → "La chaîne de montage d'une usine"
- Python decorator → "Un emballage cadeau qui change le contenu apparent"

---

## Étape 4 — Illustrations

### 4.1 Blocs de code commentés (obligatoire)
Chaque bloc de code doit être **pédagogique**, pas juste fonctionnel.

**Format obligatoire :**
```
# ✅ Ce qu'on veut faire : [objectif en 1 ligne]
# ❌ Ce qu'on évitait avant : [ancien problème]

[code]  # ← Explication inline de CE que fait cette ligne
[code]  # ← Pourquoi ce choix plutôt qu'une autre approche
```

Voir `references/code-templates.md` pour les templates par domaine.

### 4.2 Image évocatrice (obligatoire)
Pour chaque article, spécifier **une image principale** et **une image de section** selon la règle :

**Image principale (Hero image) :**
- Doit évoquer l'émotion du problème OU la satisfaction de la solution
- Peut être une photo réelle, une illustration, une métaphore visuelle
- Format : paysage 16:9, prompt de génération à fournir si IA

**Image de section (optionnelle, 1-2 par article) :**
- Diagramme d'architecture Mermaid pour les flux complexes
- Screenshot annoté (spécifier les annotations en texte)
- Illustration métaphorique si le concept est abstrait

**Prompts image à générer systématiquement :**
Pour chaque article, produire 2 prompts d'image prêts à l'emploi :
```
HERO IMAGE PROMPT:
[Description en anglais pour générateur IA : style, sujet, ambiance, couleurs]

SECTION IMAGE PROMPT (si pertinent):
[Description du diagramme ou de l'illustration secondaire]
```

### 4.3 Diagrammes Mermaid (si architecture)
Utiliser pour : pipelines CI/CD, architectures AWS, flux Git, séquences d'appels API.
```mermaid
graph LR / sequenceDiagram / flowchart TD
```

---

## Étape 5 — Rédaction du corps technique

**Principes de rédaction :**
- Paragraphes courts (3-5 lignes max)
- Une idée par paragraphe
- Alterner : explication → exemple → code → résultat attendu
- Voix active, présent de narration
- Tutoiement systématique

**Progression pédagogique :**
```
Concept simple → Complication → Solution partielle → Problème suivant → Solution complète
```
(Ne jamais donner la solution complète dès le début)

**Niveau de langage selon le public :**
- Débutant : définir tous les acronymes, analogies simples
- Junior→Intermédiaire : acronymes définis une fois, focus sur le "pourquoi"
- Intermédiaire→Senior : focus sur les trade-offs, cas limites, performance

---

## Étape 6 — Conclusion narrative

La conclusion doit boucler la boucle du storytelling :

```
1. Rappeler la scène d'ouverture (le persona et son problème)
2. Montrer la transformation (ce qu'il sait/peut faire maintenant)
3. La leçon universelle (applicable au-delà du cas technique)
4. Call-to-action doux (commenter, partager, essayer)
```

**Exemple de conclusion :**
> Il est maintenant 00h32. Thomas a revu toute son infra.
> Ses secrets sont dans AWS Secrets Manager, son pipeline est vert.
> La vraie leçon ? Ce n'était pas un problème de code, c'était un problème de confiance —
> savoir à qui on donne les clés. En prod comme dans la vie.
> Et toi, tu géères tes secrets comment ? Dis-le en commentaire. 👇

---

## Étape 7 — SEO & Métadonnées

Produire systématiquement en fin d'article :

```
📌 SEO BLOCK
─────────────────────────────────────────
Title tag (60 car. max)  : [titre optimisé]
Meta description (155 car.): [description engageante avec mot-clé principal]
Slug suggéré             : /[domaine]/[mot-cle-principal]-[contexte]
Mots-clés primaires      : [3-5 mots-clés]
Mots-clés secondaires    : [5-8 mots-clés longue traîne]
Intent de recherche      : Informationnelle / Navigationnelle / Transactionnelle
Niveau E-E-A-T           : [ce qui prouve l'expertise dans l'article]
Liens internes suggérés  : [2-3 sujets connexes à linker]
─────────────────────────────────────────
```

---

## Checklist finale avant livraison

Vérifier chaque point avant de livrer l'article :

- [ ] Hook avec persona nommé et problème reconnaissable
- [ ] Au moins 1 analogie du monde réel
- [ ] Blocs de code avec commentaires pédagogiques (✅/❌)
- [ ] 2 prompts d'image générés (hero + section si pertinent)
- [ ] Diagramme Mermaid si architecture complexe
- [ ] Conclusion qui boucle le storytelling
- [ ] SEO block complet
- [ ] Tutoiement cohérent tout au long
- [ ] Longueur cible respectée

---

## Références

- `references/personas.md` — Personas disponibles par domaine
- `references/structures-par-domaine.md` — Ossatures spécifiques AWS / Git / Python / Linux / AI-ML
- `references/code-templates.md` — Templates de blocs de code commentés par domaine
