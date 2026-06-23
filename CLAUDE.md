# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A small FastAPI demo app, containerized with Docker, deployed to AWS ECS on
Fargate behind an ALB, provisioned with Terraform, deployed by GitHub Actions
via OIDC (no long-lived AWS keys in CI). Deliberately kept minimal as a clear,
demonstrable reference, not a production template — see "Production
hardening" in README.md for what's intentionally left out.

## Commands

```bash
uv sync --dev                          # install deps (incl. dev group)
uv run uvicorn app.main:app --reload   # run locally, http://localhost:8000
uv run pytest -q                       # run tests
uv run pytest tests/test_main.py::test_health   # run a single test
uv run ruff check .                    # lint
```

Docker:

```bash
docker build -t fastapi-ecs-demo .
docker run -p 8000:8000 fastapi-ecs-demo
# or: docker compose up --build
```

Terraform (run from `terraform/`):

```bash
terraform init
terraform apply -target=aws_ecr_repository.app   # first apply only, see below
terraform apply
terraform destroy
```

## Architecture

**App** (`app/main.py`): single-file FastAPI app, in-memory dict store for
`/items` (no database — by design, this is a demo). Routes: `/`, `/health`
(used by both the ECS container health check and the ALB target group),
`/items` CRUD.

**Container** (`Dockerfile`): multi-stage build. Builder stage resolves deps
with `uv sync --frozen`; dependency installation is split into its own layer
(copy `pyproject.toml`/`uv.lock`, sync `--no-install-project`, then copy
`app/` and sync again) so dependency layers cache independently of source
changes. Runtime stage is `python:3.12-slim`, runs as non-root `appuser`,
no build tooling present.

**Infra** (`terraform/`), one AWS account, region `eu-west-2` by default:

- Reuses the account's *default VPC* and its public subnets — no NAT
  Gateway, tasks get public IPs directly (`network.tf`). This is a cost/
  simplicity tradeoff explicit to the demo; don't "fix" it without being asked.
- Two distinct IAM roles in `ecs.tf`: **execution role** (ECS agent — pulls
  image, writes logs) vs **task role** (the app's own runtime permissions,
  currently empty). Never widen the execution role for app permissions —
  attach new policies to the task role only, that separation is intentional.
- `aws_ecs_service.app` has `lifecycle { ignore_changes = [task_definition] }`
  — Terraform creates the first revision, then CI/CD (`amazon-ecs-deploy-task-definition`
  in `deploy.yml`) owns every revision after that. Don't remove this or
  `terraform apply` will fight every CI deploy.
- ECR repo is `image_tag_mutability = "IMMUTABLE"`; deploys are tagged with
  the git SHA, not `latest`.
- `iam_oidc.tf` sets up the GitHub OIDC trust so Actions can assume a role
  without stored credentials. Note the comment about one OIDC provider per
  AWS account per URL — if another project already created the
  `token.actions.githubusercontent.com` provider, swap the `resource` block
  for the `data` source described inline.
- Terraform state is local by default; there's a commented S3+DynamoDB
  backend stub in `providers.tf` for when this moves past demo stage.

**Deploy bootstrap order** matters because of a chicken-and-egg problem: the
ECR repo must exist before an image can be pushed, but the ECS service needs
an image to start. First-time setup is: `terraform apply -target=aws_ecr_repository.app`
→ build/push an initial image manually → `terraform apply` for everything
else. Full sequence is in README.md §4.

**CI/CD** (`.github/workflows/deploy.yml`): on push to `main`, runs tests,
then (only if tests pass) builds/pushes a SHA-tagged image to ECR, renders a
new task definition from the current one with the new image, and deploys via
`amazon-ecs-deploy-task-definition` with `wait-for-service-stability: true`.
