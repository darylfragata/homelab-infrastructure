variable "name" {
  description = "Name used for the EC2 instance and related resources (security group, IAM role/profile)."
  type        = string
}

variable "ami_id" {
  description = "The ID of the AMI to use for the EC2 instance."
  type        = string
}

variable "instance_type" {
  description = "The type of instance to use for the EC2 instance."
  type        = string
  default     = "t3.micro"
}

variable "vpc_id" {
  description = "The ID of the VPC to deploy the security group in."
  type        = string
}

variable "subnet_id" {
  description = "The ID of the subnet to launch the EC2 instance in. Must belong to var.vpc_id."
  type        = string
}

variable "security_group" {
  description = "Ingress/egress ports to allow on the instance's security group."
  type = object({
    ingress = list(number)
    egress  = list(number)
  })
}

variable "ado_pat_ssm_parameter_name" {
  description = "SSM Parameter Store name (SecureString) holding the Azure DevOps PAT. Managed out-of-band via `aws ssm put-parameter`, not by Terraform (see ADR-002 in homelab-documentation). Also used as the name for data.aws_ssm_parameter.ado_pat and the IAM read policy's resource ARN, so they stay in sync."
  type        = string
}

variable "azp_url" {
  description = "Azure DevOps organization URL used by configure-agent.sh.tftpl to register the self-hosted agent (e.g. https://dev.azure.com/<org>)."
  type        = string
}

variable "azp_pool" {
  description = "Azure DevOps agent pool name the instance registers into."
  type        = string
}

variable "azp_agent_name" {
  description = "Fixed name the agent registers under in the pool."
  type        = string
}