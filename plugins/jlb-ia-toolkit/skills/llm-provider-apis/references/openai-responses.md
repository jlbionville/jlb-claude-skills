# OpenAI Responses API : extraits de réponses réelles (anonymisées)

Réponse complète avec recherche web :

```json
{"id": "resp_…", "object": "response", "status": "completed", "model": "gpt-6.1-terra",
 "output": [
   {"type": "web_search_call", "id": "ws_1", "status": "completed"},
   {"type": "message", "id": "msg_1", "role": "assistant",
    "content": [{"type": "output_text", "text": "Réponse.",
                 "annotations": [{"type": "url_citation", "url": "https://exemple.org/a",
                                  "title": "Page A", "start_index": 0, "end_index": 5}]}]}],
 "usage": {"input_tokens": 50, "output_tokens": 20, "total_tokens": 70,
           "input_tokens_details": {"cached_tokens": 0}}}
```

Réponse tronquée :

```json
{"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
 "output": [{"type": "message", "content": [{"type": "output_text", "text": "Début de réponse tron", "annotations": []}]}]}
```

Refus : un bloc `{"type": "refusal", "refusal": "…"}` dans `content[]`.

Erreur 401 :

```json
{"error": {"message": "Incorrect API key provided.", "type": "invalid_request_error", "param": null, "code": "invalid_api_key"}}
```

Lecture robuste : `output[]` peut contenir des éléments sans `content` (appels d'outils) ;
`annotations` peut être absent ; `code` peut être `null` (replier sur `type`).

Source : <https://developers.openai.com/api/docs/api-reference/responses> (vérifié le 2026-11-25).
