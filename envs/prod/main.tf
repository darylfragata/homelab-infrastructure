terraform {
  backend "s3" {
    bucket       = "df-iac-tfstate"
    key          = "infra/prod/infrastructure.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true
  }
}

module "vpc" {
  source = "../../modules/vpc"

  cidr_block           = var.vpc_cidr_block
  environment          = local.environment
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  project_name         = var.project_name
}
