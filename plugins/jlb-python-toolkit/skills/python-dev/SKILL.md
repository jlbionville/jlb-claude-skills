---
name: python-dev
description: >
  Développement Python professionnel : web apps (Flask/FastAPI/Django), APIs REST, scripts CLI,
  packages PyPI. Clean architecture (domain/application/infrastructure/interface), design patterns
  (Repository, Factory, DI, Strategy), erreurs codifiées (code+libellé dans constants.py),
  zéro hardcoding (params CLI via argparse piloté par JSON, précédence CLI > fichier > défaut).
  Packages : argparse, logging, pydantic, pandas, httpx, pytest, rich.
  Déclencher pour : API REST, script Python, package Python, structurer projet Flask/FastAPI/Django,
  refactoriser code Python, design patterns, tests, gestion d'erreurs, clean architecture,
  publie package PyPI, revue de code Python. Complémentaire à devops-python (AWS/infra).
---

# Python Dev Skill

Skill pour développer du Python professionnel : web apps, APIs, scripts, packages.
Applique les design patterns, évite les anti-patterns, utilise l'écosystème communautaire.

---

## Principes fondamentaux (non négociables)

1. **Clean Architecture** — couches strictement séparées, dépendances vers l'intérieur
2. **Zéro hardcoding** — toute valeur configurable vit dans un fichier de config ou une constante
3. **Erreurs codifiées** — chaque erreur a un code et un libellé, définis dans `constants.py`
4. **Configuration avec précédence** — paramètres CLI > fichier de config > valeurs par défaut

Voir `references/clean-architecture.md` pour la structure complète des couches et exemples.

---

## Étape 0 — Collecte d'informations

Avant de générer, s'assurer d'avoir :

| Info | Exemples |
|------|---------|
| **Type de projet** | Web app, API REST, script CLI, package/lib |
| **Framework cible** | FastAPI, Flask, Django, aucun |
| **Objectif précis** | "CRUD utilisateurs", "parser des CSV", "wrapper d'API externe" |
| **Niveau** | Débutant / Intermédiaire / Senior |
| **Livrable** | Snippet inline, fichier `.py`, projet complet |

Si des infos manquent, poser **une seule question groupée**. Faire une hypothèse raisonnable et l'expliciter plutôt que de bloquer.

---

## Étape 1 — Identifier le domaine et charger la référence

Selon le domaine, lire le fichier de référence **avant** de générer :

| Domaine | Référence |
|---------|-----------|
| **Clean Architecture, erreurs, constantes, config** | `references/clean-architecture.md` ← **lire en premier** |
| Web Apps (Flask, FastAPI, Django) | `references/web.md` |
| Packages & librairies (PyPI, structuration) | `references/packages.md` |
| Scripts & CLI (argparse, typer, rich, config) | `references/scripts.md` |
| Data / Pandas / traitement de données | `references/data.md` |

**Toujours lire `clean-architecture.md` en premier**, puis la référence de domaine. Pour un projet full-stack, lire plusieurs références domaine.

---

## Étape 2 — Structure et conventions universelles

**Règles appliquées à tout code Python produit :**

### 2.1 Fondamentaux

```python
#!/usr/bin/env python3
"""
Courte description du module.

Ce module fait X en utilisant Y.
"""
from __future__ import annotations  # compatibilité type hints Python 3.9+

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)  # toujours __name__, jamais "root"
```

**Toujours :**
- `logger = logging.getLogger(__name__)` — jamais `logging.info()` directement
- Type hints sur toutes les fonctions publiques
- Docstrings Google style sur les classes et fonctions publiques
- `from __future__ import annotations` pour la compatibilité

**Jamais :**
- `print()` en production (remplacer par `logger.info()`)
- `except Exception: pass` (toujours logguer ou re-raise)
- Secrets hardcodés (utiliser `os.environ` ou `python-dotenv`)
- `import *` (imports explicites uniquement)

### 2.2 Gestion d'erreurs — Règle absolue

Chaque erreur applicative doit avoir un **code** et un **libellé** définis dans `constants.py`. Jamais de message d'erreur littéral en dur dans le code métier.

```python
# ✅ Bon — code + libellé centralisés
from mypackage.constants import ErrorCode
raise DomainError(ErrorCode.USER_NOT_FOUND)

# ❌ Mauvais — message hardcodé, non traçable
raise ValueError("User not found")
```

