variable "aws_region" {
  default = "eu-west-1"
}

variable "project_name" {
  default = "infra-explorer"
}

variable "environment" {
  default = "sandbox"
}

# Estos los sacas del output del stack persistent
variable "outputs_bucket_name" {
  description = "Nombre del bucket S3 de outputs (del stack persistent)"
  type        = string
}

variable "outputs_bucket_arn" {
  description = "ARN del bucket S3 de outputs (del stack persistent)"
  type        = string
}
