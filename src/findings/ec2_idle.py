"""Flag running EC2 instances whose average CPU is below a threshold."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models import Finding
from ..pricing import ec2_monthly

NAME = "ec2_idle"
CPU_THRESHOLD_PCT = 5.0
LOOKBACK_DAYS = 14


def scan(client, region: str) -> list[Finding]:
    findings: list[Finding] = []
    ec2 = client.ec2(region)
    cw = client.cloudwatch(region)

    resp = ec2.describe_instances()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=LOOKBACK_DAYS)

    for res in resp.get("Reservations", []):
        for inst in res.get("Instances", []):
            if inst.get("State", {}).get("Name") != "running":
                continue
            iid = inst["InstanceId"]
            itype = inst.get("InstanceType", "unknown")

            metrics = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": iid}],
                StartTime=start,
                EndTime=now,
                Period=3600,
                Statistics=["Average"],
            )
            datapoints = metrics.get("Datapoints", [])
            if not datapoints:
                # No data → can't claim idle, skip
                continue
            avg_cpu = sum(d["Average"] for d in datapoints) / len(datapoints)
            if avg_cpu > CPU_THRESHOLD_PCT:
                continue

            name = _tag(inst, "Name") or iid
            findings.append(Finding(
                resource_type=NAME,
                resource_id=iid,
                region=region,
                est_monthly_usd=ec2_monthly(itype, region),
                action=f"stop or rightsize (avg CPU {avg_cpu:.1f}% over {LOOKBACK_DAYS}d)",
                details={
                    "instance_type": itype,
                    "avg_cpu_pct": round(avg_cpu, 2),
                    "name": name,
                    "launched": inst.get("LaunchTime").isoformat() if inst.get("LaunchTime") else None,
                },
            ))
    return findings


def _tag(inst: dict, key: str) -> str | None:
    for t in inst.get("Tags", []) or []:
        if t.get("Key") == key:
            return t.get("Value")
    return None
