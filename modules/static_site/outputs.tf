output "bucket_name" {
  description = "Name of the S3 bucket holding the site content."
  value       = aws_s3_bucket.site.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket holding the site content."
  value       = aws_s3_bucket.site.arn
}

output "distribution_id" {
  description = "CloudFront distribution ID."
  value       = aws_cloudfront_distribution.site.id
}

output "distribution_domain_name" {
  description = "CloudFront distribution's default *.cloudfront.net domain name."
  value       = aws_cloudfront_distribution.site.domain_name
}

output "distribution_arn" {
  description = "CloudFront distribution ARN."
  value       = aws_cloudfront_distribution.site.arn
}
