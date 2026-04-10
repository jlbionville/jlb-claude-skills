# Référence : Lambda · DynamoDB · API Gateway

## 1. Lambda — Terraform

### Ressource Lambda minimale

```hcl
# lambda.tf
resource "aws_lambda_function" "api" {
  function_name = "${var.project}-${var.application}-handler-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  filename      = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  timeout     = 30
  memory_size = 256

  environment {
    variables = {
      TABLE_NAME  = aws_dynamodb_table.main.name
      ENVIRONMENT = var.environment
    }
  }

  tags = merge(local.common_tags, {
    Component = "${var.application}-lambda"
  })
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/.build/lambda.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Component = "${var.application}-logs"
  })
}
```

### IAM Role Lambda (moindre privilège)

```hcl
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project}-${var.application}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = merge(local.common_tags, {
    Component = "${var.application}-iam-role"
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${var.project}-${var.application}-dynamodb-policy-${var.environment}"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = [
        aws_dynamodb_table.main.arn,
        "${aws_dynamodb_table.main.arn}/index/*"
      ]
    }]
  })
}
```

---

## 2. DynamoDB — Terraform

### Table avec GSI et TTL

```hcl
# dynamodb.tf
resource "aws_dynamodb_table" "main" {
  name         = "${var.project}-${var.application}-${var.table_name}-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"   # serverless : pas de provisioning
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }
  attribute {
    name = "SK"
    type = "S"
  }
  attribute {
    name = "GSI1PK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ExpiresAt"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Component = "${var.application}-dynamodb"
  })
}
```

> **Bonnes pratiques DynamoDB :**
> - Préférer `PAY_PER_REQUEST` pour du serverless (coût à l'usage, pas de provisioning)
> - Modéliser les accès avant de définir les index (single-table design)
> - Activer PITR en prod, TTL pour les données temporaires
> - Doc : https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table

---

## 3. API Gateway — Terraform

### HTTP API (v2) — Recommandé (moins cher, moins de config)

```hcl
# api_gateway.tf
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project}-${var.application}-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["Content-Type", "Authorization"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins = var.environment == "prod" ? ["https://yourdomain.com"] : ["*"]
  }

  tags = merge(local.common_tags, {
    Component = "${var.application}-api-gateway"
  })
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn
  }

  tags = merge(local.common_tags, {
    Component = "${var.application}-api-stage"
  })
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.api.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/apigateway/${var.project}-${var.application}-${var.environment}"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Component = "${var.application}-api-logs"
  })
}
```

> **HTTP API vs REST API :**
> - HTTP API (v2) : ~70% moins cher, plus rapide, suffisant pour la plupart des cas
> - REST API (v1) : utiliser si tu as besoin de plans d'usage, clés API, ou WAF natif
> - Doc : https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api

---

## 4. Lambda Handler Python (pattern API Gateway)

```python
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ["TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event: dict, context) -> dict:
    """Handler principal — router selon la méthode HTTP."""
    logger.info("Event reçu", extra={"event": event})

    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path   = event.get("rawPath", "/")

    try:
        if method == "GET":
            return handle_get(event)
        elif method == "POST":
            return handle_post(event)
        else:
            return response(405, {"error": f"Méthode {method} non supportée"})

    except ClientError as e:
        logger.error("Erreur DynamoDB: %s", e.response["Error"]["Message"])
        return response(500, {"error": "Erreur interne"})
    except Exception as e:
        logger.exception("Erreur inattendue")
        return response(500, {"error": "Erreur interne"})


def handle_get(event: dict) -> dict:
    params = event.get("queryStringParameters") or {}
    pk = params.get("pk")
    if not pk:
        return response(400, {"error": "Paramètre 'pk' manquant"})

    result = table.get_item(Key={"PK": pk, "SK": "META"})
    item = result.get("Item")
    if not item:
        return response(404, {"error": "Ressource non trouvée"})
    return response(200, item)


def handle_post(event: dict) -> dict:
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Body JSON invalide"})

    # Validation minimale
    if "id" not in body:
        return response(400, {"error": "Champ 'id' requis"})

    item = {"PK": body["id"], "SK": "META", **body}
    table.put_item(Item=item)
    return response(201, {"message": "Créé", "id": body["id"]})


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
```

---

## 5. Outputs utiles

```hcl
# outputs.tf
output "api_url" {
  description = "URL de base de l'API"
  value       = aws_apigatewayv2_stage.main.invoke_url
}

output "lambda_arn" {
  description = "ARN de la fonction Lambda"
  value       = aws_lambda_function.api.arn
}

output "dynamodb_table_name" {
  description = "Nom de la table DynamoDB"
  value       = aws_dynamodb_table.main.name
}
```
