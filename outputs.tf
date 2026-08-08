output "vpc_id" {
  description = "Optional VPC ID for future serverless workloads."
  value       = module.vpc.vpc_id
}

output "budget_id" {
  description = "ID of the AWS Budget, if enabled."
  value       = module.budget.budget_id
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
  description = "ID of the Azure DevOps agent EC2 instance."
  value       = module.ado_agent.instance_id
}

output "ado_agent_configure_document_name" {
  description = "Run: aws ssm send-command --document-name <this> --instance-ids <ado_agent_instance_id> --region ap-southeast-1"
  value       = module.ado_agent.configure_agent_document_name
}