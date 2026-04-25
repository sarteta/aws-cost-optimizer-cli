"""NAT gateways in dev/staging VPCs -- often forgotten, ~$32-40/mo each."""

from __future__ import annotations

from ..models import Finding
from ..pricing import nat_monthly

NAME = "nat_dev"
NONPROD_ENV_TAG_VALUES = {"dev", "development", "staging", "stage", "test", "qa", "sandbox"}


def scan(client, region: str) -> list[Finding]:
    findings: list[Finding] = []
    ec2 = client.ec2(region)
    resp = ec2.describe_nat_gateways()
    for gw in resp.get("NatGateways", []):
        if gw.get("State") != "available":
            continue
        env = _tag_value(gw.get("Tags", []), "Env") or _tag_value(gw.get("Tags", []), "Environment")
        if not env:
            continue
        if env.lower() not in NONPROD_ENV_TAG_VALUES:
            continue
        findings.append(Finding(
            resource_type=NAME,
            resource_id=gw["NatGatewayId"],
            region=region,
            est_monthly_usd=nat_monthly(region),
            action=f"evaluate removal -- non-prod VPC (Env={env})",
            details={"env": env},
        ))
    return findings


def _tag_value(tags: list[dict], key: str) -> str | None:
    for t in tags or []:
        if t.get("Key") == key:
            return t.get("Value")
    return None
