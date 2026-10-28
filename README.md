# AWS Cloud Operations Lab

> **Project working notes — keep this file current during development.**
> This is an implementation/status document for the project owner and future work sessions, not yet the final public-facing portfolio README. Before making the repository public, review the account-specific details and replace this with a polished overview.

## Project purpose

Build a small, practical AWS operations lab that demonstrates infrastructure as code, secure remote administration, containerised application operations, monitoring, alerting, patch-compliance assessment, troubleshooting, and recovery.

The lab should be useful as a portfolio project while remaining cost-conscious. Avoid unnecessary AWS resources and do not make changes to unrelated existing AWS stacks.

## Current state

**Last updated:** 28 October 2026
**AWS region:** `ap-southeast-1` (Singapore)
**AWS CLI profile:** `portfolio-dev`
**EC2 instance:** `i-0cd747d495eabf8c0` (`t3.micro`, Amazon Linux 2023)
**Repository:** `https://github.com/aimanhaizal/aws-cloud-operations-lab`

### Implemented and verified

- [x] AWS CDK / CloudFormation infrastructure project.
- [x] EC2-hosted Flask dashboard served by Gunicorn inside Docker.
- [x] Dashboard container `cloudops-dashboard`; host port is bound to `127.0.0.1:8001`, not exposed directly through that binding to the public internet.
- [x] Remote administration and health checks through AWS Systems Manager Run Command.
- [x] Existing CloudWatch alarms for EC2 CPU utilisation and EC2 status-check failures.
- [x] CloudWatch Agent installed and running on the EC2 instance.
- [x] Docker container logs delivered to CloudWatch Logs group `/aws/ec2/aws-cloud-operations-lab/docker`.
- [x] Log group retention set to 14 days.
- [x] Metric filter `DemoPaymentApi-HTTP503` creates metric `CloudOps/Demo` / `DemoPaymentApiFailures` for matching Payment API HTTP 503 log events.
- [x] Alarm `CloudOps-Demo-Payment-API-Failure` triggers when the failure metric reaches at least 1 in a 60-second period.
- [x] End-to-end simulated failure test completed: Payment API health endpoint returned HTTP 503, the log event appeared in CloudWatch Logs, the metric datapoint was `1.0`, and the alarm entered `ALARM`.
- [x] Recovery test completed: `/demo/restore` returned a healthy response, `/demo/payment-health` returned HTTP 200, and the CloudWatch alarm returned to `OK` after the failure datapoint left its evaluation window.
- [x] AWS Systems Manager Patch Manager scan completed successfully on 28 October 2026. It reported 68 installed patches, 0 missing, 0 failed, 0 security non-compliant, and 0 critical non-compliant under the applied baseline. This was a **scan only**; no patch installation or reboot was performed.
- [x] Operational runbook documents access, routine health checks, monitoring, troubleshooting, recovery, patch compliance, infrastructure changes, security, and cost precautions.
- [x] Local test suite last reported `17 passed` (28 October 2026).
- [x] Git remote `origin` points to the GitHub repository; branch `main` is used.

### Latest known Git history

- `512c43a docs: record patch compliance assessment` — pushed to `main`.
- The CloudWatch monitoring and runbook changes described above were performed after that commit and may still need to be committed. Check `git status` and `git log` before assuming the current working tree or remote is up to date.

## Architecture overview

```text
Administrator workstation
        |
        | AWS CLI / Systems Manager Run Command
        v
AWS Systems Manager ---- EC2 instance (Amazon Linux 2023)
                              |
                              +-- Docker: cloudops-dashboard
                              |      Flask + Gunicorn
                              |      127.0.0.1:8001 -> container:8000
                              |
                              +-- CloudWatch Agent
                                     |
                                     v
                           CloudWatch Logs
                           /aws/ec2/aws-cloud-operations-lab/docker
                                     |
                                     v
                              Metric filter
                              DemoPaymentApi-HTTP503
                                     |
                                     v
                           CloudOps/Demo metric
                           DemoPaymentApiFailures
                                     |
                                     v
                           CloudWatch alarm
                           CloudOps-Demo-Payment-API-Failure
```

The dashboard's ordinary `/health` endpoint checks the dashboard application. The separate demo endpoint `/demo/payment-health` represents a simulated Payment API and can intentionally return HTTP 503 for monitoring demonstrations. The failure simulation does not affect a real payment service.

## Key application endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Dashboard application health; expected HTTP 200. |
| `GET` | `/demo/payment-health` | Simulated Payment API health; HTTP 200 normally and HTTP 503 while failure simulation is active. |
| `POST` | `/demo/simulate-failure` | Activates simulated Payment API failure; the activation request itself returns HTTP 200. |
| `POST` | `/demo/restore` | Restores simulated Payment API health; returns HTTP 200. |

