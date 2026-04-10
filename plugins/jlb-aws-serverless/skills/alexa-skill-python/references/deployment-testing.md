# Déploiement (Lambda + ASK CLI) et Tests

## Déploiement — ASK CLI + Lambda

### ask-resources.json (racine du projet)

```json
{
  "askcliResourcesVersion": "2020-03-31",
  "profiles": {
    "default": {
      "skillMetadata": {
        "src": "./skill-package"
      },
      "code": {
        "default": {
          "src": "./lambda",
          "buildFlow": "python-pip"
        }
      },
      "skillInfrastructure": {
        "userConfig": {
          "runtime": "python3.11",
          "handler": "lambda_function.lambda_handler",
          "templatePath": "./infrastructure/cfn-deployer/skill-stack.yaml"
        },
        "type": "@ask-cli/cfn-deployer"
      }
    }
  }
}
```

### skill.json (skill-package/)

```json
{
  "manifest": {
    "publishingInformation": {
      "locales": {
        "fr-FR": {
          "name": "Mon Skill",
          "summary": "Description courte",
          "description": "Description longue"
        }
      }
    },
    "apis": {
      "custom": {
        "endpoint": {
          "sourceDir": "lambda"
        }
      }
    },
    "manifestVersion": "1.0"
  }
}
```

### requirements.txt (lambda/)

```
ask-sdk-core>=1.19.0
ask-sdk-model>=1.89.0
ask-sdk-dynamodb-persistence-adapter>=1.19.0
ask-sdk-s3-adapter>=1.19.0
boto3>=1.26.0
```

### Workflow de déploiement complet

```bash
# 1. Premier déploiement
ask deploy

# 2. Déploiement partiel (code uniquement, plus rapide)
ask deploy --target lambda

# 3. Déploiement du modèle d'interaction uniquement
ask deploy --target skill-metadata

# 4. Voir les logs Lambda en temps réel
ask util generate-lwa-tokens  # refresh credentials si besoin
aws logs tail /aws/lambda/ask-mon-skill --follow --region eu-west-1

# 5. Simuler une requête depuis la CLI
ask dialog --locale fr-FR
```

### Lambda Layers (dépendances volumineuses)

```bash
# Créer un layer pour les dépendances Python
mkdir -p python/lib/python3.11/site-packages
pip install ask-sdk-core -t python/lib/python3.11/site-packages/
zip -r layer.zip python/
aws lambda publish-layer-version \
  --layer-name alexa-sdk-layer \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

### Environnements dev/prod

```bash
# Utiliser des profils ASK CLI séparés
ask configure --profile prod
ask deploy --profile prod

# Variables d'environnement Lambda par environnement
# Dans cfn-deployer/skill-stack.yaml :
# Environment:
#   Variables:
#     ENV: !Ref DeploymentStage
#     TABLE_NAME: !Sub "mon-skill-${DeploymentStage}"
```

---

## Tests — 4 niveaux

### Niveau 1 : Unit Tests avec pytest

```bash
pip install pytest pytest-mock
```

```python
# tests/test_handlers.py
import pytest
from unittest.mock import MagicMock, patch
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import RequestEnvelope, Session, User

from handlers.custom_handlers import LaunchRequestHandler, MonIntentHandler


def make_handler_input(request_type="LaunchRequest", intent_name=None, slots=None):
    """Factory pour créer un HandlerInput mocké."""
    mock_input = MagicMock(spec=HandlerInput)

    # Request envelope
    request = MagicMock()
    request.object_type = request_type
    if intent_name:
        request.intent = MagicMock()
        request.intent.name = intent_name
        request.intent.slots = slots or {}

    mock_input.request_envelope = MagicMock(spec=RequestEnvelope)
    mock_input.request_envelope.request = request
    mock_input.request_envelope.session = MagicMock(spec=Session)
    mock_input.request_envelope.session.user = MagicMock(spec=User)
    mock_input.request_envelope.session.user.user_id = "test-user-123"

    # Attributes manager mocké
    mock_input.attributes_manager = MagicMock()
    mock_input.attributes_manager.session_attributes = {}
    mock_input.attributes_manager.persistent_attributes = {}

    # Response builder réel (pas mocké pour tester la réponse)
    from ask_sdk_core.response_helper import ResponseFactory
    mock_input.response_builder = ResponseFactory()

    return mock_input


class TestLaunchRequestHandler:
    def setup_method(self):
        self.handler = LaunchRequestHandler()

    def test_can_handle_launch_request(self):
        hi = make_handler_input("LaunchRequest")
        assert self.handler.can_handle(hi) is True

    def test_cannot_handle_other_request(self):
        hi = make_handler_input("IntentRequest")
        assert self.handler.can_handle(hi) is False

    def test_handle_returns_response_with_speak(self):
        hi = make_handler_input("LaunchRequest")
        response = self.handler.handle(hi)
        assert response.output_speech is not None
        assert response.reprompt is not None  # session reste ouverte


