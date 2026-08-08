output "instance_id" {
  value = aws_instance.this.id
}

output "public_ip" {
  value = aws_instance.this.public_ip
}

output "security_group_id" {
  value = aws_security_group.this.id
}

output "iam_role_arn" {
  value = aws_iam_role.this.arn
}

output "configure_agent_document_name" {
  description = "SSM Document name to invoke via `aws ssm send-command` to (re)configure/register the ADO agent on this instance."
  value       = aws_ssm_document.configure_agent.name
}
