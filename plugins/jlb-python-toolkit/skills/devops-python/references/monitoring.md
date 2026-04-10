# Référence Monitoring / Logging

---

## Logging structuré (JSON) pour la prod

```python
import logging
import json
import sys

class JSONFormatter(logging.Formatter):
    """Formatter qui produit des logs JSON — idéal pour CloudWatch, ELK, Datadog."""
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
            "module":    record.module,
            **({"exc_info": self.formatException(record.exc_info)} if record.exc_info else {}),
        })

def setup_logging(level: str = "INFO", json_output: bool = False) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter() if json_output else logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    ))
    logging.basicConfig(level=level, handlers=[handler])
```

Alternative : `structlog` — plus puissant, pipeline de processeurs configurables.
Doc : https://www.structlog.org/en/stable/

---

## Métriques avec Prometheus

```python
from prometheus_client import Counter, Histogram, start_http_server
import time

# Déclarer les métriques en haut du module
REQUESTS_TOTAL = Counter(
    "script_requests_total",
    "Nombre total de requêtes traitées",
    ["status"],  # labels
)
PROCESSING_TIME = Histogram(
    "script_processing_seconds",
    "Temps de traitement",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0],
)

# Exposition sur un port HTTP pour Prometheus scraping
start_http_server(8000)

# Usage dans la logique
with PROCESSING_TIME.time():
    result = process_item()
    REQUESTS_TOTAL.labels(status="success" if result else "error").inc()
```

Doc : https://prometheus.github.io/client_python/

---

## Alertes avec seuils

```python
def check_threshold(metric_name: str, value: float, threshold: float,
                    alert_fn: callable) -> bool:
    """Déclenche une alerte si value dépasse threshold."""
    if value > threshold:
        msg = f"⚠️ {metric_name} = {value:.2f} (seuil : {threshold})"
        logger.warning(msg)
        alert_fn(msg)
        return True
    return False

# Usage
cpu_pct = get_cpu_percent()
check_threshold("CPU", cpu_pct, threshold=80.0, alert_fn=notify_slack)
```

---

## Health check HTTP simple

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *args): pass  # Silence les logs HTTP

def start_health_server(port: int = 8080) -> None:
    """Démarre un health check HTTP en thread daemon."""
    server = HTTPServer(("", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health check disponible sur :%d/health", port)
```

---

## Rotation des logs avec logging.handlers

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "/var/log/myapp/script.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,               # garder 5 fichiers
)
```

Doc logging : https://docs.python.org/3/library/logging.handlers.html
Doc CloudWatch agent : https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html
