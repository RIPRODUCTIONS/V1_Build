#!/usr/bin/env bash
set -euo pipefail
REGION=${REGION:-us-west-2}
CLUSTER=${CLUSTER:-self-healing-mvp}
aws eks update-kubeconfig --name "$CLUSTER" --region "$REGION"
