data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

resource "aws_s3_bucket" "site" {
  bucket = var.bucket_name

  tags = {
    Name = "${var.environment}-${var.project_name}-portfolio-site"
  }
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket = aws_s3_bucket.site.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "site" {
  bucket = aws_s3_bucket.site.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Placeholder page so the infra is verifiable before the content-deploy pipeline exists (Phase 3).
# ignore_changes keeps a later manual/pipeline upload from being reverted by drift correction.
resource "aws_s3_object" "placeholder_index" {
  bucket       = aws_s3_bucket.site.id
  key          = var.index_document
  content_type = "text/html"
  content      = <<-HTML
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Portfolio - Coming Soon</title>
      </head>
      <body>
        <h1>Portfolio site infrastructure is live.</h1>
        <p>Content deploy pipeline not wired up yet.</p>
      </body>
    </html>
  HTML

  lifecycle {
    ignore_changes = [content, etag, source]
  }
}

resource "aws_cloudfront_origin_access_control" "site" {
  name                              = "${var.environment}-${var.project_name}-portfolio-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "site" {
  enabled             = true
  comment             = "${var.environment}-${var.project_name}-portfolio"
  default_root_object = var.index_document
  price_class         = var.price_class

  origin {
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_id                = aws_s3_bucket.site.id
    origin_access_control_id = aws_cloudfront_origin_access_control.site.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = aws_s3_bucket.site.id
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_optimized.id
  }

  # S3 (behind OAC) returns 403, not 404, for a missing key - remap it so a missing page
  # shows error_document instead of a raw AWS XML error.
  custom_error_response {
    error_code         = 403
    response_code      = 404
    response_page_path = "/${var.error_document}"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.environment}-${var.project_name}-portfolio-cdn"
  }
}

data "aws_iam_policy_document" "site" {
  statement {
    sid     = "AllowCloudFrontServicePrincipal"
    effect  = "Allow"
    actions = ["s3:GetObject"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    resources = ["${aws_s3_bucket.site.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.site.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id
  policy = data.aws_iam_policy_document.site.json
}
