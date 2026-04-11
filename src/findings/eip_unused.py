"""Unassociated Elastic IPs — charged hourly while idle."""

from __future__ import annotations

from ..models import Finding
from ..pricing import eip_unused_monthly

NAME = "eip_unused"


def scan(client, region: str) -> list[Finding]:
    findings: list[Finding] = []
    ec2 = client.ec2(region)
    resp = ec2.describe_addresses()
    for addr in resp.get("Addresses", []):
        if addr.get("AssociationId"):
            continue
        ip = addr.get("PublicIp") or addr.get("AllocationId", "unknown")
        findings.append(Finding(
            resource_type=NAME,
            resource_id=ip,
            region=region,
            est_monthly_usd=eip_unused_monthly(region),
            action="release Elastic IP (not associated)",
            details={"allocation_id": addr.get("AllocationId")},
        ))
    return findings
