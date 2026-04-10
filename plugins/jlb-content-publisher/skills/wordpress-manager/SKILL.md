---
name: wordpress-manager
description: >
  Skill complète pour gérer un ou plusieurs sites WordPress via WP-CLI, l'API REST,
  SSH et l'interface admin. Utilise cette skill dès que l'utilisateur mentionne WordPress,
  WP-CLI, un article à rédiger ou publier, des plugins, des thèmes, des utilisateurs,
  la sécurité ou la maintenance d'un site WordPress. Déclencher aussi pour : "rédige
  un article sur X", "mets à jour mes plugins", "crée un utilisateur WordPress",
  "publie ce contenu sur mon site", "nettoie ma base WP", "optimise mon site WordPress",
  "génère une commande WP-CLI pour...", "configure Yoast/RankMath", "vide le cache
  WP Rocket", "check sécurité Wordfence", ou tout contexte où l'utilisateur veut
  interagir avec un site WordPress, que ce soit en local ou en production.
---

# WordPress Manager Skill

Skill de gestion complète de sites WordPress (multi-sites) via WP-CLI, API REST, SSH et interface admin.

## Contexte utilisateur

- **Sites** : plusieurs sites distincts → toujours demander/confirmer le site cible
- **Extensions clés** : Yoast SEO / RankMath, Elementor / builder visuel, Wordfence, WP Rocket, ACF
- **Environnement** : Claude Desktop avec accès WP-CLI local ou SSH distant
- **Workflows rédaction** : génération complète, complétion de plan, correction, publication directe via API

---

## 1. Gestion multi-sites — Profils

Avant toute action, **identifier le site cible**. Proposer à l'utilisateur de définir des profils si ce n'est pas déjà fait.

### Structure d'un profil site
```
Nom         : monsite-prod
URL         : https://monsite.fr
Chemin WP   : /var/www/monsite/
WP-CLI path : wp (ou /usr/local/bin/wp)
API Base    : https://monsite.fr/wp-json/wp/v2
Auth        : Application Password (stocké en variable d'env WP_APP_PASS_MONSITE)
SSH         : user@monsite.fr (si distant)
```

> Toujours utiliser `--path=/var/www/monsite` avec WP-CLI pour cibler le bon site.
> Pour WP Multisite : ajouter `--url=sous-domaine.monsite.fr`

---

## 2. Rédaction et gestion d'articles/pages

Consulte `references/editorial.md` pour les workflows détaillés selon le mode choisi.

### Modes disponibles

| Mode | Déclencheur utilisateur | Action Claude |
|------|------------------------|---------------|
| **Génération complète** | "Rédige un article sur X" | Produit titre, plan, contenu, méta, slug |
| **Complétion de plan** | "Complète ce plan : ..." | Développe chaque section fournie |
| **Correction/amélioration** | "Améliore cet article" | Reformule, enrichit, corrige le ton |
| **Publication directe** | "Publie cet article" | Génère commande WP-CLI ou appel API REST |

### Structure d'article générée systématiquement
```
Titre principal (H1)          ← accrocheur + mot-clé principal
├── Introduction              ← hook + problématique + promesse
├── H2 Section 1
│   └── H3 sous-section
├── H2 Section 2
│   └── H3 sous-section
├── H2 Section N
└── Conclusion + CTA

Méta-description (150-160 car.)
Slug URL (court, mots-clés)
Tags suggérés
Catégorie recommandée
Maillage interne (3-5 liens suggérés)
```

### Publication via WP-CLI
```bash
# Créer un article en brouillon
wp post create \
  --path=/var/www/monsite \
  --post_title="Titre de l'article" \
  --post_content="$(cat article.html)" \
  --post_status=draft \
  --post_author=1 \
  --post_category=5

# Publier immédiatement
wp post create ... --post_status=publish

# Mettre à jour un article existant (ID 42)
wp post update 42 --post_content="$(cat article.html)" --path=/var/www/monsite
```

### Publication via API REST
```bash
curl -X POST https://monsite.fr/wp-json/wp/v2/posts \
  -H "Authorization: Basic $(echo -n 'user:app_password' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Titre de larticle",
    "content": "<p>Contenu HTML</p>",
    "status": "draft",
    "slug": "mon-slug-seo",
    "excerpt": "Méta-description ici",
    "categories": [5],
    "tags": [12, 18]
  }'
```

### Intégration Yoast SEO / RankMath via WP-CLI
```bash
# Yoast — définir méta-description et titre SEO
wp post meta update 42 _yoast_wpseo_metadesc "Ma méta-description" --path=/var/www/monsite
wp post meta update 42 _yoast_wpseo_title "Titre SEO | Mon Site" --path=/var/www/monsite

# RankMath
wp post meta update 42 rank_math_description "Ma méta-description" --path=/var/www/monsite
wp post meta update 42 rank_math_title "Titre SEO | Mon Site" --path=/var/www/monsite
```

---

## 3. Gestion des plugins et thèmes

Consulte `references/plugins-themes.md` pour les commandes détaillées par extension.

### Commandes essentielles plugins
```bash
# Lister avec statut
wp plugin list --path=/var/www/monsite --format=table

# Mettre à jour tous les plugins
wp plugin update --all --path=/var/www/monsite

# Mettre à jour un plugin spécifique
wp plugin update woocommerce --path=/var/www/monsite

# Activer / désactiver
wp plugin activate wordfence --path=/var/www/monsite
wp plugin deactivate elementor --path=/var/www/monsite

# Installer depuis wordpress.org
wp plugin install query-monitor --activate --path=/var/www/monsite
```

