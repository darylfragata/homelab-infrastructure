output "vpc_id" {
  description = "Optional VPC ID for future serverless workloads."
  value       = module.vpc.vpc_id
}

output "budget_id" {
  description = "ID of the AWS Budget, if enabled. Null in prod - the budget only exists in the dev state (tracks whole-account spend, not per-environment)."
  value       = try(module.budget[0].budget_id, null)
}

output "public_subnet_ids" {
  description = "Public subnet IDs for future serverless workloads."
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs for future serverless workloads."
  value       = module.vpc.public_subnet_ids
}

output "ado_agent_instance_id" {
  description = "ID of the Azure DevOps agent EC2 instance. Null in prod - the agent only exists in the dev state (one physical box shared by both pipeline stages)."
  value       = try(module.ado_agent[0].instance_id, null)
}

output "ado_agent_configure_document_name" {
  description = "Run: aws ssm send-command --document-name <this> --instance-ids <ado_agent_instance_id> --region ap-southeast-1"
  value       = try(module.ado_agent[0].configure_agent_document_name, null)
}

output "ado_agent_mount_data_volume_document_name" {
  description = "Run before ado_agent_configure_document_name on a fresh instance: aws ssm send-command --document-name <this> --instance-ids <ado_agent_instance_id> --region ap-southeast-1"
  value       = try(module.ado_agent[0].mount_data_volume_document_name, null)
}