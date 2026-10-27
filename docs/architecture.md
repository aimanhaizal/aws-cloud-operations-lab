# Cloud Operations Lab — Architecture

## 1. Project overview

The Cloud Operations Lab is a portfolio project demonstrating infrastructure-as-code, secure networking, application hosting, monitoring, and operational procedures on AWS.

The application will be a small equipment-maintenance web application. The infrastructure is defined using AWS CDK with Python and synthesized into AWS CloudFormation templates.

**Current status:** Network foundation implemented locally and tested. No new AWS infrastructure has been deployed.

## 2. Design objectives

- Use infrastructure as code for repeatable provisioning.
- Separate public-facing entry points from application and data tiers.
- Use least-privilege security controls.
- Avoid unnecessary recurring charges.
- Test infrastructure definitions before deployment.
- Document operational procedures, including monitoring, patching, backups, recovery, and teardown.

## 3. Network design

The lab uses a dedicated VPC with the IPv4 CIDR range `10.20.0.0/16`.

| Component | Configuration | Purpose |
|---|---|---|
| VPC | `10.20.0.0/16` | Dedicated network for the lab |
| Availability Zones | 2 | Foundation for multi-AZ deployment |
| Public subnets | `10.20.0.0/24`, `10.20.1.0/24` | Intended location for an internet-facing load balancer |
| Isolated subnets | `10.20.2.0/24`, `10.20.3.0/24` | Intended location for resources that do not require direct internet routing |
| NAT Gateways | 0 | Avoids NAT Gateway charges in the initial design |
| Internet Gateway | 1 | Provides the internet route for public subnets |

The isolated subnets do not have a default route to the internet. This reduces direct network exposure, but it also means software installation and access to external services must be planned before deploying application instances.

## 4. Intended application architecture

The planned request path is:

1. A user sends an HTTP or HTTPS request to an Application Load Balancer.
2. The load balancer forwards permitted requests to application instances.
3. The application serves equipment-maintenance pages and health checks.
4. A managed database may store application records in isolated subnets.
5. Monitoring and operational services collect logs, metrics, and audit information.

This is the intended architecture, not a description of deployed resources. The application tier, load balancer, database, monitoring, and recovery mechanisms have not yet been implemented in AWS.

## 5. Security principles

- Do not expose application instances directly to unrestricted inbound internet traffic.
- Restrict application ingress to the load balancer security group.
- Prefer AWS Systems Manager Session Manager over inbound SSH for administration, subject to connectivity and IAM requirements.
- Use IAM roles instead of hard-coded AWS credentials.
- Keep database access limited to the application tier.
- Review synthesized CloudFormation templates before deployment.

## 6. Cost controls

- Avoid NAT Gateways in the initial design.
- Review estimated service charges and Free Tier or credit eligibility before deployment.
- Use cost alerts as notifications, not as hard spending limits.
- Deploy only after reviewing the proposed changes and obtaining explicit approval.
- Tear down temporary resources when finished and verify that no unwanted billable resources remain.
- Preserve pre-existing AWS resources that are outside this project.

AWS credits and budget alerts do not guarantee that total spending will remain below a chosen amount.

## 7. Testing and evidence

Infrastructure changes are tested locally using `pytest` and AWS CDK assertions. The synthesized CloudFormation template is reviewed before any deployment.

Future evidence will distinguish between:

- **Implemented locally:** code and tests exist in the repository.
- **Deployed:** resources were created in AWS.
- **Verified:** functionality or operational behavior was actually tested.

Screenshots, test results, and operational runbooks will be added as the project develops.

## 8. Planned next steps

1. Strengthen infrastructure security tests.
2. Build and test the Flask application locally.
3. Define the application access and management model.
4. Add monitoring and operational procedures.
5. Estimate costs and review deployment prerequisites.
6. Deploy only after explicit approval.
7. Test backup and recovery procedures and document the results.