### Thèmes
```bash
wp theme list --path=/var/www/monsite
wp theme activate astra --path=/var/www/monsite
wp theme update --all --path=/var/www/monsite
```

### Checklist mise à jour sécurisée
1. `wp db export backup-avant-maj.sql --path=/var/www/monsite`
2. `wp plugin update --all --path=/var/www/monsite`
3. `wp theme update --all --path=/var/www/monsite`
4. Vérifier le site visuellement
5. `wp cache flush --path=/var/www/monsite`

---

## 4. Gestion des utilisateurs

```bash
# Lister les utilisateurs
wp user list --path=/var/www/monsite --format=table

# Créer un utilisateur
wp user create john john@example.com \
  --role=editor \
  --user_pass=MotDePasseSecurise! \
  --path=/var/www/monsite

# Changer le rôle
wp user set-role 3 author --path=/var/www/monsite

# Réinitialiser le mot de passe
wp user update 3 --user_pass=NouveauMotDePasse --path=/var/www/monsite

# Supprimer (réassigner les posts à l'user ID 1)
wp user delete 3 --reassign=1 --path=/var/www/monsite
```

### Rôles WordPress
| Rôle | Accès |
|------|-------|
| `administrator` | Accès total |
| `editor` | Gère tous les contenus |
| `author` | Ses propres articles |
| `contributor` | Rédige, ne publie pas |
| `subscriber` | Lecture seule |

---

## 5. Configuration et maintenance

Consulte `references/maintenance.md` pour les procédures complètes.

### Nettoyage base de données
```bash
# Supprimer révisions (garder les 5 dernières)
wp post delete $(wp post list --post_type=revision --format=ids) --force --path=/var/www/monsite

# Vider la corbeille
wp post delete $(wp post list --post_status=trash --format=ids) --force --path=/var/www/monsite

# Spam comments
wp comment delete $(wp comment list --status=spam --format=ids) --force --path=/var/www/monsite

# Optimiser les tables
wp db optimize --path=/var/www/monsite

# Nettoyer les transients expirés
wp transient delete --expired --path=/var/www/monsite
```

### WP Rocket — Vider le cache
```bash
# Via WP-CLI (plugin WP-CLI pour WP Rocket requis)
wp rocket clean --confirm --path=/var/www/monsite

# Alternative : vider manuellement le dossier cache
rm -rf /var/www/monsite/wp-content/cache/wp-rocket/*
```

### Wordfence — Diagnostic sécurité
```bash
# Lancer un scan
wp wordfence scan --type=malware --path=/var/www/monsite

# Voir les alertes bloquées
wp wordfence report --path=/var/www/monsite
```

### Sauvegarde complète
```bash
# Base de données
wp db export /backups/monsite-$(date +%Y%m%d).sql --path=/var/www/monsite

# Fichiers (depuis SSH)
tar -czf /backups/monsite-files-$(date +%Y%m%d).tar.gz /var/www/monsite/
```

---

## 6. Médias et médiathèque

```bash
# Régénérer les miniatures
wp media regenerate --yes --path=/var/www/monsite

# Importer une image depuis une URL
wp media import https://example.com/image.jpg \
  --title="Mon image" \
  --alt="Description alt" \
  --path=/var/www/monsite

# Lister les médias orphelins
wp media list --post_parent=0 --format=table --path=/var/www/monsite
```

---

## 7. SEO et métadonnées

Consulte `references/seo.md` pour les stratégies SEO détaillées.

### Checklist SEO par article (générée automatiquement)
- [ ] Titre H1 contient le mot-clé principal
- [ ] Méta-description 150-160 caractères
- [ ] Slug court et descriptif (sans stop words)
- [ ] Au moins 1 image avec attribut `alt`
- [ ] Maillage interne : 3-5 liens vers d'autres articles
- [ ] Structure H2/H3 logique
- [ ] Score lisibilité Yoast ≥ vert

---

## Comportement général

### Toujours faire en premier
1. **Identifier le site cible** si multi-sites
2. **Confirmer les actions destructives** (suppression, mise à jour en masse)
3. **Proposer une sauvegarde DB** avant toute opération risquée
4. **Formater les commandes WP-CLI** avec le bon `--path`

### Format des réponses
- Commandes WP-CLI → bloc `bash` avec commentaires
- Appels API REST → bloc `bash` avec `curl` complet
- Articles générés → Markdown structuré H1/H2/H3
- Checklists → cases à cocher `[ ]`

### En cas d'ambiguïté
Demander : site cible, environnement (local/prod), version WordPress si pertinent.

---

## Références disponibles

| Fichier | Contenu |
|---------|---------|
| `references/editorial.md` | Workflows rédaction détaillés, templates articles |
| `references/plugins-themes.md` | Commandes par extension (Yoast, Elementor, ACF, WP Rocket, Wordfence) |
| `references/maintenance.md` | Procédures maintenance, sauvegardes, diagnostic |
| `references/seo.md` | Stratégies SEO, checklist, intégration Yoast/RankMath |
| `references/api-rest.md` | Référence complète API REST WP avec exemples curl/Python |
