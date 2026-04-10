# Référence : Scripts & CLI Python

## Table des matières
1. Pattern principal : argparse piloté par JSON
2. Format du fichier JSON de paramètres
3. `ArgParser` — classe réutilisable
4. Précédence : CLI > JSON (defaults) dans le script
5. Rich — output terminal professionnel
6. Gestion des fichiers — Pathlib
7. Subprocess — appels système sécurisés

---

## 1. Pattern principal : argparse piloté par JSON

**Principe :** un fichier JSON est la source de vérité pour les paramètres d'un script.
Il définit à la fois la **structure CLI** (nom, type, help, choices…) et les **valeurs par défaut runtime**.
argparse est construit dynamiquement à partir de ce fichier, jamais codé en dur.

```
constants.py          ← PARAMS_SCHEMA_FILE = "config/params.json"
config/
└── params.json       ← définition + defaults de tous les paramètres
my_script.py          ← parse_args() lit params.json → construit argparse
```

**Flux de résolution :**
```
params.json (default)
      ↓
argparse (valeur par défaut injectée depuis JSON)
      ↓  ← CLI fourni ? → CLI écrase le default
Namespace final
```

---

## 2. Format du fichier JSON de paramètres

```json
{
  "description": "Script de traitement de données clients.",
  "arguments": [
    {
      "name": "input",
      "flags": [],
      "type": "Path",
      "help": "Fichier CSV d'entrée.",
      "required": true
    },
    {
      "name": "output",
      "flags": ["-o", "--output"],
      "type": "Path",
      "default": "output/result.csv",
      "help": "Fichier de sortie.",
      "metavar": "FILE",
      "required": false
    },
    {
      "name": "log_level",
      "flags": ["--log-level"],
      "type": "str",
      "default": "INFO",
      "choices": ["DEBUG", "INFO", "WARNING", "ERROR"],
      "help": "Niveau de journalisation.",
      "required": false
    },
    {
      "name": "batch_size",
      "flags": ["-b", "--batch-size"],
      "type": "int",
      "default": 100,
      "help": "Nombre d'enregistrements par lot.",
      "metavar": "N",
      "required": false
    },
    {
      "name": "dry_run",
      "flags": ["--dry-run"],
      "type": "bool",
      "action": "store_true",
      "default": false,
      "help": "Simuler sans écrire de fichier.",
      "required": false
    },
    {
      "name": "tags",
      "flags": ["--tag"],
      "type": "str",
      "action": "append",
      "default": [],
      "help": "Tag à appliquer (répétable : --tag a --tag b).",
      "metavar": "TAG",
      "required": false
    }
  ]
}
```

### Champs supportés par paramètre

| Champ | Obligatoire | Valeurs possibles | Description |
|-------|-------------|-------------------|-------------|
| `name` | ✅ | string | Nom dest dans `Namespace` |
| `flags` | ✅ | `[]` pour positionnel, `["-x","--long"]` pour option | Flags CLI |
| `type` | ✅ | `"str"`, `"int"`, `"float"`, `"bool"`, `"Path"` | Type Python |
| `default` | — | any | Valeur par défaut runtime |
| `help` | — | string | Texte d'aide `--help` |
| `required` | — | `true`/`false` | Option obligatoire |
| `choices` | — | `["a","b","c"]` | Valeurs autorisées |
| `metavar` | — | string | Nom affiché dans `--help` |
| `action` | — | `"store_true"`, `"store_false"`, `"append"`, `"count"` | Comportement argparse |

---

## 3. `ArgParser` — classe réutilisable

À placer dans `my_package/cli/arg_parser.py` ou `my_package/interface/cli/arg_parser.py`.

