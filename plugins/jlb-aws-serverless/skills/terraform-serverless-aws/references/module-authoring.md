# Référence : Écrire un module réutilisable

## Structure obligatoire d'un module

```
modules/{nom}/
├── main.tf         ← ressources AWS
├── variables.tf    ← inputs du module
├── outputs.tf      ← valeurs exposées aux projets
├── CHANGELOG.md    ← historique des versions
└── README.md       ← documentation inputs/outputs/exemples
```

---

## variables.tf — Pattern de référence

```hcl
# ── Identification ────────────────────────────────────────────────────────────
variable "name" {
  type        = string
  description = "Nom complet de la ressource principale (déjà formaté par le projet)"
}

variable "module_version" {
  type        = string
  description = "Version du module ex: lambda-function/1.2.0 — injecté par le projet"
  default     = "lambda-function/unknown"
}

# ── Tags ──────────────────────────────────────────────────────────────────────
variable "tags" {
  type        = map(string)
  description = "Tags communs issus de local.common_tags dans le projet appelant"
  default     = {}
}

# ── Configuration métier ──────────────────────────────────────────────────────
# (variables spécifiques au module ici)
variable "handler" {
  type        = string
  description = "Handler Lambda ex: handler.lambda_handler"
  default     = "handler.lambda_handler"
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

variable "timeout" {
  type    = number
  default = 30
  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "timeout doit être entre 1 et 900 secondes."
  }
}

variable "memory_size" {
  type    = number
  default = 256
}

variable "environment_variables" {
  type        = map(string)
  description = "Variables d'environnement Lambda"
  default     = {}
}
```

---

## main.tf — Pattern de référence (module lambda-function)

```hcl
# ── Locals du module ──────────────────────────────────────────────────────────
locals {
  # Tags propres à ce module — fusionnés PAR DESSUS les tags du projet
  module_tags = {
    Module    = "lambda-function"
    Version   = var.module_version
    Component = "${var.name}-lambda"
  }

  # Tags logs légèrement différents
  log_tags = merge(var.tags, local.module_tags, {
    Component = "${var.name}-logs"
  })
}

# ── IAM Role ──────────────────────────────────────────────────────────────────
resource "aws_iam_role" "this" {
  name = "${var.name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = merge(var.tags, local.module_tags, {
    Component = "${var.name}-iam-role"
  })

  lifecycle {
    ignore_changes = [tags["CreatedAt"]]
  }
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "xray" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# ── Lambda Function ───────────────────────────────────────────────────────────
resource "aws_lambda_function" "this" {
  function_name    = var.name
  role             = aws_iam_role.this.arn
  handler          = var.handler
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size
  filename         = var.filename
  source_code_hash = var.source_code_hash

  tracing_config {
    mode = "Active"   # X-Ray activé par défaut
  }

  dynamic "environment" {
    for_each = length(var.environment_variables) > 0 ? [1] : []
    content {
      variables = merge(var.environment_variables, {
        POWERTOOLS_SERVICE_NAME = var.name
        METRICS_NAMESPACE       = lookup(var.tags, "Project", "default")
      })
    }
  }

  layers = [
    "arn:aws:lambda:${data.aws_region.current.name}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-arm64:7"
  ]

  tags = merge(var.tags, local.module_tags)

  lifecycle {
    ignore_changes = [tags["CreatedAt"]]
  }
}

# ── CloudWatch Log Group ──────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "this" {
  name = "/aws/lambda/${aws_lambda_function.this.function_name}"

  # Rétention déduite du tag Environment
  retention_in_days = lookup({
    "dev"     = 7
    "staging" = 14
    "prod"    = 90
  }, lookup(var.tags, "Environment", "dev"), 14)

  tags = local.log_tags

  lifecycle {
    ignore_changes = [tags["CreatedAt"]]
  }
}

data "aws_region" "current" {}
```

---

## outputs.tf — Exposer ce dont les projets ont besoin

```hcl
output "function_name" {
  description = "Nom de la fonction Lambda"
  value       = aws_lambda_function.this.function_name
}

output "function_arn" {
  description = "ARN de la fonction Lambda"
  value       = aws_lambda_function.this.arn
}

output "invoke_arn" {
  description = "ARN d'invocation (pour API Gateway)"
  value       = aws_lambda_function.this.invoke_arn
}

output "role_arn" {
  description = "ARN du rôle IAM de la fonction"
  value       = aws_iam_role.this.arn
}

output "role_name" {
  description = "Nom du rôle IAM (pour attacher des policies supplémentaires)"
  value       = aws_iam_role.this.name
}

output "log_group_name" {
  description = "Nom du log group CloudWatch"
  value       = aws_cloudwatch_log_group.this.name
}
```

---

## CHANGELOG.md — Template

```markdown
# Changelog — lambda-function

## [1.1.0] — 2024-03-10
### Added
- Variable `memory_size` avec default 256 (non-breaking)
- Output `log_group_name`

## [1.0.0] — 2024-01-15
### Added
- Version initiale stable
- Lambda + IAM role + Log group + X-Ray
- Powertools layer attaché par défaut
```

---

## README.md — Template

```markdown
# Module : lambda-function

Crée une fonction Lambda avec IAM role, log group CloudWatch et X-Ray activé.
Lambda Powertools layer attaché automatiquement.

## Usage

```hcl
module "api_lambda" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/lambda-function?ref=lambda-function/1.1.0"

  name           = "ecommerce-orders-api-handler-prod"
  module_version = "lambda-function/1.1.0"
  tags           = local.common_tags

  handler     = "handler.lambda_handler"
  environment_variables = {
    TABLE_NAME = "ma-table"
  }
}
```

## Inputs

| Nom | Type | Requis | Default | Description |
|-----|------|--------|---------|-------------|
| name | string | oui | — | Nom de la fonction |
| tags | map(string) | oui | {} | Tags communs du projet |
| module_version | string | non | unknown | Version du module |
| handler | string | non | handler.lambda_handler | Handler |
| timeout | number | non | 30 | Timeout en secondes |
| memory_size | number | non | 256 | Mémoire en MB |

## Outputs

| Nom | Description |
|-----|-------------|
| function_name | Nom de la Lambda |
| function_arn | ARN complet |
| invoke_arn | ARN d'invocation API Gateway |
| role_name | Nom du rôle IAM |
| log_group_name | Nom du log group |
```
