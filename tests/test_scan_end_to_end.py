import csv
import json
from pathlib import Path

from src.scan import run_scan


def test_end_to_end_mock_scan(tmp_path: Path):
    out = tmp_path / "report"
    result = run_scan(
        mock=True,
        profile=None,
        regions=["us-east-1", "us-west-2"],
        output_dir=out,
    )
    assert result.account_id == "123456789012"
    assert result.total_monthly_usd > 0
    assert (out / "actions.csv").exists()
    assert (out / "summary.md").exists()
    assert (out / "raw.json").exists()

    # CSV has at least one row, ordered by desc cost
    with (out / "actions.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 6
    costs = [float(r["est_monthly_usd"]) for r in rows]
    assert costs == sorted(costs, reverse=True)

    # JSON round-trip
    payload = json.loads((out / "raw.json").read_text())
    assert payload["account_id"] == "123456789012"
    assert len(payload["findings"]) == len(result.findings)


def test_scan_returns_all_finding_types(tmp_path: Path):
    result = run_scan(
        mock=True, profile=None, regions=["us-east-1", "us-west-2"],
        output_dir=tmp_path / "r",
    )
    types = {f.resource_type for f in result.findings}
    # Every scanner should produce at least one finding against the mock account
    assert {"ec2_idle", "ebs_orphan", "ebs_snapshot_old", "eip_unused",
            "nat_dev", "rds_oversized", "s3_no_lifecycle"} <= types
