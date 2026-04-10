# Référence : Clean Architecture, Erreurs, Constantes, Configuration

## Table des matières
1. Structure Clean Architecture
2. Module `constants.py` — erreurs codifiées
3. Gestion des erreurs applicatives
4. Configuration sans hardcoding
5. Précédence : CLI > fichier de config > défaut
6. Exemple complet intégré

---

## 1. Structure Clean Architecture

```
src/my_package/
├── __init__.py
├── constants.py           # ← codes d'erreur, constantes globales, PARAMS_SCHEMA_FILE
├── config.py              # ← chargement config fichier + résolution précédence
├── config/
│   └── params.json        # ← source de vérité : définition params CLI + defaults
│
├── domain/                # Couche 1 : règles métier pures
│   ├── __init__.py
│   ├── entities.py        # dataclasses/Pydantic, pas de framework
│   ├── value_objects.py
│   ├── repositories.py    # interfaces (ABC) — pas d'implémentation
│   └── exceptions.py      # exceptions métier (utilisent constants.py)
│
├── application/           # Couche 2 : cas d'usage (use cases)
│   ├── __init__.py
│   └── services.py        # orchestration, pas de SQL ni HTTP
│
├── infrastructure/        # Couche 3 : détails techniques
│   ├── __init__.py
│   ├── persistence/       # implémentations Repository (SQL, fichier…)
│   └── http/              # clients HTTP, intégrations externes
│
└── interface/             # Couche 4 : points d'entrée
    ├── __init__.py
    ├── cli/
    │   ├── arg_parser.py  # ArgParser — construit argparse depuis params.json
    │   └── main.py        # point d'entrée script : parse → résout config → exécute
    ├── api/               # FastAPI/Flask routers
    └── presenters.py      # transformation domain → DTO de sortie
```

**Règle de dépendance :** les flèches vont toujours vers le centre.
```
interface → application → domain
infrastructure → domain
```
- `domain` n'importe rien des autres couches
- `application` n'importe que `domain`
- `infrastructure` implémente les interfaces de `domain`
- `interface` orchestre via `application`

---

## 2. Module `constants.py` — Erreurs codifiées

**Principe :** toute erreur applicative a un code (identifiant unique) et un libellé (message humain). Ces deux informations sont définies **une seule fois** dans `constants.py`. Jamais de message d'erreur littéral ailleurs.

