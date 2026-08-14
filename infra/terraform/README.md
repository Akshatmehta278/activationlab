# AWS / Terraform Reference Architecture

This directory demonstrates how the local Docker topology maps to managed AWS infrastructure.

It is intentionally a **reference blueprint**, not a claim that this repository currently runs a public production environment.

## Services represented

| Local service | AWS-oriented mapping |
|---|---|
| Nginx frontend container | ECS/Fargate behind ALB |
| Django/Gunicorn container | ECS/Fargate behind ALB |
| Celery worker | independent ECS/Fargate service |
| MySQL | RDS MySQL |
| Redis | ElastiCache for Redis |
| RabbitMQ | Amazon MQ for RabbitMQ |
| container logs | CloudWatch Logs |

## Why separate backend and worker services?

API traffic and background import work scale differently. A queue backlog should be handled by increasing worker capacity without unnecessarily scaling HTTP containers.

## Usage

You need Terraform and AWS credentials plus already-published backend/frontend container images. Build the AWS frontend image with `frontend/Dockerfile.aws`; unlike the local Docker image, it does not proxy `/api` internally because the ALB performs path routing.

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
```

Supply secrets securely rather than committing them. For example:

```bash
export TF_VAR_database_password='...'
export TF_VAR_rabbitmq_password='...'
export TF_VAR_django_secret_key='...'
```

Then:

```bash
terraform apply
```

## Cost warning

This configuration creates billable AWS resources including RDS, ElastiCache, Amazon MQ, ECS/Fargate, and an ALB. It is intended for architecture demonstration and controlled testing, not casual unattended deployment.

Destroy resources when finished:

```bash
terraform destroy
```

## Production hardening still required

Before real internet-facing use, add:

- ACM certificate and HTTPS listener;
- Route 53/domain configuration;
- AWS WAF/rate limiting where appropriate;
- NAT/private-subnet design for application tasks or VPC endpoints;
- Secrets Manager/SSM secret injection instead of plain ECS environment values;
- RDS Multi-AZ and deletion protection;
- Redis replication/failover;
- multi-instance RabbitMQ deployment;
- ECS autoscaling based on CPU/latency/queue depth;
- S3 for uploaded files;
- CloudWatch alarms and distributed tracing;
- CI/CD image build, scan, promotion, and rollback.

## Interview discussion point

The important design choice is not "AWS because cloud." It is mapping each workload to the reliability/scaling characteristics it needs:

- stateless HTTP compute can scale horizontally;
- worker compute scales with queue depth;
- relational customer state remains transactional;
- queueing decouples request latency from import processing;
- cache/result state is isolated from the source-of-truth database;
- infrastructure is reproducible through code.
