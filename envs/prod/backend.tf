terraform {
  backend "s3" {
    bucket       = "df-iac-tfstate"
    key          = "infra/prod/infrastructure.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true
  }
}
