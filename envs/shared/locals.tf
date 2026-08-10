data "aws_ami_ids" "ubuntu" {
  owners = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-*-*-amd64-server-20260610"]
  }
}

locals {
  environment = "shared"

  vpc = {
    cidr_block           = var.vpc_cidr_block
    private_subnet_cidrs = var.private_subnet_cidrs
    public_subnet_cidrs  = var.public_subnet_cidrs
    project_name         = var.project_name
  }

  budget = {
    budget_alert_email = var.budget_alert_email
    budget_limit_usd   = var.budget_limit_usd
    enable_budget      = var.enable_budget
    project_name       = var.project_name
  }

  ec2 = {
    name          = "ado-cicd-agent"
    ami_id        = data.aws_ami_ids.ubuntu.ids[0]
    instance_type = var.instance_type
    key_pair_name = var.key_pair_name
    security_group = {
      ingress = [22]
      egress  = [80, 443]
    }
  }
}
