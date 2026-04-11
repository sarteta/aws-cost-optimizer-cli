"""Old EBS snapshots (>90 days).

We flag ALL snapshots older than the threshold — the action is "review &
delete if parent volume is gone or backup policy doesn't require it."
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models import Finding
from ..pricing import snapshot_monthly

NAME = "ebs_snapshot_old"
AGE_DAYS = 90


def scan(client, region: str) -> list[Finding]:
    findings: list[Finding] = []
    ec2 = client.ec2(region)
    cutoff = datetime.now(timezone.utc) - timedelta(days=AGE_DAYS)

    resp = ec2.describe_snapshots(OwnerIds=["self"])
    for snap in resp.get("Snapshots", []):
        start_time = snap.get("StartTime")
        if not start_time or start_time > cutoff:
            continue
        age_days = (datetime.now(timezone.utc) - start_time).days
        size = int(snap.get("VolumeSize", 0))
        findings.append(Finding(
            resource_type=NAME,
            resource_id=snap["SnapshotId"],
            region=region,
            est_monthly_usd=snapshot_monthly(size, region),
            action=f"review & delete (age {age_days}d, {size} GB)",
            details={
                "size_gb": size,
                "age_days": age_days,
                "description": snap.get("Description", ""),
            },
        ))
    return findings
