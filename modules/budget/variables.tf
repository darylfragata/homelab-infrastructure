variable "budget_alert_email" {
  description = "Email address to notify when spend crosses a budget threshold. Leave null to skip email notifications."
  type        = string
  default     = null
}

variable "budget_limit_usd" {
  description = "Monthly AWS Budget limit in USD."
  type        = number
}

variable "enable_budget" {
  description = "Whether to create the AWS monthly cost budget."
  type        = bool
  default     = true
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "project_name" {
  description = "Project name used for resource names."
  type        = string
}