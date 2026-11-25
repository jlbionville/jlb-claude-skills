# Tests des skills jlb-ia-toolkit (sous-agent sans puis avec la skill)

Date : 2026-11-25. Méthode : même question posée à un sous-agent `general-purpose` (modèle sonnet) sans la skill (RED), puis avec le contenu de la skill dans le prompt (GREEN). Résumé en deux lignes par skill.

## rust-dev

- **Sans la skill** (38 lignes) : réponse générique et correcte mais hors conventions : `reqwest` + `async_trait`, transport injectable et `wiremock`/`httpmock`/`mockall`, `cargo-deny`, tests `live` derrière `#[ignore]` ; pas de fixtures `include_str!`, pas de `--locked`, pas de threads + `mpsc`.
- **Avec la skill** (42 lignes) : fonctions pures `build_body` / `parse_reply` / `map_status`, fixtures anonymisées chargées par `include_str!`, `impl Port` mince, faux port dans le module de tests sans crate de mock, `constants.rs`, commandes `fmt --check` / `clippy --locked -D warnings` / `test --locked` ; zéro mention de `reqwest`, `tokio` ou d'une crate de mock.

