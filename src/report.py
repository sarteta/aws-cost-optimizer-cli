"""Report generation — CSV + Markdown."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import ScanResult


def write_reports(result: ScanResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_actions_csv(result, output_dir / "actions.csv")
    _write_summary_md(result, output_dir / "summary.md")
    _write_raw_json(result, output_dir / "raw.json")


def _write_actions_csv(result: ScanResult, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["rank", "resource_type", "resource_id", "region",
                         "est_monthly_usd", "action"])
        for rank, finding in enumerate(result.ranked(), start=1):
            writer.writerow([rank, finding.resource_type, finding.resource_id,
                             finding.region, finding.est_monthly_usd, finding.action])


def _write_summary_md(result: ScanResult, path: Path) -> None:
    lines: list[str] = []
    lines.append("# AWS cost-optimizer — scan summary")
    lines.append("")
    lines.append(f"- **Account:** `{result.account_id or 'unknown'}`")
    lines.append(f"- **Regions:** {', '.join(result.regions)}")
    lines.append(f"- **Findings:** {len(result.findings)}")
    lines.append(f"- **Estimated total monthly waste:** **${result.total_monthly_usd:.2f}**")
    if result.errors:
        lines.append("")
        lines.append("## Errors during scan")
        for err in result.errors:
            lines.append(f"- `{err}`")

    lines.append("")
    lines.append("## Top findings")
    lines.append("")
    lines.append("| rank | type | id | region | est. $/mo | action |")
    lines.append("|------|------|-----|--------|-----------|--------|")
    for rank, f in enumerate(result.ranked()[:25], start=1):
        lines.append(f"| {rank} | `{f.resource_type}` | `{f.resource_id}` | "
                     f"{f.region} | ${f.est_monthly_usd:.2f} | {f.action} |")

    lines.append("")
    lines.append("## Breakdown by type")
    lines.append("")
    by_type: dict[str, tuple[int, float]] = {}
    for f in result.findings:
        count, total = by_type.get(f.resource_type, (0, 0.0))
        by_type[f.resource_type] = (count + 1, total + f.est_monthly_usd)
    lines.append("| type | count | est. $/mo |")
    lines.append("|------|-------|-----------|")
    for t, (count, total) in sorted(by_type.items(), key=lambda x: -x[1][1]):
        lines.append(f"| `{t}` | {count} | ${total:.2f} |")

    path.write_text("\n".join(lines), encoding="utf-8")


def _write_raw_json(result: ScanResult, path: Path) -> None:
    payload = {
        "account_id": result.account_id,
        "regions": result.regions,
        "total_monthly_usd": result.total_monthly_usd,
        "findings": [f.to_dict() for f in result.ranked()],
        "errors": result.errors,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
