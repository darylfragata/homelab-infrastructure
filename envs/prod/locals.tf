data "aws_caller_identity" "current" {}

locals {
  static_site = {
    # Account ID suffix guarantees S3's global bucket-name uniqueness without a tfvars entry.
    bucket_name = "${var.project_name}-portfolio-${var.environment}-${data.aws_caller_identity.current.account_id}"
  }
}
