"""Each module in this package detects one class of cost leak.

They all expose a single function ``scan(client, region) -> list[Finding]``
so the orchestrator in ``src/scan.py`` can dispatch uniformly.
"""

from . import ec2_idle, ebs_orphan, ebs_snapshot_old, eip_unused, nat_dev, rds_oversized, s3_no_lifecycle

ALL_SCANNERS = [
    ec2_idle,
    ebs_orphan,
    ebs_snapshot_old,
    eip_unused,
    nat_dev,
    rds_oversized,
    s3_no_lifecycle,
]
