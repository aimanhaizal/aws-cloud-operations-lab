# AWS Cloud Operations Lab — Operations Runbook

## 1. Service Overview

### Purpose

This runbook documents the routine operation, monitoring, troubleshooting and recovery of the AWS Cloud Operations Lab.

The environment demonstrates infrastructure provisioning with AWS CDK and CloudFormation, EC2 administration, Docker-based application hosting, Systems Manager remote management, and CloudWatch monitoring.

### Application architecture

The application runs on an Amazon EC2 instance using Amazon Linux 2023. Docker hosts the Flask dashboard, which uses Gunicorn as its application server.

| Component | Purpose |
|---|---|
| Amazon VPC | Provides network isolation and subnet routing. |
| Amazon EC2 | Hosts the dashboard application. |
| Docker | Runs the dashboard container. |
| Flask and Gunicorn | Serve the dashboard and its health endpoint. |
| AWS Systems Manager | Provides remote administration through Run Command. |
| Amazon CloudWatch | Monitors EC2 CPU utilisation and instance status checks. |
| AWS CDK and CloudFormation | Define and manage the infrastructure. |

### Application access

The dashboard container is configured to bind its host port to `127.0.0.1:8001`. This makes the application accessible from the EC2 instance itself, rather than directly from the public internet.

The health endpoint is:

```text
http://127.0.0.1:8001/health
```

Administrators can run health checks and diagnostic commands remotely through AWS Systems Manager, provided the EC2 instance is online and has the required IAM permissions and Systems Manager connectivity.

## 2. Access and Prerequisites

### 2.1 Configure the AWS CLI

Run administrative commands from a workstation with the AWS CLI installed and the `portfolio-dev` profile configured.

```bash
export AWS_PROFILE=portfolio-dev
export AWS_REGION=ap-southeast-1
export INSTANCE_ID=i-0cd747d495eabf8c0
```

Verify the active AWS identity and configured region before proceeding.

```bash
aws sts get-caller-identity

aws configure get region --profile "$AWS_PROFILE"
```

**Expected result:** The identity belongs to the intended AWS account, and the configured region is `ap-southeast-1`.

If the identity or region is unexpected, stop and correct the configuration before performing administrative operations.

### 2.2 Verify the EC2 instance

```bash
aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[].Instances[].{State:State.Name,Type:InstanceType,PrivateIP:PrivateIpAddress,PublicIP:PublicIpAddress}' \
  --output table
```

Confirm that the instance exists and check its current state.

### 2.3 Verify Systems Manager connectivity

```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
  --query 'InstanceInformationList[].{InstanceId:InstanceId,PingStatus:PingStatus,AgentVersion:AgentVersion}' \
  --output table
```

**Expected result:** The instance is listed with a `PingStatus` of `Online`.

If the instance is missing or offline, check its state, Systems Manager Agent, IAM instance role and network connectivity before attempting remote commands.

### 2.4 Required permissions

The administrative identity must have permission to describe EC2 instances and status checks, inspect CloudWatch alarms, and send and retrieve Systems Manager commands.

The EC2 instance must have the appropriate IAM permissions and connectivity to register with Systems Manager.

Use the principle of least privilege when granting additional permissions.

## 3. Routine Health Checks

### 3.1 Check EC2 status

```bash
aws ec2 describe-instance-status \
  --instance-ids "$INSTANCE_ID" \
  --include-all-instances \
  --query 'InstanceStatuses[].{State:InstanceState.Name,System:SystemStatus.Status,Instance:InstanceStatus.Status}' \
  --output table
```

**Expected result:** The instance is `running`, and both the system and instance status checks report `ok`.

Investigate any failed status check before attempting application-level recovery.

### 3.2 Check application health

Send a health-check command through Systems Manager.

```bash
COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters '{"commands":["curl -sS -w \"\\nHTTP_STATUS=%{http_code}\\n\" http://127.0.0.1:8001/health"]}' \
  --query 'Command.CommandId' \
  --output text)

echo "$COMMAND_ID"
```

