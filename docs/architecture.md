# Cloud Operations Lab — Architecture

## 1. Project overview

The Cloud Operations Lab is a portfolio project demonstrating infrastructure as code, secure remote administration, containerised application hosting, monitoring, patch-compliance assessment, and operational troubleshooting on AWS.

The repository uses AWS CDK with Python and AWS CloudFormation for infrastructure definitions. The currently deployed lab also includes an EC2-hosted Flask dashboard and a verified CloudWatch log-to-alarm workflow.

**Current status:** The application and monitoring workflow described in Section 3 are deployed and tested. The VPC design in Section 4 describes the project's infrastructure foundation and intended network layout; it should not be mistaken for proof that every planned application-tier resource is deployed.

## 2. Design objectives

- Use infrastructure as code for repeatable provisioning.
- Use least-privilege security controls and Systems Manager for remote administration.
- Centralise application logs and detect a simulated service failure.
- Verify operational behavior with repeatable tests and recorded evidence.
- Avoid unnecessary recurring charges.
- Distinguish clearly between locally implemented, deployed, and verified capabilities.

## 3. Current deployed application and monitoring architecture

### 3.1 Application hosting

The dashboard runs on an Amazon EC2 instance using Amazon Linux 2023. Docker hosts the Flask application, served by Gunicorn.

| Component | Current configuration | Purpose |
|---|---|---|
| Amazon EC2 | `t3.micro`, region `ap-southeast-1` | Hosts the dashboard container |
| Docker | Container `cloudops-dashboard` | Runs the application |
| Flask and Gunicorn | Container listens on port `8000` | Serves the dashboard and health endpoints |
| Host port binding | `127.0.0.1:8001` → container port `8000` | Keeps this host-port binding local to the EC2 instance |
| AWS Systems Manager | Run Command | Runs remote health checks and administration commands |
| CloudWatch Agent | Installed and running on EC2 | Ships Docker container logs to CloudWatch Logs |

The dashboard health endpoint is `http://127.0.0.1:8001/health`. The dashboard application health check is separate from the simulated Payment API endpoint used for the monitoring demonstration.

### 3.2 Log collection, metric filter, and alarm

The verified monitoring path is:

```text
Flask application in Docker
        |
        | Docker JSON-file logs
        v
CloudWatch Agent on EC2
        |
        v
CloudWatch Logs
/aws/ec2/aws-cloud-operations-lab/docker
        |
        | Metric filter: DemoPaymentApi-HTTP503
        v
Custom metric: CloudOps/Demo
DemoPaymentApiFailures
        |
        | Threshold >= 1 over a 60-second period
        v
CloudWatch alarm:
CloudOps-Demo-Payment-API-Failure
```

Current monitoring configuration:

| Component | Name / configuration | Purpose |
|---|---|---|
| CloudWatch Logs log group | `/aws/ec2/aws-cloud-operations-lab/docker` | Central storage for Docker container logs |
| Log retention | 14 days | Limits the retention period for collected logs |
| Metric filter | `DemoPaymentApi-HTTP503` | Matches logged HTTP 503 responses from `GET /demo/payment-health` |
| Custom metric | Namespace `CloudOps/Demo`, metric `DemoPaymentApiFailures` | Counts matching failure events |
| CloudWatch alarm | `CloudOps-Demo-Payment-API-Failure` | Enters `ALARM` when the metric sum is at least 1 for a 60-second period |

The alarm currently has no notification actions configured. It changes state in CloudWatch but does not automatically send email or other messages.

### 3.3 Failure and recovery behavior

The application exposes these endpoints for the controlled demonstration:

| Method | Endpoint | Behavior |
|---|---|---|
| `GET` | `/health` | Dashboard health; expected HTTP 200 |
| `GET` | `/demo/payment-health` | Returns HTTP 200 normally and HTTP 503 while the simulated failure is active |
| `POST` | `/demo/simulate-failure` | Activates the simulated Payment API failure; the activation request itself returns HTTP 200 |
| `POST` | `/demo/restore` | Restores the simulated Payment API to healthy status |

The test completed on 28 October 2026:

1. Activated the simulated Payment API failure.
2. Requested `/demo/payment-health` and received HTTP 503.
3. Confirmed the matching request appeared in CloudWatch Logs.
4. Confirmed a custom metric datapoint of `1.0`.
5. Confirmed `CloudOps-Demo-Payment-API-Failure` entered `ALARM`.
6. Called `/demo/restore` and confirmed the Payment API endpoint returned HTTP 200.
7. Confirmed the alarm later returned to `OK` after the failure datapoint left its evaluation window.

