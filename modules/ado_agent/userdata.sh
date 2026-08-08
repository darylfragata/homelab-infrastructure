#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Redirect logs
exec > /var/log/userdata.log 2>&1
 
# Update the system
sudo apt update -y

# Install essential dependencies
sudo apt install -y unzip curl python3-pip python-is-python3 git jq

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify AWS CLI v2 installation
aws --version

# Install Terraform
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update -y
sudo apt install -y terraform

# Verify installations
terraform --version
git --version
python3 --version

# Azure Pipelines agent install/registration is handled separately, on demand,
# via the "configure_agent" SSM Document (see modules/ado_agent/main.tf:
# aws_ssm_document.configure_agent + configure-agent.sh.tftpl). It's invoked
# with `aws ssm send-command` after boot, not baked into user_data - this lets
# the agent be (re)configured without replacing the instance.

# Create a directory for tfvars files and set ownership to the Azure Pipelines agent user
mkdir -p "/home/ubuntu/tfvars"
chown -R "ubuntu:ubuntu" "/home/ubuntu/tfvars"