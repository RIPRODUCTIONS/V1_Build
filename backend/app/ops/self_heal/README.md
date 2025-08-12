# GuardDuty → WAF Auto-block Lambda

Production-optional Lambda that auto-adds offending IPs from GuardDuty high-severity findings to a
WAFv2 IPSet for 24h.

Deploy options:

- SAM/CloudFormation inline (fast): provide WAF IPSet ARN/ID via env.
- Terraform module (preferred): wire to GuardDuty event bus.

Env vars:

- `WAF_SCOPE` (REGIONAL/CLOUDFRONT)
- `WAF_IPSET_NAME`, `WAF_IPSET_ID`

Runbook:

1. Create a WAFv2 IPSet (regional), note ID.
2. Deploy Lambda with IAM perms `wafv2:GetIPSet`, `wafv2:UpdateIPSet`.
3. Create EventBridge rule for GuardDuty findings (severity >= 7.0) → target: the Lambda.
4. Test with a sample GuardDuty event.
