terraform {
  backend "s3" {}
}

module "vpc" {
  source = "./modules/vpc"

  cidr_block           = local.vpc.cidr_block
  environment          = local.vpc.environment
  private_subnet_cidrs = local.vpc.private_subnet_cidrs
  public_subnet_cidrs  = local.vpc.public_subnet_cidrs
  project_name         = local.vpc.project_name
}

module "budget" {
  source = "./modules/budget"

  budget_alert_email = local.budget.budget_alert_email
  budget_limit_usd   = local.budget.budget_limit_usd
  enable_budget      = local.budget.enable_budget
  environment        = local.budget.environment
  project_name       = local.budget.project_name
}

module "ado_agent" {
  source = "./modules/ado_agent"

  name           = local.ec2.name
  ami_id         = local.ec2.ami_id
  instance_type  = local.ec2.instance_type
  subnet_id      = module.vpc.public_subnet_ids[0]
  security_group = local.ec2.security_group
  vpc_id         = module.vpc.vpc_id

  aws_region                 = var.aws_region
  azp_url                    = var.azp_url
  azp_pool                   = var.azp_pool
  azp_agent_name             = var.azp_agent_name
  ado_pat                    = var.ado_pat
  ado_pat_ssm_parameter_name = var.ado_pat_ssm_parameter_name
}
