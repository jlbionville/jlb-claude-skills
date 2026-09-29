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
```

## Plugins

| Plugin | Skills | Agents | Description |
|--------|--------|--------|-------------|
| **jlb-python-toolkit** | `python-dev` · `devops-python` · `linux-shell` | `python-clean-architecture-reviewer` · `release-manager` · `scm-expert` · `makefile-expert` · `windows-scripts-expert` · `test-automation-engineer` | Python pro (Clean Architecture), scripts DevOps, shell/Makefile, outillage développement |
| **jlb-aws-serverless** | `aws-serverless` · `terraform-serverless-aws` · `alexa-skill-python` | `terraform-aws-iac-reviewer` · `devops-engineer` · `integration-engineer` · `data-migration-specialist` · `security-expert` | Stack serverless AWS + Terraform IaC + Skills Alexa + DevOps/sécurité/intégrations |
| **jlb-content-publisher** | `wordpress-manager` · `technical-article-writer` | — | Gestion WordPress + rédaction articles techniques FR |
| **jlb-bourse** | `bourse-investor` | — | Analyse boursière ⚠️ *claude.ai uniquement* |
| **jlb-atlassian** | — | `jira-ticket-writer` | Tickets Jira au format du template Markdown Alfaco |
| **jlb-workflow-toolkit** | — | `product-owner` · `orchestrator` · `documentation-writer` | Agents transverses : méthodologie, coordination multi-agents, documentation projet |

### Agents

**Agents de revue (lecture seule)** — produisent un rapport priorisé sans modifier le code :

| Agent | Plugin | Déclenchement | Vérifie |
|-------|--------|---------------|---------|
| `python-clean-architecture-reviewer` | `jlb-python-toolkit` | après écriture de code Python, avant commit/PR | bugs, règle de dépendance des couches, injection, erreurs codifiées, zéro hardcoding, tests |
| `terraform-aws-iac-reviewer` | `jlb-aws-serverless` | après modification de `.tf`/`.tfvars`, avant un plan en prod | IAM moindre privilège, chiffrement, state isolé, modules versionnés, 13 tags, SemVer |

**Agents d'action (peuvent écrire)** — exécutent des tâches avec confirmation avant actions destructives :

| Agent | Plugin | Rôle |
|-------|--------|------|
| `release-manager` | `jlb-python-toolkit` | SemVer, fusion PR empilées, tags Git, vérification `pip install ...@vX.Y.Z` |
| `scm-expert` | `jlb-python-toolkit` | Git, messages de commit, branches, PR |
| `makefile-expert` | `jlb-python-toolkit` | Authoring / refactoring de Makefiles modulaires |
| `windows-scripts-expert` | `jlb-python-toolkit` | Scripts Windows (batch, PowerShell) équivalents Makefile |
| `test-automation-engineer` | `jlb-python-toolkit` | Stratégie de tests, coverage, QA automatisée |
| `devops-engineer` | `jlb-aws-serverless` | CI/CD, IaC, automatisation de déploiement |
| `integration-engineer` | `jlb-aws-serverless` | Intégrations externes (Vault, SFTP/FTP), API design |
| `data-migration-specialist` | `jlb-aws-serverless` | Migrations de données, transformations Vault, opérations en masse |
| `security-expert` | `jlb-aws-serverless` | Audits sécurité (AWS IAM, Vault, credentials, données sensibles) |
| `jira-ticket-writer` | `jlb-atlassian` | Rédige tickets Jira au format template Markdown Alfaco (Epic/Story/Tâche) |
| `product-owner` | `jlb-workflow-toolkit` | Validation business, user stories, `PRODUCT_VISION.md` |
| `orchestrator` | `jlb-workflow-toolkit` | Décomposition et délégation multi-agents pour tâches complexes |
| `documentation-writer` | `jlb-workflow-toolkit` | Documentation projet, guides utilisateur, doc technique |

Ils respectent les conventions du projet relu (`CLAUDE.md`, `pyproject.toml`) en priorité
et s'appuient sur les skills associées si elles sont installées.

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
│   │   └── skills/                 (python-dev, devops-python, linux-shell)
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
│   └── jlb-workflow-toolkit/       (3 agents)
│       ├── .claude-plugin/plugin.json
│       └── agents/
│           ├── product-owner.md
│           ├── orchestrator.md
│           └── documentation-writer.md
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

- Chaque agent : `agents/<nom>.md` avec frontmatter YAML (`name`, `description`, `tools`, éventuellement `model`) — validation stricte par l'installeur (échec explicite si champs manquants)
- Chaque skill : `SKILL.md` avec frontmatter YAML (`name`, `description`) + `references/` chargés à la demande
- Chemins relatifs dans les SKILL.md (`references/xxx.md`) → compatibles avec tous les modes d'installation
- `bourse-investor` dépend de `web_search` et artifacts React → fonctionne uniquement sur claude.ai
- Certains agents contiennent des références projet-spécifiques (ex. `script4secrets`, `Vault`, `Dollar Universe`) — utilise `python installer.py --report-specifics` pour les lister

## Licence

Usage personnel.
