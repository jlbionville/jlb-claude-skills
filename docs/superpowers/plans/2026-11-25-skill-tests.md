# Tests des skills jlb-ia-toolkit (sous-agent sans puis avec la skill)

Date : 2026-11-25. Méthode : même question posée à un sous-agent `general-purpose` (modèle sonnet) sans la skill (RED), puis avec le contenu de la skill dans le prompt (GREEN). Résumé en deux lignes par skill.

## rust-dev

- **Sans la skill** (38 lignes) : réponse générique et correcte mais hors conventions : `reqwest` + `async_trait`, transport injectable et `wiremock`/`httpmock`/`mockall`, `cargo-deny`, tests `live` derrière `#[ignore]` ; pas de fixtures `include_str!`, pas de `--locked`, pas de threads + `mpsc`.
- **Avec la skill** (42 lignes) : fonctions pures `build_body` / `parse_reply` / `map_status`, fixtures anonymisées chargées par `include_str!`, `impl Port` mince, faux port dans le module de tests sans crate de mock, `constants.rs`, commandes `fmt --check` / `clippy --locked -D warnings` / `test --locked` ; zéro mention de `reqwest`, `tokio` ou d'une crate de mock.

## egui-ui-design

- **Sans la skill** (38 lignes) : architecture déjà juste (actions/événements, `mpsc` + `try_recv`, `request_repaint`, spinner), contraste et WSLg évoqués en général ; propose `tokio` et un `AbortHandle` ; aucune API egui précise au-delà de `request_repaint`.
- **Avec la skill** (44 lignes) : `request_repaint_after` seulement pendant un travail, `ViewportCommand::Close`, `id_salt` par onglet, `truncate` + infobulle, polices embarquées et séparateur U+2009, `wslview` / `libEGL` / `pixels_per_point`, contrôle de lancement `timeout 6 … → 124` ; zéro `tokio`. La skill apporte les API et les pièges, pas l'architecture (déjà connue).

## agent-cli-integration

- **Sans la skill** (49 lignes) : `claude -p --output-format stream-json --verbose` et `codex exec --json --sandbox` connus ; noms d'événements Codex donnés « de mémoire, pas certain » ; Stop par `killpg` / `tokio::process` avec `kill_on_drop` ; rien sur la consigne après `--`, rien d'explicite sur le retrait des clés d'API de l'environnement enfant.
- **Avec la skill** (31 lignes) : arguments séparés sans shell et consigne après `--`, `stdin` fermé, `env_remove` des clés, deux threads lecteurs avec `stderr` préfixé, `Finished` après la fin des deux lecteurs, Stop par `try_wait` + `kill` ; zéro `tokio`. Les noms d'événements ne sont pas recopiés dans la réponse (renvoi aux références).

## llm-provider-apis

- **Sans la skill** (46 lignes) : champs justes (`status: incomplete` + `incomplete_details`, bloc `refusal`, `stop_reason`, `created` / `created_at`, `max_input_tokens`) mais assortis de « de mémoire », « pas certain », « à vérifier » (3 réserves) ; paramètres interdits énoncés avec prudence ; pas de type d'outil de recherche daté ni de table HTTP → erreur typée.
- **Avec la skill** (45 lignes) : zéro réserve, `web_search_20260209`, table 401 / 404 / 429 / 5xx → `ApiAuthentication` / `ApiNotFound` / `ApiRateLimited` / `ApiServer` avec le code API extrait et jamais le corps brut, `budget_tokens` / `tool_choice` / `temperature` listés comme refusés (400), `max_input_tokens` affirmé.

