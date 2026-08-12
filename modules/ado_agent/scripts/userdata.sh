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

# The ADO agent install (configure_agent) and data volume mount
# (mount_data_volume) are handled by separate SSM documents, invoked on
# demand via `aws ssm send-command` - not here, so they can be re-run
# without replacing the instance.