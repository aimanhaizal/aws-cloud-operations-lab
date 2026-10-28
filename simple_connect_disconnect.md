## 1. Start the dashboard webpage

### Step 1 — Check whether EC2 is running

Open your terminal on your local computer:

```
cd /home/work/aws-cloud-operations-lab

export AWS_PROFILE=portfolio-dev
export AWS_REGION=ap-southeast-1
export INSTANCE_ID=i-0cd747d495eabf8c0

aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text
```

If the result is `running`, continue to Step 2.

If it says `stopped`, start it:

```
aws ec2 start-instances --instance-ids "$INSTANCE_ID"
```

Wait until it is ready:

```
aws ec2 wait instance-status-ok --instance-ids "$INSTANCE_ID"
```

This wait command can take a few minutes. EC2 compute charges resume while the instance is running.

### Step 2 — Open the port-forwarding session

Run this in your local terminal:

```
aws ssm start-session \
  --target "$INSTANCE_ID" \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8001"],"localPortNumber":["18001"]}'
```

Keep this terminal open while you use the webpage. This forwards your local port `18001` to port `8001` on EC2.

### Step 3 — Open the webpage and take your screenshot

Open this address in your browser:

## [http://127.0.0.1:18001/](http://127.0.0.1:18001/)

## 2. Stop EC2 after taking the screenshot

### Step 1 — Stop the instance

```
aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
```

Wait until it has stopped:

```
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"
```

Verify the result:

```
aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text
```

Expected output:

```
stopped
```
