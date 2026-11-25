# Anthropic Messages API : extraits de réponses réelles (anonymisées)

Réponse complète avec recherche web :

```json
{"id": "msg_…", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
 "content": [
   {"type": "server_tool_use", "id": "srvtoolu_1", "name": "web_search", "input": {"query": "…"}},
   {"type": "web_search_tool_result", "tool_use_id": "srvtoolu_1",
    "content": [{"type": "web_search_result", "url": "https://exemple.org/a", "title": "Page A", "encrypted_content": "…", "page_age": null}]},
   {"type": "text", "text": "Première partie.",
    "citations": [{"type": "web_search_result_location", "url": "https://exemple.org/a", "title": "Page A", "cited_text": "…"}]}],
 "stop_reason": "end_turn", "stop_sequence": null,
 "usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 0}}
```

Tronquée : `"stop_reason": "max_tokens"`.

Refusée (classifieurs de sécurité, HTTP 200) :

```json
{"content": [], "stop_reason": "refusal",
 "stop_details": {"type": "refusal", "category": "general_harms", "explanation": "…"}}
```

Erreur 401 :

```json
{"type": "error", "error": {"type": "authentication_error", "message": "invalid x-api-key"}, "request_id": "req_…"}
```

Liste des modèles (`GET /v1/models?limit=1000`) :

```json
{"data": [{"type": "model", "id": "claude-opus-5-5", "display_name": "Claude Opus 5.5",
           "created_at": "2026-…T00:00:00Z", "max_input_tokens": 1000000, "max_tokens": 128000,
           "capabilities": {"…": "…"}}],
 "has_more": false, "first_id": "…", "last_id": "…"}
```

Paramètres refusés (400) par Opus 5.5 / Sonnet 5.5 / Fable : `temperature`, `top_p`,
`top_k`, `thinking.budget_tokens`, `thinking: {type: "disabled"}`, `tool_choice` `any` /
`tool`. La réflexion est adaptative par défaut ; le réglage se fait par
`output_config.effort`. Toujours vérifier `stop_reason` avant de lire `content`.

Sources : <https://platform.claude.com/docs/en/api/messages>, <https://platform.claude.com/docs/en/api/models/list>, <https://platform.claude.com/docs/en/models/overview> (vérifiées le 2026-11-25).