```python
# constants.py
"""
Constantes globales du package.

Conventions :
- ErrorCode : codes d'erreur sous forme d'enum StrEnum
- ERROR_CATALOG : mapping code → libellé humain
- Constantes de configuration : MAJUSCULES, groupées par domaine
"""
from __future__ import annotations
from enum import StrEnum


# ── Codes d'erreur ────────────────────────────────────────────────────────────

class ErrorCode(StrEnum):
    """Codes d'erreur applicatifs.

    Convention : DOMAINE_DESCRIPTION
    Exemple    : USER_NOT_FOUND, CONFIG_MISSING_KEY, IO_READ_FAILED
    """
    # Domaine : utilisateur
    USER_NOT_FOUND       = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS  = "USER_ALREADY_EXISTS"
    USER_INVALID_EMAIL   = "USER_INVALID_EMAIL"

    # Domaine : authentification
    AUTH_INVALID_TOKEN   = "AUTH_INVALID_TOKEN"
    AUTH_EXPIRED_TOKEN   = "AUTH_EXPIRED_TOKEN"
    AUTH_UNAUTHORIZED    = "AUTH_UNAUTHORIZED"

    # Domaine : configuration
    CONFIG_MISSING_KEY   = "CONFIG_MISSING_KEY"
    CONFIG_INVALID_VALUE = "CONFIG_INVALID_VALUE"
    CONFIG_FILE_NOT_FOUND = "CONFIG_FILE_NOT_FOUND"

    # Domaine : I/O
    IO_READ_FAILED       = "IO_READ_FAILED"
    IO_WRITE_FAILED      = "IO_WRITE_FAILED"
    IO_FILE_NOT_FOUND    = "IO_FILE_NOT_FOUND"

    # Domaine : externe (API tierce, BDD…)
    EXTERNAL_TIMEOUT     = "EXTERNAL_TIMEOUT"
    EXTERNAL_UNAVAILABLE = "EXTERNAL_UNAVAILABLE"
    EXTERNAL_BAD_RESPONSE = "EXTERNAL_BAD_RESPONSE"


# ── Catalogue des libellés ────────────────────────────────────────────────────

ERROR_CATALOG: dict[ErrorCode, str] = {
    ErrorCode.USER_NOT_FOUND:        "Utilisateur introuvable.",
    ErrorCode.USER_ALREADY_EXISTS:   "Un utilisateur avec cet email existe déjà.",
    ErrorCode.USER_INVALID_EMAIL:    "L'adresse email fournie est invalide.",

    ErrorCode.AUTH_INVALID_TOKEN:    "Token d'authentification invalide.",
    ErrorCode.AUTH_EXPIRED_TOKEN:    "Token d'authentification expiré.",
    ErrorCode.AUTH_UNAUTHORIZED:     "Accès non autorisé.",

    ErrorCode.CONFIG_MISSING_KEY:    "Clé de configuration manquante : {key}.",
    ErrorCode.CONFIG_INVALID_VALUE:  "Valeur de configuration invalide pour '{key}' : {value}.",
    ErrorCode.CONFIG_FILE_NOT_FOUND: "Fichier de configuration introuvable : {path}.",

    ErrorCode.IO_READ_FAILED:        "Impossible de lire le fichier : {path}.",
    ErrorCode.IO_WRITE_FAILED:       "Impossible d'écrire dans le fichier : {path}.",
    ErrorCode.IO_FILE_NOT_FOUND:     "Fichier introuvable : {path}.",

    ErrorCode.EXTERNAL_TIMEOUT:      "Délai d'attente dépassé pour le service externe.",
    ErrorCode.EXTERNAL_UNAVAILABLE:  "Service externe indisponible.",
    ErrorCode.EXTERNAL_BAD_RESPONSE: "Réponse inattendue du service externe.",
}


# ── Constantes de configuration (valeurs par défaut) ─────────────────────────

class Defaults:
    """Valeurs par défaut de configuration.

    Ces valeurs sont les derniers maillons de la chaîne de précédence :
    CLI > fichier de config > Defaults.*
    """
    # Serveur
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    LOG_LEVEL: str = "INFO"

    # Timeouts (secondes)
    HTTP_TIMEOUT: int = 30
    DB_CONNECT_TIMEOUT: int = 10

    # Chemins
    CONFIG_FILE: str = "config.yaml"
    LOG_FILE: str = "app.log"


# ── Autres constantes métier ──────────────────────────────────────────────────

class Limits:
    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_SECONDS: float = 1.5


class HttpStatus:
    """Codes HTTP utilisés dans les réponses — évite les magic numbers."""
    OK: int = 200
    CREATED: int = 201
    BAD_REQUEST: int = 400
    UNAUTHORIZED: int = 401
    NOT_FOUND: int = 404
    CONFLICT: int = 409
    INTERNAL_ERROR: int = 500
```

---

## 3. Gestion des erreurs applicatives

### Hiérarchie d'exceptions — dans `domain/exceptions.py`

```python
# domain/exceptions.py
from __future__ import annotations
from my_package.constants import ErrorCode, ERROR_CATALOG


class AppError(Exception):
    """Exception de base du package.

    Toute exception applicative hérite de cette classe.
    Expose un code (ErrorCode) et un libellé (depuis ERROR_CATALOG).
    """

    def __init__(
        self,
        code: ErrorCode,
        *,
        detail: str | None = None,
        **format_kwargs,
    ) -> None:
        self.code = code
        template = ERROR_CATALOG[code]
        # Interpolation des placeholders optionnels ({key}, {path}…)
        self.message = template.format(**format_kwargs) if format_kwargs else template
        if detail:
            self.message = f"{self.message} {detail}"
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code!r}, message={self.message!r})"


# ── Exceptions par domaine ────────────────────────────────────────────────────

class UserError(AppError):
    """Erreurs liées aux utilisateurs."""

class AuthError(AppError):
    """Erreurs d'authentification."""

class ConfigError(AppError):
    """Erreurs de configuration."""

class IOError(AppError):  # noqa: A001
    """Erreurs d'entrées/sorties."""

class ExternalServiceError(AppError):
    """Erreurs de services externes."""
```

### Utilisation dans le code métier

```python
# application/services.py
from my_package.constants import ErrorCode
from my_package.domain.exceptions import UserError, ExternalServiceError
import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def get_user(self, user_id: int) -> User:
        user = self._repo.get(user_id)
        if user is None:
            # ✅ Code depuis constants, libellé depuis ERROR_CATALOG
            raise UserError(ErrorCode.USER_NOT_FOUND)
        return user

    def create_user(self, email: str) -> User:
        if self._repo.exists_by_email(email):
            raise UserError(ErrorCode.USER_ALREADY_EXISTS)
        # ...

    def fetch_from_api(self, resource_id: str) -> dict:
        try:
            return self._http_client.get(resource_id)
        except TimeoutError as exc:
            logger.warning("Timeout on resource %s: %s", resource_id, exc)
            # ✅ Jamais de message hardcodé
            raise ExternalServiceError(ErrorCode.EXTERNAL_TIMEOUT) from exc
```

### Sérialisation en réponse API

```python
# interface/api/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from my_package.domain.exceptions import AppError, AuthError, UserError
from my_package.constants import HttpStatus


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convertit une AppError en réponse JSON structurée."""
    status_map = {
        AuthError: HttpStatus.UNAUTHORIZED,
        UserError: HttpStatus.NOT_FOUND,
    }
    status_code = status_map.get(type(exc), HttpStatus.INTERNAL_ERROR)
    return JSONResponse(
        status_code=status_code,
        content={"error_code": exc.code, "message": exc.message},
    )
```

---

## 4. Configuration sans hardcoding

### Fichier de configuration — `config.yaml` ou `config.json`

```yaml
# config.yaml — distribué avec le projet, jamais de secrets ici
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

logging:
  level: "INFO"
  file: "app.log"

database:
  url: "${DATABASE_URL}"   # variable d'environnement pour les secrets
  pool_size: 10
  connect_timeout: 10

http_client:
  timeout: 30
  max_retries: 3
```

```json
// config.json — alternative JSON
{
  "server": { "host": "0.0.0.0", "port": 8000, "workers": 4 },
  "logging": { "level": "INFO", "file": "app.log" },
  "database": { "url": "${DATABASE_URL}", "pool_size": 10 },
  "http_client": { "timeout": 30, "max_retries": 3 }
}
```

### `config.py` — Chargement avec précédence

```python
# config.py
"""
Gestion de la configuration de l'application.

Précédence (du plus prioritaire au moins prioritaire) :
  1. Paramètres CLI passés explicitement
  2. Fichier de configuration (JSON ou YAML)
  3. Variables d'environnement
  4. Valeurs par défaut (constants.Defaults)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # pyyaml

from my_package.constants import Defaults, ErrorCode
from my_package.domain.exceptions import ConfigError

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    host: str = Defaults.HOST
    port: int = Defaults.PORT
    workers: int = Defaults.WORKERS


@dataclass
class LoggingConfig:
    level: str = Defaults.LOG_LEVEL
    file: str = Defaults.LOG_FILE


@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    http_timeout: int = Defaults.HTTP_TIMEOUT

    @classmethod
    def from_file(cls, path: Path) -> "AppConfig":
        """Charger la config depuis un fichier JSON ou YAML."""
        if not path.exists():
            raise ConfigError(ErrorCode.CONFIG_FILE_NOT_FOUND, path=str(path))

        raw = _load_file(path)
        return cls._from_dict(raw)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        srv = data.get("server", {})
        log = data.get("logging", {})
        return cls(
            server=ServerConfig(
                host=srv.get("host", Defaults.HOST),
                port=srv.get("port", Defaults.PORT),
                workers=srv.get("workers", Defaults.WORKERS),
            ),
            logging=LoggingConfig(
                level=log.get("level", Defaults.LOG_LEVEL),
                file=log.get("file", Defaults.LOG_FILE),
            ),
            http_timeout=data.get("http_client", {}).get("timeout", Defaults.HTTP_TIMEOUT),
        )


def _load_file(path: Path) -> dict[str, Any]:
    """Charger JSON ou YAML selon l'extension."""
    try:
        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(content) or {}
        return json.loads(content)
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ConfigError(ErrorCode.IO_READ_FAILED, path=str(path)) from exc


def _expand_env_vars(value: str) -> str:
    """Résoudre les variables d'environnement de style ${VAR}."""
    import re
    return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), m.group(0)), value)
```

