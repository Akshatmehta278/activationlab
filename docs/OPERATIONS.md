# Operations and Failure Modes

## Health checks

The API exposes `/api/health/` and Docker Compose configures service health checks for MySQL, Redis, RabbitMQ, and the Django API.

## CSV import failure modes

### Invalid row

Rows without a usable customer identity are counted as failed while other rows continue processing.

### Worker failure

Celery uses late task acknowledgement and rejects work on worker loss, allowing RabbitMQ to redeliver a task when a worker process disappears mid-import. Customer upserts make replay safe at the row identity level. Domain/validation failures are persisted as failed import jobs instead of being indiscriminately retried. A production worker should additionally add:

- bounded automatic retries for specifically classified transient errors;
- retry backoff/jitter;
- dead-letter handling;
- task heartbeat/staleness detection;
- idempotency token / import checksum;
- alerting on repeated failures.

### Duplicate customer

`update_or_create()` plus the `(session, external_id)` unique constraint prevents duplicate records for the same logical customer within a session.

### Duplicate onboarding request

`OnboardingStep.get_or_create()` plus the database unique constraint makes milestone completion idempotent.

## Database failure

The API should fail health/readiness checks and stop accepting traffic in a production orchestrator until connectivity recovers. Connection pooling and bounded query timeouts should be added at production scale.

## Broker failure

HTTP upload acceptance should not falsely report successful processing. The current design returns an import job, then lets the client observe processing state. A production system should explicitly handle enqueue failures and avoid leaving jobs permanently pending without alerting.

## Observability roadmap

Recommended production instrumentation:

- structured JSON logs;
- request IDs propagated through queue tasks;
- OpenTelemetry traces across browser/API/worker;
- API latency/error-rate metrics;
- queue depth and task age;
- import throughput/failure rate;
- database connection saturation;
- activation-funnel business metrics;
- experiment data-quality alerts.

## Scaling path

### API

Stateless Django containers scale horizontally behind a load balancer.

### Workers

Celery workers can scale separately based on queue depth and import latency.

### Database

RDS MySQL can scale vertically/read-replica-first, with schema/query tuning before introducing more complex storage patterns.

### Event analytics

Behavioral events should eventually leave the transactional database and flow through a durable stream/outbox into an analytics store.

## Disaster recovery

For production:

- automated RDS backups and point-in-time recovery;
- multi-AZ database deployment;
- infrastructure-as-code recreation;
- object-storage versioning/retention as required;
- tested restore runbook;
- explicit RPO/RTO targets.
