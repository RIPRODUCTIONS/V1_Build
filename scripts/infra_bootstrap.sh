#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../infra/terraform"
terraform init -backend=false
terraform plan -var-file=envs/example.auto.tfvars
