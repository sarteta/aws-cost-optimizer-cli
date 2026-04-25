"""Best-effort list-price estimates for common AWS resources.

This is deliberately small and manually curated. The AWS Pricing API
(`pricing.us-east-1.amazonaws.com`) returns 500+ MB of JSON and requires
its own credentials -- overkill for a ranking tool.

We cover:
- EC2 on-demand Linux hourly rates for the instance families we see most
  (t3, t3a, m5, m5a, m6i, c5, c6i, r5, r6i)
- RDS on-demand MySQL/Postgres hourly rates for db.t3, db.m5, db.r5
- EBS gp3 / gp2 / st1 per GB-month
- NAT Gateway flat hourly
- Elastic IP unassociated hourly
- S3 Standard per GB-month

Numbers are us-east-1 list prices as of 2026-Q1. Other regions have a
~multiplier applied (see REGION_MULTIPLIERS).
"""

from __future__ import annotations

HOURS_PER_MONTH = 730  # AWS billing convention

# -------- EC2 on-demand Linux, us-east-1, $/hour --------
EC2_HOURLY: dict[str, float] = {
    "t3.nano": 0.0052, "t3.micro": 0.0104, "t3.small": 0.0208,
    "t3.medium": 0.0416, "t3.large": 0.0832, "t3.xlarge": 0.1664,
    "t3.2xlarge": 0.3328,
    "t3a.small": 0.0188, "t3a.medium": 0.0376, "t3a.large": 0.0752,
    "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768, "m5.8xlarge": 1.536,
    "m5a.large": 0.086, "m5a.xlarge": 0.172,
    "m6i.large": 0.096, "m6i.xlarge": 0.192, "m6i.2xlarge": 0.384,
    "c5.large": 0.085, "c5.xlarge": 0.17, "c5.2xlarge": 0.34,
    "c5.4xlarge": 0.68,
    "c6i.large": 0.085, "c6i.xlarge": 0.17, "c6i.2xlarge": 0.34,
    "r5.large": 0.126, "r5.xlarge": 0.252, "r5.2xlarge": 0.504,
    "r6i.large": 0.126, "r6i.xlarge": 0.252,
}

# -------- RDS MySQL/Postgres on-demand, us-east-1, $/hour --------
RDS_HOURLY: dict[str, float] = {
    "db.t3.micro": 0.017, "db.t3.small": 0.034, "db.t3.medium": 0.068,
    "db.t3.large": 0.136, "db.t3.xlarge": 0.272,
    "db.m5.large": 0.171, "db.m5.xlarge": 0.342, "db.m5.2xlarge": 0.684,
    "db.m5.4xlarge": 1.368,
    "db.r5.large": 0.24, "db.r5.xlarge": 0.48, "db.r5.2xlarge": 0.96,
}

# -------- EBS, $/GB-month --------
EBS_GB_MONTH: dict[str, float] = {
    "gp3": 0.08, "gp2": 0.10, "st1": 0.045, "sc1": 0.015, "io2": 0.125,
    "standard": 0.05,
}

# -------- Misc --------
NAT_GATEWAY_HOURLY = 0.045       # plus data processing -- we ignore data here
ELASTIC_IP_UNUSED_HOURLY = 0.005
S3_STANDARD_GB_MONTH = 0.023
SNAPSHOT_GB_MONTH = 0.05

# -------- Region multipliers vs us-east-1 (very rough) --------
REGION_MULTIPLIERS: dict[str, float] = {
    "us-east-1": 1.0, "us-east-2": 1.0, "us-west-2": 1.0,
    "us-west-1": 1.05,
    "eu-west-1": 1.05, "eu-central-1": 1.08, "eu-west-2": 1.08,
    "ap-southeast-1": 1.12, "ap-southeast-2": 1.14, "ap-northeast-1": 1.10,
    "sa-east-1": 1.25, "ca-central-1": 1.04,
}


def region_multiplier(region: str) -> float:
    return REGION_MULTIPLIERS.get(region, 1.10)


def ec2_monthly(instance_type: str, region: str) -> float:
    base = EC2_HOURLY.get(instance_type)
    if base is None:
        # Unknown family -- return a safe mid-tier estimate so rank isn't lost
        base = 0.10
    return round(base * HOURS_PER_MONTH * region_multiplier(region), 2)


def rds_monthly(instance_class: str, region: str) -> float:
    base = RDS_HOURLY.get(instance_class, 0.20)
    return round(base * HOURS_PER_MONTH * region_multiplier(region), 2)


def ebs_monthly(volume_type: str, size_gb: int, region: str) -> float:
    rate = EBS_GB_MONTH.get(volume_type, EBS_GB_MONTH["gp3"])
    return round(rate * size_gb * region_multiplier(region), 2)


def snapshot_monthly(size_gb: int, region: str) -> float:
    return round(SNAPSHOT_GB_MONTH * size_gb * region_multiplier(region), 2)


def nat_monthly(region: str) -> float:
    return round(NAT_GATEWAY_HOURLY * HOURS_PER_MONTH * region_multiplier(region), 2)


def eip_unused_monthly(region: str) -> float:
    return round(ELASTIC_IP_UNUSED_HOURLY * HOURS_PER_MONTH * region_multiplier(region), 2)


def s3_standard_monthly(size_gb: float, region: str) -> float:
    return round(S3_STANDARD_GB_MONTH * size_gb * region_multiplier(region), 2)
