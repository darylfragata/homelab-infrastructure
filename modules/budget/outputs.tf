output "budget_id" {
  description = "ID of the AWS Budget."
  value       = try(aws_budgets_budget.monthly_cost[0].id, null)
}

output "budget_name" {
  description = "Name of the AWS Budget."
  value       = try(aws_budgets_budget.monthly_cost[0].name, null)
}