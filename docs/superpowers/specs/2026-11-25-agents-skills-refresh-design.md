# Design : refonte des agents et nouveau plugin `jlb-ia-toolkit`

Date : 2026-11-25. Statut : proposé, en attente de validation.

## Intention

Disposer, pour tous les projets (Python, AWS, Ansible, Rust), d'un seul jeu d'agents et de
skills Claude Code : génériques, courts, au frontmatter complet, maintenus dans ce dépôt et
installés comme plugins. Y ajouter le savoir qui manque pour l'IA workbench Rust : design
d'interface egui, développement Rust, intégration des CLI agentiques (Claude Code, Codex),
APIs OpenAI et Anthropic, APIs REST Jira et Confluence.

## État constaté le 2026-11-25

| Emplacement | Contenu | Problème |
|---|---|---|
| `~/depots/jlb-claude-skills` (= `origin/main`, 2026-09-29) | 9 skills, 15 agents dans 5 plugins, `model: sonnet` | Descriptions « USE PROACTIVELY », pas de `color`, pas de scénarios ; Vault / Dollar Universe / SFTP toujours en dur (89 mentions dans `integration-engineer`) ; 8 agents > 650 lignes (max 1 023) ; `release-manager` (79 lignes) ne connaît que `pip` |
| `~/.claude/plugins/` | marketplace clonée au 2026-04-10 ; seuls `jlb-python-toolkit` et `jlb-aws-serverless` 1.0.0 installés, **sans agents** | Les plugins `jlb-atlassian`, `jlb-workflow-toolkit` et les agents de septembre ne sont pas installés |
| `~/.claude/agents/<catégorie>/` | 13 copies du 2026-09-01, antérieures à la migration en plugins | Doublonneront les agents des plugins dès que ceux-ci seront installés |
| `~/.claude/skills/synced/` | 35 skills descendues de claude.ai | Copie, jamais à éditer |

## Objectifs

1. Reprendre les 15 agents du dépôt : frontmatter `name`, `description` (« Use this agent
   when… », 2 à 4 scénarios en prose), `tools` minimaux, `model`, `color` ; corps < 300 lignes
   et < 10 000 caractères ; contexte projet lu depuis le `CLAUDE.md` du projet courant ;
   Vault, SFTP, Dollar Universe deviennent des exemples conditionnels (« si le projet
   utilise… »).
2. Les gros modèles (template de PR, changelog Keep a Changelog, matrice de capacités)
   quittent les agents pour des fichiers de référence dans les skills du même plugin ; l'agent
   les précharge via le champ de frontmatter `skills:` (contenu injecté au démarrage).
   L'outil de délégation s'écrit `Agent` (`Task` n'est qu'un alias depuis la 2.1.63).
3. `release-manager` devient agnostique du langage : source de version détectée
   (`pyproject.toml`, `Cargo.toml` workspace, `package.json`, `.version`), lock refresh
   (`uv lock`, `cargo update --workspace`), tag annoté `vX.Y.Z`, GitHub Release via `gh`.
4. Nouveau plugin `jlb-ia-toolkit` : 5 skills (`rust-dev`, `egui-ui-design`,
   `agent-cli-integration`, `llm-provider-apis`, `atlassian-rest-api`) et 2 agents
   (`rust-reviewer`, `ui-designer`). Enregistré dans `marketplace.json`, `README.md`,
   `Makefile` (`install-ia`).
5. Synchroniser l'installation locale : sauvegarde de `~/.claude/agents/` dans
   `~/.claude/backups/agents-2026-11-25/` puis suppression des 13 copies ; mise à jour de la
   marketplace ; installation des plugins `jlb-atlassian`, `jlb-workflow-toolkit`,
   `jlb-ia-toolkit` et mise à jour des deux autres.

## Non-objectifs

