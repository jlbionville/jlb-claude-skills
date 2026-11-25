---
name: atlassian-rest-api
description: >
  Use when a program creates Jira Cloud issues or Confluence Cloud pages through the REST
  API (not the MCP connector): endpoints and exact request bodies, API token Basic auth,
  Markdown converted to Atlassian Document Format (ADF) or Confluence storage format,
  building the created issue / page URL, summarizing 400 / 401 / 404 error bodies without
  leaking them. Déclencheurs FR : « créer un ticket Jira par l'API », « créer une page
  Confluence », « ADF », « storage format », « spaceId », « jeton d'API Atlassian »,
  « Basic auth », « errorMessages », « publier un Markdown vers Jira / Confluence ».
  Pour lire ou chercher dans Jira / Confluence depuis Claude, utiliser le plugin atlassian
  (MCP) plutôt que cette skill.
---

# Publier vers Jira et Confluence Cloud par l'API REST

## Vue d'ensemble

Jira Cloud (API v3) attend une **description en ADF** (JSON) ; Confluence Cloud (API v2)
attend un **corps en storage format** (XHTML restreint). Un seul compte Atlassian (e-mail
+ jeton d'API) sert à toutes les organisations : l'authentification est HTTP Basic
`email:jeton`, encodée en base64, jamais journalisée. Faits vérifiés le 2026-11-25 sur les
OpenAPI publics et des réponses réelles.

## Quand l'utiliser

- Écrire ou corriger un adaptateur « publier ce Markdown comme ticket / page ».
- Convertir du Markdown en ADF ou en storage format.
- Présenter proprement une erreur Atlassian.
- Ne pas l'utiliser pour : rechercher, lire, commenter ou transitionner des tickets
  depuis une session Claude (plugin `atlassian`, MCP), ni pour OAuth 2.0 (3LO).

## Authentification

```
Authorization: Basic base64("<email>:<jeton d'API>")
Accept: application/json
```

- Le jeton se crée sur <https://id.atlassian.com/manage-profile/security/api-tokens> ;
  il est lié au **compte**, pas au site : un même jeton sert plusieurs organisations
  (`https://<site>.atlassian.net`).
- Le `Debug` du type d'authentification affiche `Secret(***)` ; l'en-tête n'apparaît
  dans aucun journal (journaliser seulement le chemin appelé : `Appel Atlassian /rest/…`).
- Site valide : `https://…` sans `/` final ; valider avant d'appeler.

## Créer un ticket Jira : `POST {site}/rest/api/3/issue`

```json
{"fields": {
   "project": {"key": "PROJ"},
   "issuetype": {"name": "Task"},
   "summary": "Titre (80 caractères max conseillé)",
   "description": {"type": "doc", "version": 1, "content": [ …ADF… ]}}}
```

- Réponse **201** : `{"id": "10001", "key": "PROJ-12", "self": "…"}` ; URL pour
  l'utilisateur : `{site}/browse/{key}`.
- `description` doit être un **document ADF**, pas une chaîne ; sous-ensemble sûr dans
  `references/adf-subset.md`.
- `issuetype.name` dépend du projet (`Task`, `Bug`, `Story`…) ; un nom inconnu → 400
  `errors.issuetype`.

## Créer une page Confluence : `POST {site}/wiki/api/v2/pages`

```json
{"spaceId": "123", "status": "current", "title": "Titre",
 "body": {"representation": "storage", "value": "<h1>…</h1><p>…</p>"}}
```

- `spaceId` est l'identifiant **numérique** de l'espace (pas la clé `DOC`) : visible dans
  l'URL d'administration de l'espace ou via `GET {site}/wiki/api/v2/spaces`.
- Réponse **200** : `{"id": "98765", "title": "…", "_links": {"webui": "/spaces/DOC/pages/98765/T", …}}` ;
  URL : `{site}/wiki{_links.webui}` (il n'y a pas toujours de `_links.base`).
- Un titre déjà pris dans l'espace → 400 (`A page with this title already exists`) :
  proposer un suffixe daté.
- Storage format : XHTML restreint, **tout texte et tout attribut échappés** ; sous-ensemble
  dans `references/storage-format.md`.

## Markdown → ADF / storage : règles de dégradation

| Markdown | ADF | Storage |
|---|---|---|
| `#`…`######` | `heading` (`attrs.level`) | `<h1>`…`<h6>` |
| paragraphe | `paragraph` | `<p>` |
| `- ` / `1. ` | `bulletList` / `orderedList` → `listItem` → `paragraph` | `<ul>` / `<ol>` → `<li>` |
| ``` code ``` | `codeBlock` (`attrs.language`) → `text` | `<ac:structured-macro ac:name="code">` ou `<pre>` |
| `**`, `*`, `` ` `` | marques `strong`, `em`, `code` (`code` jamais combinée) | `<strong>`, `<em>`, `<code>` |
| `[t](http…)` | marque `link` (`attrs.href`) si `http`, `https`, `mailto` ; sinon texte seul | `<a href>` idem |
| tableau, image, citation, HTML brut | **texte** dans un `paragraph` (cellules jointes par ` \| `) | texte échappé dans `<p>` |
| ligne vide / `\` | `hardBreak` | `<br/>` |
| `---` | `rule` | `<hr/>` |

- Un titre **dans** un élément de liste n'est pas admis en ADF : le dégrader en
  paragraphe gras.
- Un élément de liste vide → `paragraph` vide (un `listItem` sans contenu est refusé).
- Parcourir le Markdown avec un analyseur d'événements (`pulldown-cmark` en Rust,
  `markdown-it` en Python) et une pile de blocs ouverts ; ne jamais construire le JSON à
  la main par concaténation.

## Erreurs : résumer, ne jamais recopier

| HTTP | Corps typique | Message à afficher |
|---|---|---|
| 400 Jira | `{"errorMessages": [...], "errors": {"project": "Project key invalid", "issuetype": "Issue type is required"}}` | « Atlassian HTTP 400 : project : Project key invalid ; issuetype : Issue type is required » |
| 400/404 Confluence | `{"errors": [{"status": 404, "code": "NOT_FOUND", "title": "Space not found"}]}` | « Atlassian HTTP 404 : Space not found » |
| 401 | corps HTML ou vide | « Atlassian HTTP 401 : e-mail ou jeton d'API incorrects. » |
| 403 | | « Atlassian HTTP 403 : accès refusé à ce projet / espace. » |
| 5xx | | « Atlassian HTTP 5xx : erreur côté serveur, réessayer. » |

Extraire seulement `errorMessages[]`, `errors{}` (clé : valeur) et `errors[].title` ; le
reste du corps n'est jamais affiché (il peut contenir des identifiants internes). Pas d'URL
complète dans le message : le site suffit à l'utilisateur.

## Contenu publié

Publier la question, la réponse, les sources et une ligne de métadonnées ; **aucun chemin
local, aucun secret**. Le titre vient du Markdown (premier `#`) et devient `summary` /
`title` ; il est retiré du corps.

## Sources (vérifiées le 2026-11-25)

- Jira Cloud REST v3, créer un ticket :
  <https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post>
- Confluence Cloud REST v2, créer une page :
  <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/#api-pages-post>
- Atlassian Document Format : <https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/>
- Storage format : <https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html>
- Jetons d'API et Basic auth :
  <https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/>
- OpenAPI publics : `https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json`,
  `https://dac-static.atlassian.com/cloud/confluence/openapi-v2.v3.json`
