# Référence : Observabilité — Logs · Métriques · Tracing

## Vue d'ensemble : les 3 piliers

| Pilier | Outil AWS | Usage |
|--------|-----------|-------|
| **Logs** | CloudWatch Logs + Powertools | Journalisation JSON structurée |
| **Métriques** | CloudWatch Metrics + EMF | KPIs métier et techniques |
| **Tracing** | X-Ray | Trace distribuée inter-services |

---

## 1. Logging structuré — Lambda Powertools

### Dépendance (layer ou package)

```hcl
# lambda.tf — Layer AWS géré (recommandé, pas de déploiement manuel)
resource "aws_lambda_function" "api" {
  # ...
  layers = [
    "arn:aws:lambda:${var.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-arm64:7"
  ]

  environment {
    variables = {
      # Powertools configuration
      POWERTOOLS_SERVICE_NAME      = "${var.project}-${var.application}"
      POWERTOOLS_LOG_LEVEL         = var.environment == "prod" ? "INFO" : "DEBUG"
      POWERTOOLS_LOGGER_SAMPLE_RATE = "0.1"   # 10% des requêtes en DEBUG en prod
    }
  }
}
```

> Trouver la dernière version du layer : https://docs.powertools.aws.dev/lambda/python/latest/

### Handler Python avec Powertools Logger

```python
import json
import os
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

logger  = Logger(service=os.environ["POWERTOOLS_SERVICE_NAME"])
tracer  = Tracer()
metrics = Metrics(namespace=os.environ["METRICS_NAMESPACE"])


@logger.inject_lambda_context(log_event=True, clear_state=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    try:
        result = process(event)
        metrics.add_metric(name="SuccessCount", unit=MetricUnit.Count, value=1)
        return response(200, result)

    except ValueError as e:
        logger.warning("Validation échouée", extra={"error": str(e)})
        metrics.add_metric(name="ValidationErrorCount", unit=MetricUnit.Count, value=1)
        return response(400, {"error": str(e)})

    except Exception as e:
        logger.exception("Erreur inattendue")
        metrics.add_metric(name="ErrorCount", unit=MetricUnit.Count, value=1)
        return response(500, {"error": "Erreur interne"})


@tracer.capture_method
def process(event: dict) -> dict:
    # Enrichir les logs avec du contexte métier
    logger.append_keys(order_id=event.get("order_id"), user_id=event.get("user_id"))
    logger.info("Traitement commande démarré")
    # ... logique métier
    return {}


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
```

**Ce que Powertools apporte automatiquement dans chaque log :**
```json
{
  "level": "INFO",
  "location": "handler.process:42",
  "message": "Traitement commande démarré",
  "service": "ecommerce-orders-api",
  "timestamp": "2024-01-15T10:23:45.123Z",
  "xray_trace_id": "1-65a4b123-...",
  "cold_start": false,
  "function_name": "ecommerce-orders-api-handler-prod",
  "function_request_id": "abc-123",
  "order_id": "ORD-456",
  "user_id": "USR-789"
}
```

---

## 2. CloudWatch Logs — Terraform

### Log Groups pour chaque composant

```hcl
# observability.tf

# Log group Lambda
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = local.log_retention_days

  tags = merge(local.common_tags, {
    Component = "${var.application}-lambda-logs"
  })
}

# Log group API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project}-${var.application}-${var.environment}"
  retention_in_days = local.log_retention_days

  tags = merge(local.common_tags, {
    Component = "${var.application}-apigw-logs"
  })
}

# Log group Step Functions
resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/states/${var.project}-${var.application}-${var.environment}"
  retention_in_days = local.log_retention_days

  tags = merge(local.common_tags, {
    Component = "${var.application}-sfn-logs"
  })
}

# Rétention selon l'environnement
locals {
  log_retention_days = {
    dev     = 7
    staging = 14
    prod    = 90
  }[var.environment]
}
```

### Metric Filter — extraire une métrique depuis les logs

```hcl
# Compter les erreurs 5xx à partir des logs Lambda
resource "aws_cloudwatch_log_metric_filter" "lambda_errors" {
  name           = "${var.project}-${var.application}-errors-${var.environment}"
  log_group_name = aws_cloudwatch_log_group.lambda.name
  pattern        = "{ $.level = \"ERROR\" }"

  metric_transformation {
    name      = "${var.application}-ErrorCount"
    namespace = "${var.project}/${var.application}"
    value     = "1"
    unit      = "Count"
  }
}

# Compter les cold starts
resource "aws_cloudwatch_log_metric_filter" "cold_starts" {
  name           = "${var.project}-${var.application}-coldstarts-${var.environment}"
  log_group_name = aws_cloudwatch_log_group.lambda.name
  pattern        = "{ $.cold_start = true }"

  metric_transformation {
    name      = "${var.application}-ColdStartCount"
    namespace = "${var.project}/${var.application}"
    value     = "1"
    unit      = "Count"
  }
}
```

---

## 3. X-Ray — Tracing distribué

### Activer X-Ray sur Lambda et API Gateway

```hcl
# lambda.tf
resource "aws_lambda_function" "api" {
  # ...
  tracing_config {
    mode = "Active"   # "PassThrough" si tu veux désactiver
  }
}

# api_gateway.tf (HTTP API v2)
resource "aws_apigatewayv2_stage" "main" {
  # ...
  default_route_settings {
    logging_level          = "INFO"
    data_trace_enabled     = false   # true seulement en debug (coûteux)
    throttling_burst_limit = 500
    throttling_rate_limit  = 100
  }
}

# IAM : autoriser Lambda à écrire dans X-Ray
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}
```

### Instrumenter les appels DynamoDB/SQS dans le code

