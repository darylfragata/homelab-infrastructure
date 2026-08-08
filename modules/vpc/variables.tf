variable "project_name" {
  description = "Project name used for resource names."
  type        = string
}

variable "cidr_block" {
  description = "VPC CIDR block."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks used only when enable_vpc is true."
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks used only when enable_vpc is true."
  type        = list(string)
}