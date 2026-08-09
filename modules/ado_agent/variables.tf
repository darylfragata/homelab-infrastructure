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
  description = "SSM Parameter Store name (SecureString) holding the Azure DevOps PAT. Also used as the resource name for aws_ssm_parameter.ado_pat, so the IAM read policy and the parameter itself always stay in sync."
  type        = string
}

variable "ado_pat" {
  description = "Azure DevOps Personal Access Token (Agent Pools: Read & manage scope), written into SSM Parameter Store as a SecureString. Supply via TF_VAR_ado_pat or an untracked/secured tfvars file - never commit this value."
  type        = string
  sensitive   = true
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

variable "data_volume_size" {
  description = "Size (GB) of the EBS volume used for agent working data (git checkouts, tfvars, etc)."
  type        = number
  default     = 15
}

variable "data_volume_type" {
  description = "EBS volume type for the agent data volume."
  type        = string
  default     = "gp3"
}

variable "data_volume_device_name" {
  description = "Device name to request from the AWS API for the data volume attachment. Purely an API-level request - on Nitro instances the volume actually shows up as a raw NVMe disk (see mount-data-volume.sh, which detects it directly instead of relying on this name)."
  type        = string
  default     = "/dev/sdf"
}