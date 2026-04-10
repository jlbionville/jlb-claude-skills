# Smart Home Skill — Patterns Python (ASK SDK)

## Architecture spécifique Smart Home

> ⚠️ Les Smart Home Skills N'utilisent PAS `speak()` ni le CustomSkillBuilder standard.
> Elles reçoivent des **directives structurées** et renvoient des **réponses JSON structurées**.

```python
# lambda/lambda_function.py — Smart Home
import json
import logging

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """Point d'entrée — routage des directives Smart Home."""
    namespace = event["directive"]["header"]["namespace"]
    name = event["directive"]["header"]["name"]

    logger.info(f"Directive: {namespace}/{name}")

    if namespace == "Alexa.Discovery":
        return handle_discovery(event)
    elif namespace == "Alexa.PowerController":
        return handle_power(event, name)
    elif namespace == "Alexa.BrightnessController":
        return handle_brightness(event, name)
    else:
        return error_response(event, "INVALID_DIRECTIVE", f"Namespace inconnu: {namespace}")
```

---

## Alexa.Discovery — Inventorier les appareils

```python
def handle_discovery(event):
    """Retourne la liste des appareils supportés."""
    endpoints = [
        {
            "endpointId": "lumiere-salon-001",
            "friendlyName": "Lumière du salon",
            "description": "Ampoule connectée salon",
            "manufacturerName": "MonFabricant",
            "displayCategories": ["LIGHT"],
            "cookie": {},
            "capabilities": [
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa",
                    "version": "3"
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.PowerController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "powerState"}],
                        "retrievable": True,
                        "proactivelyReported": False
                    }
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa.BrightnessController",
                    "version": "3",
                    "properties": {
                        "supported": [{"name": "brightness"}],
                        "retrievable": True,
                        "proactivelyReported": False
                    }
                }
            ]
        }
    ]

    return {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover.Response",
                "payloadVersion": "3",
                "messageId": event["directive"]["header"]["messageId"]
            },
            "payload": {
                "endpoints": endpoints
            }
        }
    }
```

---

## Interfaces de contrôle courantes

### PowerController (allumer/éteindre)

```python
def handle_power(event, name):
    endpoint_id = event["directive"]["endpoint"]["endpointId"]
    correlation_token = event["directive"]["header"].get("correlationToken")

    # name = "TurnOn" ou "TurnOff"
    new_state = "ON" if name == "TurnOn" else "OFF"

    # ICI : appeler votre API IoT / MQTT / etc.
    set_device_power(endpoint_id, new_state)

    return alexa_response(
        endpoint_id=endpoint_id,
        correlation_token=correlation_token,
        properties=[{
            "namespace": "Alexa.PowerController",
            "name": "powerState",
            "value": new_state
        }]
    )
```

### BrightnessController (luminosité)

```python
def handle_brightness(event, name):
    endpoint_id = event["directive"]["endpoint"]["endpointId"]
    correlation_token = event["directive"]["header"].get("correlationToken")
    payload = event["directive"]["payload"]

    if name == "SetBrightness":
        brightness = payload["brightness"]  # 0-100
    elif name == "AdjustBrightness":
        delta = payload["brightnessDelta"]  # négatif ou positif
        current = get_device_brightness(endpoint_id)
        brightness = max(0, min(100, current + delta))

    set_device_brightness(endpoint_id, brightness)

    return alexa_response(
        endpoint_id=endpoint_id,
        correlation_token=correlation_token,
        properties=[{
            "namespace": "Alexa.BrightnessController",
            "name": "brightness",
            "value": brightness
        }]
    )
```

### Autres interfaces utiles

| Interface | Propriété | Directives |
|---|---|---|
| `Alexa.ColorController` | `color` (HSB) | `SetColor` |
| `Alexa.ThermostatController` | `targetSetpoint` | `SetTargetTemperature` |
| `Alexa.LockController` | `lockState` | `Lock`, `Unlock` |
| `Alexa.PercentageController` | `percentage` | `SetPercentage`, `AdjustPercentage` |
| `Alexa.SceneController` | — | `Activate`, `Deactivate` |

---

## Helper — Construire une réponse Alexa standard

```python
import uuid
from datetime import datetime, timezone

def alexa_response(endpoint_id: str, correlation_token: str, properties: list) -> dict:
    """Construit une réponse Alexa.Response standard."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    return {
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": str(uuid.uuid4()),
                "correlationToken": correlation_token
            },
            "endpoint": {
                "endpointId": endpoint_id
            },
            "payload": {}
        },
        "context": {
            "properties": [
                {
                    **prop,
                    "timeOfSample": now,
                    "uncertaintyInMilliseconds": 500
                }
                for prop in properties
            ]
        }
    }

def error_response(event, error_type: str, message: str) -> dict:
    """Retourne une réponse d'erreur Alexa."""
    return {
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "ErrorResponse",
                "payloadVersion": "3",
                "messageId": str(uuid.uuid4())
            },
            "endpoint": event["directive"].get("endpoint", {}),
            "payload": {
                "type": error_type,
                "message": message
            }
        }
    }
```

---

## Account Linking (OAuth2) — Configuration

> ⚠️ **Obligatoire** pour les Smart Home Skills.

### Dans la console Alexa Developer

1. **Build → Account Linking → Enable**
2. Remplir :
   - `Authorization URI` : `https://ton-serveur/oauth/authorize`
   - `Access Token URI` : `https://ton-serveur/oauth/token`
   - `Client ID` et `Client Secret`
   - `Scopes` : selon ton API
   - `Redirect URLs` à whitelist côté OAuth server (fournis par Amazon)

### Récupérer le token dans Lambda

```python
def get_access_token(event) -> str:
    """Extrait le token OAuth2 de la requête Alexa."""
    try:
        return event["directive"]["endpoint"]["scope"]["token"]
    except KeyError:
        # Pour Discovery, le token est dans payload
        return event["directive"]["payload"]["scope"]["token"]

# Usage dans un handler
def handle_power(event, name):
    token = get_access_token(event)
    # Utiliser le token pour appeler ton API backend
    response = call_my_api(token, endpoint_id, action=name)
```

---

## Pièges Smart Home spécifiques

| Problème | Cause | Solution |
|---|---|---|
| Discovery vide | `displayCategories` invalide | Utiliser les valeurs officielles Amazon |
| Directive ignorée | Mauvais `namespace` | Copier exactement depuis la doc |
| Token expiré | OAuth2 non rafraîchi | Implémenter refresh_token |
| Timeout | Backend IoT lent | Timeout Lambda ≤ 8s recommandé |
| Pas de retour d'état | `retrievable: false` | Passer à `true` + implémenter `Alexa.ReportState` |
