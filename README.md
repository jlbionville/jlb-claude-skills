# jlb-claude-skills

Skills et agents modulaires pour **Claude Code** — développement Python, AWS serverless, rédaction technique, WordPress et investissement boursier.

## Installation rapide (recommandé)

Dans Claude Code :

```
/plugin marketplace add jlbionville/jlb-claude-skills
```

Puis installer les plugins souhaités :

```
/plugin install jlb-python-toolkit@jlb-claude-skills
/plugin install jlb-aws-serverless@jlb-claude-skills
/plugin install jlb-content-publisher@jlb-claude-skills
/plugin install jlb-bourse@jlb-claude-skills
/plugin install jlb-atlassian@jlb-claude-skills
/plugin install jlb-workflow-toolkit@jlb-claude-skills
/plugin install jlb-ia-toolkit@jlb-claude-skills
```

## Plugins

| Plugin | Skills | Agents | Description |
|--------|--------|--------|-------------|
| **jlb-python-toolkit** | `python-dev` · `devops-python` · `linux-shell` · `git-release-templates` | `python-clean-architecture-reviewer` · `release-manager` · `scm-expert` · `makefile-expert` · `windows-scripts-expert` · `test-automation-engineer` | Python pro (Clean Architecture), scripts DevOps, shell/Makefile, outillage développement |
| **jlb-aws-serverless** | `aws-serverless` · `terraform-serverless-aws` · `alexa-skill-python` | `terraform-aws-iac-reviewer` · `devops-engineer` · `integration-engineer` · `data-migration-specialist` · `security-expert` | Stack serverless AWS + Terraform IaC + Skills Alexa + DevOps/sécurité/intégrations |
| **jlb-content-publisher** | `wordpress-manager` · `technical-article-writer` | — | Gestion WordPress + rédaction articles techniques FR |
| **jlb-bourse** | `bourse-investor` | — | Analyse boursière ⚠️ *claude.ai uniquement* |
| **jlb-atlassian** | — | `jira-ticket-writer` | Tickets Jira au format du template Markdown Alfaco |
| **jlb-workflow-toolkit** | — | `product-owner` · `orchestrator` · `documentation-writer` | Agents transverses : méthodologie, coordination multi-agents, documentation projet |
| **jlb-ia-toolkit** | `rust-dev` · `egui-ui-design` · `agent-cli-integration` · `llm-provider-apis` · `atlassian-rest-api` | `rust-reviewer` · `ui-designer` | Outillage IA : Rust et egui, CLI agentiques Claude Code / Codex, API OpenAI et Anthropic, API REST Jira et Confluence |

### Agents

**Agents de revue (lecture seule)** — produisent un rapport priorisé sans modifier le code :

| Agent | Plugin | Déclenchement | Vérifie |
|-------|--------|---------------|---------|
| `python-clean-architecture-reviewer` | `jlb-python-toolkit` | après écriture de code Python, avant commit/PR | bugs, règle de dépendance des couches, injection, erreurs codifiées, zéro hardcoding, tests |
| `terraform-aws-iac-reviewer` | `jlb-aws-serverless` | après modification de `.tf`/`.tfvars`, avant un plan en prod | IAM moindre privilège, chiffrement, state isolé, modules versionnés, 13 tags, SemVer |
| `rust-reviewer` | `jlb-ia-toolkit` | après écriture de code Rust, avant commit/PR | fmt, clippy `-D warnings`, tests `--locked`, invariants du `CLAUDE.md` (secrets, dépendances par crate, threads) |
| `ui-designer` | `jlb-ia-toolkit` | avant de coder un écran ou un onglet (egui / eframe) | maquette texte, états, intents, plan d'implémentation ; n'écrit pas de code |

**Agents d'action (peuvent écrire)** — exécutent des tâches avec confirmation avant actions destructives :

