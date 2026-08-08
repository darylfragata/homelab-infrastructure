data "aws_caller_identity" "current" {}

locals {

  vpc = {
    cidr_block           = var.vpc_cidr_block
    private_subnet_cidrs = var.private_subnet_cidrs
    public_subnet_cidrs  = var.public_subnet_cidrs
    environment          = var.environment
    project_name         = var.project_name
  }

  budget = {
    budget_alert_email = var.budget_alert_email
    budget_limit_usd   = var.budget_limit_usd
    enable_budget      = var.enable_budget
    environment        = var.environment
    project_name       = var.project_name
  }

  ec2 = {
    name          = "${var.environment}-cicd-agent"
    ami_id        = "ami-03acbba64aef9bf5c" # Ubuntu Server 24.04 LTS (HVM), SSD Volume Type
    instance_type = var.instance_type
    security_group = {
      ingress = [22]
      egress  = [80, 443]
    }
  }

}
