# API REST WordPress — Référence complète

## Configuration de l'authentification

### Application Passwords (recommandé)
1. Dashboard WP → Utilisateurs → Profil → "Application Passwords"
2. Générer un mot de passe applicatif (format : `xxxx xxxx xxxx xxxx xxxx xxxx`)
3. Encoder en base64 : `echo -n 'user:xxxx xxxx xxxx xxxx xxxx xxxx' | base64`

```bash
# Variable d'environnement (à mettre dans ~/.bashrc ou ~/.zshrc)
export WP_AUTH_MONSITE="$(echo -n 'admin:xxxx xxxx xxxx xxxx' | base64)"
export WP_API_MONSITE="https://monsite.fr/wp-json/wp/v2"
```

---

## Posts — CRUD complet

### Lister les articles
```bash
# Derniers articles publiés
curl -s "$WP_API_MONSITE/posts?status=publish&per_page=10" \
  -H "Authorization: Basic $WP_AUTH_MONSITE" | jq '.[].title.rendered'

# Articles en brouillon
curl -s "$WP_API_MONSITE/posts?status=draft" \
  -H "Authorization: Basic $WP_AUTH_MONSITE" | jq '.[] | {id, title: .title.rendered}'
```

### Créer un article
```bash
curl -X POST "$WP_API_MONSITE/posts" \
  -H "Authorization: Basic $WP_AUTH_MONSITE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Titre de larticle",
    "content": "<p>Contenu HTML complet.</p><h2>Sous-titre</h2><p>Suite...</p>",
    "excerpt": "Méta-description 150-160 caractères.",
    "slug": "mon-slug-seo",
    "status": "draft",
    "categories": [5],
    "tags": [12, 18],
    "featured_media": 88
  }'
```

### Modifier un article existant
```bash
curl -X POST "$WP_API_MONSITE/posts/42" \
  -H "Authorization: Basic $WP_AUTH_MONSITE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Nouveau titre",
    "content": "<p>Contenu mis à jour</p>",
    "status": "publish"
  }'
```

### Supprimer un article
```bash
# Mettre à la corbeille
curl -X DELETE "$WP_API_MONSITE/posts/42" \
  -H "Authorization: Basic $WP_AUTH_MONSITE"

# Suppression définitive
curl -X DELETE "$WP_API_MONSITE/posts/42?force=true" \
  -H "Authorization: Basic $WP_AUTH_MONSITE"
```

---

## Pages

```bash
# Lister les pages
curl -s "$WP_API_MONSITE/pages" -H "Authorization: Basic $WP_AUTH_MONSITE" | \
  jq '.[] | {id, title: .title.rendered, slug}'

# Créer une page
curl -X POST "$WP_API_MONSITE/pages" \
  -H "Authorization: Basic $WP_AUTH_MONSITE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "À propos",
    "content": "<p>Contenu de la page</p>",
    "status": "publish",
    "parent": 0
  }'
```

---

## Médias

```bash
# Uploader une image
curl -X POST "$WP_API_MONSITE/media" \
  -H "Authorization: Basic $WP_AUTH_MONSITE" \
  -H "Content-Disposition: attachment; filename=mon-image.jpg" \
  -H "Content-Type: image/jpeg" \
  --data-binary @/chemin/vers/mon-image.jpg

# Réponse → récupérer l'ID pour l'utiliser comme featured_media
```

---

## Taxonomies

```bash
# Lister les catégories
curl -s "$WP_API_MONSITE/categories" | jq '.[] | {id, name, slug}'

# Créer une catégorie
curl -X POST "$WP_API_MONSITE/categories" \
  -H "Authorization: Basic $WP_AUTH_MONSITE" \
  -H "Content-Type: application/json" \
  -d '{"name": "Ma catégorie", "slug": "ma-categorie"}'

# Lister les tags
curl -s "$WP_API_MONSITE/tags" | jq '.[] | {id, name}'

# Créer un tag
curl -X POST "$WP_API_MONSITE/tags" \
  -H "Authorization: Basic $WP_AUTH_MONSITE" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mon tag"}'
```