| Agent | Plugin | Rôle |
|-------|--------|------|
| `release-manager` | `jlb-python-toolkit` | SemVer d'après les commits, fichier de version (`pyproject.toml`, `Cargo.toml`, `package.json`, `.version`) et verrou, CHANGELOG, fusion de PR empilées, tag annoté, GitHub Release |
| `scm-expert` | `jlb-python-toolkit` | Git, messages de commit, branches, PR |
| `makefile-expert` | `jlb-python-toolkit` | Authoring / refactoring de Makefiles modulaires |
| `windows-scripts-expert` | `jlb-python-toolkit` | Scripts Windows (batch, PowerShell) équivalents Makefile |
| `test-automation-engineer` | `jlb-python-toolkit` | Stratégie de tests, coverage, QA automatisée |
| `devops-engineer` | `jlb-aws-serverless` | CI/CD, IaC, automatisation de déploiement |
| `integration-engineer` | `jlb-aws-serverless` | Intégrations externes : API, files de messages, SFTP/FTP, gestionnaires de secrets (Vault en exemple) |
| `data-migration-specialist` | `jlb-aws-serverless` | Migrations de données et opérations en masse : sauvegarde, dry-run, lots, intégrité, retour arrière |
| `security-expert` | `jlb-aws-serverless` | Audits sécurité : secrets, IAM, gestionnaires de secrets, données sensibles, entrées |
| `jira-ticket-writer` | `jlb-atlassian` | Rédige tickets Jira au format template Markdown Alfaco (Epic/Story/Tâche) |
| `product-owner` | `jlb-workflow-toolkit` | Besoin métier, user stories, critères d'acceptation, priorisation |
| `orchestrator` | `jlb-workflow-toolkit` | Découpe une demande multi-domaines, délègue aux agents disponibles dans la session, synthétise ; ne code pas |
| `documentation-writer` | `jlb-workflow-toolkit` | Documentation projet dans la langue du `CLAUDE.md` ; validation avant toute suppression |

Tous les agents lisent d'abord le `CLAUDE.md` du projet courant (conventions, commandes,
interdits) : ils sont génériques et ne connaissent aucun projet en particulier. Les agents
qui exécutent des commandes proposent puis attendent l'accord pour commit, fusion, push,
tag ou suppression. Les agents de revue ne modifient rien.

- **Via le plugin** : installés automatiquement, préfixés par le plugin
  (ex. `jlb-python-toolkit:release-manager`, `jlb-atlassian:jira-ticket-writer`).