Voir `references/clean-architecture.md` → section "Erreurs codifiées" pour le pattern complet.

### 2.3 Configuration — Règle de précédence

```
Paramètres CLI  >  Fichier de config (JSON/YAML)  >  Valeurs par défaut
```

Jamais de valeur en dur dans le code. Toute valeur configurable passe par cette chaîne.

Voir `references/clean-architecture.md` → section "Configuration sans hardcoding" pour le pattern complet.


---

## Étape 3 — Design Patterns à appliquer

### Pattern : Repository (accès données)
Séparer la logique métier de l'accès aux données.

```python
# Abstraction
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def get(self, user_id: int) -> User | None: ...
    @abstractmethod
    def save(self, user: User) -> User: ...

# Implémentation concrète
class SQLUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def save(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user
```

**Quand l'utiliser :** Dès qu'on accède à une BDD, une API externe, ou des fichiers.

### Pattern : Dependency Injection
Passer les dépendances en paramètres plutôt que de les instancier en dur.

```python
# ✅ Bon — injectable, testable
class UserService:
    def __init__(self, repo: UserRepository, mailer: Mailer) -> None:
        self._repo = repo
        self._mailer = mailer

    def register(self, email: str) -> User:
        user = User(email=email)
        saved = self._repo.save(user)
        self._mailer.send_welcome(saved)
        return saved

# ❌ Mauvais — couplage fort, impossible à tester
class UserService:
    def register(self, email: str) -> User:
        repo = SQLUserRepository(get_db())  # instanciation cachée
        user = repo.save(User(email=email))
        SmtpMailer().send_welcome(user)     # dépendance cachée
        return user
```

### Pattern : Factory
Créer des objets sans exposer la logique de construction.

```python
from enum import StrEnum

class StorageBackend(StrEnum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"

def create_storage(backend: StorageBackend, **kwargs) -> Storage:
    match backend:
        case StorageBackend.LOCAL:
            return LocalStorage(kwargs["path"])
        case StorageBackend.S3:
            return S3Storage(kwargs["bucket"])
        case StorageBackend.GCS:
            return GCSStorage(kwargs["bucket"])
        case _:
            raise ValueError(f"Unknown backend: {backend}")
```

### Pattern : Strategy
Encapsuler des algorithmes interchangeables.

```python
from typing import Protocol

class ExportStrategy(Protocol):
    def export(self, data: list[dict]) -> bytes: ...

class CSVExporter:
    def export(self, data: list[dict]) -> bytes:
        import csv, io
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return buf.getvalue().encode()

class JSONExporter:
    def export(self, data: list[dict]) -> bytes:
        import json
        return json.dumps(data, ensure_ascii=False).encode()

class ReportGenerator:
    def __init__(self, strategy: ExportStrategy) -> None:
        self._strategy = strategy

    def generate(self, data: list[dict]) -> bytes:
        return self._strategy.export(data)
```

### Pattern : Observer / Event
Découpler les effets de bord de la logique métier.

```python
from collections import defaultdict
from collections.abc import Callable

class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        self._handlers[event].append(handler)

    def publish(self, event: str, **payload) -> None:
        for handler in self._handlers[event]:
            handler(**payload)

bus = EventBus()
bus.subscribe("user.registered", send_welcome_email)
bus.subscribe("user.registered", create_free_trial)
```

---

## Étape 4 — Anti-patterns à éliminer

| Anti-pattern | Problème | Solution |
|---|---|---|
| **God Object** | Classe qui fait tout | Décomposer en services spécialisés |
| **Mutable default args** | `def f(lst=[])` → partagé entre appels | `def f(lst=None): lst = lst or []` |
| **Catch-all silencieux** | `except: pass` | Exceptions spécifiques + logging |
| **Magic strings** | `status == "active"` partout | `class Status(StrEnum): ACTIVE = "active"` |
| **Couplage fort** | `UserService` crée `SmtpMailer()` | Injection de dépendances |
| **Logique dans `__init__`** | Appels réseau dans le constructeur | Factory ou `classmethod` de construction |
| **Mutation implicite** | Modifier un argument en place sans le signaler | Retourner une nouvelle valeur ou documenter |
| **Nombres magiques** | `time.sleep(86400)` | `SECONDS_PER_DAY = 86_400` |

---

## Étape 5 — Packages recommandés par domaine

