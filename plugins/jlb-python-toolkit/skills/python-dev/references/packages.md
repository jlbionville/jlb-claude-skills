# Référence : Packages & Librairies Python

## Structure d'un package moderne

```
my_package/
├── pyproject.toml          # ← tout est ici (PEP 517/518/621)
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .github/
│   └── workflows/
│       └── publish.yml     # CI/CD PyPI
├── src/
│   └── my_package/         # src layout (recommandé)
│       ├── __init__.py
│       ├── py.typed         # indique que le package est typé
│       ├── core.py
│       ├── exceptions.py
│       └── _internal/       # modules internes (convention _)
└── tests/
    ├── conftest.py
    └── test_core.py
```

**Pourquoi src layout ?** Évite d'importer accidentellement le code source au lieu du package installé. Force l'installation pour tester, ce qui détecte les problèmes de packaging tôt.

---

## pyproject.toml — Template complet

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
description = "Une description claire et concise"
readme = "README.md"
license = { file = "LICENSE" }
authors = [{ name = "Prénom Nom", email = "email@example.com" }]
requires-python = ">=3.11"
keywords = ["keyword1", "keyword2"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
]
docs = ["mkdocs-material>=9.0"]

[project.urls]
Homepage = "https://github.com/user/my-package"
Documentation = "https://my-package.readthedocs.io"
Changelog = "https://github.com/user/my-package/blob/main/CHANGELOG.md"

# Si le package expose une CLI
[project.scripts]
my-cli = "my_package.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]

# Ruff — linting + formatting
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ANN"]
ignore = ["ANN101", "ANN102"]

# Mypy — type checking
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true

# Pytest
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src/my_package --cov-report=term-missing"

[tool.coverage.report]
exclude_lines = ["if TYPE_CHECKING:", "raise NotImplementedError"]
```

---

## __init__.py — API publique claire

```python
"""
my_package — description courte.

Usage rapide:
    from my_package import Client
    client = Client(api_key="...")
    result = client.fetch("resource")
"""
from my_package.core import Client
from my_package.exceptions import MyPackageError, AuthError

__all__ = ["Client", "MyPackageError", "AuthError"]
__version__ = "0.1.0"
```

**Règles pour `__all__` :**
- Tout ce qui est dans `__all__` est public et soumis à la semver
- Ce qui n'y est pas est privé (peut changer sans breaking change)
- Préfixer avec `_` les modules/fonctions internes

---

## Gestion des exceptions

```python
# exceptions.py — hiérarchie claire
class MyPackageError(Exception):
    """Base exception for my_package."""

class AuthError(MyPackageError):
    """Authentication failed."""
    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code

class RateLimitError(MyPackageError):
    """API rate limit exceeded."""
    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Rate limited. Retry after {retry_after}s")
        self.retry_after = retry_after
```

**Règle :** Toujours définir une exception de base au niveau du package. Les utilisateurs peuvent alors faire `except MyPackageError` pour tout attraper.

---

## Versionning — Semantic Versioning

```
MAJOR.MINOR.PATCH
  │     │     └─ Bug fixes, pas de breaking change
  │     └─ Nouvelles fonctionnalités, rétrocompatible
  └─ Breaking changes de l'API publique
```

- `0.x.y` : API instable, breaking changes autorisés en MINOR
- `1.0.0` : API stable, respecter la semver strictement
- Utiliser `CHANGELOG.md` avec format [Keep a Changelog](https://keepachangelog.com/)

---

## Publish sur PyPI

### Manuel (une fois)
```bash
pip install build twine
python -m build                          # crée dist/
twine check dist/*                       # vérifie le package
twine upload --repository testpypi dist/*  # test sur TestPyPI d'abord
twine upload dist/*                      # prod PyPI
```

### Automatisé (GitHub Actions)
```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  push:
    tags: ["v*"]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # OIDC — pas de token PyPI nécessaire
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install build && python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

**Utiliser Trusted Publishing** (OIDC) plutôt qu'un token PyPI — plus sécurisé, pas de secret à gérer.

---

## Liens officiels

- Python Packaging Guide : https://packaging.python.org/en/latest/
- Hatch : https://hatch.pypa.io/
- Ruff : https://docs.astral.sh/ruff/
- Mypy : https://mypy.readthedocs.io/
- Semantic Versioning : https://semver.org/
- Trusted Publishing PyPI : https://docs.pypi.org/trusted-publishers/