Retrieve the result:

```bash
aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --query '{Status:Status,Output:StandardOutputContent,Errors:StandardErrorContent}' \
  --output json
```

**Expected result:** The HTTP status is `200`, and the response contains:

```json
{"status":"healthy"}
```

If the invocation is still pending, retrieve the result again after the command has completed.

### 3.3 Check container state and logs

```bash
COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters '{"commands":["docker ps -a --filter name=cloudops-dashboard","docker logs --tail 50 cloudops-dashboard"]}' \
  --query 'Command.CommandId' \
  --output text)

aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --query '{Status:Status,Output:StandardOutputContent,Errors:StandardErrorContent}' \
  --output json
```

Check that the container exists, determine whether it is running, and review the logs for exceptions, startup failures or repeated errors.

### 3.4 Inspect Docker health status

A running container is not necessarily a healthy application. If a Docker health check is configured, inspect its state separately.

```bash
COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters '{"commands":["docker inspect --format \"{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}\" cloudops-dashboard","docker inspect --format \"{{json .State.Health}}\" cloudops-dashboard"]}' \
  --query 'Command.CommandId' \
  --output text)

aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --query '{Status:Status,Output:StandardOutputContent,Errors:StandardErrorContent}' \
  --output json
```

Interpret the results as follows:

- `running healthy`: Docker reports the container as healthy.
- `running unhealthy`: Docker reports that its configured health check is failing.
- `running no-healthcheck`: The container is running, but Docker has no configured health check.
- `exited`: The container has stopped.

Regardless of Docker's health status, use the application health endpoint to verify that the dashboard is responding correctly.

## 4. Monitoring and Alarms

### 4.1 Configured CloudWatch alarms

The project runbook documents two CloudWatch alarms.

| Alarm | Metric | Documented threshold |
|---|---|---|
| `CloudOps-High-CPU` | `AWS/EC2` — `CPUUtilization` | Average CPU utilisation above 70% for two consecutive five-minute periods. |
| `CloudOps-EC2-Status-Check-Failed` | `AWS/EC2` — `StatusCheckFailed` | Maximum status-check failure value greater than or equal to 1 during one five-minute period. |

These thresholds should be checked against the deployed alarm configuration before being treated as verified production settings.

### 4.2 Inspect alarm states

```bash
aws cloudwatch describe-alarms \
  --alarm-names \
    CloudOps-High-CPU \
    CloudOps-EC2-Status-Check-Failed \
  --query 'MetricAlarms[].{Alarm:AlarmName,State:StateValue,Reason:StateReason,Metric:MetricName,Namespace:Namespace,Threshold:Threshold,Comparison:ComparisonOperator,Period:Period,EvaluationPeriods:EvaluationPeriods,Statistic:Statistic}' \
  --output table
```

Review the reported state, metric, threshold and evaluation settings.

Possible states include:

- `OK`: The alarm's configured conditions are not currently breached.
- `ALARM`: The alarm's conditions have been breached.
- `INSUFFICIENT_DATA`: There is insufficient metric data to determine the state.

An `INSUFFICIENT_DATA` state is not, by itself, proof of an infrastructure failure.

### 4.3 Investigate an alarm

1. Identify the alarm and determine when its state changed.
2. Review the associated CloudWatch metric and recent datapoints.
3. Check the EC2 instance state and status checks.
4. Verify Systems Manager connectivity.
5. Inspect the dashboard container state and application logs.
6. Determine whether the issue is resource pressure, an instance-level problem or an application failure.
7. Apply an appropriate recovery action and verify the result.
8. Record the cause, corrective action and outcome.

For a CPU alarm, investigate sustained utilisation and potential resource contention before changing instance capacity.

For an EC2 status-check alarm, determine whether the failure originates from the underlying system or the instance itself before attempting application recovery.

### 4.4 Alerting limitations

The documented implementation includes two CloudWatch alarms. Alarm notifications and automatic remediation are not documented as configured capabilities.

