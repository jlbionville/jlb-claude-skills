# Référence : Step Functions

## Quand utiliser Step Functions ?

- Orchestration de plusieurs Lambdas avec logique conditionnelle
- Workflows longs (> 15 min, limite Lambda)
- Gestion des erreurs et retries entre étapes
- Traçabilité visuelle des exécutions

## Terraform

```hcl
# step-functions.tf

resource "aws_sfn_state_machine" "main" {
  name     = "${var.project}-${var.application}-workflow-${var.environment}"
  role_arn = aws_iam_role.sfn_exec.arn

  definition = jsonencode({
    Comment = "Workflow ${var.application}"
    StartAt = "ValidateInput"
    States = {
      ValidateInput = {
        Type     = "Task"
        Resource = aws_lambda_function.validator.arn
        Next     = "ProcessOrder"
        Retry = [{
          ErrorEquals     = ["Lambda.ServiceException", "Lambda.TooManyRequestsException"]
          IntervalSeconds = 2
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["ValidationError"]
          Next        = "HandleValidationError"
        }]
      }
      ProcessOrder = {
        Type     = "Task"
        Resource = aws_lambda_function.processor.arn
        Next     = "NotifySuccess"
      }
      NotifySuccess = {
        Type     = "Task"
        Resource = aws_lambda_function.notifier.arn
        End      = true
      }
      HandleValidationError = {
        Type   = "Fail"
        Error  = "ValidationFailed"
        Cause  = "Input invalide"
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }

  tags = merge(local.common_tags, {
    Component = "${var.application}-step-functions"
  })
}

resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/states/${var.project}-${var.application}-${var.environment}"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Component = "${var.application}-sfn-logs"
  })
}

resource "aws_iam_role" "sfn_exec" {
  name = "${var.project}-${var.application}-sfn-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
    }]
  })

  tags = merge(local.common_tags, {
    Component = "${var.application}-sfn-role"
  })
}

resource "aws_iam_role_policy" "sfn_lambda" {
  name = "${var.project}-${var.application}-sfn-policy-${var.environment}"
  role = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = [
          aws_lambda_function.validator.arn,
          aws_lambda_function.processor.arn,
          aws_lambda_function.notifier.arn,
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:PutLogEvents",
          "logs:GetLogDelivery"
        ]
        Resource = "*"
      }
    ]
  })
}
```

## Démarrer une exécution depuis Lambda (Python)

```python
import boto3
import json
import os

sfn_client = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def start_workflow(order_id: str, payload: dict) -> str:
    response = sfn_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=f"order-{order_id}",   # unique par exécution
        input=json.dumps(payload),
    )
    return response["executionArn"]
```

## Points d'attention

- Le `name` d'exécution doit être unique → utiliser un ID métier
- `Express Workflows` pour les workflows courts et à fort volume (< 5 min, facturation à l'exécution)
- `Standard Workflows` pour les workflows longs, avec garantie exactly-once
- Doc : https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sfn_state_machine