```python
from aws_lambda_powertools import Tracer
import boto3
from aws_xray_sdk.core import patch_all

patch_all()   # instrumente automatiquement boto3, requests, etc.

tracer  = Tracer()
dynamodb = boto3.resource("dynamodb")


@tracer.capture_method
def get_order(order_id: str) -> dict:
    """X-Ray crée automatiquement un sous-segment pour cet appel DynamoDB."""
    table = dynamodb.Table(os.environ["TABLE_NAME"])
    result = table.get_item(Key={"PK": order_id, "SK": "META"})
    return result.get("Item", {})
```

---

## 4. Alarmes CloudWatch

```hcl
# observability.tf

# Alarme sur les erreurs Lambda
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project}-${var.application}-lambda-errors-${var.environment}"
  alarm_description   = "Erreurs Lambda > seuil sur 5 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.environment == "prod" ? 5 : 20
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = merge(local.common_tags, {
    Component = "${var.application}-alarm-errors"
  })
}

# Alarme sur la durée d'exécution (P99)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.project}-${var.application}-lambda-duration-${var.environment}"
  alarm_description   = "P99 durée Lambda > 80% du timeout"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 60
  extended_statistic  = "p99"
  threshold           = aws_lambda_function.api.timeout * 800   # 80% en ms
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = merge(local.common_tags, {
    Component = "${var.application}-alarm-duration"
  })
}

# Alarme sur la profondeur de file SQS (messages non traités)
resource "aws_cloudwatch_metric_alarm" "sqs_depth" {
  alarm_name          = "${var.project}-${var.application}-sqs-depth-${var.environment}"
  alarm_description   = "File SQS : messages en attente > seuil"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesNotVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 100
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.main.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = merge(local.common_tags, {
    Component = "${var.application}-alarm-sqs"
  })
}

# Alarme DLQ — message dans la DLQ = problème critique
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project}-${var.application}-dlq-${var.environment}"
  alarm_description   = "⚠️ Messages dans la DLQ — traitement en échec"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = merge(local.common_tags, {
    Component = "${var.application}-alarm-dlq"
  })
}

# Topic SNS pour les alertes ops
resource "aws_sns_topic" "alerts" {
  name = "${var.project}-${var.application}-alerts-${var.environment}"

  tags = merge(local.common_tags, {
    Component = "${var.application}-alerts-topic"
  })
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.ops_alert_email
}
```

---

## 5. Dashboard CloudWatch

```hcl
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project}-${var.application}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title  = "Lambda — Invocations & Erreurs"
          period = 300
          stat   = "Sum"
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.api.function_name],
            ["AWS/Lambda", "Errors",      "FunctionName", aws_lambda_function.api.function_name],
            ["AWS/Lambda", "Throttles",   "FunctionName", aws_lambda_function.api.function_name],
          ]
        }
      },
      {
        type = "metric"
        properties = {
          title  = "Lambda — Durée P50 / P99"
          period = 60
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.api.function_name, { stat = "p50" }],
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.api.function_name, { stat = "p99" }],
          ]
        }
      },
      {
        type = "metric"
        properties = {
          title  = "API Gateway — Latence & 4xx/5xx"
          period = 60
          metrics = [
            ["AWS/ApiGateway", "Latency",    "ApiId", aws_apigatewayv2_api.main.id, { stat = "p99" }],
            ["AWS/ApiGateway", "4XXError",   "ApiId", aws_apigatewayv2_api.main.id, { stat = "Sum" }],
            ["AWS/ApiGateway", "5XXError",   "ApiId", aws_apigatewayv2_api.main.id, { stat = "Sum" }],
          ]
        }
      },
      {
        type = "metric"
        properties = {
          title  = "SQS — File principale & DLQ"
          period = 60
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible",    "QueueName", aws_sqs_queue.main.name, { stat = "Maximum" }],
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible",    "QueueName", aws_sqs_queue.dlq.name,  { stat = "Maximum", color = "#d62728" }],
            ["AWS/SQS", "NumberOfMessagesSent",                  "QueueName", aws_sqs_queue.main.name, { stat = "Sum" }],
          ]
        }
      },
    ]
  })
}
```

---

## 6. Variables Terraform à ajouter

```hcl
variable "ops_alert_email" {
  type        = string
  description = "Email destinataire des alertes opérationnelles"
}

variable "metrics_namespace" {
  type        = string
  description = "Namespace CloudWatch pour les métriques custom"
  default     = ""   # calculé dans locals.tf
}
```

```hcl
# locals.tf — ajouter
locals {
  metrics_namespace  = "${var.project}/${var.application}"
  log_retention_days = { dev = 7, staging = 14, prod = 90 }[var.environment]
}
```

Et passer `METRICS_NAMESPACE = local.metrics_namespace` en variable d'environnement Lambda.

---

## 7. Structure de fichiers mise à jour

```
infrastructure/
├── observability.tf   # ← NOUVEAU : log groups, alarmes, dashboard, metric filters
└── ...
```

---

## Points d'attention

- **`log_event=True`** dans `@logger.inject_lambda_context` : logge tout l'event → désactiver en prod si les events contiennent des données sensibles (PII)
- **X-Ray coûts** : ~$5 / million de traces ; `PassThrough` en dev pour économiser
- **Rétention des logs** : toujours la définir (default AWS = infini → coût croissant)
- **DLQ alarm** : seuil à 0 → moindre message = alerte immédiate
- **Powertools layer ARN** : vérifier la version selon la runtime Python et l'architecture (arm64 vs x86_64)
- Doc Powertools : https://docs.powertools.aws.dev/lambda/python/latest/
- Doc X-Ray Terraform : https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_sampling_rule