---

## 5. Précédence : CLI > JSON params (defaults)

**Mécanisme :** `params.json` définit les paramètres CLI ET leurs valeurs par défaut.
argparse est construit dynamiquement depuis ce fichier via `ArgParser`.
Quand l'utilisateur passe un argument CLI, argparse écrase naturellement le default du JSON.
Il n'y a pas de phase de "merge" manuelle — la précédence est native à argparse.

```
params.json (default=100)    →  ArgParser  →  argparse default=100
                                                     ↑
CLI : --batch-size 500       →  argparse parse  →  args.batch_size = 500  ✅ précédence
CLI : (absent)               →  argparse parse  →  args.batch_size = 100  (default JSON)
```

### Point d'entrée CLI — avec ArgParser piloté par JSON

```python
# interface/cli/main.py
"""Point d'entrée CLI — applique la précédence de configuration."""
from __future__ import annotations

import logging
import sys

from my_package.cli.arg_parser import ArgParser
from my_package.constants import PARAMS_SCHEMA_FILE

logger = logging.getLogger(__name__)


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )


def main() -> int:
    # ── 1. Parser les arguments (CLI > defaults du JSON) ─────────────────────
    #    La précédence est native : argparse injecte le default depuis le JSON,
    #    et l'écrase si l'argument est fourni en CLI.
    arg_parser = ArgParser(PARAMS_SCHEMA_FILE)
    args = arg_parser.parse()

    # ── 2. Configurer le logging avec la valeur résolue ──────────────────────
    setup_logging(args.log_level)

    logger.info("Démarrage — input=%s batch_size=%d dry_run=%s",
                args.input, args.batch_size, args.dry_run)

    # ── 3. Logique applicative ────────────────────────────────────────────────
    if args.dry_run:
        logger.info("[DRY RUN] Aucune écriture effectuée.")
        return 0

    return _run(args)


def _run(args) -> int:
    """Orchestrer le traitement avec les arguments résolus."""
    # Transmettre aux services applicatifs via la couche application
    ...
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Voir `references/scripts.md`** pour le code complet de `ArgParser`, le format JSON des paramètres, et des exemples de chaque type d'argument.

---

## 6. Exemple de structure complète

```
src/my_package/
├── __init__.py
├── constants.py               # ErrorCode, ERROR_CATALOG, Defaults, PARAMS_SCHEMA_FILE
├── config.py                  # AppConfig (pour la config applicative non-CLI)
├── config/
│   ├── params.json            # source de vérité : params CLI + defaults
│   └── params_export.json     # params d'un second script (si plusieurs scripts)
│
├── domain/
│   ├── entities.py            # class User(BaseModel): ...
│   ├── repositories.py        # class UserRepository(Protocol): ...
│   └── exceptions.py          # class UserError(AppError): ...
│
├── application/
│   └── services.py            # class UserService: (utilise repo + constants)
│
├── infrastructure/
│   └── persistence/
│       └── sql_user_repo.py   # class SQLUserRepository(UserRepository):
│
└── interface/
    ├── cli/
    │   ├── arg_parser.py      # ArgParser — construit argparse depuis JSON
    │   └── main.py            # point d'entrée : parse → logique → exit code
    └── api/
        ├── main.py
        ├── routers/
        └── error_handlers.py  # mapping AppError → JSONResponse

.env                           # secrets locaux, jamais commités
```

---

## Liens officiels

- Clean Architecture (Robert C. Martin) : https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Argparse : https://docs.python.org/3/library/argparse.html
- JSON (stdlib) : https://docs.python.org/3/library/json.html
- PyYAML : https://pyyaml.org/wiki/PyYAMLDocumentation
- Pydantic Settings : https://docs.pydantic.dev/latest/concepts/pydantic_settings/