Do not assume that an alarm automatically sends an email, pages an administrator or repairs the affected resource.

## 5. Troubleshooting and Recovery

### 5.1 Initial investigation

**Trigger:** The dashboard health endpoint stops returning HTTP 200, the container stops, or Docker reports an unhealthy container.

First, check the instance, application endpoint, container state and logs.

```bash
COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters '{"commands":["curl -sS -w \"\\nHTTP_STATUS=%{http_code}\\n\" http://127.0.0.1:8001/health","docker ps -a --filter name=cloudops-dashboard","docker inspect --format \"{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}\" cloudops-dashboard","docker logs --tail 100 cloudops-dashboard"]}' \
  --query 'Command.CommandId' \
  --output text)

aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --query '{Status:Status,Output:StandardOutputContent,Errors:StandardErrorContent}' \
  --output json
```

If the command has not finished, retrieve the invocation again.

Investigate the following:

- Is the EC2 instance running and passing status checks?
- Is Systems Manager reporting the instance as online?
- Does the dashboard container exist?
- Is the container stopped, running or unhealthy?
- Do the logs show application exceptions or startup failures?
- Is Gunicorn starting successfully?
- Is the expected host-port binding present?
- Is the application's health endpoint responding correctly?

Do not delete the container or rebuild the image before checking the logs and identifying the likely cause.

### 5.2 Recovery: Container is stopped

If the existing container is confirmed to be stopped and its image remains available locally, restart it.

```bash
COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters '{"commands":["docker start cloudops-dashboard"]}' \
  --query 'Command.CommandId' \
  --output text)

aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --query '{Status:Status,Output:StandardOutputContent,Errors:StandardErrorContent}' \
  --output json
```

After the command completes, verify the container state, review the recent logs and repeat the application health check in Section 3.2.

If the container fails to start, inspect the resulting error and logs rather than repeatedly attempting to restart it.

If the container has been removed or its image is missing, investigate the deployment artefact and deployment procedure before recreating it.

### 5.3 Recovery: Container is running but unhealthy

A running container with an unhealthy application requires a different response from a stopped container.

**Do not assume that restarting the container will resolve the issue.**

1. Review the application logs.

   ```bash
   docker logs --tail 100 cloudops-dashboard
   ```

2. Inspect Docker health-check results, if a health check is configured.

   ```bash
   docker inspect --format '{{json .State.Health}}' cloudops-dashboard
   ```

3. Test the health endpoint from the EC2 instance.

   ```bash
   curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
     http://127.0.0.1:8001/health
   ```

4. Identify the likely cause, such as an application exception, failed dependency, startup problem or incorrect configuration.

5. Apply the appropriate corrective action. If the cause is understood and a restart is justified, restart the existing container:

   ```bash
   docker restart cloudops-dashboard
   ```

6. Recheck the application endpoint, container state and logs.

If the container remains unhealthy, continue investigating the underlying problem. Do not treat a successful Docker restart as proof of recovery.

If the application is responding correctly but Docker still reports `unhealthy`, investigate whether the configured Docker health check accurately reflects the application's health.

### 5.4 Recovery: EC2 or Systems Manager failure

If the EC2 instance is stopped, failing status checks or unavailable through Systems Manager, investigate the infrastructure before attempting container recovery.

1. Check EC2 state and status checks using Sections 2.2 and 3.1.
2. Check Systems Manager connectivity using Section 2.3.
3. Review the relevant CloudWatch alarm and metrics.
4. Determine whether the issue requires instance-level recovery, IAM correction or network troubleshooting.
5. Restore management connectivity before attempting application-level operations.

If Systems Manager is offline, Run Command cannot be relied upon to repair the application. Resolve the underlying connectivity or management issue first.

### 5.5 Verify recovery

After any recovery action, repeat the health check in Section 3.2 and inspect the container state and logs.

Recovery is confirmed when:

- The container is running.
- The application health endpoint returns HTTP 200.
- The response contains `{"status":"healthy"}`.
- No new startup or application errors are evident in the logs.

