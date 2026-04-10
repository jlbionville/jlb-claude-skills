# Référence : Cognito — Auth serverless

## 1. User Pool + App Client — Terraform

```hcl
# auth.tf

resource "aws_cognito_user_pool" "main" {
  name = "${var.project}-${var.application}-users-${var.environment}"

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  auto_verified_attributes = ["email"]

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }

  tags = merge(local.common_tags, {
    Component = "${var.application}-cognito-userpool"
  })
}

resource "aws_cognito_user_pool_client" "app" {
  name         = "${var.project}-${var.application}-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret                      = false   # false pour SPA/mobile
  explicit_auth_flows                  = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  prevent_user_existence_errors        = "ENABLED"
  access_token_validity                = 60       # minutes
  id_token_validity                    = 60
  refresh_token_validity               = 30       # jours

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}
```

## 2. Autorisation API Gateway v2 via Cognito JWT

```hcl
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${var.application}-cognito-authorizer"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.app.id]
    issuer   = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
  }
}

# Appliquer l'authorizer sur une route
resource "aws_apigatewayv2_route" "protected" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /protected"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}
```

## 3. Lire l'identité depuis Lambda (Python)

```python
def lambda_handler(event: dict, context) -> dict:
    # Cognito injecte le contexte JWT dans requestContext
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    user_id = claims["sub"]            # UUID Cognito de l'utilisateur
    email   = claims.get("email", "")
    groups  = claims.get("cognito:groups", "").split(",")
    ...
```

## Points d'attention

- Ne jamais valider le JWT manuellement en Lambda — laisser API Gateway le faire
- `generate_secret = false` pour les apps frontend (SPA, mobile) ; `true` pour server-to-server
- Préférer les **Cognito Groups** pour les rôles (admin, user) plutôt qu'un attribut custom
- Doc : https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cognito_user_pool
