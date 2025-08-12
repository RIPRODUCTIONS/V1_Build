from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import boto3


def _now() -> datetime:
    return datetime.now(tz=UTC)


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    waf = boto3.client('wafv2')
    scope = os.getenv('WAF_SCOPE', 'REGIONAL')
    ipset_name = os.getenv('WAF_IPSET_NAME', 'guardduty-autoblock')
    ipset_id = os.getenv('WAF_IPSET_ID', '')  # TODO: supply via env/stack
    # optional concurrency lock token env not used; left for future extension

    findings = event.get('detail', {}).get('service', {}).get('action', {})
    src_ip = findings.get('networkConnectionAction', {}).get('remoteIpDetails', {}).get(
        'ipAddressV4'
    ) or findings.get('portProbeAction', {}).get('portProbeDetails', [{}])[0].get(
        'remoteIpDetails', {}
    ).get('ipAddressV4')
    if not src_ip:
        return {'status': 'skipped', 'reason': 'no ip'}

    resp = waf.get_ip_set(Name=ipset_name, Scope=scope, Id=ipset_id)
    addresses: list[str] = resp['IPSet']['Addresses']
    lock_token: str = resp['LockToken']
    cidr = f'{src_ip}/32'
    if cidr not in addresses:
        addresses.append(cidr)

    waf.update_ip_set(
        Name=ipset_name,
        Scope=scope,
        Id=ipset_id,
        Addresses=addresses,
        LockToken=lock_token,
    )
    # Expiration tracking can be done via DynamoDB or tag; left as exercise
    return {'status': 'updated', 'ip': src_ip}