```python
# cli/arg_parser.py
"""
Constructeur argparse piloté par un fichier JSON de définition des paramètres.

Usage :
    from my_package.cli.arg_parser import ArgParser
    from my_package.constants import PARAMS_SCHEMA_FILE

    parser = ArgParser(PARAMS_SCHEMA_FILE)
    args = parser.parse()
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from my_package.constants import ErrorCode
from my_package.domain.exceptions import ConfigError

logger = logging.getLogger(__name__)

# Mapping des types JSON → types Python
_TYPE_MAP: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "Path": Path,
}


class ArgParser:
    """Construit et expose un ArgumentParser depuis un fichier JSON de définition.

    Args:
        schema_path: Chemin vers le fichier JSON de définition des paramètres.
            Doit être résolu depuis constants.PARAMS_SCHEMA_FILE.

    Example:
        parser = ArgParser(PARAMS_SCHEMA_FILE)
        args = parser.parse()
        print(args.output)  # valeur CLI ou default du JSON
    """

    def __init__(self, schema_path: Path) -> None:
        self._schema_path = schema_path
        self._schema = self._load_schema()
        self._parser = self._build_parser()

    # ── API publique ──────────────────────────────────────────────────────────

    def parse(self, argv: list[str] | None = None) -> argparse.Namespace:
        """Parser les arguments CLI. Retourne un Namespace avec les valeurs résolues.

        Les valeurs par défaut viennent du JSON. Les valeurs CLI ont précédence.
        """
        return self._parser.parse_args(argv)

    def print_help(self) -> None:
        self._parser.print_help()

    # ── Construction du parser ────────────────────────────────────────────────

    def _load_schema(self) -> dict[str, Any]:
        if not self._schema_path.exists():
            raise ConfigError(
                ErrorCode.CONFIG_FILE_NOT_FOUND,
                path=str(self._schema_path),
            )
        try:
            return json.loads(self._schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(
                ErrorCode.CONFIG_INVALID_VALUE,
                key=str(self._schema_path),
                value=str(exc),
            ) from exc

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description=self._schema.get("description", ""),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        for arg_def in self._schema.get("arguments", []):
            self._add_argument(parser, arg_def)
        return parser

    def _add_argument(
        self,
        parser: argparse.ArgumentParser,
        arg_def: dict[str, Any],
    ) -> None:
        """Ajouter un argument au parser depuis sa définition JSON."""
        name: str = arg_def["name"]
        flags: list[str] = arg_def.get("flags", [])
        raw_type: str = arg_def.get("type", "str")
        action: str | None = arg_def.get("action")

        # Construire les kwargs pour add_argument
        kwargs: dict[str, Any] = {
            "help": arg_def.get("help", ""),
            "dest": name,
        }

        # Type — ignoré pour store_true/store_false/append sans type
        if action in ("store_true", "store_false"):
            kwargs["action"] = action
            kwargs["default"] = arg_def.get("default", False)
        elif action == "append":
            kwargs["action"] = "append"
            kwargs["type"] = _TYPE_MAP.get(raw_type, str)
            kwargs["default"] = arg_def.get("default", []) or None
            # argparse append + default=[] produit des doublons → on utilise None
        elif action == "count":
            kwargs["action"] = "count"
            kwargs["default"] = arg_def.get("default", 0)
        else:
            kwargs["type"] = _TYPE_MAP.get(raw_type, str)
            if "default" in arg_def:
                default = arg_def["default"]
                # Convertir les defaults Path stockés en string
                if raw_type == "Path" and isinstance(default, str):
                    default = Path(default)
                kwargs["default"] = default

        # Champs optionnels
        if "choices" in arg_def:
            kwargs["choices"] = arg_def["choices"]
        if "metavar" in arg_def:
            kwargs["metavar"] = arg_def["metavar"]
        if "required" in arg_def and flags:  # required n'a de sens que pour les options
            kwargs["required"] = arg_def["required"]

        # Argument positionnel (flags vide) vs option (flags non vide)
        if flags:
            parser.add_argument(*flags, **kwargs)
        else:
            # Positionnel : pas de default ni required
            kwargs.pop("required", None)
            kwargs.pop("default", None)
            parser.add_argument(name, **kwargs)

        logger.debug("Argument enregistré : %s (flags=%s, default=%s)",
                     name, flags, arg_def.get("default"))
```

---

## 4. Précédence : CLI > JSON (defaults) dans le script

