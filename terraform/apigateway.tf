resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.analyzer.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "analyze" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /analyze"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "download" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /download/{analysis_id}/{filename}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "status" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /status/{analysis_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "history" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /history"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "accounts_list" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /accounts"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "accounts_create" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /accounts"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "accounts_update" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "PUT /accounts/{group_id}/{account_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "accounts_delete" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "DELETE /accounts/{group_id}/{account_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "profile_get" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /profiles/{group_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "profile_put" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "PUT /profiles/{group_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "notion" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /notion/{s3_prefix}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}


resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-authorizer"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.web.id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
  }
}
