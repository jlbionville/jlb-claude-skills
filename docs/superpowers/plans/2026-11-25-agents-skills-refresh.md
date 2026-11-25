# Plan : refonte des agents et plugin `jlb-ia-toolkit`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un seul jeu d'agents Claude Code génériques, courts et au frontmatter complet dans ce dépôt, plus un plugin `jlb-ia-toolkit` (5 skills, 2 agents) pour le design d'interface egui, Rust, les CLI agentiques, les API OpenAI/Anthropic et les API REST Atlassian ; installation locale resynchronisée sans doublon.

**Architecture:** Tout vit dans `plugins/<plugin>/{agents,skills}`. Un script `scripts/validate_components.py` (argparse, classes, pytest) vérifie le frontmatter de chaque agent et skill ; il sert de garde-fou à chaque tâche. Les agents repris lisent le `CLAUDE.md` du projet courant au lieu d'un contexte projet figé ; leurs gros gabarits (PR, changelog) deviennent des fichiers de référence d'une skill du même plugin, préchargée par le champ `skills:`. Le plugin `jlb-ia-toolkit` suit la même disposition que `jlb-python-toolkit`.

**Tech Stack:** Markdown + YAML frontmatter, Python 3.12 (`installer.py`, nouveau `scripts/validate_components.py`, `pytest`), `claude plugin validate`, Make.

**Spec:** `docs/superpowers/specs/2026-11-25-agents-skills-refresh-design.md`

## Global Constraints

- Agents : frontmatter `name` (minuscules, chiffres, tirets, 3-50 caractères), `description` commençant par « À utiliser quand… » / « Use this agent when… » avec 2 à 4 déclencheurs en prose, `tools` minimaux, `model` (`sonnet` pour les agents repris, `inherit` pour `rust-reviewer` et `ui-designer`), `color` parmi `red, blue, green, yellow, purple, orange, pink, cyan`. Corps < 300 lignes et < 10 000 caractères, en seconde personne, section « Quand m'appeler » (2 à 4 scénarios), section « Sortie ».
- Skills : `SKILL.md` avec `name` et `description` (« Use when… », déclencheurs FR + EN, < 1 024 caractères, sans résumer le déroulé), corps < 300 lignes (limite documentée : 500), références lourdes dans `references/*.md`. Chaque fait d'API cite sa page officielle et une date de vérification. Aucune clé d'API, même factice.
- Langue : skills en français pédagogique ; agents en **français** (style des quatre agents de septembre : `release-manager`, `python-clean-architecture-reviewer`, `terraform-aws-iac-reviewer`, `jira-ticket-writer`) ; identifiants anglais. Décision du plan, voir ci-dessous.
- Agents exécutant des commandes (`scm-expert`, `release-manager`, `rust-reviewer`) : proposer puis exécuter seulement après accord pour commit, fusion, tag, push, suppression.
- `~/.claude/skills/synced/` n'est jamais touché. `~/.claude/agents/` n'est modifié qu'à la dernière tâche, après sauvegarde.
- Après chaque tâche : `python3 scripts/validate_components.py` vert, `python3 installer.py --list` et `--report-specifics` verts, `claude plugin validate plugins/<plugin>` vert pour chaque plugin touché.
- Branche `feat/agents-refresh-ia-toolkit` depuis `main` (`b6d4bd4`). Commits conventionnels en anglais, sans mention d'un assistant ; **push et installation seulement après accord explicite** (dernière tâche).

## Décisions du plan (là où le spec laisse le choix)

