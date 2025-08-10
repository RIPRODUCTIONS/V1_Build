#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-}
if [[ -z "$HOST" ]]; then
  HOST=$(kubectl get ing -n builder -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')
fi

echo "Testing http://$HOST"
curl -fsS "http://$HOST/healthz"
curl -fsS "http://$HOST/metrics" | grep -E "fastapi|http" >/dev/null
curl -fsS "http://$HOST/automation" || true
