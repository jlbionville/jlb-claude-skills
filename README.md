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
```

## Plugins

| Plugin | Skills | Agents | Description |
|--------|--------|--------|-------------|
| **jlb-python-toolkit** | `python-dev` · `devops-python` · `linux-shell` | `python-clean-architecture-reviewer` · `release-manager` | Python pro (Clean Architecture), scripts DevOps, shell/Makefile |
| **jlb-aws-serverless** | `aws-serverless` · `terraform-serverless-aws` · `alexa-skill-python` | `release-manager` | « prépare la release », « fusionne les PR et crée les tags » | SemVer, mise à jour pyproject/README/CLAUDE.md/CHANGELOG, fusion de PR empilées dans l'ordre (merge commit + retarget), tags annotés, vérification `pip install …@vX.Y.Z`. Demande confirmation avant fusion, tag et push |
| `jira-ticket-writer` | « rédige une story », « découpe cette epic en tickets » | Écrit des fichiers `.md` au format du template Alfaco (sections, hiérarchie Epic/Story/Tâche/Sous-tâche, Markdown supporté par le convertisseur ADF), plus un `00-plan.md` d'ordre de création. Ne crée pas les tickets dans Jira |
| `terraform-aws-iac-reviewer` | Stack serverless AWS + Terraform IaC + Skills Alexa |
| **jlb-content-publisher** | `wordpress-manager` · `technical-article-writer` | — | Gestion WordPress + rédaction articles techniques FR |
| **jlb-bourse** | `bourse-investor` | — | Analyse boursière ⚠️ *claude.ai uniquement* |
| **jlb-atlassian** | — | `jira-ticket-writer` | Tickets Jira au format du template Markdown Alfaco |

### Agents

Les deux agents de **revue** sont en lecture seule : ils produisent un rapport priorisé
(`fichier:ligne`, scénario, correction minimale) sans modifier le code.

| Agent | Déclenchement | Vérifie |
|-------|---------------|---------|
| `python-clean-architecture-reviewer` | après écriture de code Python, avant commit/PR, « relis mon code Python » | bugs, règle de dépendance des couches, injection, erreurs codifiées, zéro hardcoding, tests (lance `pytest`/`ruff`/`mypy` si configurés) |
| `terraform-aws-iac-reviewer` | après modification de `.tf`/`.tfvars`, avant un plan en prod, « revue Terraform » | IAM moindre privilège, chiffrement, state isolé, modules versionnés, 13 tags + validations, SemVer, observabilité. N'exécute jamais `apply`/`destroy`/`state` |

Ils respectent les conventions du projet relu (`CLAUDE.md`, `pyproject.toml`) en priorité
et s'appuient sur les skills associées si elles sont installées.

- **Via le plugin** : installés automatiquement, préfixés par le plugin
  (ex. `jlb-python-toolkit:release-manager`, `jlb-atlassian:jira-ticket-writer`).
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
│   ├── jlb-python-toolkit/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json         ← Manifeste du plugin
│   │   ├── agents/
│   │   │   ├── python-clean-architecture-reviewer.md
│   │   │   └── release-manager.md
│   │   └── skills/
│   │       ├── python-dev/
│   │       │   ├── SKILL.md
│   │       │   └── references/
│   │       ├── devops-python/
│   │       │   ├── SKILL.md
│   │       │   └── references/
│   │       └── linux-shell/
│   │           ├── SKILL.md
│   │           └── references/
│   ├── jlb-aws-serverless/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── agents/
│   │   │   └── terraform-aws-iac-reviewer.md
│   │   └── skills/
│   │       ├── aws-serverless/
│   │       ├── terraform-serverless-aws/
│   │       └── alexa-skill-python/
│   ├── jlb-content-publisher/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       ├── wordpress-manager/
│   │       └── technical-article-writer/
│   ├── jlb-bourse/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── bourse-investor/
│   └── jlb-atlassian/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── agents/
│           └── jira-ticket-writer.md
├── install.sh                      ← Legacy: shell installer
├── Makefile                        ← Legacy: make installer
└── installer.py                    ← Legacy: Python installer
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

### Python

```bash
python installer.py                              # Tout
python installer.py -p jlb-aws-serverless        # Un plugin
python installer.py -p jlb-python-toolkit -p jlb-aws-serverless  # Plusieurs
python installer.py --project ~/my-repo           # Dans un projet
```

## Conventions

- Chaque agent : `agents/<nom>.md` avec frontmatter (`name`, `description`, `tools`, `model`) — revue en lecture seule
- Chaque skill : `SKILL.md` avec frontmatter YAML (`name`, `description`) + `references/` chargés à la demande
- Chemins relatifs dans les SKILL.md (`references/xxx.md`) → compatibles avec tous les modes d'installation
- `bourse-investor` dépend de `web_search` et artifacts React → fonctionne uniquement sur claude.ai

## Licence

Usage personnel.
