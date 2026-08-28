module "vpc" {
  source = "../../modules/vpc"

  cidr_block           = var.vpc_cidr_block
  environment          = var.environment
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  project_name         = var.project_name
}