- **Langue des agents** : le spec disait « anglais comme les 15 existants » ; en réalité les 4 agents les plus récents du dépôt sont en français, courts et structurés. Les agents repris et les deux nouveaux adoptent ce style. À confirmer par l'utilisateur à la validation du plan.
- **Gabarits déplacés** : `jlb-python-toolkit/skills/git-release-templates/` (PR, changelog Keep a Changelog, checklist de revue) préchargée par `scm-expert` et `release-manager` ; la matrice de capacités de `orchestrator` est supprimée (il découvre les agents disponibles dans la session).
- **Généralisation Vault** : les passages Vault / Dollar Universe / SFTP deviennent une sous-section « Si le projet utilise un gestionnaire de secrets (ex. Vault)… » de 10 lignes maximum par agent ; `installer.py --report-specifics` garde ses mots-clés (`Dollar Universe` doit disparaître des corps).
- **`release-manager` agnostique** : détection de la source de version dans l'ordre `pyproject.toml` → `Cargo.toml` (`[workspace.package] version` puis `[package]`) → `package.json` → `.version` ; verrou : `uv lock` / `cargo update --workspace` / `npm install --package-lock-only` ; tag annoté `vX.Y.Z` ; GitHub Release via `gh release create`.
- **Tests de skills** : un scénario de recherche par skill, joué par un sous-agent `general-purpose` sans la skill (RED : réponse incomplète ou fausse attendue) puis avec le contenu de la skill dans le prompt (GREEN) ; le résultat (deux lignes) est consigné dans `docs/superpowers/plans/2026-11-25-skill-tests.md`.
- **Versions** : `jlb-python-toolkit` 1.3.0 → 1.4.0, `jlb-aws-serverless` 1.2.0 → 1.3.0, `jlb-workflow-toolkit` 1.0.0 → 1.1.0, `jlb-atlassian` 1.0.0 → 1.1.0, `jlb-ia-toolkit` 1.0.0, `marketplace.json` 1.0.0 → 1.1.0.

## Review Focus

- Un agent dont la description résume le déroulé : le modèle suit la description au lieu du corps (tâches 10 à 14 : relire chaque description).
- Préchargement `skills:` d'une skill de plugin : vérifier le nom réellement attendu (`git-release-templates` ou `jlb-python-toolkit:git-release-templates`) en session réelle après installation (tâche 16) ; si le préchargement échoue, l'agent doit quand même nommer la skill dans son corps.
- Un `~/.claude/agents/<nom>.md` subsistant après la tâche 16 masque ou double l'agent du plugin : la vérification liste les deux emplacements.
- `claude plugin validate` refuse un `plugin.json` dont `name` contient autre chose que du kebab-case : tâche 2.
- Une skill `SKILL.md` > 500 lignes est tronquée au rechargement après compaction : le script de validation borne à 300.

---

### Task 1 : script de validation des composants (pytest)

**Files:**
- Create: `scripts/validate_components.py`, `scripts/constants.py`, `tests/test_validate_components.py`, `pyproject.toml` (section `[tool.pytest.ini_options]`, dépendance dev `pytest`, `requires-python = ">=3.12"`)

**Interfaces:**
- Produces: `python3 scripts/validate_components.py [--root plugins] [--max-agent-lines 300] [--max-skill-lines 300] [--json]` ; exit `0` si tout passe, `3` (`ExitCode.VALIDATION_ERROR`) sinon, une ligne par défaut : `plugins/x/agents/y.md: description does not start with a trigger phrase`. Classes `Frontmatter`, `AgentRule`, `SkillRule`, `ComponentValidator`, `Result` ; `ALLOWED_COLORS`, `ALLOWED_MODELS`, `TRIGGER_PREFIXES = ("À utiliser", "Use this agent when", "Use when")` dans `constants.py`.

- [ ] **Step 1: Write the failing tests** (`tests/test_validate_components.py`, fichiers temporaires via `tmp_path`) : `test_valid_agent_passes`, `test_agent_without_color_fails`, `test_agent_color_outside_list_fails` (`magenta`), `test_agent_body_over_limit_fails` (301 lignes), `test_agent_description_without_trigger_fails` (« USE PROACTIVELY… »), `test_skill_over_300_lines_fails`, `test_skill_description_over_1024_fails`, `test_cli_returns_3_on_error_and_0_otherwise` (via `subprocess.run([sys.executable, "scripts/validate_components.py", "--root", tmp])`).
- [ ] **Step 2: Run** `python3 -m pytest -q` → FAIL (module absent).
- [ ] **Step 3: Implement** le script (argparse, logging, lecture du frontmatter YAML sans dépendance : bloc `---` parsé à la main, clés simples et `description: >` multi-lignes).
- [ ] **Step 4: Run** `python3 -m pytest -q` → PASS ; `python3 scripts/validate_components.py` sur le dépôt → liste des défauts actuels (attendu : 15 agents sans `color`, 11 descriptions sans déclencheur, 8 corps > 300 lignes) ; exit 3.
- [ ] **Step 5: Commit** `feat(tooling): validate agent and skill frontmatter`

