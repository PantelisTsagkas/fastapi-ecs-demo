# fastapi-ecs-demo

A small FastAPI app, containerized with Docker, deployed to AWS ECS on Fargate
behind an Application Load Balancer, provisioned with Terraform, deployed by
GitHub Actions via OIDC (no AWS access keys in CI).

## Stack

- App: FastAPI, dependency management via `uv`
- Container: multi-stage Dockerfile, non-root runtime user
- Registry: Amazon ECR (image scanning on push)
- Compute: ECS on Fargate (serverless, no EC2 to patch)
- Networking: ALB → ECS service, target-tracking autoscaling on CPU
- IaC: Terraform
- CI/CD: GitHub Actions, OIDC role assumption

## 1. Local development

```bash
uv sync --dev
uv run uvicorn app.main:app --reload
```

Visit `http://localhost:8000/health`. Run tests with `uv run pytest`.

## 2. Build and run in Docker

```bash
docker build -t fastapi-ecs-demo .
docker run -p 8000:8000 fastapi-ecs-demo
# or: docker compose up --build
```

Same `/health` check, now coming from the container.

## 3. AWS prerequisites

- AWS CLI configured locally (`aws configure` or SSO), with permissions to
  create ECR, ECS, IAM, ELB, and CloudWatch resources.
- Terraform >= 1.7.
- Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars`
  and fill in your GitHub org/repo (used to scope the OIDC trust policy so
  *only* your repo can assume the deploy role).

## 4. First deploy (chicken-and-egg: the ECR repo must exist before you can push an image)

```bash
cd terraform
terraform init
terraform apply -target=aws_ecr_repository.app   # create just the registry first
```

Build, tag, and push an initial image so the ECS service has something to run:

```bash
cd ..
aws ecr get-login-password --region eu-west-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-2.amazonaws.com

docker build -t fastapi-ecs-demo .
docker tag fastapi-ecs-demo:latest <account-id>.dkr.ecr.eu-west-2.amazonaws.com/fastapi-ecs-demo:latest
docker push <account-id>.dkr.ecr.eu-west-2.amazonaws.com/fastapi-ecs-demo:latest
```

Now create everything else:

```bash
cd terraform
terraform apply
```

Take the `alb_dns_name` output and hit `/health` on it. Also note the
`github_actions_role_arn` output, you'll need it next.

## 5. Wire up CI/CD

In your GitHub repo: Settings → Secrets and variables → Actions → Variables,
add `AWS_GITHUB_ACTIONS_ROLE_ARN` set to the `github_actions_role_arn` output.
Push to `main` and the workflow builds, tests, pushes a commit-SHA-tagged
image, and updates the ECS service. Terraform won't fight this: the service's
`task_definition` is set to `ignore_changes`, so CI owns deploys after the
first apply.

## Cost note

This is sized to be cheap for a demo, not free. Roughly, running 24/7 in
`eu-west-2`:

- Fargate task (0.25 vCPU / 0.5 GB, smallest size): ~£7-9/month
- ALB: ~£14-18/month base, plus a small per-request charge
- Public IPv4 on the task (assigned since there's no NAT Gateway): ~£3/month

Call it **£25-35/month** if left running continuously. Nothing here uses the
AWS Free Tier. Run `terraform destroy` when you're not actively testing it:

```bash
cd terraform
terraform destroy
```

ECR images persist independently of `destroy` unless you also remove the
repository; the lifecycle policy only expires *untagged* images after 7 days.

## Production hardening (not done here, deliberately, to keep this a clear demo)

- Move tasks into private subnets behind a NAT Gateway or VPC endpoints,
  drop `assign_public_ip`
- Add an ACM certificate and a 443 listener on the ALB, redirect 80 → 443
- Move Terraform state to S3 with a DynamoDB lock table (commented stub in
  `providers.tf`)
- If the app needs to call other AWS services, attach narrowly-scoped
  policies to the `task` role only, never the `execution` role
- Consider Fargate Spot for non-critical workloads to cut compute cost ~70%