### Universels
| Package | Usage | Alternative |
|---------|-------|-------------|
| `pydantic` | Validation de données, modèles | `attrs`, `dataclasses` |
| `python-dotenv` | Chargement `.env` | `pydantic-settings` (+ puissant) |
| `pytest` | Tests unitaires | `unittest` (stdlib) |
| `pytest-cov` | Couverture de tests | — |
| `ruff` | Linting + formatting | `flake8` + `black` |
| `mypy` | Type checking statique | `pyright` |
| `loguru` | Logging amélioré | `logging` (stdlib) |

### Web / API
| Package | Usage |
|---------|-------|
| `fastapi` | API REST moderne, async, OpenAPI auto |
| `flask` | Web app légère, grande communauté |
| `django` | Full-stack, ORM, admin intégré |
| `httpx` | Client HTTP async/sync (remplace `requests`) |
| `pydantic-settings` | Config via env vars pour APIs |
| `sqlalchemy` | ORM + query builder |
| `alembic` | Migrations de BDD |
| `celery` | Tâches asynchrones / queues |

### Data / Scripts
| Package | Usage |
|---------|-------|
| `pandas` | DataFrames, manipulation de données |
| `polars` | Pandas mais 10x plus rapide (recommandé pour gros volumes) |
| `typer` | CLI élégant basé sur type hints |
| `rich` | Output terminal coloré, tables, progress bars |
| `tqdm` | Barres de progression simples |
| `pathlib` | Manipulation de chemins (builtin, préféré à `os.path`) |

---

## Étape 6 — Tests

Tout code produit doit être accompagné de tests ou d'un plan de test :

```python
# Structure recommandée
tests/
├── conftest.py          # fixtures partagées
├── unit/
│   ├── test_services.py
│   └── test_models.py
└── integration/
    └── test_api.py

# conftest.py — fixtures de base
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_user_repo():
    return MagicMock(spec=UserRepository)

@pytest.fixture
def user_service(mock_user_repo, mock_mailer):
    return UserService(repo=mock_user_repo, mailer=mock_mailer)

# test_services.py — test unitaire
def test_register_user_sends_welcome_email(user_service, mock_mailer):
    user = user_service.register("alice@example.com")
    mock_mailer.send_welcome.assert_called_once_with(user)
```

**Règles :**
- Un test = un comportement (pas une méthode)
- Nommer : `test_<quoi>_<condition>_<résultat_attendu>`
- Mocker les dépendances externes (BDD, APIs, email)
- Coverage minimum recommandé : 80% sur la logique métier

---

## Étape 7 — Checklist avant livraison

**Clean Architecture**
- [ ] Couches respectées : domain / application / infrastructure / interface
- [ ] Dépendances vers l'intérieur uniquement (domain n'importe jamais infrastructure)
- [ ] Logique métier dans le domain, indépendante du framework

**Erreurs et constantes**
- [ ] Toutes les erreurs applicatives ont un code + libellé dans `constants.py`
- [ ] Aucun message d'erreur littéral hardcodé dans le code métier
- [ ] Valeurs "magiques" remplacées par des constantes nommées

**Configuration**
- [ ] Zéro valeur en dur dans le code (URL, chemins, seuils, timeouts…)
- [ ] Fichier de config JSON/YAML présent avec toutes les valeurs par défaut
- [ ] Paramètres CLI disponibles pour surcharger chaque valeur critique
- [ ] Précédence respectée : CLI > fichier de config > défaut

**Code**
- [ ] Type hints sur toutes les fonctions publiques
- [ ] Docstrings Google style sur classes et fonctions publiques
- [ ] `logger = logging.getLogger(__name__)` (pas de `print`)
- [ ] Exceptions spécifiques avec `raise X from exc`
- [ ] Design pattern approprié appliqué
- [ ] Anti-patterns absents
- [ ] Tests ou plan de test fourni
- [ ] Bloc "Pourquoi ces choix ?" avec alternatives

---

## Références

- `references/clean-architecture.md` — **Lire en premier** : couches clean archi, erreurs codifiées (code+libellé dans constants.py), configuration sans hardcoding avec précédence CLI > fichier > défaut
- `references/web.md` — FastAPI, Flask, Django : structure, auth, BDD, middleware
- `references/packages.md` — Structure package PyPI, pyproject.toml, publish, versioning
- `references/scripts.md` — **ArgParser piloté par JSON** (pattern principal), argparse, rich, Pathlib, subprocess
- `references/data.md` — Pandas, Polars, traitement CSV/JSON/Excel, pipelines de données
