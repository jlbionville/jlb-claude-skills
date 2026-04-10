# SEO WordPress — Stratégies et checklists

## Checklist SEO complète par article

### Structure de contenu
- [ ] Titre H1 unique, contient le mot-clé principal
- [ ] Mot-clé dans les 100 premiers mots
- [ ] Structure H2/H3 logique et hiérarchique
- [ ] Longueur minimale : 600 mots (standard : 1200+)
- [ ] Paragraphes courts (3-4 lignes max)
- [ ] Listes à puces/numérotées pour les énumérations

### Métadonnées
- [ ] Titre SEO : 50-60 caractères (mot-clé en début)
- [ ] Méta-description : 150-160 caractères (mot-clé + CTA)
- [ ] Slug : court, descriptif, trait d'union, pas d'accents
- [ ] Canonical URL définie si contenu dupliqué

### Médias
- [ ] Image à la une définie
- [ ] Attribut `alt` sur toutes les images (contient le mot-clé sur l'image principale)
- [ ] Images compressées (< 200Ko idéalement)
- [ ] Nom de fichier image descriptif (ex: guide-wp-cli.jpg)

### Maillage
- [ ] 3-5 liens internes vers d'autres articles du site
- [ ] 1-2 liens externes vers des sources autoritaires
- [ ] Ancres de liens descriptives (pas "cliquez ici")

### Technique
- [ ] Article accessible aux robots (pas de noindex)
- [ ] URL canonique correcte
- [ ] Schéma markup si pertinent (Article, FAQ, HowTo)

---

## Mots-clés — Stratégie de ciblage

### Règle de base
Chaque article cible **1 mot-clé principal** + 2-4 **mots-clés secondaires** (variantes, synonymes, longue traîne).

### Template de brief SEO
```
MOT-CLÉ PRINCIPAL : [kw avec volume de recherche idéalement > 100/mois]
INTENTION         : [informationnelle / transactionnelle / navigationnelle]
MOTS-CLÉS SEC.    : [kw1], [kw2], [kw3]
CONCURRENTS       : [URL des 3 premiers résultats Google]
LONGUEUR CIBLE    : [basée sur les articles concurrents]
FORMAT PRIVILÉGIÉ : [article, guide, liste, comparatif, tutoriel]
```

---

## Yoast SEO — Clés meta complètes

```bash
# Article/Page
_yoast_wpseo_title           # Titre SEO personnalisé
_yoast_wpseo_metadesc        # Méta-description
_yoast_wpseo_focuskw         # Mot-clé focus
_yoast_wpseo_canonical        # URL canonique
_yoast_wpseo_meta-robots-noindex  # 1 = noindex
_yoast_wpseo_meta-robots-nofollow # 1 = nofollow

# Open Graph (réseaux sociaux)
_yoast_wpseo_opengraph-title       # Titre OG personnalisé
_yoast_wpseo_opengraph-description # Description OG
_yoast_wpseo_opengraph-image       # URL image OG

# Script WP-CLI pour appliquer SEO à un post
wp post meta update 42 _yoast_wpseo_title "Titre SEO — 60 car max" --path=/var/www/monsite
wp post meta update 42 _yoast_wpseo_metadesc "Description 150-160 car avec mot-clé" --path=/var/www/monsite
wp post meta update 42 _yoast_wpseo_focuskw "mot-clé principal" --path=/var/www/monsite
```

---

## RankMath — Clés meta complètes

```bash
rank_math_title              # Titre SEO
rank_math_description        # Méta-description
rank_math_focus_keyword      # Mot-clé focus (séparés par virgule pour plusieurs)
rank_math_canonical_url      # URL canonique
rank_math_robots             # ["noindex"] ou ["index","follow"]

# Open Graph
rank_math_facebook_title
rank_math_facebook_description
rank_math_facebook_image

# Schéma
rank_math_schema_Article     # JSON-LD Schema markup

# Appliquer via WP-CLI
wp post meta update 42 rank_math_title "Titre SEO" --path=/var/www/monsite
wp post meta update 42 rank_math_description "Méta-description 150-160 car." --path=/var/www/monsite
wp post meta update 42 rank_math_focus_keyword "mot-clé" --path=/var/www/monsite
```

---

## Schéma Markup — FAQ

Ajouter une FAQ structurée dans un article augmente la visibilité dans les résultats enrichis Google.

### Format HTML à injecter dans le contenu
```html
<!-- Schema FAQ — à inclure dans le contenu de l'article -->
<div class="wp-block-faq schema-faq">
  <details class="schema-faq-item">
    <summary class="schema-faq-question">Question 1 ?</summary>
    <div class="schema-faq-answer"><p>Réponse complète à la question 1.</p></div>
  </details>
  <details class="schema-faq-item">
    <summary class="schema-faq-question">Question 2 ?</summary>
    <div class="schema-faq-answer"><p>Réponse complète à la question 2.</p></div>
  </details>
</div>
```

---

## Audit SEO rapide d'un site

```bash
# Lister les articles sans méta-description Yoast
wp post list --post_type=post --post_status=publish --format=ids --path=/var/www/monsite | \
  xargs -I{} sh -c 'desc=$(wp post meta get {} _yoast_wpseo_metadesc --path=/var/www/monsite); \
  [ -z "$desc" ] && echo "Post {} : pas de méta-description"'

# Lister les articles sans image à la une
wp post list --post_type=post --post_status=publish --format=json --path=/var/www/monsite | \
  wp eval 'foreach(json_decode(file_get_contents("php://stdin"), true) as $p) { if(!get_post_thumbnail_id($p["ID"])) echo "ID {$p["ID"]} : pas d image à la une\n"; }'

# Compter les articles par catégorie
wp term list category --path=/var/www/monsite --format=table --fields=name,count
```

---

## Sitemap

```bash
# Yoast génère le sitemap automatiquement à :
# https://monsite.fr/sitemap_index.xml

# Forcer la regénération du sitemap Yoast
wp option delete wpseo_sitemap_cache_validator --path=/var/www/monsite
wp cache flush --path=/var/www/monsite

# Soumettre à Google Search Console via API (si configuré)
# → Utiliser l'interface GSC ou l'API Google directement
```
