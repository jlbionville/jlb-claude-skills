# Maintenance WordPress — Procédures complètes

## Checklist mensuelle

```bash
#!/bin/bash
# maintenance-mensuelle.sh — à adapter par site
SITE_PATH="/var/www/monsite"
BACKUP_DIR="/backups/monsite"
DATE=$(date +%Y%m%d)

echo "=== MAINTENANCE MENSUELLE WordPress ==="
echo "Site : $SITE_PATH"
echo "Date : $DATE"
echo ""

# 1. Sauvegarde préventive
echo "1. Sauvegarde de la base de données..."
wp db export "$BACKUP_DIR/db-$DATE.sql" --path=$SITE_PATH
echo "   ✓ DB sauvegardée : db-$DATE.sql"

# 2. Mises à jour WordPress core
echo "2. Mise à jour WordPress core..."
wp core update --path=$SITE_PATH
wp core update-db --path=$SITE_PATH
echo "   ✓ Core à jour : $(wp core version --path=$SITE_PATH)"

# 3. Mise à jour plugins
echo "3. Mise à jour des plugins..."
wp plugin update --all --path=$SITE_PATH
echo "   ✓ Plugins mis à jour"

# 4. Mise à jour thèmes
echo "4. Mise à jour des thèmes..."
wp theme update --all --path=$SITE_PATH
echo "   ✓ Thèmes mis à jour"

# 5. Nettoyage DB
echo "5. Nettoyage de la base de données..."
wp post delete $(wp post list --post_type=revision --format=ids --path=$SITE_PATH) --force --path=$SITE_PATH 2>/dev/null
wp comment delete $(wp comment list --status=spam --format=ids --path=$SITE_PATH) --force --path=$SITE_PATH 2>/dev/null
wp transient delete --expired --path=$SITE_PATH
wp db optimize --path=$SITE_PATH
echo "   ✓ Base nettoyée et optimisée"

# 6. Vider les caches
echo "6. Vidage des caches..."
wp cache flush --path=$SITE_PATH
wp rocket clean --confirm --path=$SITE_PATH 2>/dev/null || rm -rf /var/www/monsite/wp-content/cache/wp-rocket/*
echo "   ✓ Caches vidés"

# 7. Vérification sécurité
echo "7. Vérification intégrité core..."
wp core verify-checksums --path=$SITE_PATH
wp plugin verify-checksums --all --path=$SITE_PATH
echo "   ✓ Vérification terminée"

echo ""
echo "=== MAINTENANCE TERMINÉE ==="
```

---

## Sauvegarde complète

### Base de données
```bash
# Export simple
wp db export /backups/monsite-db-$(date +%Y%m%d-%H%M).sql --path=/var/www/monsite

# Export compressé
wp db export - --path=/var/www/monsite | gzip > /backups/monsite-db-$(date +%Y%m%d).sql.gz

# Export d'une table spécifique
wp db export /backups/wp-posts.sql --tables=wp_posts --path=/var/www/monsite
```

### Fichiers
```bash
# Archive complète du site
tar -czf /backups/monsite-files-$(date +%Y%m%d).tar.gz \
  --exclude='/var/www/monsite/wp-content/cache' \
  /var/www/monsite/

# Seulement wp-content (uploads, plugins, themes)
tar -czf /backups/wp-content-$(date +%Y%m%d).tar.gz \
  /var/www/monsite/wp-content/
```

### Restauration
```bash
# Restaurer la base de données
wp db import /backups/monsite-db-20240115.sql --path=/var/www/monsite

# Restaurer et remplacer l'URL si changement de domaine
wp db import /backups/monsite-db-20240115.sql --path=/var/www/monsite
wp search-replace 'https://ancien.fr' 'https://nouveau.fr' --path=/var/www/monsite
wp cache flush --path=/var/www/monsite
```

---

## Mode maintenance (site inaccessible aux visiteurs)

```bash
# Activer le mode maintenance
wp maintenance-mode activate --path=/var/www/monsite

# Vérifier le statut
wp maintenance-mode status --path=/var/www/monsite

# Désactiver
wp maintenance-mode deactivate --path=/var/www/monsite
```

---

## Diagnostic de performance

```bash
# Taille de la base de données par table
wp db query "SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb 
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
ORDER BY size_mb DESC;" --path=/var/www/monsite

# Nombre de révisions accumulées
wp db query "SELECT COUNT(*) as revisions FROM wp_posts WHERE post_type='revision';" --path=/var/www/monsite

# Nombre de transients
wp db query "SELECT COUNT(*) FROM wp_options WHERE option_name LIKE '_transient_%';" --path=/var/www/monsite

# Taille des uploads
du -sh /var/www/monsite/wp-content/uploads/
```

---

## Procédure migration site

```bash
# ÉTAPE 1 — Sur l'ancien serveur
wp db export migration.sql --path=/var/www/ancien-site
tar -czf wp-content.tar.gz /var/www/ancien-site/wp-content/

# ÉTAPE 2 — Transférer les fichiers
scp migration.sql user@nouveau-serveur:/var/www/nouveau-site/
scp wp-content.tar.gz user@nouveau-serveur:/var/www/nouveau-site/

# ÉTAPE 3 — Sur le nouveau serveur
cd /var/www/nouveau-site
wp db import migration.sql --path=.
tar -xzf wp-content.tar.gz --strip-components=4
wp search-replace 'https://ancien.fr' 'https://nouveau.fr' --path=. --skip-columns=guid
wp cache flush --path=.

# ÉTAPE 4 — Vérifications
wp core verify-checksums --path=.
wp option get siteurl --path=.
wp option get home --path=.
```

---

## Gestion wp-config.php

```bash
# Voir toutes les constantes définies
wp config list --path=/var/www/monsite

# Modifier une valeur
wp config set WP_DEBUG false --raw --path=/var/www/monsite
wp config set WP_MEMORY_LIMIT 256M --path=/var/www/monsite

# Ajouter une constante personnalisée
wp config set MON_API_KEY "valeur" --type=constant --path=/var/www/monsite

# Voir la valeur d'une constante
wp config get WP_DEBUG --path=/var/www/monsite
```