This is a simulated application failure for monitoring practice; it does not affect a real payment service.

## 4. Network design and intended architecture

The CDK design includes a VPC with IPv4 CIDR range `10.20.0.0/16`.

| Component | Design configuration | Purpose / status |
|---|---|---|
| VPC | `10.20.0.0/16` | Dedicated network foundation |
| Availability Zones | 2 | Foundation for multi-AZ design |
| Public subnets | `10.20.0.0/24`, `10.20.1.0/24` | Intended location for an internet-facing load balancer |
| Isolated subnets | `10.20.2.0/24`, `10.20.3.0/24` | Intended location for resources without direct internet routing |
| NAT Gateways | 0 in the intended design | Avoids NAT Gateway charges |
| Internet Gateway | 1 in the VPC design | Provides the internet route for public subnets |

The intended future request path for a more complete application deployment is:

1. A user sends an HTTP or HTTPS request to an Application Load Balancer.
2. The load balancer forwards permitted requests to application instances.
3. The application serves equipment-maintenance pages and health checks.
4. A managed database may store application records in isolated subnets.
5. Monitoring and operational services collect logs, metrics, and audit information.

**Important:** The load balancer and managed database in this future design are not part of the currently verified monitoring deployment. Do not infer their existence from this architecture description. Review the deployed CloudFormation stack and AWS resource state before making changes.

The isolated subnets do not have a default route to the internet. Software installation and access to external services must be planned before placing workloads there.

## 5. Security principles

- Prefer Systems Manager for administrative access rather than opening SSH to the internet.
- Use IAM roles instead of hard-coded AWS credentials.
- Restrict application ingress to the required source security group.
- Keep credentials, access keys, tokens, and other secrets out of source control.
- Review security-group and IAM changes before deployment.
- Inspect application logs before restarting or replacing a service.
- Review synthesized CloudFormation templates and `cdk diff` output before deployment.
- The `127.0.0.1:8001` host binding limits access through that binding to the EC2 instance itself; it does not, by itself, establish the security of every other service or network path.

## 6. Monitoring, operations, and patch compliance

The current operational runbook is `docs/runbook.md`. It documents routine health checks, Systems Manager commands, container troubleshooting, CloudWatch alarms, recovery procedures, patch-compliance assessment, infrastructure changes, and cost controls.

A Systems Manager Patch Manager scan completed on 28 October 2026. It reported 68 installed patches, zero missing patches, zero failed patches, zero security non-compliant patches, and zero critical non-compliant patches under the applied baseline. This was a scan only; no patch installation or reboot was performed. The available-security-update count was unavailable, so the result does not independently prove that every possible security update was installed.

Existing EC2 alarms also include:

- `CloudOps-High-CPU` — `AWS/EC2` `CPUUtilization`.
- `CloudOps-EC2-Status-Check-Failed` — `AWS/EC2` `StatusCheckFailed`.

Check the deployed alarm settings before treating documented thresholds as authoritative.

## 7. Cost controls and resource preservation

- Review estimated charges before adding AWS resources.
- Avoid NAT Gateways, load balancers, extra instances, or detailed monitoring unless their value and cost have been reviewed.
- Treat budgets as alerts, not hard spending limits.
- Remember that stopping EC2 reduces compute charges but does not necessarily eliminate EBS, public IPv4, CloudWatch Logs, or other service charges.
- Preserve unrelated existing resources and stacks, including `ServerlessPortfolioStack`, `CDKToolkit`, existing DynamoDB resources, and the CDK asset bucket.
- Do not install operating-system patches, reboot the instance, or deploy infrastructure changes without planning and reviewing the impact.

## 8. Testing and evidence

Infrastructure changes are tested locally using `pytest` and AWS CDK assertions. The last confirmed local test run on 28 October 2026 reported **17 passed**.

For future work, distinguish between:

- **Implemented locally:** code and tests exist in the repository.
- **Deployed:** resources were created or configured in AWS.
- **Verified:** behavior was tested and supported by observed output.

Keep screenshots, command output, and runbook records aligned with the actual deployed configuration.

## 9. Planned next steps

1. Review and commit the current architecture and operational documentation.
2. Decide whether CloudWatch alarm notifications are useful; review setup and costs before adding them.
3. Consider managing the CloudWatch Agent configuration through repeatable project configuration rather than relying solely on one-off SSM commands.
4. Document a repeatable dashboard image build and deployment/update process.
5. Improve operational tests and capture sanitized portfolio evidence.
6. Continue expanding the application architecture only after reviewing the infrastructure diff, security impact, and cost.
