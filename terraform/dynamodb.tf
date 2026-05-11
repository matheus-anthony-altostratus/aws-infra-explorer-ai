resource "aws_dynamodb_table" "accounts" {
  name         = "${var.project_name}-accounts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "group_id"
  range_key    = "account_id"

  attribute {
    name = "group_id"
    type = "S"
  }

  attribute {
    name = "account_id"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "history" {
  name         = "${var.project_name}-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "analysis_id"
  range_key    = "timestamp"

  attribute {
    name = "analysis_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}
