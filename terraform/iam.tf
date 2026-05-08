resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvoke"
        Effect = "Allow"
        Action = "bedrock:InvokeModel"
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:*:590183851235:inference-profile/*"
        ]
      },
      {
        Sid      = "LambdaSelfInvoke"
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.analyzer.arn
      },
      {
        Sid      = "S3Outputs"
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${var.outputs_bucket_arn}/*"
      },
      {
        Sid    = "AssumeRoleClients"
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Resource = [
          aws_iam_role.reader.arn,
          "arn:aws:iam::*:role/infra-explorer-read-only"
        ]
      }
    ]
  })
}

# --- Rol que la Lambda asume para leer infraestructura ---
resource "aws_iam_role" "reader" {
  name = "${var.project_name}-read-only"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda.arn
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "reader_readonly" {
  role       = aws_iam_role.reader.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
