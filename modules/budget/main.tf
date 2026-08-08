resource "aws_budgets_budget" "monthly_cost" {
  count = var.enable_budget ? 1 : 0

  name         = "${var.environment}-${var.project_name}-monthly-budget"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = var.budget_alert_email != null ? [60, 70] : []

    content {
      comparison_operator        = "GREATER_THAN"
      notification_type          = notification.value == 70 ? "FORECASTED" : "ACTUAL"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      subscriber_email_addresses = [var.budget_alert_email]
    }
  }
}