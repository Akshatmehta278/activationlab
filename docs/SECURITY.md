# Security Model

ActivationLab is a portfolio project, but security decisions are intentionally explicit.

## Secrets

- `.env` is ignored by Git.
- `.env.example` contains only development-safe placeholders.
- external AI provider keys are read by Django only;
- the React bundle never receives server secrets.

For a real deployment, secrets should be stored in a managed secret store such as AWS Secrets Manager or SSM Parameter Store and injected at runtime.

## AI least privilege

The copilot has no direct mutation tools. It returns recommendations for a human to review. This prevents an LLM response from autonomously:

- deleting customer data;
- sending a campaign;
- changing integrations;
- running shell commands;
- performing arbitrary database writes.

## Uploads

The Django configuration limits upload memory size. Production hardening should additionally include:

- object storage instead of a shared filesystem;
- explicit file-size limits at ingress;
- content-type and extension validation;
- malware scanning where appropriate;
- CSV formula-injection defenses before exporting data;
- row-count and field-length limits;
- retention/deletion policy.

## Authentication and tenancy

The demo intentionally avoids account provisioning so the onboarding flow is easy to exercise. A production version must add:

- authenticated users;
- organizations/tenants;
- RBAC;
- per-tenant query scoping;
- authorization tests;
- audit logs for privileged actions.

## Web security

Django supplies CSRF, clickjacking, and standard security middleware. Production should additionally enforce HTTPS, HSTS, secure cookies, strict allowed hosts/origins, and a Content Security Policy at the ingress/frontend layer.

## Data minimization

The sample dataset contains synthetic data. Do not upload real customer PII to a public demo environment.

## Vulnerability reporting

See the root [`SECURITY.md`](../SECURITY.md) for responsible disclosure guidance.
