# aws-cost-optimizer-cli

Python CLI that scans an AWS account and lists the obvious cost leaks
most teams can clean up in a sprint:

- Idle EC2 instances (avg CPU <5% over last 14 days)
- Unattached EBS volumes (billed, never mounted)
- Old EBS snapshots (>90 days, parent volume deleted)
- Unassociated Elastic IPs ($0.005/h each, easy to forget)
- Oversized RDS (avg CPU <20% + connections <10% of max)
- S3 buckets without lifecycle policies (standard storage >180 days)
- NAT gateways in dev VPCs

Output is a ranked CSV + a Markdown summary you can paste into Jira or Slack.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   AWS account              ── boto3 read-only ──►   optimizer.scan()    │
│   (IAM: ReadOnlyAccess)                                   │              │
│                                                           ▼              │
│                                                     findings/            │
│                                                      ├─ idle_ec2.json   │
│                                                      ├─ orphan_ebs.json │
│                                                      └─ …               │
│                                                           │              │
│                                                           ▼              │
│                                                     reports/             │
│                                                      ├─ summary.md      │
│                                                      └─ actions.csv     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Why this exists

Every AWS account I've taken over had 15-25% of spend on things nobody was
using. The commercial tools that flag this stuff (Compute Optimizer,
Trusted Advisor Business, Vantage, CloudHealth) charge per account and the
findings are usually the same handful of patterns. This CLI covers those
patterns in ~800 lines of Python you can read in an afternoon.

Read-only. It doesn't delete, resize or modify anything — it just writes
a report. Actual cleanup is a separate Terraform PR, done by a human.

## Quickstart

```bash
# Requires Python 3.11+ and AWS credentials (env / profile / role)
pip install -r requirements.txt

# Dry scan against the configured profile (read-only, ~30-90s)
python -m src.scan --profile default --region us-east-1

# Multi-region scan, write reports
python -m src.scan \
  --profile prod \
  --regions us-east-1,us-west-2,eu-west-1 \
  --output reports/2026-04-prod

# Mock mode — no AWS account needed, useful for demos / CI
python -m src.scan --mock --output reports/mock-demo
```

## What you get

A ranked `reports/<run>/actions.csv`:

| rank | resource          | id               | region    | est_monthly_usd | action               |
|------|-------------------|------------------|-----------|-----------------|----------------------|
| 1    | NAT gateway       | nat-0abc...      | us-west-2 | 32.40           | delete (dev VPC)     |
| 2    | RDS db.m5.xlarge  | prod-legacy      | us-east-1 | 192.00          | downsize → m5.large  |
| 3    | EC2 c5.2xlarge    | i-04a…bastion    | us-east-1 | 247.00          | stop (idle 18d)      |
| 4    | EBS gp3 500GB     | vol-0abcdef      | us-east-1 | 40.00           | delete (unattached)  |
| …    | …                 | …                | …         | …               | …                    |

And a `reports/<run>/summary.md` you can paste anywhere.

## IAM permissions

The CLI is read-only. The included `iam/cost-optimizer-readonly.json` is a
minimal policy — about 25 actions across `ec2:Describe*`, `rds:Describe*`,
`s3:GetBucket*`, `ce:GetCostAndUsage`, `cloudwatch:GetMetricStatistics`.

## Design notes

See `docs/ARCHITECTURE.md` for:

- How the pricing estimates are computed. They use list price per instance
  type. Savings Plans / RIs will distort the numbers — the report is a
  ranking signal, not an invoice.
- Why each finding is its own module under `src/findings/`. Teams can
  disable the ones that don't apply to their account shape.
- What the mock mode does (builds a synthetic account with known leaks
  so you can demo / test without real AWS creds).

## Roadmap

- [ ] `--apply` mode that writes Terraform import blocks for orphan
      resources (so you can manage-then-destroy)
- [ ] Slack notifier (post top 5 findings weekly)
- [ ] Compute Savings Plans coverage estimator
- [ ] Lambda cold-resource finder (functions not invoked in 60+ days)

## License

MIT © 2026 Santiago Arteta
