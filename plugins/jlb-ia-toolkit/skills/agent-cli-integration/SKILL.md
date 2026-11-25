---
name: agent-cli-integration
description: >
  Use when a program must launch Claude Code (claude -p) or Codex CLI (codex exec) as a
  child process: non-interactive flags, stream-json / JSONL output and how to read it line
  by line, a Stop button that kills the process, keeping API keys out of the child's
  environment, and avoiding shell injection. Déclencheurs FR : « lancer Claude Code depuis
  mon programme », « sortie en direct de l'agent », « bouton Stop », « codex exec »,
  « stream-json », « JSONL », « l'agent me demande une confirmation », « clé d'API visible
  par l'agent ».
---

# Intégrer Claude Code et Codex CLI comme processus enfants

## Vue d'ensemble

Les deux CLI ont un mode non interactif qui lit la consigne en argument et écrit des
**événements JSON, un par ligne** (JSONL). Un programme hôte les lance sans shell, lit
`stdout` et `stderr` dans deux threads, extrait le texte utile de chaque événement, et
garde une poignée sur le processus pour l'arrêter. Formes constatées le 2026-11-25 sur
Claude Code 2.1.329 et codex-cli 0.42.0 ; les versions bougent, les tests sur fixtures
disent quand.

## Quand l'utiliser

- Un onglet « Agent » dans une fenêtre, un bot, un script d'orchestration.
- Lire ou déboguer la sortie `stream-json` / `--json`.
- Ne pas l'utiliser pour : piloter Claude par l'API Messages (voir la skill
  `llm-provider-apis` ou le skill intégré `claude-api`), ni pour le SDK Agent.

## Commandes

| | Claude Code | Codex CLI |
|---|---|---|
| Mode non interactif | `claude -p` | `codex exec` |
| Sortie JSONL | `--output-format stream-json --verbose` (`--verbose` est requis avec `stream-json` en `-p`) | `--json` |
| Autorisations | `--permission-mode <default\|acceptEdits\|plan\|auto\|dontAsk\|bypassPermissions>` (`manual` = alias de `default`) ; `--allowedTools "Bash(cargo test)"` (répétable) | `--sandbox <read-only\|workspace-write\|danger-full-access>` |
| Dossier de travail | `current_dir(dir)` du processus | `-C <dir>` |
| Hors dépôt Git | — | `--skip-git-repo-check` (sinon refus) |
| Consigne | **après `--`**, dernier argument | **après `--`**, dernier argument |

Exemple complet (arguments séparés, jamais une chaîne shell) :

```rust
let mut command = std::process::Command::new(&settings.claude_command);  // "claude"
command.args(["-p", "--output-format", "stream-json", "--verbose", "--permission-mode", mode]);
for tool in &settings.allowed_tools { command.args(["--allowedTools", tool]); }
command.current_dir(&working_dir).args(["--", &instruction]);
command.stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::piped());
for name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"] { command.env_remove(name); }
```

Pourquoi chaque ligne :

- **Toujours passer le mode d'autorisation** : sans `--permission-mode`, une session `-p`
  démarre en mode manuel et **refuse** toute demande d'autorisation (l'agent échoue au
  premier outil non autorisé).
- **Pas de shell** (`sh -c`) : la consigne vient de l'utilisateur ; passée en argument
  séparé après `--`, elle ne peut pas devenir une option ni une commande.
- **`stdin` fermé** : l'agent ne peut rien demander au clavier ; une question bloquante
  devient une fin immédiate, pas un gel.
