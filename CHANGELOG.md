# Changelog

## [Unreleased]

## [0.1.0] -- 2026-04-20

First tagged release. Covers what I actually use against Socialnet's account
for the monthly review.

### Added

- `aws-cost-optimizer scan` -- walks the 4 usual suspects (idle EC2, unattached
  EBS, underutilized RDS, orphaned Elastic IPs) and writes a Markdown report
  to `reports/`.
- `aws-cost-optimizer report` -- prints a cost delta summary against the
  previous run.
- Read-only IAM policy JSON under `iam/` so you don't paste admin creds into
  a read-only tool.
- Pytest suite over all 4 finders with mocked `boto3` clients. Runs offline.

### Known gaps

- CUR (Cost and Usage Report) parsing not yet wired -- currently everything is
  derived from `describe_*` + `get-metric-statistics`. Works for small accounts;
  on bigger accounts CUR would be cheaper and more complete.
- No auto-tag recommendations yet. Probably v0.2.
