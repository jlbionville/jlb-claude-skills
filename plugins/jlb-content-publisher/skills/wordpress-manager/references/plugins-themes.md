# Plugins & Thèmes — Commandes WP-CLI par extension

## Yoast SEO

```bash
# Lire les métadonnées SEO d'un post
wp post meta get 42 _yoast_wpseo_metadesc --path=/var/www/monsite
wp post meta get 42 _yoast_wpseo_title --path=/var/www/monsite
wp post meta get 42 _yoast_wpseo_focuskw --path=/var/www/monsite

# Écrire les métadonnées SEO
wp post meta update 42 _yoast_wpseo_metadesc "Description 150-160 car." --path=/var/www/monsite
wp post meta update 42 _yoast_wpseo_title "Titre SEO | Nom du Site" --path=/var/www/monsite
wp post meta update 42 _yoast_wpseo_focuskw "mot-clé principal" --path=/var/www/monsite

# Désactiver l'indexation d'un post
wp post meta update 42 _yoast_wpseo_meta-robots-noindex 1 --path=/var/www/monsite

# Vider le sitemap cache Yoast
wp option delete wpseo_sitemap_cache_validator --path=/var/www/monsite
```

---

## RankMath SEO

```bash
# Clés méta RankMath
wp post meta update 42 rank_math_title "Titre SEO" --path=/var/www/monsite
wp post meta update 42 rank_math_description "Méta-description" --path=/var/www/monsite
wp post meta update 42 rank_math_focus_keyword "mot-clé" --path=/var/www/monsite
wp post meta update 42 rank_math_robots '["index","follow"]' --path=/var/www/monsite
```

---

## ACF (Advanced Custom Fields)

```bash
# Lire un champ ACF d'un post
wp post meta get 42 mon_champ_acf --path=/var/www/monsite

# Écrire un champ ACF simple
wp post meta update 42 mon_champ_acf "valeur" --path=/var/www/monsite

# Champ ACF de type tableau (repeater) — utiliser JSON
wp post meta update 42 mon_repeater \
  '[{"sous_champ_1":"val1","sous_champ_2":"val2"}]' \
  --path=/var/www/monsite --format=json

# Lister tous les champs méta d'un post (pour debug ACF)
wp post meta list 42 --path=/var/www/monsite --format=table
```

---

## WP Rocket

```bash
# Vider tout le cache
wp rocket clean --confirm --path=/var/www/monsite

# Vider le cache d'une URL spécifique
wp rocket clean --urls=https://monsite.fr/ma-page/ --path=/var/www/monsite

# Précharger le cache
wp rocket preload --path=/var/www/monsite

# Alternative manuelle si plugin CLI WP Rocket non disponible
rm -rf /var/www/monsite/wp-content/cache/wp-rocket/*
rm -rf /var/www/monsite/wp-content/cache/busting/*

# Désactiver WP Rocket temporairement (maintenance)
wp plugin deactivate wp-rocket --path=/var/www/monsite
# ... opérations ...
wp plugin activate wp-rocket --path=/var/www/monsite
wp rocket preload --path=/var/www/monsite
```

---

## Wordfence

```bash
# Lancer un scan complet
wp wordfence scan --type=malware --path=/var/www/monsite

# Rapport de sécurité
wp wordfence report --path=/var/www/monsite

# Voir les IPs bloquées
wp wordfence blocked-ips --path=/var/www/monsite

# Bloquer une IP manuellement
wp wordfence block-ip 192.168.1.1 --path=/var/www/monsite

# Mode apprentissage firewall (désactiver)
wp option update wf_option_learningModeEnabled 0 --path=/var/www/monsite
```

### Checklist sécurité Wordfence
```bash
# 1. Vérifier les fichiers core WordPress
wp core verify-checksums --path=/var/www/monsite

# 2. Vérifier les plugins
wp plugin verify-checksums --all --path=/var/www/monsite

# 3. Lister les admins (repérer les inconnus)
wp user list --role=administrator --path=/var/www/monsite --format=table

# 4. Lister les applications passwords actives
wp user application-password list 1 --path=/var/www/monsite

# 5. Vérifier la version WordPress
wp core version --path=/var/www/monsite

# 6. Lister les plugins avec mises à jour disponibles
wp plugin list --update=available --path=/var/www/monsite --format=table
```

---

## Elementor

```bash
# Régénérer les CSS Elementor (résout les problèmes d'affichage)
wp elementor flush-css --path=/var/www/monsite

# Nettoyer le kit Elementor
wp elementor kit reset --path=/var/www/monsite

# Replacer des URLs (après migration)
wp elementor replace-urls https://ancien-site.fr https://nouveau-site.fr --path=/var/www/monsite

# Voir la version Elementor active
wp plugin get elementor --field=version --path=/var/www/monsite
```

---

## Migration / Remplacement d'URL (général)

```bash
# Après migration de domaine
wp search-replace 'https://ancien.fr' 'https://nouveau.fr' \
  --path=/var/www/monsite \
  --skip-columns=guid \
  --report-changed-only

# Dry-run (simulation sans modification)
wp search-replace 'https://ancien.fr' 'https://nouveau.fr' \
  --path=/var/www/monsite \
  --dry-run
```

---

## Diagnostic général

```bash
# Infos système complet
wp --info --path=/var/www/monsite

# Version PHP, WordPress, plugins actifs
wp core version --path=/var/www/monsite
php -v

# Tester la connexion DB
wp db check --path=/var/www/monsite

# Voir les erreurs PHP récentes (si WP_DEBUG_LOG actif)
tail -50 /var/www/monsite/wp-content/debug.log

# Activer le mode debug temporairement
wp config set WP_DEBUG true --raw --path=/var/www/monsite
wp config set WP_DEBUG_LOG true --raw --path=/var/www/monsite
# ... investiguer ...
wp config set WP_DEBUG false --raw --path=/var/www/monsite
```
