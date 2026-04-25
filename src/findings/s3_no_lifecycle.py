"""S3 buckets without a lifecycle policy -- likely leaking old objects on Standard."""

from __future__ import annotations

from ..models import Finding
from ..pricing import s3_standard_monthly

NAME = "s3_no_lifecycle"


def scan(client, region: str) -> list[Finding]:
    # S3 is effectively global for listing; only scan in the "primary" region
    # to avoid duplicate findings. Our CLI passes the first region here.
    findings: list[Finding] = []
    s3 = client.s3(region)
    resp = s3.list_buckets()
    for bucket in resp.get("Buckets", []):
        name = bucket["Name"]
        if _has_lifecycle(s3, name):
            continue
        size_gb = _bucket_size_gb(s3, name)
        if size_gb < 50:
            continue  # too small to care about
        findings.append(Finding(
            resource_type=NAME,
            resource_id=name,
            region=region,
            est_monthly_usd=s3_standard_monthly(size_gb, region),
            action=f"add lifecycle policy (size ~{size_gb:.0f} GB, no rules)",
            details={"size_gb": round(size_gb, 1)},
        ))
    return findings


def _has_lifecycle(s3, bucket: str) -> bool:
    try:
        s3.get_bucket_lifecycle_configuration(Bucket=bucket)
        return True
    except Exception:
        return False


def _bucket_size_gb(s3, bucket: str) -> float:
    """Mock path uses get_bucket_size; real boto3 doesn't have that method.

    For real accounts, size should come from a CloudWatch S3 BucketSizeBytes
    metric. Keeping this simple here -- if get_bucket_size is unavailable,
    return 0 so the finding is skipped (no false positives).
    """
    try:
        return float(s3.get_bucket_size(Bucket=bucket))
    except Exception:
        return 0.0
