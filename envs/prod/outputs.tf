output "vpc_id" {
  description = "VPC ID."
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs."
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs."
  value       = module.vpc.private_subnet_ids
}

output "site_bucket_name" {
  description = "Name of the S3 bucket holding the portfolio site content."
  value       = module.static_site.bucket_name
}

output "site_distribution_id" {
  description = "CloudFront distribution ID for the portfolio site."
  value       = module.static_site.distribution_id
}

output "site_distribution_domain_name" {
  description = "Portfolio site's default CloudFront domain (browse this over HTTPS to verify the site)."
  value       = module.static_site.distribution_domain_name
}
