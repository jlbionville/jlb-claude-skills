# Événements `codex exec --json` (codex-cli 0.42.0)

Un objet JSON par ligne. Champ discriminant : `type` ; les éléments de travail sont
dans `item` avec leur propre `item.type`.

| `type` | `item.type` | Contenu utile | Affichage conseillé |
|---|---|---|---|
| `thread.started` | — | `thread_id` | ignorer |
| `turn.started` | — | — | ignorer |
| `item.started` / `item.updated` | `reasoning`, `command_execution`, … | partiel | ignorer (attendre `item.completed`) |
| `item.completed` | `agent_message` | `item.text` | texte tel quel |
| `item.completed` | `command_execution` | `item.command`, `item.aggregated_output`, `item.exit_code`, `item.status` | `$ <command>` (+ sortie repliée) |
| `item.completed` | autres | — | ignorer |
| `turn.completed` | — | `usage.input_tokens`, `cached_input_tokens`, `output_tokens` | `[tour terminé]` |
| `error` | — | `message` | `erreur : <message>` |

Exemple (fixture) :

```json
{"type":"thread.started","thread_id":"th1"}
{"type":"turn.started"}
{"type":"item.started","item":{"id":"i1","type":"reasoning","text":""}}
{"type":"item.completed","item":{"id":"i2","type":"command_execution","command":"ls -la","aggregated_output":"...","exit_code":0,"status":"completed"}}
{"type":"item.completed","item":{"id":"i3","type":"agent_message","text":"Voici le résultat."}}
{"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":0,"output_tokens":5}}
```

Particularités : `codex exec` refuse de tourner hors d'un dépôt Git sans
`--skip-git-repo-check` (afficher « pas de retour arrière possible » avant de l'ajouter) ;
`-C <dir>` fixe le dossier de travail ; `--sandbox danger-full-access` contourne toute
protection.

Source : formes **constatées** sur codex-cli 0.42.0 (fixtures du projet IA workbench, 2026-11-25) ; la page officielle <https://learn.chatgpt.com/docs/codex/cli> ne les détaille pas à cette date.
