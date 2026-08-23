data "aws_ami_ids" "ubuntu" {
  owners = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-*-*-amd64-server-20260610"]
  }
}

locals {
  ec2 = {
    name          = "ado-cicd-agent"
    ami_id        = data.aws_ami_ids.ubuntu.ids[0]
    instance_type = var.instance_type
    key_pair_name = var.key_pair_name
    security_group = {
      ingress = [22]
      egress  = [80, 443]
    }
  }
}
