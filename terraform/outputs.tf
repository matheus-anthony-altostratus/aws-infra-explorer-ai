output "api_gateway_url" {
  value = aws_apigatewayv2_api.main.api_endpoint
}

output "lambda_function_name" {
  value = aws_lambda_function.analyzer.function_name
}
