module "vpc" {
  source = "../../modules/vpc"

  cidr_block           = var.vpc_cidr_block
  environment          = var.environment
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  project_name         = var.project_name
}

module "budget" {
  source = "../../modules/budget"

  budget_alert_email = var.budget_alert_email
  budget_limit_usd   = var.budget_limit_usd
  enable_budget      = var.enable_budget
  environment        = var.environment
  project_name       = var.project_name
}

module "ado_agent" {
  source = "../../modules/ado_agent"

  name           = local.ec2.name
  ami_id         = local.ec2.ami_id
  instance_type  = local.ec2.instance_type
  key_pair_name  = local.ec2.key_pair_name
  subnet_id      = module.vpc.public_subnet_ids[0]
  security_group = local.ec2.security_group
  vpc_id         = module.vpc.vpc_id

  azp_url                    = var.azp_url
  azp_pool                   = var.azp_pool
  azp_agent_name             = var.azp_agent_name
  ado_pat                    = var.ado_pat
  ado_pat_ssm_parameter_name = var.ado_pat_ssm_parameter_name
}
