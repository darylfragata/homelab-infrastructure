data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}

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

data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# IAM Policy for S3 Access
resource "aws_iam_policy" "this" {
  name        = "${var.name}-policy"
  description = "Allow S3 access for ADO Agent"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ],
        Resource = [
          "arn:aws:s3:::df-iac-tfstate",
          "arn:aws:s3:::df-iac-tfstate/*",
          "arn:aws:s3:::df-iac-tfvars",
          "arn:aws:s3:::df-iac-tfvars/*"
        ]
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
  name        = "${var.name}-ado-pat-policy"
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

resource "aws_ssm_parameter" "ado_pat" {
  name  = var.ado_pat_ssm_parameter_name
  type  = "SecureString"
  value = var.ado_pat
}

resource "aws_ssm_document" "configure_agent" {
  name            = "configure-${var.name}"
  document_type   = "Command"
  document_format = "JSON"

  content = jsonencode({
    schemaVersion = "2.2"
    description   = "Installs/registers (or re-registers) the Azure Pipelines self-hosted agent on ${var.name}. Invoke on demand via aws ssm send-command; safe to re-run; does not require replacing the instance."
    mainSteps = [{
      action = "aws:runShellScript"
      name   = "configureAdoAgent"
      inputs = {
        timeoutSeconds = "300"
        runCommand = [
          templatefile("${path.module}/configure-agent.sh.tftpl", {
            azp_url                = var.azp_url
            azp_pool               = var.azp_pool
            azp_agent_name         = var.azp_agent_name
            ado_pat_parameter_name = var.ado_pat_ssm_parameter_name
            aws_region             = var.aws_region
          })
        ]
      }
    }]
  })
}

resource "aws_iam_instance_profile" "this" {
  name = "${var.name}-profile"
  role = aws_iam_role.this.name
}

resource "aws_instance" "this" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.this.id]
  iam_instance_profile   = aws_iam_instance_profile.this.name
  user_data              = file("${path.module}/userdata.sh")
  # cloud-init only runs user_data once per instance ID - without this, editing
  # userdata.sh has no effect on an already-running instance (confirmed: AWS
  # accepted the in-place user_data update, but cloud-init never re-executed it).
  # userdata.sh is now just OS bootstrap though, so this should trigger rarely -
  # ADO agent (re)configuration goes through aws_ssm_document.configure_agent
  # instead, which doesn't require replacing the instance.
  user_data_replace_on_change = true

  tags = {
    Name = var.name
  }
}
