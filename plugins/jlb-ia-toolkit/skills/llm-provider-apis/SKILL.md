---
name: llm-provider-apis
description: >
  Use when calling the OpenAI Responses API or the Anthropic Messages API directly over
  HTTPS (no SDK): minimal request bodies, reading the answer and its truncation or refusal
  status, listing models (/models fields: release date, context window), mapping HTTP
  status codes to typed errors, web search tool types, and parameters recent Anthropic
  models reject. Déclencheurs FR : « appel direct à l'API OpenAI / Anthropic », « réponse
  tronquée », « max_tokens atteint », « 401 / 429 », « liste des modèles », « quel champ
  dit que… », « corps JSON minimal ». Pour l'usage du SDK Anthropic ou des agents, voir
  le skill intégré claude-api.
---

# Appeler les API OpenAI et Anthropic en HTTPS direct

## Vue d'ensemble

Deux API, une même discipline : un corps JSON minimal construit par une fonction pure, une
réponse analysée par une autre fonction pure, les statuts HTTP convertis en erreurs typées
sans jamais recopier le corps d'erreur brut ni la clé. Faits vérifiés le 2026-11-25 sur les
pages officielles et sur des réponses réelles enregistrées en fixtures.

## Quand l'utiliser

- Écrire ou corriger un adaptateur HTTP vers l'une des deux API.
- Savoir où lire « tronqué », « refusé », « date de sortie », « fenêtre de contexte ».
- Déboguer un 400 sur un modèle Anthropic récent (paramètre devenu interdit).
- Ne pas l'utiliser pour : les SDK officiels (`anthropic`, `openai`), le streaming SSE
  détaillé, les agents managés : voir le skill intégré `claude-api`.

## Corps minimaux

OpenAI, `POST {base}/responses` (en-tête `Authorization: Bearer <clé>`) :

```json
{"model": "gpt-6.1-terra", "instructions": "<système>", "input": "<question>",
 "max_output_tokens": 2000, "store": false,
 "tools": [{"type": "web_search"}], "tool_choice": "required"}
```

Anthropic, `POST {base}/messages` (en-têtes `x-api-key: <clé>`, `anthropic-version: 2023-06-01`) :

```json
{"model": "claude-opus-5-5", "max_tokens": 2000, "system": "<système>",
 "messages": [{"role": "user", "content": "<question>"}],
 "tools": [{"type": "web_search_20260209", "name": "web_search"}]}
```

- `store: false` côté OpenAI : la réponse n'est pas conservée côté serveur.
- Le type d'outil de recherche Anthropic est **daté** (`web_search_20260209` pour les
  modèles 4.6 et plus récents ; `web_search_20250305` avant) : un type trop récent pour le
  modèle donne un 400.
- **À ne pas envoyer** aux modèles Anthropic récents (Opus 5.5, Sonnet 5.5, Fable) :
  `temperature`, `top_p`, `top_k`, `thinking.budget_tokens`, `thinking: {type: "disabled"}`,
  `tool_choice: any|tool` → 400. Un test doit **affirmer l'absence** de ces clés dans le corps.

## Lire la réponse

| Besoin | OpenAI Responses | Anthropic Messages |
|---|---|---|
| Texte | `output[].content[]` avec `type: "output_text"` → `text` | `content[]` avec `type: "text"` → `text` |
| Sources (recherche web) | `annotations[]` `type: "url_citation"` → `url`, `title` | `citations[]` `type: "web_search_result_location"` → `url`, `title` |
| **Tronqué** | `status: "incomplete"` + `incomplete_details.reason` (`max_output_tokens`) | `stop_reason: "max_tokens"` |
| **Refusé** | bloc `content[]` `type: "refusal"` → `refusal` (texte) | `stop_reason: "refusal"` + `stop_details {category, explanation}` |
| Terminé normalement | `status: "completed"` | `stop_reason: "end_turn"` |
| Consommation | `usage.input_tokens`, `output_tokens`, `input_tokens_details.cached_tokens` | `usage.input_tokens`, `output_tokens`, `cache_read_input_tokens` |
| Modèle effectif | `model` | `model` |

Ignorer sans erreur les blocs techniques (`web_search_call`, `server_tool_use`,
`web_search_tool_result`) et tout `type` inconnu : une API ajoute des blocs, le programme
ne doit pas casser. Dédoublonner les sources par URL.

## Lister les modèles

| | OpenAI `GET {base}/models` | Anthropic `GET {base}/models?limit=1000` |
|---|---|---|
| Identifiant | `data[].id` | `data[].id` |
| Date de mise à disposition | `data[].created` (secondes Unix) | `data[].created_at` (ISO 8601 `…Z`) |
| Nom lisible | — | `data[].display_name` |
| Fenêtre / sortie max | non fournis | `max_input_tokens`, `max_tokens`, `capabilities` (depuis 2026) |
| Pagination | aucune | `has_more`, `first_id`, `last_id` |

Trier du plus récent au plus ancien par la date ; une date illisible vaut « sans date »,
jamais une erreur. Les caractéristiques absentes (OpenAI) viennent d'un catalogue local
maintenu à la main, chaque valeur avec sa source et sa date de vérification.

## Statuts HTTP → erreurs typées

| HTTP | Code applicatif | Message utilisateur | Code API utile |
|---|---|---|---|
| 401 | `ApiAuthentication` | « Clé API invalide. » | OpenAI `error.code = invalid_api_key` ; Anthropic `error.type = authentication_error` |
| 403 | `ApiForbidden` | « Accès refusé. » | |
| 404 | `ApiNotFound` | « Vérifie le nom du modèle et son accès. » | modèle inconnu ou non autorisé |
| 429 | `ApiRateLimited` | « Vérifie tes crédits et limites de requêtes. » | quota, crédits, débit |
| 5xx | `ApiServer` | « Erreur côté fournisseur, réessaie plus tard. » | |
| autre 4xx | `ApiRejected` | « Requête refusée par le fournisseur. » | OpenAI `error.code` ou `error.type` ; Anthropic `error.type` |

Règles : lire le corps des 4xx (`http_status_as_error(false)` avec `ureq`, ou équivalent)
pour en extraire le **code** seulement ; le message final cite `HTTP <statut> (code API :
<code>)`, jamais le corps brut, jamais l'URL complète, jamais la clé. Une erreur réseau
(DNS, TLS, délai) devient `Network` sans l'URL.

## Coûts et prudence

- Chaque appel réel est facturé ; la recherche web ajoute un coût par appel. Vérifier avec
  des tests sur fixtures, jamais en cliquant.
- Un `max_output_tokens` / `max_tokens` trop bas tronque : le signaler à l'utilisateur
  (« augmente le plafond ») plutôt que relancer en silence.
- La présence d'une clé ne garantit ni ses droits ni son solde : l'API le dit à l'appel.

Détails et extraits de réponses : `references/openai-responses.md`,
`references/anthropic-messages.md`.

## Sources (vérifiées le 2026-11-25)

- OpenAI Responses API : <https://developers.openai.com/api/docs/api-reference/responses>
- OpenAI Models : <https://developers.openai.com/api/docs/models>,
  <https://developers.openai.com/api/docs/api-reference/models>
- Anthropic Messages API : <https://platform.claude.com/docs/en/api/messages>
- Anthropic Models API : <https://platform.claude.com/docs/en/api/models/list>
- Anthropic, vue d'ensemble des modèles (contexte, sortie, tarifs) :
  <https://platform.claude.com/docs/en/models/overview>
- Anthropic, recherche web (types datés) :
  <https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool>