- **Via l'installeur local** : `python installer.py --component agents` (voir section legacy plus bas).
- **Manuellement** : lier le fichier dans `~/.claude/agents/` (ou `.claude/agents/` d'un projet) :

```bash
mkdir -p ~/.claude/agents
ln -s "$PWD"/plugins/*/agents/*.md ~/.claude/agents/
```

Invocation explicite : « utilise l'agent python-clean-architecture-reviewer sur le diff »,
ou `@` puis le nom de l'agent.

### Dépendances entre skills

```
python-dev ←→ devops-python     "Complémentaire"
     ↕              ↕
   linux-shell (Makefile Python, scripts DevOps)

aws-serverless ←→ terraform-serverless-aws   "Toujours ensemble"
       ↑
alexa-skill-python (Lambda + DynamoDB)

wordpress-manager ←→ technical-article-writer (rédaction → publication)
```

## Utilisation

Après installation, les skills se déclenchent **automatiquement** quand Claude détecte un contexte pertinent, ou via commande slash :

```
/python-dev                    # Dev Python pro
/devops-python                 # Scripts DevOps/boto3
/linux-shell                   # Shell, sed/awk, Makefile
/aws-serverless                # Lambda, DynamoDB, API GW
/terraform-serverless-aws      # Modules Terraform, tagging
/alexa-skill-python            # Skills Alexa Custom + Smart Home
/wordpress-manager             # WordPress multi-sites
/technical-article-writer      # Articles techniques FR
/bourse-investor               # Analyse boursière (claude.ai)
```

## Structure du repo

```
jlb-claude-skills/
├── .claude-plugin/
│   └── marketplace.json            ← Catalogue des plugins
├── plugins/
│   ├── jlb-python-toolkit/         (3 skills + 6 agents)
│   │   ├── .claude-plugin/plugin.json
│   │   ├── agents/                 ← 6 agents .md
│   │   │   ├── python-clean-architecture-reviewer.md
│   │   │   ├── release-manager.md
│   │   │   ├── scm-expert.md
│   │   │   ├── makefile-expert.md
│   │   │   ├── windows-scripts-expert.md
│   │   │   └── test-automation-engineer.md
│   │   └── skills/                 (python-dev, devops-python, linux-shell, git-release-templates)
│   ├── jlb-aws-serverless/         (3 skills + 5 agents)
│   │   ├── .claude-plugin/plugin.json
│   │   ├── agents/
│   │   │   ├── terraform-aws-iac-reviewer.md
│   │   │   ├── devops-engineer.md
│   │   │   ├── integration-engineer.md
│   │   │   ├── data-migration-specialist.md
│   │   │   └── security-expert.md
│   │   └── skills/                 (aws-serverless, terraform-serverless-aws, alexa-skill-python)
│   ├── jlb-content-publisher/      (2 skills)
│   ├── jlb-bourse/                 (1 skill)
│   ├── jlb-atlassian/              (1 agent : jira-ticket-writer)
│   ├── jlb-workflow-toolkit/       (3 agents)
│   │   ├── .claude-plugin/plugin.json
│   │   └── agents/
│   │       ├── product-owner.md
│   │       ├── orchestrator.md
│   │       └── documentation-writer.md
│   └── jlb-ia-toolkit/             (5 skills + 2 agents)
│       ├── .claude-plugin/plugin.json
│       ├── agents/                 (rust-reviewer, ui-designer)
│       └── skills/                 (rust-dev, egui-ui-design, agent-cli-integration,
│                                    llm-provider-apis, atlassian-rest-api)
├── scripts/validate_components.py  ← Validation du frontmatter des agents et skills
├── tests/                          ← pytest du validateur (uv run --group dev python -m pytest)
├── install.sh                      ← Legacy: shell installer (skills uniquement)
├── Makefile                        ← Legacy: make installer
└── installer.py                    ← Legacy: installeur Python (skills + agents)
```

## Installation legacy (alternatives)

### Shell

```bash
git clone https://github.com/jlbionville/jlb-claude-skills.git
cd jlb-claude-skills

./install.sh                                # Tout, symlinks
./install.sh --copy                         # Tout, copie
./install.sh --plugin jlb-aws-serverless    # Un plugin
./install.sh --project ~/my-repo            # Dans un projet
./install.sh --list                         # Lister
./install.sh --uninstall                    # Supprimer
```

### Makefile

```bash
make install                    # Tout, symlink
make install-aws                # Plugin AWS
make install-python             # Plugin Python
make project P=~/my-repo        # Dans un projet
```

### Python (recommandé — supporte skills ET agents)

```bash
python installer.py                                     # Tout (skills + agents), symlink
python installer.py --component agents                  # Uniquement les agents
python installer.py --component skills                  # Uniquement les skills
python installer.py --plugin jlb-workflow-toolkit       # Un plugin spécifique
python installer.py --project ~/my-repo                 # Dans un projet (.claude/skills/ et .claude/agents/)
python installer.py --dry-run                           # Aperçu sans écriture
python installer.py --report-specifics                  # Détecter les refs projet-spécifiques dans les agents
python installer.py --list                              # Lister plugins, skills, agents
python installer.py --uninstall                         # Tout supprimer
```

Cibles par défaut :
- Skills → `~/.claude/skills/`
- Agents → `~/.claude/agents/`
- Avec `--project /path` → `<path>/.claude/skills/` et `<path>/.claude/agents/`

## Conventions

- Chaque agent : `agents/<nom>.md` avec frontmatter YAML `name`, `description`, `tools`, `model`, `color` (parmi `red, blue, green, yellow, purple, orange, pink, cyan`), éventuellement `skills:` (skills préchargées). La description commence par « À utiliser quand… » et nomme 2 à 4 déclencheurs ; elle ne résume pas le déroulé. Corps en français, en seconde personne, < 300 lignes et < 10 000 caractères, avec une section « Quand m'appeler » et une section de sortie.
- Chaque skill : `SKILL.md` avec frontmatter YAML (`name`, `description` commençant par « Use when » / « À utiliser », déclencheurs FR + EN, < 1 024 caractères) + `references/` chargés à la demande ; corps < 300 lignes visé (500 maximum) ; tout fait d'API cite sa page officielle et une date de vérification.
- Chemins relatifs dans les SKILL.md (`references/xxx.md`) → compatibles avec tous les modes d'installation
- Les agents sont génériques : contexte projet lu dans le `CLAUDE.md` du projet courant ; les outils propres à un projet (ex. Vault) n'apparaissent qu'en sous-section conditionnelle. `python installer.py --report-specifics` doit rester vide.
- Validation : `python3 scripts/validate_components.py` (option `--plugin <nom>`, `--json`) ; tests du validateur : `uv run --group dev python -m pytest`. `claude plugin validate plugins/<nom>` pour le manifeste.
- `bourse-investor` dépend de `web_search` et artifacts React → fonctionne uniquement sur claude.ai

## Licence

Usage personnel.
