output "api_gateway_url" {
  value = aws_apigatewayv2_api.main.api_endpoint
}

output "lambda_function_name" {
  value = aws_lambda_function.analyzer.function_name
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.web.id
}

output "cognito_hosted_ui_url" {
  value = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
}

output "dynamodb_accounts_table" {
  value = aws_dynamodb_table.accounts.name
}

output "dynamodb_history_table" {
  value = aws_dynamodb_table.history.name
}
