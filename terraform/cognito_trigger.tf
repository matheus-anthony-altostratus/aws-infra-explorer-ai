data "archive_file" "cognito_presignup" {
  type        = "zip"
  output_path = "${path.module}/cognito_presignup.zip"

  source {
    content  = file("${path.root}/../src/cognito_presignup/handler.py")
    filename = "handler.py"
  }
}

resource "aws_lambda_function" "cognito_presignup" {
  function_name = "${var.project_name}-cognito-presignup"
  role          = aws_iam_role.cognito_trigger.arn
  handler       = "handler.handler"
  runtime       = "python3.12"
  timeout       = 5

  filename         = data.archive_file.cognito_presignup.output_path
  source_code_hash = data.archive_file.cognito_presignup.output_base64sha256
}

resource "aws_iam_role" "cognito_trigger" {
  name = "${var.project_name}-cognito-trigger-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cognito_trigger_logs" {
  role       = aws_iam_role.cognito_trigger.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permiso para que Cognito invoque la Lambda
resource "aws_lambda_permission" "cognito_presignup" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_presignup.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}