- Ne pas toucher `~/.claude/skills/synced/`.
- Ne pas recréer `version-manager` (fusionné dans `release-manager` en septembre) ni ajouter
  d'agents d'orchestration, git, documentation ou versions : les quatre existent
  (`orchestrator`, `scm-expert`, `documentation-writer`, `release-manager`) et sont améliorés.
- Ne pas dupliquer le skill intégré `claude-api` ni le plugin officiel `atlassian` (MCP) :
  `llm-provider-apis` couvre la Responses API OpenAI et la Messages API brute ;
  `atlassian-rest-api` couvre REST v3 / v2, ADF et storage format.
- Pas de hooks, pas de modification de `~/.claude/CLAUDE.md`.

## Anti-objectifs

- Un agent qui recopie un `CLAUDE.md` de projet ou un autre agent.
- Une clé d'API, même factice, dans un exemple.
- Un fait d'API sans lien vers la doc officielle et sans date de vérification.
- Une description de skill qui résume son déroulé (l'agent la suivrait sans lire la skill).

## Contraintes

- Langue : skills en français pédagogique (comme les 9 existantes) ; agents en anglais
  (comme les 15 existants) ; identifiants anglais.
- `model: sonnet` conservé sur les agents existants (choix de septembre, économie) ; les deux
  nouveaux agents de revue et design prennent `inherit` pour profiter du modèle de la session.
  Décision de l'auteur, modifiable en une ligne.
- Agents exécutant des commandes (`scm-expert`, `release-manager`, `rust-reviewer`) :
  proposer, puis exécuter seulement après accord pour commit, merge, tag, push, suppression.
- Les skills ne font aucun appel API réel ; les exemples sont des extraits de corps/réponses.

## Approches envisagées

| Question | Options | Décision |
|---|---|---|
| Où maintenir | projet `.claude/` / `~/.claude/` direct / dépôt de plugins | **Dépôt de plugins** (choix utilisateur, 2026-11-25) |
| Profondeur de reprise des agents | frontmatter seul / frontmatter + contexte / **agnostiques + condensés** | **Agnostiques + condensés** (choix utilisateur) |
| `integration-engineer`, `data-migration-specialist` | intacts / archiver / **généraliser** | **Généraliser** (choix utilisateur) |
| Copies `~/.claude/agents/` | garder (doublons) / **sauvegarder puis supprimer** | **Sauvegarder puis supprimer** (auteur) |
| Nouveaux agents transverses | ajouter / **améliorer les existants** | **Améliorer** : 4 agents existent déjà (auteur) |

## Le plugin `jlb-ia-toolkit`

| Skill | Déclencheurs | Contenu | Sources |
|---|---|---|---|
| `rust-dev` | cargo, clippy, workspace, thiserror, mpsc, fixtures, edition 2024 | Workspace multi-crates et règle de dépendance, erreurs typées + code de sortie, tests sur fixtures, threads + `mpsc`, lecture de `clippy -D warnings`, checklist « nouveau port / adaptateur » | Rust book, Clippy lints, Cargo book |
| `egui-ui-design` | egui, eframe, panneau, layout, thème, palette, contraste, WSLg | Panneaux qui rendent des intents, `Style`/`Visuals`, palette et contraste WCAG, `ScrollArea`, repaint, pièges WSLg, `egui_commonmark` | docs.rs egui, WCAG 2.2 |
| `agent-cli-integration` | Claude Code CLI, Codex CLI, stream-json, JSONL, spawn, kill | Flags, événements JSONL et leur lecture, spawn sans shell, `--`, `env_remove`, `Stdio::null`, arrêt propre | Doc CLI Claude Code, doc Codex CLI |
| `llm-provider-apis` | Responses API, Messages API, `max_output_tokens`, `stop_reason`, 401/429 | Corps minimaux, champs de réponse, table HTTP → erreur typée, interdits du corps Anthropic, coût des appels | platform.openai.com, docs.claude.com |
| `atlassian-rest-api` | Jira REST, Confluence REST, ADF, storage format, Basic auth | Endpoints v3 / v2, Basic `email:token`, Markdown → ADF / storage et dégradations, résumé des erreurs | developer.atlassian.com |

| Agent | Outils | Rôle | Sortie |
|---|---|---|---|
| `rust-reviewer` (blue, inherit) | Read, Grep, Glob, Bash | `cargo fmt --check`, `clippy -D warnings`, `cargo test --locked`, puis invariants du `CLAUDE.md` du projet | Verdict puis `fichier:ligne` + gravité ; ne modifie rien |
| `ui-designer` (purple, inherit) | Read, Grep, Glob | Lit l'UI existante, propose disposition / thème / accessibilité en maquette texte + plan | Maquette ASCII + fichiers à toucher ; n'écrit pas de code |

## Reprise des 15 agents existants

| Agent | Plugin | Cible | Changement principal |
|---|---|---|---|
| `orchestrator` | workflow | < 250 l. | Découvre les agents disponibles au lieu d'une liste figée ; ordre design → plan → code → review → docs → release |
| `documentation-writer` | workflow | < 250 l. | Règles de langue lues dans le `CLAUDE.md` du projet ; validation avant suppression conservée |
| `product-owner` | workflow | < 200 l. | Frontmatter seulement |
| `scm-expert` | python | < 250 l. | Scopes déduits de l'arborescence ; template de PR vers skill ; pas de mention d'outil IA dans les commits |
| `release-manager` | python | < 200 l. | Agnostique du langage (voir objectif 3) |
| `python-clean-architecture-reviewer` | python | — | Frontmatter seulement |
| `makefile-expert`, `windows-scripts-expert`, `test-automation-engineer` | python | < 300 l. | Vault conditionnel, exemples génériques |
| `terraform-aws-iac-reviewer` | aws | — | Frontmatter seulement |
| `devops-engineer`, `security-expert` | aws | < 300 l. | Vault / credentials conditionnels |
| `integration-engineer`, `data-migration-specialist` | aws | < 300 l. | Généralisés : API REST, SFTP, gestionnaires de secrets ; migrations de données ; Vault en exemple |
| `jira-ticket-writer` | atlassian | — | Frontmatter seulement |

Versions : chaque plugin modifié monte en MINOR ; `marketplace.json` passe en 1.1.0.

## Vérification

- `python installer.py --list` et `--report-specifics` verts ; `--dry-run` liste le nouveau
  plugin.
- Frontmatter de chaque agent et skill validé par un script (nom, champs requis, couleur
  parmi les 8 valeurs documentées, longueur de description, taille du corps) et
  `claude plugin validate plugins/<plugin>` vert pour chaque plugin.
- Pour chaque nouvelle skill : un scénario de recherche joué par un sous-agent sans puis
  avec la skill.
- Pour `rust-reviewer` : lancement sur `~/depots/rust_openai_gui`, verdict vert attendu.
  Pour `scm-expert` et `release-manager` : état et proposition sans commit ni tag.
- Après installation : `claude` liste les agents sans doublon.

## Sources (vérifiées le 2026-11-25)

- Subagents (frontmatter, `tools`, `skills`, `color`, `model`) :
  https://code.claude.com/docs/en/sub-agents.md
- Skills (frontmatter, « Keep SKILL.md under 500 lines », description tronquée à 1 536
  caractères) : https://code.claude.com/docs/en/skills.md
- Plugins (manifeste, découverte `skills/<name>/SKILL.md`, `agents/<name>.md`,
  `claude plugin validate`) : https://code.claude.com/docs/en/plugins-reference.md
- Spécification des skills : https://agentskills.io/specification

## Laissé au constructeur

- Ordre des sections dans chaque fichier, URL précises (vérifiées le jour de la rédaction).
- Découpage en fichiers de référence quand une skill dépasse 300 lignes.
