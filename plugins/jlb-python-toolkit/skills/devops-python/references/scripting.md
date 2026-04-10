# Référence Scripting Python — Patterns génériques

---

## Retry avec back-off exponentiel

```python
import time
import functools
from typing import Callable, Type, Tuple

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Décorateur de retry avec back-off exponentiel."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            wait = delay
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt == max_attempts:
                        logger.error("Échec après %d tentatives : %s", max_attempts, e)
                        raise
                    logger.warning("Tentative %d/%d échouée, retry dans %.1fs : %s",
                                   attempt, max_attempts, wait, e)
                    time.sleep(wait)
                    wait *= backoff
        return wrapper
    return decorator

# Usage
@retry(max_attempts=3, delay=2.0, exceptions=(requests.RequestException,))
def call_api(url: str) -> dict:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

Alternative : `tenacity` — bibliothèque dédiée, plus expressive.
Doc : https://tenacity.readthedocs.io/

---

## Configuration externalisée

```python
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    """Configuration du script — priorité : env vars > defaults."""
    region:      str           = field(default_factory=lambda: os.getenv("AWS_REGION", "eu-west-1"))
    log_level:   str           = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    slack_hook:  Optional[str] = field(default_factory=lambda: os.getenv("SLACK_WEBHOOK"))
    dry_run:     bool          = False

# Ou via un fichier YAML avec PyYAML / tomllib (Python 3.11+)
import tomllib  # stdlib Python 3.11+

with open("config.toml", "rb") as f:
    raw = tomllib.load(f)
```

Doc tomllib : https://docs.python.org/3/library/tomllib.html

---

## Subprocess sécurisé

```python
import subprocess
import shlex

# ✅ Toujours passer une liste, jamais une string avec shell=True
result = subprocess.run(
    ["git", "log", "--oneline", "-10"],
    capture_output=True,
    text=True,
    timeout=30,
    check=True,   # lève CalledProcessError si exit code != 0
)
logger.debug("git log output:\n%s", result.stdout)

# ❌ Dangereux si user_input est contrôlable
# subprocess.run(f"git log {user_input}", shell=True)
```

Doc : https://docs.python.org/3/library/subprocess.html

---

## Context managers pour les ressources

```python
from contextlib import contextmanager

@contextmanager
def temp_directory():
    """Crée un répertoire temporaire et le nettoie à la sortie."""
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.debug("Répertoire temporaire nettoyé : %s", tmpdir)

# Usage
with temp_directory() as tmpdir:
    process_files(tmpdir)
# tmpdir supprimé automatiquement, même en cas d'exception
```

---

## Concurrence pour les tâches I/O-bound

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_items_parallel(items: list, max_workers: int = 10) -> list:
    """Traite une liste d'éléments en parallèle (I/O-bound)."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_item, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                logger.error("Erreur pour l'item %s : %s", item, e)
    return results
```

Pour les tâches CPU-bound : `ProcessPoolExecutor`.
Pour l'async I/O : `asyncio` + `aiohttp` / `aioboto3`.
Doc : https://docs.python.org/3/library/concurrent.futures.html

---

## Gestion des fichiers et paths

```python
from pathlib import Path

# ✅ Toujours utiliser pathlib, jamais os.path
input_dir  = Path(args.input_dir).resolve()
output_dir = Path(args.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)

for csv_file in input_dir.glob("**/*.csv"):
    output_file = output_dir / csv_file.relative_to(input_dir)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    process(csv_file, output_file)
```

Doc pathlib : https://docs.python.org/3/library/pathlib.html
