# Événements `claude -p --output-format stream-json --verbose` (Claude Code 2.1.329)

Un objet JSON par ligne. Champ discriminant : `type`.

| `type` | Contenu utile | Affichage conseillé |
|---|---|---|
| `system` (`subtype: init`) | `cwd`, `session_id`, `tools`, `model`, `permissionMode` | ignorer (ou une ligne « session ouverte ») |
| `assistant` | `message.content[]` : blocs `{"type":"text","text":…}` et `{"type":"tool_use","name":…,"input":…}` | texte tel quel ; `→ outil <name>` pour un appel d'outil |
| `user` | `message.content[]` : `tool_result` (sortie des outils) | ignorer (souvent long) ou replier |
| `stream_event` | deltas de flux (si activés) | ignorer : le bloc complet arrive dans `assistant` |
| `result` | `subtype` (`success`, `error_max_turns`, `error_during_execution`…), `is_error`, `result` (texte final), `duration_ms`, `num_turns`, `total_cost_usd` | `result` s'il est non vide, sinon `[fin : <subtype>]` |

Exemple (fixture) :

```json
{"type":"system","subtype":"init","cwd":"/tmp/x","session_id":"s1","tools":["Read"],"model":"claude-opus-5-5","permissionMode":"acceptEdits"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"Bonjour, je lis le dépôt."}]},"session_id":"s1"}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Read","input":{"file_path":"/tmp/x/README.md"}}]},"session_id":"s1"}
{"type":"user","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t1","content":"..."}]},"session_id":"s1"}
{"type":"result","subtype":"success","is_error":false,"duration_ms":1200,"num_turns":2,"result":"Résumé final.","session_id":"s1","total_cost_usd":0.01}
```

Lignes non JSON possibles sur `stdout` (ex. `npm WARN deprecated`) : afficher brut.
`stderr` porte les erreurs d'authentification et de réseau : toujours le lire.

Source : <https://code.claude.com/docs/en/headless> (vérifié le 2026-11-25) ; formes constatées sur la version installée.
