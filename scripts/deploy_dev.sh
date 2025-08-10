#!/usr/bin/env bash
set -euo pipefail
DIR="$(dirname "$0")/.."

# Build images locally if KIND=true
KIND=${KIND:-}
TAG=${TAG:-dev}
REGION=${REGION:-us-west-2}
ACCOUNT_ID=${ACCOUNT_ID:-}

if [[ -n "$KIND" ]]; then
  echo "Loading images into kind... (placeholder)"
else
  if [[ -z "$ACCOUNT_ID" ]]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  fi
  API_IMG="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/builder-api:$TAG"
  WRK_IMG="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/builder-worker:$TAG"
  echo "Using images: $API_IMG, $WRK_IMG"
fi

kubectl apply -k "$DIR/deploy/k8s/overlays/dev"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace builder --create-namespace \
  -f "$DIR/deploy/observability/kube-prometheus-stack/values.yaml"

ING=$(kubectl get ing -n builder -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')
echo "Ingress hostname: $ING"