class TestMonIntentHandler:
    def setup_method(self):
        self.handler = MonIntentHandler()

    def test_handle_with_slot(self):
        slot_mock = MagicMock()
        slot_mock.value = "Paris"
        hi = make_handler_input(
            "IntentRequest",
            intent_name="MonIntent",
            slots={"monSlot": slot_mock}
        )
        response = self.handler.handle(hi)
        assert "Paris" in response.output_speech.ssml
```

```bash
# Lancer les tests
pytest tests/ -v --tb=short

# Avec coverage
pytest tests/ --cov=lambda --cov-report=term-missing
```

---

### Niveau 2 : ask-sdk-test (conversations complètes)

```bash
pip install ask-sdk-test
```

```python
# tests/test_skill_flow.py
from ask_sdk_test import SkillTestingFramework, AlexaClient, SkillInvoker
from lambda_function import sb  # ton SkillBuilder

class TestSkillConversation:
    def setup_method(self):
        self.skill_invoker = SkillInvoker(sb.create())
        self.alexa_client = AlexaClient(skill_invoker=self.skill_invoker)

    def test_launch_and_intent_flow(self):
        """Test d'une conversation complète."""
        # 1. Lancement
        response = self.alexa_client.launch()
        assert response.response.output_speech is not None

        # 2. Intent
        response = self.alexa_client.intent("MonIntent", {"monSlot": "Paris"})
        assert "Paris" in response.response.output_speech.ssml

        # 3. Session toujours ouverte
        assert response.response.should_end_session is False

    def test_session_ends_on_stop(self):
        self.alexa_client.launch()
        response = self.alexa_client.intent("AMAZON.StopIntent")
        assert response.response.should_end_session is True
```

---

### Niveau 3 : Mocking de requêtes JSON brutes

```python
# tests/test_raw_requests.py
import json
import pytest
from lambda_function import lambda_handler

LAUNCH_REQUEST = {
    "version": "1.0",
    "session": {
        "new": True,
        "sessionId": "amzn1.echo-api.session.test",
        "application": {"applicationId": "amzn1.ask.skill.test"},
        "user": {"userId": "amzn1.ask.account.test"}
    },
    "request": {
        "type": "LaunchRequest",
        "requestId": "amzn1.echo-api.request.test",
        "timestamp": "2024-01-01T00:00:00Z",
        "locale": "fr-FR"
    }
}

INTENT_REQUEST = {
    "version": "1.0",
    "session": {
        "new": False,
        "sessionId": "amzn1.echo-api.session.test",
        "application": {"applicationId": "amzn1.ask.skill.test"},
        "user": {"userId": "amzn1.ask.account.test"}
    },
    "request": {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.test2",
        "timestamp": "2024-01-01T00:00:01Z",
        "locale": "fr-FR",
        "intent": {
            "name": "MonIntent",
            "confirmationStatus": "NONE",
            "slots": {
                "monSlot": {
                    "name": "monSlot",
                    "value": "Paris",
                    "confirmationStatus": "NONE"
                }
            }
        }
    }
}

def test_launch_request():
    """Test du handler avec une requête JSON brute."""
    context = MagicMock()
    response = lambda_handler(LAUNCH_REQUEST, context)
    assert "outputSpeech" in response["response"]
    assert response["response"]["shouldEndSession"] is False

def test_intent_request_with_slot():
    context = MagicMock()
    response = lambda_handler(INTENT_REQUEST, context)
    speech = response["response"]["outputSpeech"]["ssml"]
    assert "Paris" in speech
```

---

### Niveau 4 : Alexa Simulator (console Developer)

```bash
# Via ASK CLI — simuler un échange vocal
ask dialog --locale fr-FR

# Commandes dans le simulateur interactif :
# > ouvre mon skill         (LaunchRequest)
# > dis moi Paris           (MonIntent avec slot)
# > stop                    (AMAZON.StopIntent)
# > .quit                   (quitter le simulateur)

# Tester une utterance spécifique directement
ask smapi simulate-skill \
  --skill-id amzn1.ask.skill.XXXX \
  --stage development \
  --input-content "ouvre mon skill" \
  --device-locale fr-FR
```

---

## Débogage CloudWatch

```python
# Dans chaque handler — logs structurés
import json

def log_request(handler_input):
    """Log la requête entrante pour debug."""
    request = handler_input.request_envelope.request
    logger.info(json.dumps({
        "type": request.object_type,
        "intent": getattr(request, "intent", {}).name if hasattr(request, "intent") else None,
        "session_id": handler_input.request_envelope.session.session_id if handler_input.request_envelope.session else None
    }))
```

```bash
# Voir les logs en temps réel
aws logs tail /aws/lambda/ask-mon-skill \
  --follow \
  --format short \
  --filter-pattern "ERROR"
```
