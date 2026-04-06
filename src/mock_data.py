"""Synthetic AWS account used by MockClient.

The shape of the responses mirrors boto3's so findings code is identical
between real and mock runs. The account has a deliberate mix of leaks
so the full scan pipeline gets exercised.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _iso(days_ago: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


def build_mock_account() -> dict:
    """Return a nested dict of {service: {method: fn(region, **kwargs)}}."""

    # --- EC2 data ---
    ec2_instances = {
        "us-east-1": [
            # Legit production instance
            {"InstanceId": "i-prod001", "InstanceType": "c5.xlarge",
             "State": {"Name": "running"}, "LaunchTime": _iso(420),
             "Tags": [{"Key": "Env", "Value": "prod"}]},
            # Idle bastion, huge
            {"InstanceId": "i-bastion", "InstanceType": "c5.2xlarge",
             "State": {"Name": "running"}, "LaunchTime": _iso(800),
             "Tags": [{"Key": "Name", "Value": "legacy-bastion"}]},
            # Stopped — we ignore these
            {"InstanceId": "i-stopped", "InstanceType": "m5.large",
             "State": {"Name": "stopped"}, "LaunchTime": _iso(90),
             "Tags": []},
        ],
        "us-west-2": [
            # Forgotten dev box
            {"InstanceId": "i-devbox", "InstanceType": "m5.xlarge",
             "State": {"Name": "running"}, "LaunchTime": _iso(200),
             "Tags": [{"Key": "Env", "Value": "dev"}, {"Key": "Owner", "Value": "(none)"}]},
        ],
    }

    # CloudWatch CPU metrics — key = (region, instance_id)
    cw_cpu: dict[tuple[str, str], list[dict]] = {
        ("us-east-1", "i-prod001"): [{"Average": 38.0}, {"Average": 42.0}, {"Average": 45.0}],
        ("us-east-1", "i-bastion"): [{"Average": 0.4}, {"Average": 0.8}, {"Average": 1.1}],
        ("us-west-2", "i-devbox"): [{"Average": 2.0}, {"Average": 1.5}, {"Average": 2.8}],
    }

    # --- EBS volumes ---
    ebs_volumes = {
        "us-east-1": [
            {"VolumeId": "vol-prod", "State": "in-use", "Size": 200,
             "VolumeType": "gp3", "Attachments": [{"InstanceId": "i-prod001"}]},
            {"VolumeId": "vol-orphan1", "State": "available", "Size": 500,
             "VolumeType": "gp3", "Attachments": []},
            {"VolumeId": "vol-orphan2", "State": "available", "Size": 100,
             "VolumeType": "gp2", "Attachments": []},
        ],
        "us-west-2": [
            {"VolumeId": "vol-devprod", "State": "in-use", "Size": 50,
             "VolumeType": "gp3", "Attachments": [{"InstanceId": "i-devbox"}]},
        ],
    }

    # --- Snapshots (old, parent volume gone) ---
    ebs_snapshots = {
        "us-east-1": [
            {"SnapshotId": "snap-ancient", "VolumeSize": 250,
             "StartTime": _iso(540), "Description": "backup of vol-gonelong-ago"},
            {"SnapshotId": "snap-recent", "VolumeSize": 100,
             "StartTime": _iso(7), "Description": "daily backup"},
        ],
        "us-west-2": [],
    }

    # --- Elastic IPs ---
    elastic_ips = {
        "us-east-1": [
            {"PublicIp": "3.210.1.1", "AssociationId": "eipassoc-xxx"},   # associated, fine
            {"PublicIp": "3.210.2.2"},                                      # unassociated → leak
            {"PublicIp": "3.210.3.3"},                                      # unassociated → leak
        ],
        "us-west-2": [],
    }

    # --- NAT gateways ---
    nat_gateways = {
        "us-east-1": [
            {"NatGatewayId": "nat-prod", "State": "available",
             "Tags": [{"Key": "Env", "Value": "prod"}]},
        ],
        "us-west-2": [
            {"NatGatewayId": "nat-dev", "State": "available",
             "Tags": [{"Key": "Env", "Value": "dev"}]},
        ],
    }

    # --- RDS ---
    rds_instances = {
        "us-east-1": [
            {"DBInstanceIdentifier": "prod-legacy", "DBInstanceClass": "db.m5.xlarge",
             "DBInstanceStatus": "available", "Engine": "postgres"},
            {"DBInstanceIdentifier": "reports-readrep", "DBInstanceClass": "db.t3.medium",
             "DBInstanceStatus": "available", "Engine": "postgres"},
        ],
        "us-west-2": [],
    }
    rds_cpu = {
        ("us-east-1", "prod-legacy"): [{"Average": 8.0}, {"Average": 11.0}, {"Average": 9.0}],
        ("us-east-1", "reports-readrep"): [{"Average": 55.0}, {"Average": 62.0}],
    }

    # --- S3 ---
    s3_buckets = [
        {"Name": "prod-app-assets", "CreationDate": _iso(900)},
        {"Name": "old-backups-2022", "CreationDate": _iso(1100)},
        {"Name": "temp-exports-forgotten", "CreationDate": _iso(800)},
    ]
    s3_lifecycle: dict[str, bool] = {
        "prod-app-assets": True,
        "old-backups-2022": False,
        "temp-exports-forgotten": False,
    }
    s3_sizes_gb: dict[str, float] = {
        "prod-app-assets": 800.0,
        "old-backups-2022": 3200.0,
        "temp-exports-forgotten": 450.0,
    }

    # --- method handlers (return shape mimics boto3) ---

    def describe_instances(region, **_):
        items = ec2_instances.get(region, [])
        return {"Reservations": [{"Instances": items}]}

    def describe_volumes(region, **_):
        return {"Volumes": ebs_volumes.get(region, [])}

    def describe_snapshots(region, **_):
        return {"Snapshots": ebs_snapshots.get(region, [])}

    def describe_addresses(region, **_):
        return {"Addresses": elastic_ips.get(region, [])}

    def describe_nat_gateways(region, **_):
        return {"NatGateways": nat_gateways.get(region, [])}

    def describe_db_instances(region, **_):
        return {"DBInstances": rds_instances.get(region, [])}

    def list_buckets(region, **_):
        return {"Buckets": s3_buckets}

    def get_bucket_lifecycle_configuration(region, *, Bucket):
        if s3_lifecycle.get(Bucket):
            return {"Rules": [{"Status": "Enabled"}]}
        from botocore.exceptions import ClientError  # type: ignore
        raise ClientError(
            {"Error": {"Code": "NoSuchLifecycleConfiguration"}},
            "GetBucketLifecycleConfiguration",
        )

    def get_bucket_location(region, *, Bucket):
        return {"LocationConstraint": "us-east-1"}

    def get_metric_statistics(region, *, Namespace, MetricName, Dimensions, **_):
        if Namespace == "AWS/EC2":
            iid = next((d["Value"] for d in Dimensions if d["Name"] == "InstanceId"), "")
            return {"Datapoints": cw_cpu.get((region, iid), [])}
        if Namespace == "AWS/RDS":
            db = next((d["Value"] for d in Dimensions if d["Name"] == "DBInstanceIdentifier"), "")
            return {"Datapoints": rds_cpu.get((region, db), [])}
        return {"Datapoints": []}

    def get_bucket_size(region, *, Bucket):
        return s3_sizes_gb.get(Bucket, 0.0)

    return {
        "ec2": {
            "describe_instances": describe_instances,
            "describe_volumes": describe_volumes,
            "describe_snapshots": describe_snapshots,
            "describe_addresses": describe_addresses,
            "describe_nat_gateways": describe_nat_gateways,
        },
        "rds": {
            "describe_db_instances": describe_db_instances,
        },
        "s3": {
            "list_buckets": list_buckets,
            "get_bucket_lifecycle_configuration": get_bucket_lifecycle_configuration,
            "get_bucket_location": get_bucket_location,
            "get_bucket_size": get_bucket_size,
        },
        "cloudwatch": {
            "get_metric_statistics": get_metric_statistics,
        },
    }