- **`env_remove`** des clés d'API : l'agent a son propre compte ; les clés de la fenêtre
  ne doivent pas financer son travail ni fuiter dans ses journaux. Décider explicitement
  pour chaque autre secret (ex. un jeton Atlassian gardé **volontairement** pour que
  l'agent publie).
- Modes qui contournent toute confirmation (`bypassPermissions`, `danger-full-access`) :
  les afficher en rouge et les documenter, jamais par défaut.

## Lire la sortie

- Deux threads lecteurs (`BufRead::lines` sur `stdout` et sur `stderr`) ; chaque ligne
  devient un événement envoyé à l'hôte par `mpsc`. `stderr` est affiché préfixé
  (`stderr : …`) : npm, avertissements, erreurs d'authentification y passent.
- Lire les octets, pas des `String` : une ligne non UTF-8 (`read_until(b'\n')` +
  `String::from_utf8_lossy`) s'affiche avec `�` au lieu de tuer le lecteur.
- `extract(line) -> Skip | Text(String) | Raw(String)` : une ligne non JSON est affichée
  brute, un type connu sans texte utile est ignoré, un type inconnu est affiché brut.
  **Ne jamais perdre une ligne silencieusement.**
- Émettre `Finished { success, code }` seulement quand `wait()` a rendu la main **et** que
  les deux lecteurs ont fini : sinon les dernières lignes arrivent après la « fin ».
- Plafonner l'affichage (ex. 5 000 lignes) et le dire dans la documentation.

Événements et champs à extraire : `references/claude-code-events.md`,
`references/codex-events.md`.

## Stop

- Garder `Arc<Mutex<Child>>` : le thread d'attente tient le verrou pendant `wait()` ; Stop
  fait `try_wait()` puis `kill()`. Ne pas bloquer l'interface sur le verrou : `try_lock`
  ou un `wait` par sondage (`try_wait` + `sleep(50 ms)`).
- `impl Drop` sur la poignée → `kill()` : fermer la fenêtre arrête l'agent.
- Après `kill`, les tubes se ferment, les lecteurs se terminent, `Finished` part avec
  `success = false`.

## Tests sans agent réel

- `build_command` est pur : tester `get_args()`, `get_envs()` (clés retirées), `--` avant
  la consigne, `--skip-git-repo-check` conditionnel.
- `extract` sur des fixtures `.jsonl` (une ligne par forme : init, texte, outil, résultat,
  non-JSON, type inconnu).
- Le flux complet avec `/bin/sh -c 'echo …; echo … >&2'` **dans les tests seulement**, et
  Stop sur `/bin/sleep 30` (doit finir en moins de 2 s). Jamais `claude` ni `codex` dans
  les tests : coût et non-déterminisme.

## Erreurs courantes

- Oublier `--verbose` avec `stream-json` : Claude Code refuse ou n'émet rien d'exploitable.
- Mettre la consigne avant `--` : une consigne commençant par `-` devient une option.
- Lire `stdout` dans le thread de l'interface : la fenêtre se fige.
- `wait()` sous le même verrou que `kill()` sans `try_wait` : Stop attend la fin.
- Afficher la commande complète dans le journal avec ses arguments : la consigne peut
  contenir des données sensibles ; journaliser le binaire et le mode seulement.

## Sources (vérifiées le 2026-11-25)

- Référence CLI Claude Code (options `-p`, `--output-format`, `--permission-mode`,
  `--allowedTools`) : <https://code.claude.com/docs/en/cli-reference>
- Mode non interactif / sortie JSON Claude Code :
  <https://code.claude.com/docs/en/headless>
- Codex CLI : page d'entrée <https://learn.chatgpt.com/docs/codex/cli> (redirigée depuis
  developers.openai.com/codex/cli) ; à la date de vérification elle ne détaille pas
  `exec --json`, `--sandbox`, `-C` ni `--skip-git-repo-check`. Ces options et les formes
  d'événements Codex sont **constatées sur codex-cli 0.42.0** (`codex exec --help`, fixtures
  du projet IA workbench), pas lues sur la page.
- Formes d'événements Claude Code : constatées sur 2.1.329 et cohérentes avec la page
  « Run Claude Code programmatically » ; fixtures `claude_stream.jsonl` et
  `codex_exec.jsonl` reproduites dans `references/`.
