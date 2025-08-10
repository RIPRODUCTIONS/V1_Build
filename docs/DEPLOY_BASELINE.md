# Baseline EKS + Self-Healing Deployment

Prereqs:
- AWS account with OIDC role for GitHub Actions (`AWS_OIDC_ROLE_ARN`)
- AWS CLI, kubectl, helm, terraform

What gets deployed:

```
Internet → ALB → [api Service] → api Pods (FastAPI)
                      └─> worker Pods (Celery)
Redis (in-cluster)
Prometheus + Grafana (kube-prometheus-stack)
```

Quickstart:
1) Infra dry run
   cd infra/terraform && terraform init && terraform plan -var-file=envs/example.auto.tfvars

2) (optional) Apply small cluster
   terraform apply -auto-approve -var-file=envs/example.auto.tfvars

3) Connect
   ../../scripts/kube_connect.sh

4) Deploy app + observability
   ../../scripts/deploy_dev.sh

5) Smoke
   ../../scripts/smoke.sh

GuardDuty → WAF auto-block:
- See `backend/app/ops/self_heal/README.md`. Provide WAF IPSet details via Lambda env.

Costs: defaults are minimal (t3.medium spot group for EKS, single Redis Deployment, basic Prometheus stack). Scale up later.
