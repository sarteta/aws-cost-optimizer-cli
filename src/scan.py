"""CLI entry point.

    python -m src.scan --mock --output reports/demo
    python -m src.scan --profile prod --regions us-east-1,us-west-2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .aws_client import build_client
from .findings import ALL_SCANNERS, s3_no_lifecycle
from .models import ScanResult
from .report import write_reports


def run_scan(*, mock: bool, profile: str | None, regions: list[str],
             output_dir: Path) -> ScanResult:
    client = build_client(mock=mock, profile=profile)
    result = ScanResult(account_id=client.account_id, regions=regions)

    for region in regions:
        for scanner in ALL_SCANNERS:
            # S3 findings only run once (first region) -- S3 listing is global
            if scanner is s3_no_lifecycle and region != regions[0]:
                continue
            try:
                result.findings.extend(scanner.scan(client, region))
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"{scanner.NAME}@{region}: {exc!r}")

    write_reports(result, output_dir)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aws-cost-optimizer",
                                     description="Scan an AWS account for common cost leaks.")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--regions", default="us-east-1",
                        help="Comma-separated region list (default: us-east-1)")
    parser.add_argument("--mock", action="store_true",
                        help="Use synthetic data (no AWS account needed)")
    parser.add_argument("--output", default="reports/latest",
                        help="Output directory for reports")
    args = parser.parse_args(argv)

    regions = [r.strip() for r in args.regions.split(",") if r.strip()]
    result = run_scan(
        mock=args.mock,
        profile=args.profile,
        regions=regions,
        output_dir=Path(args.output),
    )

    print(f"Scanned {len(regions)} region(s) on account {result.account_id or 'unknown'}")
    print(f"Findings: {len(result.findings)}   "
          f"Est. monthly waste: ${result.total_monthly_usd:.2f}")
    if result.errors:
        print(f"Errors: {len(result.errors)}  (see raw.json)", file=sys.stderr)
    print(f"Reports written to: {args.output}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
