# Référence : Appeler un module depuis un projet

## Structure d'un projet

```
projects/ecommerce-orders-api/
├── backend.tf      ← provider + state S3 isolé
├── locals.tf       ← common_tags + calculs
├── variables.tf    ← déclaration de toutes les variables + validation
├── main.tf         ← appels aux modules
├── outputs.tf      ← exports utiles (URL API, ARN Lambda...)
└── envs/
    ├── dev.tfvars
    ├── staging.tfvars
    └── prod.tfvars
```

---

## variables.tf — Toutes les variables avec validation

```hcl
# ── Identification ────────────────────────────────────────────────────────────
variable "project"     { type = string }
variable "application" { type = string }
variable "team"        { type = string }
variable "author"      { type = string }
variable "cost_center" { type = string }
variable "git_repo"    { type = string  default = "infra-platform" }
variable "region"      { type = string  default = "eu-west-1" }

# ── Validés ───────────────────────────────────────────────────────────────────
variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment : dev | staging | prod"
  }
}

variable "criticality" {
  type = string
  validation {
    condition     = contains(["high", "medium", "low"], var.criticality)
    error_message = "criticality : high | medium | low"
  }
}

# ── CI/CD ─────────────────────────────────────────────────────────────────────
variable "deployed_at" {
  type    = string
  default = ""
  description = "Injecté par la CI : date ISO du deploy. Figé à la création via ignore_changes."
}

# ── Observabilité ─────────────────────────────────────────────────────────────
variable "ops_alert_email"    { type = string }
variable "monthly_budget_usd" { type = string  default = "100" }
```

---

## locals.tf — common_tags complet

```hcl
locals {
  common_tags = {
    Project            = var.project
    Application        = var.application
    Environment        = var.environment
    Team               = var.team
    Author             = var.author
    CostCenter         = var.cost_center
    ManagedBy          = "terraform"
    GitRepo            = var.git_repo
    TerraformWorkspace = terraform.workspace
    Criticality        = var.criticality
    CreatedAt          = var.deployed_at
    UpdatedAt          = ""   # géré par AWS Config Rule
  }

  log_retention_days = { dev = 7, staging = 14, prod = 90 }[var.environment]
  metrics_namespace  = "${var.project}/${var.application}"
}
```

---

## backend.tf — State isolé par projet

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }

  backend "s3" {
    # Clé unique : {projet}/{application}/{environnement}
    # La valeur exacte est injectée via -backend-config en CI
    bucket         = "mon-org-terraform-states"
    key            = "ecommerce/orders-api/prod/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "mon-org-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region

  # Tags appliqués automatiquement sur toutes les ressources du projet
  default_tags {
    tags = {
      ManagedBy = "terraform"
      GitRepo   = var.git_repo
    }
  }
}
```

---

## main.tf — Appel des modules avec version fixe

```hcl
# ── Lambda principale ─────────────────────────────────────────────────────────
module "api_lambda" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/lambda-function?ref=lambda-function/1.2.0"

  name           = "${var.project}-${var.application}-handler-${var.environment}"
  module_version = "lambda-function/1.2.0"
  tags           = local.common_tags

  handler     = "handler.lambda_handler"
  runtime     = "python3.12"
  timeout     = 30
  memory_size = 256
  filename    = "../src/lambda.zip"

  environment_variables = {
    TABLE_NAME        = module.orders_table.table_name
    EVENT_BUS_NAME    = module.messaging.event_bus_name
    METRICS_NAMESPACE = local.metrics_namespace
    ENVIRONMENT       = var.environment
  }
}

# ── DynamoDB ──────────────────────────────────────────────────────────────────
module "orders_table" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/dynamodb-table?ref=dynamodb-table/1.0.0"

  name           = "${var.project}-${var.application}-orders-${var.environment}"
  module_version = "dynamodb-table/1.0.0"
  tags           = local.common_tags
}

# ── API Gateway ───────────────────────────────────────────────────────────────
module "api" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/api-gateway-http?ref=api-gateway-http/1.0.0"

  name           = "${var.project}-${var.application}-api-${var.environment}"
  module_version = "api-gateway-http/1.0.0"
  tags           = local.common_tags

  lambda_invoke_arn    = module.api_lambda.invoke_arn
  lambda_function_name = module.api_lambda.function_name
  environment          = var.environment
}

# ── Observabilité ─────────────────────────────────────────────────────────────
module "observability" {
  source = "git::https://github.com/mon-org/infra-platform.git//modules/observability?ref=observability/1.1.0"

  name           = "${var.project}-${var.application}-${var.environment}"
  module_version = "observability/1.1.0"
  tags           = local.common_tags

  lambda_function_name = module.api_lambda.function_name
  api_gateway_id       = module.api.api_id
  ops_alert_email      = var.ops_alert_email
  monthly_budget_usd   = var.monthly_budget_usd
}

# Attacher la policy DynamoDB au rôle Lambda (cross-module)
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${var.project}-${var.application}-dynamodb-policy-${var.environment}"
  role = module.api_lambda.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem",
                  "dynamodb:DeleteItem", "dynamodb:Query"]
      Resource = [module.orders_table.table_arn, "${module.orders_table.table_arn}/index/*"]
    }]
  })
}
```

---

## outputs.tf

```hcl
output "api_url" {
  description = "URL publique de l'API"
  value       = module.api.invoke_url
}

output "lambda_arn" {
  description = "ARN de la Lambda principale"
  value       = module.api_lambda.function_arn
}

output "table_name" {
  description = "Nom de la table DynamoDB"
  value       = module.orders_table.table_name
}
```

---

## Commandes de déploiement

```bash
# Init (première fois ou après changement de backend)
terraform init \
  -backend-config="key=ecommerce/orders-api/prod/terraform.tfstate"

# Plan
terraform plan \
  -var-file="envs/prod.tfvars" \
  -var="deployed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Apply
terraform apply \
  -var-file="envs/prod.tfvars" \
  -var="deployed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -auto-approve
```
