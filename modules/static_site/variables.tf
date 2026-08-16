variable "bucket_name" {
  description = "Globally-unique S3 bucket name for the site content."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "project_name" {
  description = "Project name used for resource names."
  type        = string
}

variable "index_document" {
  description = "S3 key served as the CloudFront default root object."
  type        = string
  default     = "index.html"
}

variable "error_document" {
  description = "S3 key served when CloudFront remaps the private bucket's 403-for-missing-object response. Defaults to the same page as index_document until a dedicated error page exists."
  type        = string
  default     = "index.html"
}

variable "price_class" {
  description = "CloudFront price class controlling which edge locations serve the distribution."
  type        = string
  default     = "PriceClass_100"
}