Application source: `src/cloudops_lab/__init__.py`
Dashboard template: `src/cloudops_lab/templates/index.html`
Runbook: `docs/runbook.md`
Architecture notes: `docs/architecture.md`

## AWS resources and cost guardrails

Known resources/settings relevant to this lab:

- Region: `ap-southeast-1`.
- EC2 instance ID: `i-0cd747d495eabf8c0`.
- Instance type: `t3.micro`.
- CloudWatch Logs group: `/aws/ec2/aws-cloud-operations-lab/docker`.
- Log retention: 14 days.
- CloudWatch Agent package: `amazon-cloudwatch-agent` (version last observed: `1.300071.0-1.amzn2023.x86_64`).
- The instance uses Systems Manager for remote administration; do not open SSH to the internet as a shortcut.
- No NAT Gateway or Application Load Balancer is currently part of this lab deployment.
- The CloudWatch failure alarm currently has no notification actions configured. It changes state in AWS but does not itself send an email or message.

Cost and safety rules:

1. Review the expected cost before creating any additional billable AWS resources.
2. Avoid NAT Gateways, load balancers, extra instances, and detailed monitoring unless their value and cost are reviewed first.
3. Remember that budgets are alerts, not hard spending caps.
4. Stopping EC2 reduces compute charges but does not necessarily stop EBS, public IPv4, log storage, or other service charges.
5. Preserve unrelated resources and stacks, including `ServerlessPortfolioStack`, `CDKToolkit`, existing DynamoDB resources, and the CDK asset bucket.
6. Do not install operating-system patches or reboot the instance without explicitly planning the maintenance.
7. Do not claim all available security updates are installed based solely on the last Patch Manager scan; its `AvailableSecurityUpdateCount` was unavailable.

## Development environment and useful commands

The project is developed locally on Linux at:

```text
/home/work/aws-cloud-operations-lab
```

A Python virtual environment named `.venv` is used. The user prefers editing files in VS Code rather than `nano`.

Activate the environment and run tests:

```bash
cd /home/work/aws-cloud-operations-lab
source .venv/bin/activate
pytest -q
```

Check repository state before editing or committing:

```bash
git status --short
git log -5 --oneline
git remote -v
```

Review changes and check whitespace:

```bash
git diff
git diff --check
```

The AWS CDK project can be synthesised and reviewed before deployment:

```bash
cdk synth
cdk diff --profile portfolio-dev
```

Use the intended profile and region for AWS commands. Review the CDK diff carefully before any deployment; do not deploy or destroy resources automatically.

## Plan and next steps

### Immediate documentation work

- [ ] Review the edited `docs/runbook.md` in the repository and compare it with the current file before replacing it.
- [ ] Update `docs/architecture.md` to include CloudWatch Agent → CloudWatch Logs → metric filter → custom metric → alarm.
- [ ] Run `pytest -q` and `git diff --check`.
- [ ] Review the README and runbook changes, then commit and push the documentation updates.

### Monitoring improvements

- [ ] Decide whether notifications are useful; if so, compare SNS/email setup and costs before implementation.
- [ ] Consider adding an explicit recovery/incident test procedure that is safe to repeat.
- [ ] Optionally capture sanitized screenshots of the dashboard and CloudWatch alarm history for the portfolio.

### Operational quality

- [ ] Verify the existing EC2 alarm thresholds and evaluation settings against deployed configuration before documenting them as definitive.
- [ ] Review whether the CloudWatch Agent configuration should be managed through infrastructure/configuration files rather than only by one-off SSM commands.
- [ ] Add a repeatable deployment/update procedure for rebuilding and replacing the dashboard container.
- [ ] Consider automated tests for configuration and runbook commands where appropriate.

### Public portfolio polish — later

- [ ] Replace this internal status-oriented README with a concise public overview: problem, architecture, key features, safe demo steps, screenshots, test results, and limitations.
- [ ] Remove or generalise account-specific operational identifiers from public-facing docs where appropriate.
- [ ] Make sure all claims are backed by implemented and tested functionality.

## Working rules for future sessions

- Check the current repository state and relevant source files before assuming a previous step is still current.
- Distinguish local source, deployed AWS configuration, and documented intent; they may differ.
- Do not invent test results, alarm settings, or deployed resources.
- Prefer small, verifiable steps with commands and expected outputs.
- Avoid unnecessary infrastructure changes and preserve unrelated AWS resources.
- After meaningful changes, update this status document and the appropriate user-facing documentation.