---

## Utilisateurs

```bash
# Profil de l'utilisateur courant
curl -s "$WP_API_MONSITE/users/me" -H "Authorization: Basic $WP_AUTH_MONSITE"

# Lister les utilisateurs (admin requis)
curl -s "$WP_API_MONSITE/users" -H "Authorization: Basic $WP_AUTH_MONSITE" | \
  jq '.[] | {id, name, roles}'
```

---

## Client Python réutilisable

```python
"""
wp_api_client.py — Client WordPress REST API
Usage: from wp_api_client import WPClient
"""
import requests
import base64
from typing import Optional

class WPClient:
    def __init__(self, site_url: str, user: str, app_password: str):
        credentials = base64.b64encode(f"{user}:{app_password}".encode()).decode()
        self.base_url = f"{site_url.rstrip('/')}/wp-json/wp/v2"
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }

    def get_posts(self, status="publish", per_page=10):
        r = requests.get(f"{self.base_url}/posts",
                        params={"status": status, "per_page": per_page},
                        headers=self.headers)
        r.raise_for_status()
        return r.json()

    def create_post(self, title: str, content: str, status="draft",
                   excerpt="", slug="", categories=None, tags=None,
                   featured_media: Optional[int] = None):
        payload = {
            "title": title,
            "content": content,
            "status": status,
            "excerpt": excerpt,
            "slug": slug,
            "categories": categories or [],
            "tags": tags or [],
        }
        if featured_media:
            payload["featured_media"] = featured_media
        r = requests.post(f"{self.base_url}/posts", json=payload, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def update_post(self, post_id: int, **kwargs):
        r = requests.post(f"{self.base_url}/posts/{post_id}",
                         json=kwargs, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def delete_post(self, post_id: int, force=False):
        r = requests.delete(f"{self.base_url}/posts/{post_id}",
                           params={"force": force}, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_categories(self):
        r = requests.get(f"{self.base_url}/categories", headers=self.headers)
        r.raise_for_status()
        return r.json()

    def upload_media(self, file_path: str, title=""):
        with open(file_path, 'rb') as f:
            filename = file_path.split('/')[-1]
            headers = {**self.headers}
            headers["Content-Disposition"] = f"attachment; filename={filename}"
            del headers["Content-Type"]
            r = requests.post(f"{self.base_url}/media",
                            data=f, headers=headers,
                            params={"title": title})
        r.raise_for_status()
        return r.json()

# Exemple d'utilisation
if __name__ == "__main__":
    wp = WPClient(
        site_url="https://monsite.fr",
        user="admin",
        app_password="xxxx xxxx xxxx xxxx xxxx xxxx"
    )
    
    # Créer et publier un article
    post = wp.create_post(
        title="Mon article généré par Claude",
        content="<p>Contenu de l'article...</p>",
        excerpt="Méta-description courte",
        slug="mon-article-claude",
        status="publish",
        categories=[5],
        tags=[12]
    )
    print(f"Article publié : {post['link']}")
```

---

## Endpoints REST utiles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/wp/v2/posts` | GET | Lister les articles |
| `/wp/v2/posts` | POST | Créer un article |
| `/wp/v2/posts/{id}` | POST/PUT | Modifier un article |
| `/wp/v2/posts/{id}` | DELETE | Supprimer un article |
| `/wp/v2/pages` | GET/POST | Lister/créer des pages |
| `/wp/v2/media` | POST | Uploader un média |
| `/wp/v2/categories` | GET/POST | Catégories |
| `/wp/v2/tags` | GET/POST | Tags |
| `/wp/v2/users` | GET | Utilisateurs |
| `/wp/v2/users/me` | GET | Profil courant |
| `/wp/v2/settings` | GET/POST | Paramètres site (admin) |
