# ---- Data sources ----
data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}

# ---- Networking ----
resource "aws_security_group" "this" {
  name        = "${var.name}-sg"
  description = "${var.name} security group"
  vpc_id      = var.vpc_id

  # A rename forces replacement. Without this, Terraform tries to delete the
  # old SG before the instance is repointed at a new one, which AWS refuses
  # (DependencyViolation) since it's still attached to the running instance's
  # ENI - the provider then retries the delete indefinitely. create_before_destroy
  # ensures the new SG exists and the instance is updated first.
  lifecycle {
    create_before_destroy = true
  }

  dynamic "ingress" {
    for_each = var.security_group.ingress
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  dynamic "egress" {
    for_each = var.security_group.egress
    content {
      from_port   = egress.value
      to_port     = egress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}

# ---- IAM ----
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# IAM Policy for Azure DevOps self-hosted agent.
resource "aws_iam_policy" "this" {
  name        = "${var.name}-pipeline-policy"
  description = "IAM permissions for Azure DevOps self-hosted agent"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "ec2:*",
          "lambda:*",
          "iam:*",
          "s3:*",
          "dynamodb:*",
          "sqs:*",
          "events:*",
          "logs:*",
          "ssm:*",
          "cloudwatch:*",
          "sns:*",
          "ses:*",
          "acm:*",
          "cloudfront:*",
          "route53:*",
          "budgets:*",
          "kms:ListAliases",
          "kms:DescribeKey"
        ]

        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "this" {
  name               = "${var.name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.this.arn
}

# Lets configure-agent.sh.tftpl (run via aws_ssm_document.configure_agent) fetch the
# Azure DevOps PAT from SSM Parameter Store instead of embedding it in plaintext.
resource "aws_iam_policy" "ado_pat" {
  name        = "${var.name}-ssm-policy"
  description = "Allow reading the Azure DevOps PAT SecureString parameter for unattended agent registration"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["ssm:GetParameter"],
        Resource = "arn:aws:ssm:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:parameter${var.ado_pat_ssm_parameter_name}"
      },
      {
        Effect   = "Allow",
        Action   = ["kms:Decrypt"],
        Resource = data.aws_kms_alias.ssm.target_key_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ado_pat" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.ado_pat.arn
}

resource "aws_iam_instance_profile" "this" {
  name = "${var.name}-profile"
  role = aws_iam_role.this.name
}

# ---- SSM Parameter (Azure DevOps PAT) ----
resource "aws_ssm_parameter" "ado_pat" {
  name  = var.ado_pat_ssm_parameter_name
  type  = "SecureString"
  value = var.ado_pat
}

# ---- EC2 instance ----
resource "aws_instance" "this" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.this.id]
  iam_instance_profile   = aws_iam_instance_profile.this.name
  key_name               = var.key_pair_name
  user_data              = file("${path.module}/scripts/userdata.sh")
  # cloud-init only runs user_data once per instance ID - without this, editing
  # userdata.sh has no effect on an already-running instance (confirmed: AWS
  # accepted the in-place user_data update, but cloud-init never re-executed it).
  # userdata.sh is now just OS bootstrap though, so this should trigger rarely -
  # ADO agent (re)configuration and data volume mounting go through the SSM
  # documents below instead, neither of which require replacing the instance.
  user_data_replace_on_change = true

  tags = {
    Name = var.name
  }
}

# ---- Data volume ----
# Standalone (not inline ebs_block_device) so it survives instance replacement -
# Terraform detaches/reattaches it instead of recreating it.
resource "aws_ebs_volume" "data" {
  availability_zone = aws_instance.this.availability_zone
  size              = var.data_volume_size
  type              = var.data_volume_type

  tags = {
    Name = "${var.name}-data"
  }
}

resource "aws_volume_attachment" "data" {
  device_name = var.data_volume_device_name
  volume_id   = aws_ebs_volume.data.id
  instance_id = aws_instance.this.id

  # The agent service runs out of a directory symlinked onto this volume
  # (see mount-data-volume.sh), so the guest OS never releases it cleanly on
  # its own - detaching while the instance is running gets stuck "busy".
  # Stopping the instance first forces a clean shutdown/unmount instead.
  stop_instance_before_detaching = true
}

# ---- SSM Documents ----
# Both are invoked on demand via `aws ssm send-command`, safe to re-run, and
# never require replacing the instance. mount_data_volume must be run before
# configure_agent (configure-agent.sh.tftpl checks for this and fails fast
# with instructions if the data volume isn't mounted yet).

# Formats (if needed) and mounts the data volume, separate from configure_agent
# so it can be (re)run independently - e.g. after the volume is resized/replaced,
# or to pick up mount-data-volume.sh.tftpl changes - without touching userdata.sh
# or replacing the instance.
resource "aws_ssm_document" "mount_data_volume" {
  name            = "mount-data-volume-${var.name}"
  document_type   = "Command"
  document_format = "JSON"

  content = jsonencode({
    schemaVersion = "2.2"
    description   = "Formats (if needed) and mounts the ${var.name} data volume at /mnt/ado-data, symlinking the agent's working directories onto it. Invoke on demand via aws ssm send-command; safe to re-run; does not require replacing the instance."
    mainSteps = [{
      action = "aws:runShellScript"
      name   = "mountDataVolume"
      inputs = {
        timeoutSeconds = "180"
        runCommand = [
          file("${path.module}/scripts/mount-data-volume.sh")
        ]
      }
    }]
  })
}

resource "aws_ssm_document" "configure_agent" {
  name            = "configure-${var.name}"
  document_type   = "Command"
  document_format = "JSON"

  content = jsonencode({
    schemaVersion = "2.2"
    description   = "Installs/registers (or re-registers) the Azure Pipelines self-hosted agent on ${var.name}. Invoke on demand via aws ssm send-command; safe to re-run; does not require replacing the instance. Requires mount_data_volume to have been run first."
    mainSteps = [{
      action = "aws:runShellScript"
      name   = "configureAdoAgent"
      inputs = {
        timeoutSeconds = "300"
        runCommand = [
          templatefile("${path.module}/scripts/configure-agent.sh.tftpl", {
            azp_url                = var.azp_url
            azp_pool               = var.azp_pool
            azp_agent_name         = var.azp_agent_name
            ado_pat_parameter_name = var.ado_pat_ssm_parameter_name
            aws_region             = data.aws_region.current.region
          })
        ]
      }
    }]
  })
}
