# Persistance — DynamoDB et S3 avec ASK SDK Python

## Quand utiliser quoi ?

| Solution | Quand l'utiliser | Limites |
|---|---|---|
| **Session attributes** | Données temporaires dans une session | Perdues à la fermeture |
| **DynamoDB** | Profil utilisateur, scores, préférences | Coût par requête |
| **S3** | Données volumineuses, fichiers, logs | Latence légèrement plus élevée |

---

## DynamoDB — Configuration

### Installation

```bash
pip install ask-sdk-dynamodb-persistence-adapter boto3
```

### Setup dans lambda_function.py

```python
import boto3
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_core.skill_builder import CustomSkillBuilder

# Option 1 : laisser le SDK créer la table automatiquement
dynamo_client = boto3.resource("dynamodb", region_name="eu-west-1")

db_adapter = DynamoDbAdapter(
    table_name="mon-skill-users",
    create_table=True,          # crée la table si inexistante
    dynamodb_resource=dynamo_client
)

sb = CustomSkillBuilder(persistence_adapter=db_adapter)
```

### IAM Policy Lambda requise

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:CreateTable"
      ],
      "Resource": "arn:aws:dynamodb:eu-west-1:*:table/mon-skill-users"
    }
  ]
}
```

### Lecture / Écriture en Python

```python
class MonIntentHandler(AbstractRequestHandler):
    def handle(self, handler_input):
        attrs_manager = handler_input.attributes_manager

        # Lecture — charge depuis DynamoDB (lazy, une seule fois par session)
        persistent = attrs_manager.persistent_attributes
        parties_jouees = persistent.get("parties_jouees", 0)
        meilleur_score = persistent.get("meilleur_score", 0)

        # ... logique du skill ...
        nouveau_score = 150

        # Mise à jour
        persistent["parties_jouees"] = parties_jouees + 1
        if nouveau_score > meilleur_score:
            persistent["meilleur_score"] = nouveau_score

        # Sauvegarde — écrit dans DynamoDB
        attrs_manager.save_persistent_attributes()

        speak = f"Votre meilleur score est {persistent['meilleur_score']} !"
        return handler_input.response_builder.speak(speak).response
```

### Structure d'un enregistrement DynamoDB

```json
{
  "id": "amzn1.ask.account.ABCDEFG...",   // userId Alexa (partition key)
  "attributes": {
    "parties_jouees": 5,
    "meilleur_score": 200,
    "preferences": {
      "langue": "fr",
      "difficulte": "moyen"
    }
  }
}
```

### Ajouter un TTL (expiration automatique)

```python
# Dans la configuration de la table DynamoDB
# Activer "TTL" sur l'attribut "expireAt" dans la console AWS

from datetime import datetime, timedelta
import time

def set_ttl(persistent_attrs: dict, days: int = 90):
    """Fait expirer les données après N jours d'inactivité."""
    expire_at = int((datetime.now() + timedelta(days=days)).timestamp())
    persistent_attrs["expireAt"] = expire_at
```

---

## S3 — Configuration

### Installation

```bash
pip install ask-sdk-s3-adapter boto3
```

### Setup dans lambda_function.py

```python
from ask_sdk_s3.adapter import S3Adapter

s3_adapter = S3Adapter(
    bucket_name="mon-skill-bucket",
    path_prefix="user-data/"    # optionnel, préfixe pour les clés S3
)

sb = CustomSkillBuilder(persistence_adapter=s3_adapter)
```

### IAM Policy Lambda pour S3

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::mon-skill-bucket/*"
    }
  ]
}
```

### Usage S3 (identique à DynamoDB côté code !)

```python
# L'API est identique — le SDK abstrait DynamoDB et S3
persistent = attrs_manager.persistent_attributes
persistent["donnees_volumineuses"] = {...}
attrs_manager.save_persistent_attributes()
```

> 💡 **Astuce :** S3 stocke les attributs en JSON dans un fichier par userId.
> Pratique pour déboguer : tu peux lire/modifier directement les fichiers S3.

---

## Combiner session et persistance

```python
class QuizHandler(AbstractRequestHandler):
    def handle(self, handler_input):
        attrs_manager = handler_input.attributes_manager

        # Session : état courant de la partie (temporaire)
        session = attrs_manager.session_attributes
        question_actuelle = session.get("question_idx", 0)
        score_partie = session.get("score", 0)

        # Persistant : historique toutes parties (permanent)
        persistent = attrs_manager.persistent_attributes
        total_parties = persistent.get("total_parties", 0)

        # Nouvelle question
        session["question_idx"] = question_actuelle + 1
        session["score"] = score_partie + 10

        # Fin de partie → persister
        if question_actuelle >= 9:
            persistent["total_parties"] = total_parties + 1
            persistent["dernier_score"] = session["score"]
            attrs_manager.save_persistent_attributes()
            speak = f"Fin du quiz ! Score : {session['score']}/100"
        else:
            speak = f"Question {question_actuelle + 1} : ..."

        return handler_input.response_builder.speak(speak).ask("...").response
```

---

## Réinitialisation des données utilisateur

```python
class ResetDataHandler(AbstractRequestHandler):
    def can_handle(self, handler_input) -> bool:
        return is_intent_name("ResetDataIntent")(handler_input)

    def handle(self, handler_input):
        attrs_manager = handler_input.attributes_manager
        attrs_manager.delete_persistent_attributes()  # supprime de DynamoDB/S3
        attrs_manager.session_attributes.clear()

        return (
            handler_input.response_builder
            .speak("Vos données ont été effacées.")
            .response
        )
```
