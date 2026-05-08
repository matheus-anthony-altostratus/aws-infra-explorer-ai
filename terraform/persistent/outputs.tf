output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "frontend_bucket_arn" {
  value = aws_s3_bucket.frontend.arn
}

output "outputs_bucket_name" {
  value = aws_s3_bucket.outputs.bucket
}

output "outputs_bucket_arn" {
  value = aws_s3_bucket.outputs.arn
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.main.domain_name
}
