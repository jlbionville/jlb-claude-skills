---
name: alexa-skill-python
description: >
  Guide complet pour développer des Skills Alexa en Python avec l'ASK SDK officiel d'Amazon.
  Utilise ce skill dès que l'utilisateur veut créer, modifier, déboguer ou déployer un skill Alexa
  en Python — qu'il s'agisse d'un Custom Skill (intents/utterances), d'un Smart Home Skill
  (contrôle d'appareils connectés), ou des deux. Déclencher aussi pour : "comment créer un handler
  Alexa", "je veux que mon skill Alexa gère les slots", "comment déployer mon skill sur Lambda",
  "comment tester mon skill Alexa en Python", "account linking Alexa", "DynamoDB avec ASK SDK",
  "ASK CLI deploy", "smart home discovery", ou tout code Python lié à ask-sdk-core / ask-sdk-s3-adapter /
  ask-sdk-dynamodb-persistence-adapter. Couvre le workflow complet : setup → développement →
  persistance → déploiement Lambda + ASK CLI → tests (pytest, ask-sdk-test, mocking).
---

# Alexa Skill Python — Guide Complet (ASK SDK)

## Vue d'ensemble

Ce skill couvre deux types de développement Alexa en Python :

| Type | Cas d'usage | Invocation |
|---|---|---|
| **Custom Skill** | Chatbot vocal, quiz, utilitaire | *"Alexa, ouvre Mon Skill"* |
| **Smart Home Skill** | Contrôle d'appareils IoT | *"Alexa, allume la lumière"* |

**Stack cible :** ASK SDK Python · AWS Lambda · ASK CLI · DynamoDB / S3 · pytest

---

## 1. Setup du projet

### Prérequis

```bash
pip install ask-sdk-core ask-sdk-model
pip install ask-sdk-dynamodb-persistence-adapter  # persistance DynamoDB
pip install ask-sdk-s3-adapter                    # persistance S3
pip install boto3                                  # AWS SDK

# ASK CLI (Node.js requis)
npm install -g ask-cli
ask configure   # configure les credentials AWS + Amazon Developer
```

### Structure recommandée

```
my-alexa-skill/
├── lambda/
│   ├── lambda_function.py      # point d'entrée Lambda
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── custom_handlers.py  # LaunchRequest, Intents
│   │   └── smarthome_handlers.py
│   ├── utils/
│   │   ├── persistence.py      # DynamoDB / S3 helpers
│   │   └── response_builder.py
│   └── requirements.txt
├── skill-package/
│   ├── skill.json              # metadata du skill
│   └── interactionModels/
│       └── custom/
│           └── fr-FR.json      # modèle d'interaction
└── ask-resources.json          # config ASK CLI
```

### Initialisation avec ASK CLI

```bash
ask new --skill-name "mon-skill" --locale fr-FR
cd mon-skill
ask deploy   # déploie Lambda + configure le skill dans la console Alexa
```

---

## 2. Architecture commune ASK SDK

### SkillBuilder et point d'entrée Lambda

```python
# lambda/lambda_function.py
import logging
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb_persistence_adapter import DynamoDbPersistenceAdapter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Persistence DynamoDB
persistence_adapter = DynamoDbPersistenceAdapter(
    table_name="mon-skill-table",
    create_table=True  # crée la table si elle n'existe pas
)

sb = CustomSkillBuilder(persistence_adapter=persistence_adapter)

# Enregistrement des handlers (voir sections suivantes)
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(MonIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
sb.add_global_request_interceptor(LoggingRequestInterceptor())

lambda_handler = sb.lambda_handler()
```

### Interceptors (logging, i18n)

```python
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor

class LoggingRequestInterceptor(AbstractRequestInterceptor):
    def process(self, handler_input):
        logger.info(f"Request: {handler_input.request_envelope.request.object_type}")
```

---

## 3. Custom Skill — Handlers et Intents

→ **Lire `references/custom-skill-patterns.md`** pour :
- `LaunchRequestHandler`, `IntentRequestHandler`, `SessionEndedRequestHandler`
- Gestion des slots (natifs AMAZON.* et custom)
- Dialog Management multi-tours
- Session attributes vs persistance DynamoDB
- SSML (voix, pauses, sons)
- Boilerplate complet prêt à l'emploi

---

## 4. Smart Home Skill — Directives et Discovery

→ **Lire `references/smart-home-patterns.md`** pour :
- Architecture spécifique (pas de `speak()`, directives structurées)
- `Alexa.Discovery` — inventorier les appareils
- Interfaces de contrôle (`PowerController`, `BrightnessController`, etc.)
- Account Linking obligatoire (OAuth2)
- Format des réponses Smart Home
- Boilerplate complet prêt à l'emploi

---

## 5. Persistance — DynamoDB et S3

→ **Lire `references/persistence-patterns.md`** pour :
- Configuration DynamoDB (table, partition key, TTL)
- Configuration S3 (bucket, prefix)
- Patterns de lecture/écriture avec `get_persistent_attributes` / `save_persistent_attributes`
- Quand utiliser DynamoDB vs S3 vs session attributes

---

## 6. Déploiement — Lambda + ASK CLI

→ **Lire `references/deployment-testing.md`** pour :
- Configuration `ask-resources.json` et `skill.json`
- Workflow `ask deploy` complet
- Gestion des environnements (dev/prod)
- IAM roles et permissions Lambda
- Layers Lambda pour les dépendances Python
- Logs CloudWatch pour le débogage

---

## 7. Tests

→ **Lire `references/deployment-testing.md`** (section Tests) pour :
- Unit tests avec `pytest` + fixtures de requêtes Alexa
- `ask-sdk-test` framework — simuler des conversations complètes
- Mocking des requêtes Alexa (JSON brut)
- Alexa Simulator dans la console Developer
- Exemples de `conftest.py` prêt à l'emploi

---

## Checklist de démarrage rapide

```
[ ] ask configure  (credentials Amazon + AWS)
[ ] Créer le DynamoDB table (ou laisser create_table=True)
[ ] Définir les intents dans fr-FR.json (Custom) ou endpoints (Smart Home)
[ ] Implémenter les handlers Python
[ ] ask deploy
[ ] Tester dans le simulateur Alexa
[ ] pytest sur les handlers critiques
```

## Pièges courants à éviter

| Problème | Cause fréquente | Solution |
|---|---|---|
| `SkillId mismatch` | skill.json mal configuré | Vérifier `apis.custom.endpoint` |
| Timeout Lambda | Dépendances trop lourdes | Utiliser Lambda Layers |
| `No response` Smart Home | Mauvais namespace de directive | Vérifier `header.namespace` |
| Session perdue | Mauvais usage attributes | Utiliser `persistent_attributes` |
| Account linking échoue | OAuth2 mal configuré | Vérifier redirect URIs dans la console |
