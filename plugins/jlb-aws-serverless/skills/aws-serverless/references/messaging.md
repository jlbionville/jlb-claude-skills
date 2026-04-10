# Référence : Messaging — SQS · SNS · EventBridge

## Quand utiliser quoi ?

| Service | Cas d'usage | Modèle |
|---------|-------------|--------|
| **SQS** | File de traitement asynchrone, découplage producteur/consommateur unique | Point-à-point (pull) |
| **SNS** | Notification fan-out vers plusieurs consommateurs | Pub/Sub (push) |
| **EventBridge** | Routage d'événements basé sur des règles, intégrations AWS/SaaS | Event bus (push) |

---

## 1. SQS — Terraform

### Queue standard + DLQ + trigger Lambda

```hcl
# messaging.tf

# Dead Letter Queue — reçoit les messages en échec
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project}-${var.application}-dlq-${var.environment}"
  message_retention_seconds = 1209600  # 14 jours

  tags = merge(local.common_tags, {
    Component = "${var.application}-sqs-dlq"
  })
}

# Queue principale
resource "aws_sqs_queue" "main" {
  name                       = "${var.project}-${var.application}-queue-${var.environment}"
  visibility_timeout_seconds = 60       # >= timeout Lambda
  message_retention_seconds  = 345600   # 4 jours
  delay_seconds              = 0
  receive_wait_time_seconds  = 20       # long polling (économise les requêtes)

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3             # 3 tentatives avant DLQ
  })

  tags = merge(local.common_tags, {
    Component = "${var.application}-sqs"
  })
}

# Trigger Lambda depuis SQS
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn = aws_sqs_queue.main.arn
  function_name    = aws_lambda_function.processor.arn
  batch_size       = 10
  enabled          = true

  function_response_types = ["ReportBatchItemFailures"]  # retry partiel
}

# Permission IAM Lambda pour SQS
resource "aws_iam_role_policy" "lambda_sqs" {
  name = "${var.project}-${var.application}-sqs-policy-${var.environment}"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ChangeMessageVisibility"
      ]
      Resource = aws_sqs_queue.main.arn
    }]
  })
}
```

### Handler Lambda SQS (Python)

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context) -> dict:
    """Traitement de messages SQS avec retry partiel."""
    batch_item_failures = []

    for record in event["Records"]:
        message_id = record["messageId"]
        try:
            body = json.loads(record["body"])
            logger.info("Traitement message %s : %s", message_id, body)
            process_message(body)

        except Exception as e:
            logger.error("Échec message %s : %s", message_id, str(e))
            batch_item_failures.append({"itemIdentifier": message_id})

    # Retourner les IDs en échec → SQS les retentera
    return {"batchItemFailures": batch_item_failures}


def process_message(body: dict) -> None:
    """Logique métier ici."""
    pass
```

---

## 2. SNS — Terraform

### Topic SNS + abonnements SQS + Lambda

```hcl
resource "aws_sns_topic" "events" {
  name = "${var.project}-${var.application}-events-${var.environment}"

  tags = merge(local.common_tags, {
    Component = "${var.application}-sns"
  })
}

# Abonnement SQS (fan-out)
resource "aws_sns_topic_subscription" "to_queue" {
  topic_arn = aws_sns_topic.events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.main.arn

  filter_policy = jsonencode({
    eventType = ["order_created", "order_updated"]   # filtrage optionnel
  })
}

# Autorisation SNS → SQS
resource "aws_sqs_queue_policy" "sns_to_sqs" {
  queue_url = aws_sqs_queue.main.url

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.main.arn
      Condition = {
        ArnEquals = { "aws:SourceArn" = aws_sns_topic.events.arn }
      }
    }]
  })
}
```

---

## 3. EventBridge — Terraform

### Event Bus personnalisé + règle + cible Lambda

```hcl
resource "aws_cloudwatch_event_bus" "main" {
  name = "${var.project}-${var.application}-bus-${var.environment}"

  tags = merge(local.common_tags, {
    Component = "${var.application}-eventbridge"
  })
}

resource "aws_cloudwatch_event_rule" "order_created" {
  name           = "${var.project}-${var.application}-order-created-${var.environment}"
  event_bus_name = aws_cloudwatch_event_bus.main.name
  description    = "Déclenche le traitement des nouvelles commandes"

  event_pattern = jsonencode({
    source      = ["${var.application}.orders"]
    detail-type = ["OrderCreated"]
    detail = {
      status = ["PENDING"]
    }
  })

  tags = merge(local.common_tags, {
    Component = "${var.application}-eb-rule"
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule           = aws_cloudwatch_event_rule.order_created.name
  event_bus_name = aws_cloudwatch_event_bus.main.name
  arn            = aws_lambda_function.processor.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.order_created.arn
}
```

### Publier un événement depuis Lambda (Python)

```python
import boto3
import json
import os

events_client = boto3.client("events")
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
APP_NAME       = os.environ["APPLICATION"]


def publish_order_created(order: dict) -> None:
    events_client.put_events(Entries=[{
        "Source":       f"{APP_NAME}.orders",
        "DetailType":   "OrderCreated",
        "Detail":       json.dumps(order),
        "EventBusName": EVENT_BUS_NAME,
    }])
```

---

## Points d'attention

- **SQS visibility timeout** doit être ≥ timeout Lambda (sinon le message est re-traité)
- **DLQ toujours configurée** en prod pour ne pas perdre de messages
- **`ReportBatchItemFailures`** permet le retry partiel : seuls les messages échoués repassent
- **EventBridge** : les events non matchés par une règle sont silencieusement ignorés → monitorer le bus
- Doc SQS Terraform : https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
- Doc EventBridge Terraform : https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule
