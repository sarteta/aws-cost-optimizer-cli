"""Oversized RDS instances — low avg CPU over lookback window.

We don't check connection count here (would need Performance Insights or
enhanced monitoring enabled on every instance). CPU alone gives a good
first pass.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models import Finding
from ..pricing import rds_monthly

NAME = "rds_oversized"
CPU_THRESHOLD_PCT = 20.0
LOOKBACK_DAYS = 14


def scan(client, region: str) -> list[Finding]:
    findings: list[Finding] = []
    rds = client.rds(region)
    cw = client.cloudwatch(region)
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=LOOKBACK_DAYS)

    resp = rds.describe_db_instances()
    for db in resp.get("DBInstances", []):
        if db.get("DBInstanceStatus") != "available":
            continue
        db_id = db["DBInstanceIdentifier"]
        klass = db.get("DBInstanceClass", "unknown")

        metrics = cw.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
            StartTime=start,
            EndTime=now,
            Period=3600,
            Statistics=["Average"],
        )
        datapoints = metrics.get("Datapoints", [])
        if not datapoints:
            continue
        avg = sum(d["Average"] for d in datapoints) / len(datapoints)
        if avg > CPU_THRESHOLD_PCT:
            continue

        # Downsize suggestion: naive shift to next-smaller family member
        suggested = _suggest_smaller(klass)
        findings.append(Finding(
            resource_type=NAME,
            resource_id=db_id,
            region=region,
            est_monthly_usd=rds_monthly(klass, region),
            action=f"downsize {klass} → {suggested} (avg CPU {avg:.1f}%)",
            details={
                "current_class": klass,
                "suggested_class": suggested,
                "avg_cpu_pct": round(avg, 2),
                "engine": db.get("Engine"),
            },
        ))
    return findings


_STEP_DOWN = {
    "db.m5.4xlarge": "db.m5.2xlarge",
    "db.m5.2xlarge": "db.m5.xlarge",
    "db.m5.xlarge": "db.m5.large",
    "db.m5.large": "db.t3.large",
    "db.r5.2xlarge": "db.r5.xlarge",
    "db.r5.xlarge": "db.r5.large",
    "db.r5.large": "db.m5.large",
    "db.t3.xlarge": "db.t3.large",
    "db.t3.large": "db.t3.medium",
    "db.t3.medium": "db.t3.small",
}


def _suggest_smaller(klass: str) -> str:
    return _STEP_DOWN.get(klass, klass)
