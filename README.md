# AWS cost-optimizer CLI

A small, opinionated Python CLI that scans an AWS account and surfaces the
**top cost leaks** a DevOps team can safely act on in one sprint:

- **Idle EC2 instances** (avg CPU <5% over last 14 days)
- **Unattached EBS volumes** (available, billed, never mounted)
- **Old EBS snapshots** (>90 days, parent volume deleted)
- **Unassociated Elastic IPs** ($0.005/h each, sneaky)
- **Oversized RDS instances** (avg CPU <20% + connections <10% capacity)
- **S3 buckets without lifecycle policies** (standard storage > 180 days)
- **NAT gateways** in dev VPCs (expensive + often forgotten)

Output: a ranked CSV + Markdown report you can paste into a Jira ticket or
a team Slack.

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

Every AWS account I've inherited has ~15-25% of spend going to resources
that nobody would miss. Most "AWS cost tools" charge for the obvious stuff
(Compute Optimizer, Trusted Advisor Business tier, Vantage, CloudHealth).
This CLI does the **80% of the value for free**, in ~800 lines of Python
you can read in an afternoon.

It's **read-only** by design. It never deletes, resizes, or modifies
anything — it produces a report, and a human (or a follow-up Terraform PR)
takes action.

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

- How pricing estimates are computed (CSV of list-price per instance type,
  updated quarterly — yes, we know Savings Plans & RIs distort this; the
  report is a ranking signal, not an invoice)
- Why each "finding" is a separate module (`src/findings/*.py`) so teams
  can disable the ones that don't apply to their account shape
- How the mock mode builds a synthetic account with known leaks so the
  ranking / report code is testable without AWS

## Roadmap

- [ ] `--apply` mode that writes Terraform import blocks for orphan
      resources (so you can manage-then-destroy)
- [ ] Slack notifier (post top 5 findings weekly)
- [ ] Compute Savings Plans coverage estimator
- [ ] Lambda cold-resource finder (functions not invoked in 60+ days)

## License

MIT © 2026 Santiago Arteta