### Task 2 : squelette du plugin `jlb-ia-toolkit`

**Files:**
- Create: `plugins/jlb-ia-toolkit/.claude-plugin/plugin.json`, `plugins/jlb-ia-toolkit/skills/.gitkeep`, `plugins/jlb-ia-toolkit/agents/.gitkeep`
- Modify: `.claude-plugin/marketplace.json` (entrée `jlb-ia-toolkit`, catégorie `development`, mots-clés `rust, egui, claude-code, codex, openai, anthropic, jira, confluence, atlassian, agent`), `README.md` (tableau Plugins, ligne d'installation), `Makefile` (`install-ia`)

- [ ] **Step 1: Write** `plugin.json` : `{"name": "jlb-ia-toolkit", "description": "…", "version": "1.0.0", "author": {"name": "jlbionville"}}`.
- [ ] **Step 2: Verify** `claude plugin validate plugins/jlb-ia-toolkit` → OK ; `python3 installer.py --list` liste `jlb-ia-toolkit` (0 skill, 0 agent) ; `make -n install-ia` affiche les deux commandes.
- [ ] **Step 3: Commit** `feat(ia-toolkit): scaffold plugin`

### Task 3 : skill `rust-dev`

**Files:**
- Create: `plugins/jlb-ia-toolkit/skills/rust-dev/SKILL.md`, `plugins/jlb-ia-toolkit/skills/rust-dev/references/clippy-messages.md`

- [ ] **Step 1: RED** : sous-agent sans skill, question « Dans un workspace Rust en clean architecture, où mettre un nouveau port et son adaptateur, et comment tester l'adaptateur sans réseau ? » ; noter la réponse (attendu : générique, sans fixture ni `--locked`, sans règle de dépendance entre crates).
- [ ] **Step 2: Write** `SKILL.md` : déclencheurs (cargo, clippy, workspace, thiserror, mpsc, fixture, edition 2024, `-D warnings`), sections : règle de dépendance entre crates (le compilateur l'impose), erreurs typées + code de sortie, tests sur fixtures `include_str!`, threads + `mpsc` (jamais d'`Arc<Mutex>` partagé avec l'UI), checklist « nouveau port / adaptateur / cas d'usage », lecture des erreurs clippy fréquentes (référence), commandes (`fmt --check`, `clippy --all-targets --locked -- -D warnings`, `test --workspace --locked`). Sources : Rust Book, Clippy lints, Cargo Book, avec date.
- [ ] **Step 3: GREEN** : même question avec la skill → la réponse cite la règle de dépendance, les fixtures et `--locked`. Consigner dans `docs/superpowers/plans/2026-11-25-skill-tests.md`.
- [ ] **Step 4: Verify** `python3 scripts/validate_components.py` vert pour cette skill.
- [ ] **Step 5: Commit** `feat(ia-toolkit): rust-dev skill`

### Task 4 : skill `egui-ui-design`

**Files:**
- Create: `plugins/jlb-ia-toolkit/skills/egui-ui-design/SKILL.md`, `references/wslg-pitfalls.md`

- [ ] **Step 1: RED** : « Comment organiser une fenêtre egui avec une colonne de navigation, un panneau central et une barre d'état, en gardant l'état testable sans egui ? » (attendu sans skill : code inline, état mêlé à l'UI).
- [ ] **Step 2: Write** : panneaux qui rendent des intents et un état sans egui, `SidePanel`/`CentralPanel`/`TopBottomPanel`, `ScrollArea` et `truncate`, `Style`/`Visuals`, palette 3 couleurs et contraste WCAG 2.2 (ratio 4,5:1), repaint pendant un travail en arrière-plan, `ViewportCommand::Close`, pièges WSLg (DPI, presse-papiers, `wslview`), `egui_commonmark` sans images. Sources : docs.rs egui 0.33, egui demo, WCAG 2.2, avec date.
- [ ] **Step 3: GREEN**, **Step 4: Verify**, **Step 5: Commit** `feat(ia-toolkit): egui-ui-design skill`

### Task 5 : skill `agent-cli-integration`

**Files:**
- Create: `plugins/jlb-ia-toolkit/skills/agent-cli-integration/SKILL.md`, `references/claude-code-events.md`, `references/codex-events.md`

- [ ] **Step 1: RED** : « Comment lancer `claude -p` depuis un programme et afficher sa sortie en direct sans exposer mes clés d'API ? » (attendu sans skill : shell string, pas de `--output-format stream-json`, pas de `env_remove`).
- [ ] **Step 2: Write** : flags des deux CLI (`claude -p --output-format stream-json --verbose --permission-mode`, `codex exec --json --sandbox`), consigne après `--`, arguments séparés sans shell, `stdin` fermé, `env_remove` des clés, deux threads lecteurs, arrêt propre (kill via Drop), formes d'événements JSONL et champ texte à extraire (références). Sources : doc CLI Claude Code (code.claude.com), doc Codex CLI, avec date et versions constatées.
- [ ] **Step 3: GREEN**, **Step 4: Verify**, **Step 5: Commit** `feat(ia-toolkit): agent-cli-integration skill`

### Task 6 : skill `llm-provider-apis`

**Files:**
- Create: `plugins/jlb-ia-toolkit/skills/llm-provider-apis/SKILL.md`, `references/openai-responses.md`, `references/anthropic-messages.md`

- [ ] **Step 1: RED** : « Quel champ de la réponse OpenAI Responses dit que la sortie a été tronquée, et son équivalent chez Anthropic ? » (attendu sans skill : `finish_reason` de l'ancienne API, ou hésitation).
- [ ] **Step 2: Write** : corps minimaux des deux API, champs de réponse (`status: incomplete` + `incomplete_details.reason`, `stop_reason: max_tokens` / `refusal`), `/models` (`created`, `created_at`, `display_name`, `max_input_tokens`), table HTTP → erreur typée (401, 404 modèle, 429, 5xx), en-têtes (`anthropic-version`), ce qu'un corps Anthropic ne doit pas contenir sur les modèles récents (`temperature`, `budget_tokens`, `tool_choice` forcé), type d'outil `web_search_20260209`, coût des appels réels. Renvoi au skill intégré `claude-api` pour le reste. Sources : platform.openai.com/docs, platform.claude.com/docs, avec date.
- [ ] **Step 3: GREEN**, **Step 4: Verify**, **Step 5: Commit** `feat(ia-toolkit): llm-provider-apis skill`

### Task 7 : skill `atlassian-rest-api`

**Files:**
- Create: `plugins/jlb-ia-toolkit/skills/atlassian-rest-api/SKILL.md`, `references/adf-subset.md`, `references/storage-format.md`

- [ ] **Step 1: RED** : « Comment créer une page Confluence Cloud par l'API REST avec un corps venant de Markdown, et quelle authentification ? » (attendu sans skill : API v1 `/rest/api/content`, ou OAuth sans Basic).
- [ ] **Step 2: Write** : Basic `email:token` (en-tête jamais journalisé), `POST /rest/api/3/issue` avec `description` ADF, `POST /wiki/api/v2/pages` avec `body.representation = "storage"`, `spaceId` numérique, liens `_links.webui`, résumé des erreurs (`errorMessages`, `errors`, `title`) sans écho du corps, sous-ensemble ADF et storage avec dégradations (tableaux, images, HTML brut → texte ; liens non `http/https/mailto` perdent le lien). Renvoi au plugin officiel `atlassian` pour l'usage MCP. Sources : developer.atlassian.com (REST v3, Confluence v2, ADF), avec date.
- [ ] **Step 3: GREEN**, **Step 4: Verify**, **Step 5: Commit** `feat(ia-toolkit): atlassian-rest-api skill`

### Task 8 : agent `rust-reviewer`

**Files:**
- Create: `plugins/jlb-ia-toolkit/agents/rust-reviewer.md`

- [ ] **Step 1: Write** : frontmatter (`tools: Read, Grep, Glob, Bash`, `model: inherit`, `color: blue`, `skills: [rust-dev]`), corps : lecture du `CLAUDE.md` du projet, `cargo fmt --all --check`, `clippy --workspace --all-targets --locked -- -D warnings`, `cargo test --workspace --locked`, puis relecture du diff contre les invariants du `CLAUDE.md` (secrets dans `Debug`/logs, `Arc<Mutex>` hors cas autorisé, `env_remove`, versions épinglées), rapport : verdict puis `fichier:ligne` + gravité ; ne modifie rien.
- [ ] **Step 2: Verify** validation verte ; lancement sur `~/depots/rust_openai_gui` (branche courante) via `claude -p "utilise l'agent rust-reviewer sur la branche" --agent …` ou en session : verdict rendu sans modification (`git status` propre après).
- [ ] **Step 3: Commit** `feat(ia-toolkit): rust-reviewer agent`

### Task 9 : agent `ui-designer`

**Files:**
- Create: `plugins/jlb-ia-toolkit/agents/ui-designer.md`

- [ ] **Step 1: Write** : frontmatter (`tools: Read, Grep, Glob`, `model: inherit`, `color: purple`, `skills: [egui-ui-design]`), corps : lire l'UI existante (panneaux, thème, état), proposer disposition / thème / accessibilité en maquette texte (ASCII) + plan d'implémentation (intents, états, fichiers à toucher), sans écrire de code.
- [ ] **Step 2: Verify** validation verte ; lancement sur le workbench : maquette rendue, aucun fichier écrit.
- [ ] **Step 3: Commit** `feat(ia-toolkit): ui-designer agent`

### Task 10 : skill `git-release-templates` et reprise de `scm-expert`, `release-manager`

**Files:**
- Create: `plugins/jlb-python-toolkit/skills/git-release-templates/SKILL.md`, `references/pr-template.md`, `references/changelog-template.md`, `references/review-checklist.md`
- Modify: `plugins/jlb-python-toolkit/agents/scm-expert.md` (657 → < 250 l.), `plugins/jlb-python-toolkit/agents/release-manager.md` (79 → < 200 l., agnostique du langage)

- [ ] **Step 1: Write** la skill (gabarits extraits mot pour mot de `scm-expert.md` lignes 215-335, sans la section « Vault Impact » qui devient « Impact sur les secrets / la configuration »).
- [ ] **Step 2: Rewrite** `scm-expert` : français, `color: green`, `skills: [git-release-templates]`, scopes déduits de l'arborescence (`domain`, `application`, `infrastructure`, `interface`, `tests`, `docs`), pas de mention d'outil IA dans les commits, validation avant commit/merge/suppression ; `release-manager` : détection de version et verrous par langage (décision ci-dessus), `color: red`.
- [ ] **Step 3: Verify** validation verte ; `--report-specifics` vert ; lancement de `release-manager` sur `~/depots/rust_openai_gui` : proposition de version sans toucher à `Cargo.toml`.
- [ ] **Step 4: Commit** `refactor(python-toolkit): condense scm-expert, language-agnostic release-manager, templates skill`

### Task 11 : reprise de `orchestrator`, `documentation-writer`, `product-owner`

**Files:**
- Modify: `plugins/jlb-workflow-toolkit/agents/{orchestrator,documentation-writer,product-owner}.md`

- [ ] **Step 1: Rewrite** `orchestrator` (905 → < 250 l., `color: cyan`, `tools: Read, Grep, Glob, Agent`) : découpe, choix d'agent parmi ceux disponibles dans la session (plus de liste figée ni de matrice), ordre design → plan → code → review → docs → release, synthèse ; `documentation-writer` (755 → < 250 l., `color: yellow`) : langue et emplacements lus dans le `CLAUDE.md` du projet, validation avant suppression conservée ; `product-owner` : frontmatter seulement (`color: orange`).
- [ ] **Step 2: Verify** validation verte ; lancement de `orchestrator` sur une demande multi-domaines factice : plan de délégation sans lancer d'agent.
- [ ] **Step 3: Commit** `refactor(workflow-toolkit): generic orchestrator and documentation-writer`

### Task 12 : reprise des agents AWS

**Files:**
- Modify: `plugins/jlb-aws-serverless/agents/{devops-engineer,security-expert,integration-engineer,data-migration-specialist,terraform-aws-iac-reviewer}.md`

- [ ] **Step 1: Rewrite** `integration-engineer` (1 023 → < 300 l., `color: cyan`) : intégrations externes (API REST, SFTP, files de messages, gestionnaires de secrets) avec Vault en sous-section conditionnelle ; `data-migration-specialist` (811 → < 300 l., `color: orange`) : migrations de données génériques (plan, dry-run, validation, retour arrière) ; `devops-engineer` (760 → < 300 l., `color: green`), `security-expert` (660 → < 300 l., `color: red`) : Vault/credentials conditionnels ; `terraform-aws-iac-reviewer` : `color: blue` seulement.
- [ ] **Step 2: Verify** validation verte ; `--report-specifics` vert (plus de `Dollar Universe`).
- [ ] **Step 3: Commit** `refactor(aws-serverless): project-agnostic operations agents`

### Task 13 : reprise des autres agents Python et Atlassian

**Files:**
- Modify: `plugins/jlb-python-toolkit/agents/{makefile-expert,windows-scripts-expert,test-automation-engineer,python-clean-architecture-reviewer}.md`, `plugins/jlb-atlassian/agents/jira-ticket-writer.md`

- [ ] **Step 1: Rewrite** `test-automation-engineer` (838 → < 300 l., `color: yellow`), `makefile-expert` (348 → < 300 l., `color: green`), `windows-scripts-expert` (370 → < 300 l., `color: green`) : exemples génériques, Vault retiré ; `python-clean-architecture-reviewer` et `jira-ticket-writer` : `color` (`blue`, `orange`) et description au format déclencheur.
- [ ] **Step 2: Verify** validation verte sur **tout** le dépôt (exit 0).
- [ ] **Step 3: Commit** `refactor(agents): complete frontmatter and condense remaining agents`

### Task 14 : versions, README, documentation

**Files:**
- Modify: `.claude-plugin/marketplace.json`, `plugins/*/.claude-plugin/plugin.json` (versions, descriptions), `README.md` (tableaux Plugins et Agents, section Conventions : règles de frontmatter, script de validation, langue), `docs/superpowers/plans/2026-11-25-skill-tests.md` (déjà alimenté par les tâches 3 à 7)

- [ ] **Step 1: Write** les versions (décision ci-dessus) et la documentation.
- [ ] **Step 2: Verify** `claude plugin validate` vert sur les 7 plugins ; `python3 installer.py --list` cohérent avec le README.
- [ ] **Step 3: Commit** `chore: bump plugin versions and document agent conventions`

### Task 15 : revue finale et accord

- [ ] **Step 1** : revue de la branche entière par un réviseur neuf (voir skill d'exécution), corrections éventuelles.
- [ ] **Step 2** : présenter à l'utilisateur le résumé et demander l'accord pour le push et l'installation (tâche 16).

### Task 16 : push et resynchronisation locale (après accord explicite)

- [ ] **Step 1** : `git push -u origin feat/agents-refresh-ia-toolkit` ; PR vers `main` (`gh pr create`) ; fusion après accord ; `git checkout main && git pull`.
- [ ] **Step 2** : `mkdir -p ~/.claude/backups/agents-2026-11-25 && cp -r ~/.claude/agents/. ~/.claude/backups/agents-2026-11-25/ && rm -rf ~/.claude/agents/*` (confirmation demandée juste avant le `rm`).
- [ ] **Step 3** : `claude plugin marketplace update jlb-claude-skills` ; `claude plugin install jlb-ia-toolkit@jlb-claude-skills`, `jlb-atlassian@…`, `jlb-workflow-toolkit@…` ; `claude plugin update jlb-python-toolkit@…`, `jlb-aws-serverless@…`.
- [ ] **Step 4: Verify** : `claude plugin list` montre les 5 plugins aux nouvelles versions ; `find ~/.claude/plugins/cache/jlb-claude-skills -path '*/agents/*.md' | wc -l` = 17 ; `ls ~/.claude/agents` vide ; dans une session `claude`, `/agents` liste chaque agent une seule fois et le préchargement `skills:` de `rust-reviewer` fonctionne (sinon corriger le nom et refaire un patch).
