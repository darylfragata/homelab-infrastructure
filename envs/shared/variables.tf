variable "project_name" {
  description = "Project name used for resource names and tags."
  type        = string
}

variable "aws_region" {
  description = "AWS region for regional resources."
  type        = string
  default     = "ap-southeast-1"
}

variable "vpc_cidr_block" {
  description = "VPC CIDR block."
  type        = string
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks."
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks."
  type        = list(string)
}

variable "budget_alert_email" {
  description = "Email address to notify when monthly spend crosses the budget threshold. Leave null to skip email notifications."
  type        = string
  default     = null

  validation {
    condition     = var.budget_alert_email == null || can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.budget_alert_email))
    error_message = "Budget alert email must be a valid email address or null."
  }
}

variable "budget_limit_usd" {
  description = "Monthly AWS Budget limit in USD."
  type        = number
  default     = 10

  validation {
    condition     = var.budget_limit_usd > 0
    error_message = "Budget limit must be greater than zero."
  }
}

variable "enable_budget" {
  description = "Whether to create an AWS monthly cost budget."
  type        = bool
  default     = true
}

variable "instance_type" {
  description = "EC2 instance type for the Azure DevOps agent."
  type        = string
}

variable "key_pair_name" {
  description = "Name of an existing AWS EC2 key pair for SSH break-glass access to the ADO agent instance, in case SSM Agent is unavailable. Leave null to launch without one (SSM-only access)."
  type        = string
  default     = null
}

variable "azp_url" {
  description = "Azure DevOps organization URL used to register the self-hosted agent."
  type        = string
  default     = "https://dev.azure.com/df-homelab"
}

variable "azp_pool" {
  description = "Azure DevOps agent pool name to register the agent into."
  type        = string
  default     = "Default"
}

variable "azp_agent_name" {
  description = "Fixed name the agent registers under in the pool."
  type        = string
}

variable "ado_pat_ssm_parameter_name" {
  description = "SSM Parameter Store name (SecureString) holding the Azure DevOps PAT. Also used as the resource name for aws_ssm_parameter.ado_pat, so the IAM read policy and the parameter itself always stay in sync."
  type        = string
}

variable "ado_pat" {
  description = "Azure DevOps Personal Access Token (Agent Pools: Read & manage scope). Supply via TF_VAR_ado_pat or an untracked/secured tfvars file - never commit this value."
  type        = string
  sensitive   = true
}