If Docker health checks are configured, also confirm that the container returns to `healthy`.

Record the incident, root cause, corrective action and verification results.

## 6. Patch Compliance Assessment

AWS Systems Manager Patch Manager was used to run a scan against the Amazon Linux EC2 application instance.

**Assessment record**

- Operation: `Scan`
- Assessment completed: 28 October 2026, 09:41 MYT
- Installed patches reported: 68
- Missing patches: 0
- Failed patches: 0
- Security non-compliant patches: 0
- Critical non-compliant patches: 0
- Patch baseline: `pb-017dc15c6301bae06`

The scan completed successfully and reported no missing patches under the baseline applied to the instance. The scan assessed compliance only; it did not install updates or initiate a reboot.

The `AvailableSecurityUpdateCount` field was unavailable in this assessment, so the results should not be interpreted as independent confirmation that every available security update has been installed.

**Operational procedure**

1. Run a Patch Manager scan before scheduling maintenance.
2. Review the compliance counts and any command errors.
3. Investigate non-compliant or failed patches before proceeding.
4. Obtain approval before installing updates, particularly when a reboot may be required.
5. Run another scan after maintenance to verify the resulting compliance state.

Repeat the assessment periodically and retain the results as operational evidence.



## 7. Infrastructure Changes

AWS CDK defines the infrastructure and synthesises a CloudFormation template. CloudFormation manages the deployed resources as a stack.

### 7.1 Review changes before deployment

Run the following commands from the project directory using the intended CDK environment and configuration.

```bash
cdk synth
cdk diff
```

Review the output for:

- Resource additions, replacements and deletions.
- Changes to network exposure or security-group rules.
- Changes to IAM permissions.
- Changes to EC2 configuration or application deployment.
- Resources that may incur additional AWS charges.
- Changes that could affect existing resources or applications.

Where necessary, inspect the synthesized CloudFormation template and deployed stack configuration before proceeding.

### 7.2 Deploy reviewed changes

Deploy only after reviewing the proposed changes and confirming the target AWS profile and region.

```bash
cdk deploy AwsCloudOperationsLabStack \
  --profile portfolio-dev \
  --region ap-southeast-1
```

Monitor the deployment until CloudFormation reports its outcome. If deployment fails, inspect the stack events before attempting another deployment.

Do not delete or replace unrelated stacks, including `ServerlessPortfolioStack` and `CDKToolkit`.

Preserve existing DynamoDB resources and the CDK asset bucket unless a separately reviewed change explicitly requires otherwise.

## 8. Security and Cost Considerations

### 8.1 Security controls

- Prefer Systems Manager for administrative access instead of opening SSH to the internet.
- Follow least-privilege IAM practices when adding permissions.
- Restrict application ingress to the required source security group.
- Keep credentials, access keys, tokens and other secrets out of source control.
- Review security-group changes before deployment.
- Inspect application logs before restarting or replacing a service.
- Review infrastructure changes with `cdk diff`.
- Confirm the target AWS account and region before administrative operations.

The documented dashboard binding to `127.0.0.1:8001` prevents direct access through the EC2 instance's external network interfaces via that binding. It does not, by itself, establish the security of every other service or network path.

### 8.2 Cost controls

- Check AWS billing and resource usage regularly.
- Do not assume that a budget alert is a spending cap.
- Review estimated charges before introducing new resources.
- Avoid creating NAT Gateways, load balancers, additional compute instances or other billable resources without reviewing their costs first.
- Review the consequences of CDK changes before deploying them.
- Preserve unrelated stacks and resources during cleanup.

When pausing work, identify temporary resources created specifically for the lab and stop or remove them according to the intended cleanup procedure. Verify the resulting resource states.

Do not assume that stopping an EC2 instance eliminates every associated cost. Storage, retained resources and other services may continue to incur charges.

Do not remove `ServerlessPortfolioStack`, `CDKToolkit`, or their associated resources as part of routine lab cleanup.
