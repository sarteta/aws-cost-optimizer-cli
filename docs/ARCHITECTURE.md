# Architecture notes

## Why read-only

The optimizer never mutates AWS state. Three reasons:

1. **Blast radius.** Deleting the wrong EBS volume or stopping the wrong
   EC2 instance is a much worse bug than under-reporting savings. A
   read-only tool can be run in production by anyone with the IAM
   policy, no Change Advisory Board required.
2. **Trust.** Teams adopt cost tools slowly. They're much more willing
   to run "tell me what's wrong" than "fix it for me." The delta in
   adoption is ~10x.
3. **Terraform reality.** In any serious AWS account, real fixes go
   through Terraform/CDK/CloudFormation. An opinionated "auto-fix"
   mode would fight drift detection. The CLI outputs a ranked list;
   the IaC PR is the action.

## Why each finding is its own module

`src/findings/*.py` each expose the same `scan(client, region) -> list[Finding]`
interface. This buys us:

- **Disable unwanted checks** by deleting them from `ALL_SCANNERS` in
  `findings/__init__.py`. A team with no RDS can skip that file.
- **Parallel evolution.** Adding a new check (e.g. Lambda cold
  functions) means dropping in a new module, no changes to the core.
- **Testability.** Each check has its own narrow unit test against the
  mock account. Tests are ~2x faster than running the full end-to-end
  scan for every change.

## Why pricing lives in a hardcoded table

The AWS Pricing API (`pricing.us-east-1.amazonaws.com`) returns ~500MB
of JSON per service. Pulling that on every scan would be 10x slower and
requires its own IAM policy.

Our `src/pricing.py` has ~40 common instance types and a region
multiplier lookup. It's deliberately low-fidelity:

- Doesn't account for Savings Plans / Reserved Instances (those distort
  effective price, but the *ranking* of leaks doesn't really change)
- Doesn't account for Spot (same)
- Doesn't include data-transfer charges (sneaky but not the biggest
  leaks)

For a more accurate number, pipe the CSV output into
[infracost](https://www.infracost.io/) or the AWS Cost Explorer API.

## Why mock mode matters

`--mock` lets us:

- Run the full scan pipeline in CI with no AWS creds
- Demo the tool in a README without screenshots of real account IDs
- Write unit tests in ~200 lines of synthetic data instead of moto
- Catch bugs in the report writer before they hit production accounts

The mock data in `src/mock_data.py` is deliberately constructed so each
finding module produces at least one hit -- it's both a demo fixture and
an integration test.

## Roadmap: why `--apply`?

A future `--apply` flag would generate Terraform import blocks for
orphan resources so the team can `terraform import` → `terraform
destroy` safely. This is the only "fix" mode we'd build; anything that
modifies AWS state directly is a separate tool.
