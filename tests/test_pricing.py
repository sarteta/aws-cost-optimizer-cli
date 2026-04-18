from src.pricing import (
    ec2_monthly,
    rds_monthly,
    ebs_monthly,
    nat_monthly,
    eip_unused_monthly,
    region_multiplier,
    HOURS_PER_MONTH,
)


def test_ec2_monthly_known_type():
    # m5.xlarge @ 0.192/h * 730 = 140.16 in us-east-1
    assert abs(ec2_monthly("m5.xlarge", "us-east-1") - round(0.192 * HOURS_PER_MONTH, 2)) < 0.01


def test_ec2_monthly_unknown_falls_back():
    # Unknown type uses $0.10/h fallback
    val = ec2_monthly("zz.weirdtype", "us-east-1")
    assert val == round(0.10 * HOURS_PER_MONTH, 2)


def test_region_multiplier_sa_east_is_expensive():
    assert region_multiplier("sa-east-1") > region_multiplier("us-east-1")


def test_rds_monthly_uses_multiplier():
    base = rds_monthly("db.m5.xlarge", "us-east-1")
    multi = rds_monthly("db.m5.xlarge", "sa-east-1")
    assert multi > base


def test_ebs_monthly_scales_with_size():
    a = ebs_monthly("gp3", 100, "us-east-1")
    b = ebs_monthly("gp3", 500, "us-east-1")
    assert abs(b - a * 5) < 0.01


def test_nat_monthly_nontrivial():
    assert nat_monthly("us-east-1") > 30.0


def test_eip_monthly_small_but_nonzero():
    v = eip_unused_monthly("us-east-1")
    assert 3.0 < v < 5.0
