# jlb-claude-skills

Skills modulaires pour **Claude Code** — développement Python, AWS serverless, rédaction technique, WordPress et investissement boursier.

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
```

## Plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| **jlb-python-toolkit** | `python-dev` · `devops-python` · `linux-shell` | Python pro (Clean Architecture), scripts DevOps, shell/Makefile |
| **jlb-aws-serverless** | `aws-serverless` · `terraform-serverless-aws` · `alexa-skill-python` | Stack serverless AWS + Terraform IaC + Skills Alexa |
| **jlb-content-publisher** | `wordpress-manager` · `technical-article-writer` | Gestion WordPress + rédaction articles techniques FR |
| **jlb-bourse** | `bourse-investor` | Analyse boursière ⚠️ *claude.ai uniquement* |

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
│   └── jlb-bourse/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── bourse-investor/
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

- Chaque skill : `SKILL.md` avec frontmatter YAML (`name`, `description`) + `references/` chargés à la demande
- Chemins relatifs dans les SKILL.md (`references/xxx.md`) → compatibles avec tous les modes d'installation
- `bourse-investor` dépend de `web_search` et artifacts React → fonctionne uniquement sur claude.ai

## Licence

Usage personnel.