```python
#!/usr/bin/env python3
"""
Script de traitement de données.

Usage:
    python process.py data/input.csv
    python process.py data/input.csv --output out.csv --log-level DEBUG --dry-run
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from my_package.cli.arg_parser import ArgParser
from my_package.constants import PARAMS_SCHEMA_FILE

logger = logging.getLogger(__name__)


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    # ── 1. Parser les arguments (CLI écrase les defaults du JSON) ─────────────
    arg_parser = ArgParser(PARAMS_SCHEMA_FILE)
    args = arg_parser.parse()

    # ── 2. Configurer le logging avec la valeur résolue ──────────────────────
    setup_logging(args.log_level)

    logger.info("Démarrage — input=%s output=%s batch_size=%d dry_run=%s",
                args.input, args.output, args.batch_size, args.dry_run)

    # ── 3. Logique métier ─────────────────────────────────────────────────────
    input_path: Path = args.input
    if not input_path.exists():
        logger.error("Fichier introuvable : %s", input_path)
        return 1

    if args.dry_run:
        logger.info("[DRY RUN] Simulation sans écriture.")
        return 0

    # ... traitement réel
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Constante dans `constants.py`

```python
# constants.py
from pathlib import Path

class Paths:
    """Chemins structurels du package — jamais hardcodés ailleurs."""
    PACKAGE_ROOT: Path = Path(__file__).parent
    CONFIG_DIR: Path = PACKAGE_ROOT / "config"

# Chemin vers le fichier de définition des paramètres CLI
PARAMS_SCHEMA_FILE: Path = Paths.CONFIG_DIR / "params.json"
```

### Structure résultante

```
src/my_package/
├── constants.py               # PARAMS_SCHEMA_FILE = Paths.CONFIG_DIR / "params.json"
├── config/
│   └── params.json            # source de vérité : définition + defaults
├── cli/
│   └── arg_parser.py          # ArgParser — réutilisable par tous les scripts
└── interface/
    └── cli.py                 # script principal — parse + logique

# Plusieurs scripts → plusieurs JSON
config/
├── params_import.json
├── params_export.json
└── params_report.json
```

Pour plusieurs scripts, on instancie `ArgParser` avec le fichier JSON correspondant :
```python
# Chaque script déclare son propre JSON
IMPORT_PARAMS_FILE: Path = Paths.CONFIG_DIR / "params_import.json"
EXPORT_PARAMS_FILE: Path = Paths.CONFIG_DIR / "params_export.json"
```

---

---

## 5. Rich — Output terminal professionnel

```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeRemainingColumn
from rich import print as rprint

console = Console()

# Table
def display_results(users: list[dict]) -> None:
    table = Table(title="Utilisateurs", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Nom")
    table.add_column("Email")
    table.add_column("Statut")

    for user in users:
        status_color = "green" if user["active"] else "red"
        table.add_row(
            str(user["id"]),
            user["name"],
            user["email"],
            f"[{status_color}]{'actif' if user['active'] else 'inactif'}[/]",
        )
    console.print(table)

# Progress bar personnalisée
with Progress(
    SpinnerColumn(),
    "[progress.description]{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeRemainingColumn(),
) as progress:
    task = progress.add_task("Traitement...", total=len(items))
    for item in items:
        process(item)
        progress.advance(task)
```

---

## 6. Gestion des fichiers — Pathlib (toujours)

```python
from pathlib import Path

# ✅ Pathlib — idiomatique Python 3
data_dir = Path("data")
output = data_dir / "results" / "output.csv"
output.parent.mkdir(parents=True, exist_ok=True)

# Lecture
text = output.read_text(encoding="utf-8")
lines = output.read_text().splitlines()

# Glob
csv_files = list(data_dir.glob("**/*.csv"))

# ❌ os.path — à éviter
import os
output = os.path.join("data", "results", "output.csv")
```

---

## 7. Subprocess — Appels système sécurisés

```python
import subprocess
import shlex

# ✅ Bon — liste d'arguments, pas de shell injection
result = subprocess.run(
    ["git", "log", "--oneline", "-n", "10"],
    capture_output=True,
    text=True,
    check=True,  # lève CalledProcessError si code != 0
    timeout=30,
)
print(result.stdout)

# ✅ Si vous devez passer une commande en string
cmd = "git log --oneline -n 10"
result = subprocess.run(shlex.split(cmd), capture_output=True, text=True, check=True)

# ❌ Dangereux — injection possible si user_input vient de l'extérieur
subprocess.run(f"git log {user_input}", shell=True)
```

---

## Liens officiels

- Argparse : https://docs.python.org/3/library/argparse.html
- Rich : https://rich.readthedocs.io/
- Pathlib : https://docs.python.org/3/library/pathlib.html
- Subprocess : https://docs.python.org/3/library/subprocess.html
- JSON (stdlib) : https://docs.python.org/3/library/json.html
