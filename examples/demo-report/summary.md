# AWS cost-optimizer — scan summary

- **Account:** `123456789012`
- **Regions:** us-east-1
- **Findings:** 9
- **Estimated total monthly waste:** **$651.61**

## Top findings

| rank | type | id | region | est. $/mo | action |
|------|------|-----|--------|-----------|--------|
| 1 | `rds_oversized` | `prod-legacy` | us-east-1 | $249.66 | downsize db.m5.xlarge → db.m5.large (avg CPU 9.3%) |
| 2 | `ec2_idle` | `i-bastion` | us-east-1 | $248.20 | stop or rightsize (avg CPU 0.8% over 14d) |
| 3 | `s3_no_lifecycle` | `old-backups-2022` | us-east-1 | $73.60 | add lifecycle policy (size ~3200 GB, no rules) |
| 4 | `ebs_orphan` | `vol-orphan1` | us-east-1 | $40.00 | delete (unattached gp3 volume, 500 GB) |
| 5 | `ebs_snapshot_old` | `snap-ancient` | us-east-1 | $12.50 | review & delete (age 540d, 250 GB) |
| 6 | `s3_no_lifecycle` | `temp-exports-forgotten` | us-east-1 | $10.35 | add lifecycle policy (size ~450 GB, no rules) |
| 7 | `ebs_orphan` | `vol-orphan2` | us-east-1 | $10.00 | delete (unattached gp2 volume, 100 GB) |
| 8 | `eip_unused` | `3.210.2.2` | us-east-1 | $3.65 | release Elastic IP (not associated) |
| 9 | `eip_unused` | `3.210.3.3` | us-east-1 | $3.65 | release Elastic IP (not associated) |

## Breakdown by type

| type | count | est. $/mo |
|------|-------|-----------|
| `rds_oversized` | 1 | $249.66 |
| `ec2_idle` | 1 | $248.20 |
| `s3_no_lifecycle` | 2 | $83.95 |
| `ebs_orphan` | 2 | $50.00 |
| `ebs_snapshot_old` | 1 | $12.50 |
| `eip_unused` | 2 | $7.30 |