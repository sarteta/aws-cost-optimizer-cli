from src.aws_client import MockClient
from src.findings import ec2_idle, ebs_orphan, ebs_snapshot_old, eip_unused, nat_dev, rds_oversized, s3_no_lifecycle


def test_ec2_idle_finds_the_idle_bastion():
    client = MockClient()
    findings = ec2_idle.scan(client, "us-east-1")
    ids = [f.resource_id for f in findings]
    assert "i-bastion" in ids
    assert "i-prod001" not in ids  # prod CPU is >30%


def test_ec2_idle_respects_stopped_state():
    client = MockClient()
    findings = ec2_idle.scan(client, "us-east-1")
    assert "i-stopped" not in [f.resource_id for f in findings]


def test_ebs_orphan_detects_unattached():
    client = MockClient()
    findings = ebs_orphan.scan(client, "us-east-1")
    ids = [f.resource_id for f in findings]
    assert "vol-orphan1" in ids
    assert "vol-orphan2" in ids
    assert "vol-prod" not in ids


def test_ebs_snapshot_old_only_flags_old_ones():
    client = MockClient()
    findings = ebs_snapshot_old.scan(client, "us-east-1")
    ids = [f.resource_id for f in findings]
    assert "snap-ancient" in ids
    assert "snap-recent" not in ids  # 7 days old


def test_eip_unused_flags_both_idle():
    client = MockClient()
    findings = eip_unused.scan(client, "us-east-1")
    ips = [f.resource_id for f in findings]
    assert "3.210.2.2" in ips
    assert "3.210.3.3" in ips
    assert "3.210.1.1" not in ips  # associated


def test_nat_dev_only_flags_nonprod():
    client = MockClient()
    e_findings = nat_dev.scan(client, "us-east-1")
    w_findings = nat_dev.scan(client, "us-west-2")
    assert not e_findings                               # prod NAT stays
    assert len(w_findings) == 1 and w_findings[0].resource_id == "nat-dev"


def test_rds_oversized_flags_low_cpu():
    client = MockClient()
    findings = rds_oversized.scan(client, "us-east-1")
    ids = [f.resource_id for f in findings]
    assert "prod-legacy" in ids          # avg CPU ~9%
    assert "reports-readrep" not in ids  # CPU ~60%


def test_rds_downsize_suggestion_is_sensible():
    client = MockClient()
    findings = rds_oversized.scan(client, "us-east-1")
    legacy = [f for f in findings if f.resource_id == "prod-legacy"][0]
    assert legacy.details["suggested_class"] == "db.m5.large"


def test_s3_flags_buckets_without_lifecycle():
    client = MockClient()
    findings = s3_no_lifecycle.scan(client, "us-east-1")
    names = [f.resource_id for f in findings]
    assert "old-backups-2022" in names
    assert "temp-exports-forgotten" in names
    assert "prod-app-assets" not in names
