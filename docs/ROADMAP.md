# Roadmap

## Implemented

- React/TypeScript onboarding experience
- Django REST API
- deterministic experiment assignment
- product-event instrumentation
- four-step activation funnel
- CSV customer ingestion
- MySQL/SQLite persistence profiles
- RabbitMQ + Celery async worker profile
- Redis result backend
- experiment analytics and significance calculation
- sample-ratio mismatch guardrail
- rules-based copilot fallback
- optional server-side AI provider
- Docker Compose
- backend behavioral tests
- GitHub Actions CI
- Terraform AWS reference architecture

## Next engineering milestones

### Product

- authenticated user/workspace model
- resumable onboarding across authenticated devices
- real integration OAuth flow
- campaign preview editor
- customer segmentation UI

### Experimentation

- experiment IDs/versions
- configurable traffic allocation
- holdouts and mutually exclusive layers
- power/sample-size calculator
- exposure event distinct from assignment
- sequential testing or fixed-horizon enforcement

### Platform

- transactional outbox for product events
- object storage for imports
- dead-letter queue and retry policy
- rate limiting
- OpenTelemetry tracing
- centralized dashboards/alerts

### Data

- schema versioning for product events
- warehouse export
- cohort/retention metrics
- segment evaluation on customer behavior
