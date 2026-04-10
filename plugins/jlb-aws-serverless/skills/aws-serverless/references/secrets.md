# Référence : Secrets Manager · SSM Parameter Store

## Quand utiliser quoi ?

| | Secrets Manager | SSM Parameter Store |
|--|----------------|-------------------|
| **Usage** | Secrets rotatifs (clés API, passwords DB) | Config applicative, paramètres non-secrets |
| **Rotation** | ✅ Automatique | ❌ Manuelle |
| **Chiffrement** | KMS obligatoire | KMS optionnel (SecureString) |
| **Coût** | ~$0.40/secret/mois | Gratuit (Standard), $0.05/10k ops (Advanced) |
| **Recommandation** | Credentials sensibles | Feature flags, URLs, config env |

---

## 1. Secrets Manager — Terraform

```hcl
# secrets.tf

resource "aws_secretsmanager_secret" "api_key" {
  name        = "${var.project}/${var.application}/${var.environment}/api-key"
  description = "Clé API tierce pour ${var.application}"

  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(local.common_tags, {
    Component = "${var.application}-secret-api-key"
  })
}

resource "aws_secretsmanager_secret_version" "api_key" {
  secret_id = aws_secretsmanager_secret.api_key.id

  # Ne pas stocker la valeur réelle dans Terraform !
  # Initialiser avec un placeholder, puis mettre à jour via AWS CLI ou console
  secret_string = jsonencode({
    api_key = "PLACEHOLDER_CHANGE_ME"
  })

  lifecycle {
    ignore_changes = [secret_string]   # Terraform ne remet pas la valeur après init
  }
}

# IAM : permettre à Lambda de lire ce secret
resource "aws_iam_role_policy" "lambda_secrets" {
  name = "${var.project}-${var.application}-secrets-policy-${var.environment}"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = aws_secretsmanager_secret.api_key.arn
    }]
  })
}
```

### Lire un secret depuis Lambda (Python) — avec cache

```python
import boto3
import json
import os

secrets_client = boto3.client("secretsmanager")
_cache: dict = {}   # Cache en mémoire (durée de vie du container Lambda)

SECRET_ARN = os.environ["API_KEY_SECRET_ARN"]


def get_secret(secret_arn: str) -> dict:
    if secret_arn not in _cache:
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        _cache[secret_arn] = json.loads(response["SecretString"])
    return _cache[secret_arn]


def lambda_handler(event, context):
    secret = get_secret(SECRET_ARN)
    api_key = secret["api_key"]
    ...
```

> **Bonne pratique** : utiliser [AWS Parameters and Secrets Lambda Extension](https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html)
> pour un cache géré automatiquement sans code supplémentaire.

---

## 2. SSM Parameter Store — Terraform

```hcl
# Pour une valeur non-sensible
resource "aws_ssm_parameter" "app_config" {
  name  = "/${var.project}/${var.application}/${var.environment}/config/feature-flag"
  type  = "String"
  value = "true"

  tags = merge(local.common_tags, {
    Component = "${var.application}-ssm-config"
  })
}

# Pour une valeur sensible (chiffrée KMS)
resource "aws_ssm_parameter" "db_password" {
  name   = "/${var.project}/${var.application}/${var.environment}/secrets/db-password"
  type   = "SecureString"
  value  = "PLACEHOLDER_CHANGE_ME"

  lifecycle {
    ignore_changes = [value]
  }

  tags = merge(local.common_tags, {
    Component = "${var.application}-ssm-secret"
  })
}

# IAM Lambda pour SSM
resource "aws_iam_role_policy" "lambda_ssm" {
  name = "${var.project}-${var.application}-ssm-policy-${var.environment}"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"]
      Resource = "arn:aws:ssm:${var.region}:*:parameter/${var.project}/${var.application}/${var.environment}/*"
    }]
  })
}
```

### Lire depuis Lambda (Python)

```python
import boto3
import os

ssm = boto3.client("ssm")

def get_parameter(name: str, with_decryption: bool = True) -> str:
    response = ssm.get_parameter(Name=name, WithDecryption=with_decryption)
    return response["Parameter"]["Value"]

def get_parameters_by_path(path: str) -> dict:
    """Charge tous les paramètres d'un chemin d'un coup."""
    response = ssm.get_parameters_by_path(
        Path=path, Recursive=True, WithDecryption=True
    )
    return {p["Name"].split("/")[-1]: p["Value"] for p in response["Parameters"]}
```

---

## Convention de nommage des secrets/paramètres

```
/{projet}/{application}/{environnement}/secrets/{nom}   # Secrets Manager / SSM SecureString
/{projet}/{application}/{environnement}/config/{nom}    # SSM String (config)
```

Exemples :
- `/ecommerce/orders-api/prod/secrets/stripe-api-key`
- `/ecommerce/orders-api/prod/config/max-retries`
