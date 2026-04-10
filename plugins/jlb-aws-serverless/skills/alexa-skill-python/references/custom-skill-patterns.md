# Custom Skill — Patterns Python (ASK SDK)

## Handlers fondamentaux

### LaunchRequestHandler

```python
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input) -> Response:
        speak = "Bienvenue ! Que puis-je faire pour vous ?"
        reprompt = "Dites-moi ce que vous voulez faire."

        return (
            handler_input.response_builder
            .speak(speak)
            .ask(reprompt)           # .ask() garde la session ouverte
            .response
        )
```

### IntentRequestHandler (pattern générique)

```python
class MonIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input) -> bool:
        return is_intent_name("MonIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        # Lecture d'un slot
        slots = handler_input.request_envelope.request.intent.slots
        valeur = slots.get("monSlot")
        slot_value = valeur.value if valeur else "inconnu"

        speak = f"Vous avez dit : {slot_value}"
        return handler_input.response_builder.speak(speak).response
```

### SessionEndedRequestHandler (obligatoire)

```python
class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input) -> Response:
        # Sauvegarder l'état si nécessaire — pas de response ici
        handler_input.attributes_manager.save_persistent_attributes()
        return handler_input.response_builder.response
```

### CatchAllExceptionHandler

```python
from ask_sdk_core.dispatch_components import AbstractExceptionHandler

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception) -> bool:
        return True

    def handle(self, handler_input, exception) -> Response:
        logger.error(f"Erreur : {exception}", exc_info=True)
        speak = "Désolé, une erreur est survenue. Réessayez."
        return (
            handler_input.response_builder
            .speak(speak)
            .ask(speak)
            .response
        )
```

---

## Gestion des Slots

### Types natifs Amazon utiles

| Type | Exemple | Usage |
|---|---|---|
| `AMAZON.Date` | "demain", "lundi" | Rendez-vous, rappels |
| `AMAZON.Time` | "14h30", "ce soir" | Horaires |
| `AMAZON.Number` | "trois", "42" | Quantités |
| `AMAZON.City` | "Paris", "Lyon" | Localisation |
| `AMAZON.FirstName` | "Marie" | Personnalisation |
| `AMAZON.SearchQuery` | texte libre | Recherche |

### Slot custom dans fr-FR.json

```json
{
  "types": [
    {
      "name": "COULEUR_TYPE",
      "values": [
        {"name": {"value": "rouge", "synonyms": ["rouge vif", "écarlate"]}},
        {"name": {"value": "bleu", "synonyms": ["bleu ciel", "azure"]}}
      ]
    }
  ]
}
```

### Lecture sécurisée d'un slot en Python

```python
def get_slot_value(handler_input, slot_name: str, default=None):
    """Lecture robuste d'un slot avec résolution de synonymes."""
    try:
        slot = handler_input.request_envelope.request.intent.slots.get(slot_name)
        if not slot or not slot.value:
            return default
        # Résolution du synonyme → valeur canonique
        if slot.resolutions and slot.resolutions.resolutions_per_authority:
            authority = slot.resolutions.resolutions_per_authority[0]
            if authority.status.code.value == "ER_SUCCESS_MATCH":
                return authority.values[0].value.name
        return slot.value
    except Exception:
        return default
```

---

## Dialog Management (conversations multi-tours)

### Intent avec confirmation obligatoire

```json
// Dans fr-FR.json — intent avec elicitSlot
{
  "name": "CommanderPizzaIntent",
  "slots": [
    {"name": "taille", "type": "TAILLE_TYPE", "samples": ["taille {taille}"]},
    {"name": "garniture", "type": "GARNITURE_TYPE"}
  ],
  "samples": ["je veux une pizza {taille} avec {garniture}"]
}
```

```python
from ask_sdk_model.dialog import ElicitSlotDirective, ConfirmIntentDirective
from ask_sdk_model import Intent

class CommanderPizzaHandler(AbstractRequestHandler):
    def can_handle(self, handler_input) -> bool:
        return is_intent_name("CommanderPizzaIntent")(handler_input)

    def handle(self, handler_input) -> Response:
        current_intent = handler_input.request_envelope.request.intent
        slots = current_intent.slots

        # Étape 1 : demander la taille si manquante
        if not slots["taille"].value:
            return (
                handler_input.response_builder
                .speak("Quelle taille voulez-vous ? Petite, moyenne ou grande ?")
                .add_directive(ElicitSlotDirective(slot_to_elicit="taille", updated_intent=current_intent))
                .response
            )

        # Étape 2 : demander la garniture
        if not slots["garniture"].value:
            return (
                handler_input.response_builder
                .speak("Avec quelle garniture ?")
                .add_directive(ElicitSlotDirective(slot_to_elicit="garniture", updated_intent=current_intent))
                .response
            )

        # Étape 3 : confirmation finale
        taille = slots["taille"].value
        garniture = slots["garniture"].value
        speak = f"Je commande une pizza {taille} avec {garniture}. C'est bien ça ?"

        return (
            handler_input.response_builder
            .speak(speak)
            .add_directive(ConfirmIntentDirective(updated_intent=current_intent))
            .response
        )
```

---

## Session Attributes vs Persistance DynamoDB

```python
# Session attributes — perdus à la fin de la session
attrs_manager = handler_input.attributes_manager

# Écriture session (in-memory)
attrs_manager.session_attributes["score"] = 42

# Lecture session
score = attrs_manager.session_attributes.get("score", 0)

# Persistance DynamoDB — survit entre les sessions
persistent = attrs_manager.persistent_attributes  # lecture
persistent["total_parties"] = persistent.get("total_parties", 0) + 1
attrs_manager.save_persistent_attributes()         # écriture
```

---

## SSML — Voix enrichie

```python
def build_ssml_response(texte: str, pause_ms: int = 500) -> str:
    """Construit une réponse SSML avec pause et emphase."""
    return f"""
    <speak>
        {texte}
        <break time="{pause_ms}ms"/>
        <emphasis level="moderate">Bonne chance !</emphasis>
        <audio src="soundbank://soundlibrary/ui/gameshow/amzn_ui_sfx_gameshow_intro_01"/>
    </speak>
    """

# Dans le handler :
handler_input.response_builder.speak(build_ssml_response("Bienvenue au quiz !"))
```

### Tags SSML les plus utiles

| Tag | Usage |
|---|---|
| `<break time="500ms"/>` | Pause |
| `<emphasis level="strong">` | Emphase vocale |
| `<prosody rate="slow">` | Vitesse de parole |
| `<say-as interpret-as="digits">` | Épeler les chiffres |
| `<audio src="..."/>` | Jouer un son MP3 |

---

## Modèle d'interaction fr-FR.json (template)

```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "mon skill",
      "intents": [
        {
          "name": "AMAZON.HelpIntent",
          "samples": []
        },
        {
          "name": "AMAZON.CancelIntent",
          "samples": ["annule", "stop", "quitte"]
        },
        {
          "name": "AMAZON.StopIntent",
          "samples": ["arrête", "stop", "quitte"]
        },
        {
          "name": "MonIntent",
          "slots": [
            {
              "name": "monSlot",
              "type": "AMAZON.SearchQuery"
            }
          ],
          "samples": [
            "dis moi {monSlot}",
            "je veux savoir {monSlot}",
            "{monSlot}"
          ]
        }
      ],
      "types": []
    }
  }
}
```
