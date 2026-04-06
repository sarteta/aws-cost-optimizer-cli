"""Data models for the scanner output.

We keep findings as plain dataclasses (no ORM / no persistence layer —
reports are regenerated from a fresh scan every time) and serialize them
to JSON via `dataclasses.asdict`.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Finding:
    """A single cost-leak finding.

    `resource_type` is a short string like ``ec2_idle``, ``ebs_orphan``,
    ``rds_oversized`` — it maps 1:1 to the module under
    ``src/findings/`` that produced it.

    `est_monthly_usd` is a best-effort list-price estimate. It does NOT
    account for RIs/Savings Plans. It exists to rank findings, not to
    quote exact savings.
    """

    resource_type: str
    resource_id: str
    region: str
    est_monthly_usd: float
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    discovered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanResult:
    """Aggregate of a single scan run."""

    account_id: str | None
    regions: list[str]
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total_monthly_usd(self) -> float:
        return round(sum(f.est_monthly_usd for f in self.findings), 2)

    def ranked(self) -> list[Finding]:
        """Findings sorted by estimated monthly cost, descending."""
        return sorted(self.findings, key=lambda f: f.est_monthly_usd, reverse=True)
