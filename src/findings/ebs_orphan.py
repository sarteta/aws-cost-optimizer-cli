"""Unattached EBS volumes -- billed for storage even though nothing uses them."""

from __future__ import annotations

from ..models import Finding
from ..pricing import ebs_monthly

NAME = "ebs_orphan"


def scan(client, region: str) -> list[Finding]:
    findings: list[Finding] = []
    ec2 = client.ec2(region)
    resp = ec2.describe_volumes()
    for vol in resp.get("Volumes", []):
        if vol.get("State") != "available":
            continue  # in-use, skip
        if vol.get("Attachments"):
            continue
        vid = vol["VolumeId"]
        size = int(vol.get("Size", 0))
        vtype = vol.get("VolumeType", "gp3")
        findings.append(Finding(
            resource_type=NAME,
            resource_id=vid,
            region=region,
            est_monthly_usd=ebs_monthly(vtype, size, region),
            action=f"delete (unattached {vtype} volume, {size} GB)",
            details={"size_gb": size, "volume_type": vtype},
        ))
    return findings
