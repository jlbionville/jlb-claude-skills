# Workflows éditoriaux WordPress

## Mode 1 — Génération complète d'article

### Prompt interne à suivre
Quand l'utilisateur dit "rédige un article sur [sujet]", produire dans cet ordre :

1. **Brief éditorial** (confirmer avant de rédiger)
   - Sujet exact + angle
   - Audience cible
   - Longueur souhaitée (courte ~600 mots / standard ~1200 mots / longue ~2500 mots)
   - Ton (informatif, conversationnel, expert, commercial)

2. **Article complet** en Markdown
3. **Fiche SEO** (voir template ci-dessous)
4. **Commande de publication** (WP-CLI ou API REST)

### Template article standard
```markdown
# [Titre principal — contient le mot-clé]

[Introduction : 2-3 paragraphes]
- Hook (question, stat, situation)
- Problématique
- Promesse de l'article

## [H2 — Section principale 1]

[Contenu 200-300 mots]

### [H3 optionnel si sous-thème]

## [H2 — Section principale 2]

[Contenu 200-300 mots]

## [H2 — Section principale N]

## Conclusion

[Synthèse + CTA clair]
```

### Fiche SEO générée avec chaque article
```
FICHE SEO
─────────────────────────────────────
Titre SEO     : [60 car. max]
Méta-desc     : [150-160 car.]
Slug          : /mon-slug-seo-optimise/
Mot-clé princ.: [mot clé]
Mots-clés sec.: [kw1], [kw2], [kw3]
Catégorie     : [catégorie WP]
Tags          : [tag1], [tag2], [tag3]
Image mise en avant : [description suggérée]
Maillage interne suggéré :
  → [Article lié 1] : /slug-article-1/
  → [Article lié 2] : /slug-article-2/
  → [Article lié 3] : /slug-article-3/
─────────────────────────────────────
```

---

## Mode 2 — Complétion de plan

L'utilisateur fournit un plan structuré. Claude :
1. Respecte scrupuleusement le plan fourni
2. Développe chaque section (200-400 mots par H2)
3. Ajoute introduction et conclusion
4. Génère la fiche SEO

---

## Mode 3 — Correction et amélioration

Axes d'amélioration proposés systématiquement :
- **Clarté** : phrases trop longues, jargon inutile
- **Structure** : hiérarchie H2/H3, transitions
- **SEO** : densité mot-clé, balises, maillage
- **Engagement** : exemples concrets, visuels suggérés
- **CTA** : appel à l'action présent et clair

Retourner : texte corrigé + liste des modifications effectuées.

---

## Mode 4 — Publication directe

### Flux complet publication WP-CLI
```bash
# 1. Créer le fichier article
cat > /tmp/article.html << 'EOF'
<p>Contenu de l'article en HTML...</p>
EOF

# 2. Créer le post en brouillon
POST_ID=$(wp post create \
  --path=/var/www/monsite \
  --post_title="Titre de l'article" \
  --post_content="$(cat /tmp/article.html)" \
  --post_status=draft \
  --post_author=1 \
  --porcelain)

echo "Post créé : ID $POST_ID"

# 3. Ajouter les métadonnées SEO (Yoast)
wp post meta update $POST_ID _yoast_wpseo_metadesc "Ma méta-description" --path=/var/www/monsite
wp post meta update $POST_ID _yoast_wpseo_title "Titre SEO | Mon Site" --path=/var/www/monsite

# 4. Assigner catégorie et tags
wp post term add $POST_ID category 5 --path=/var/www/monsite
wp post term add $POST_ID post_tag 12 18 --path=/var/www/monsite

# 5. Définir l'image à la une (si ID média connu)
wp post meta update $POST_ID _thumbnail_id 88 --path=/var/www/monsite

# 6. Publier
wp post update $POST_ID --post_status=publish --path=/var/www/monsite

echo "Article publié : https://monsite.fr/?p=$POST_ID"
```

### Flux complet publication API REST (Python)
```python
import requests
import base64

# Configuration
SITE_URL = "https://monsite.fr"
WP_USER = "admin"
WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"

# Auth
credentials = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

# Payload article
payload = {
    "title": "Titre de l'article",
    "content": "<p>Contenu HTML de l'article</p>",
    "excerpt": "Méta-description de 150-160 caractères",
    "slug": "mon-slug-seo",
    "status": "draft",  # ou "publish"
    "categories": [5],
    "tags": [12, 18],
    "meta": {
        "_yoast_wpseo_metadesc": "Ma méta-description",
        "_yoast_wpseo_title": "Titre SEO | Mon Site"
    }
}

# Envoi
response = requests.post(f"{SITE_URL}/wp-json/wp/v2/posts", json=payload, headers=headers)
post = response.json()
print(f"Article créé — ID: {post['id']} — URL: {post['link']}")
```

---

## Tonalités disponibles

| Ton | Description | Usage |
|-----|-------------|-------|
| `informatif` | Neutre, factuel, pédagogique | Blog tutoriel, documentation |
| `conversationnel` | Chaleureux, direct, "tu" | Blog personnel, lifestyle |
| `expert` | Technique, précis, références | B2B, secteur spécialisé |
| `commercial` | Persuasif, bénéfices, CTA fort | Landing page, promotion |
| `journalistique` | Structuré, inverted pyramid | News, actualité |

---

## Gestion des pages (vs articles)

```bash
# Créer une page
wp post create \
  --post_type=page \
  --post_title="À propos" \
  --post_content="$(cat page.html)" \
  --post_status=publish \
  --path=/var/www/monsite

# Définir une page parente
wp post update 55 --post_parent=10 --path=/var/www/monsite

# Définir comme page d'accueil
wp option update page_on_front 55 --path=/var/www/monsite
wp option update show_on_front page --path=/var/www/monsite
```
