# Architecture

## Goals

ActivationLab is designed to demonstrate a product-engineering system that is easy to run locally while still exposing realistic architectural decisions around experimentation, customer data, asynchronous work, reliability, and AI-assisted UX.

The project therefore separates concerns into four layers:

1. **Experience layer** — React/TypeScript onboarding, experiment dashboard, and copilot.
2. **Application layer** — Django REST endpoints and serializers.
3. **Domain/services layer** — experiment assignment, event tracking, activation rules, customer ingestion, statistics, and copilot policy.
4. **Infrastructure layer** — MySQL, RabbitMQ, Celery, Redis, Docker, and an AWS/Terraform reference architecture.

## Domain model

### `OnboardingSession`

Represents one visitor participating in the onboarding experience. It owns the stable experiment variant and activation timestamp.

### `OnboardingStep`

Stores durable completion of the four activation milestones. A database uniqueness constraint on `(session, key)` makes milestone completion idempotent.

### `ProductEvent`

Stores behavioral events independently of current session state. This separation allows the application to answer both "what is true now?" and "what happened over time?"

### `Integration`

Represents the connected source system for a session.

### `CustomerImport`

Tracks an uploaded customer-data job through `pending`, `processing`, `completed`, or `failed` states.

### `Customer`

Stores imported customer profiles. The `(session, external_id)` uniqueness constraint makes upsert behavior safe for repeated imports.

### `Campaign`

Represents a campaign draft created as the final activation milestone.

### `CopilotInteraction`

Persists recommendation-provider metadata and output for auditability.

## Request lifecycle

A typical onboarding action follows:

```text
React UI
  -> typed API helper
  -> DRF endpoint
  -> serializer validation
  -> domain service
  -> database transaction / event
  -> serialized response
  -> UI state update
```

Domain rules such as activation detection live in `services.py` rather than React or endpoint glue. This keeps behavior testable and prevents multiple clients from implementing different business logic.

## Activation transaction

`complete_step()` uses an atomic transaction and `get_or_create()` for milestone persistence. It then checks whether the required milestone set is a subset of the completed set. The first request that completes the funnel writes `activated_at` and emits `onboarding_completed`.

This gives the system two protections:

- duplicate step requests do not produce duplicate milestones;
- activation is emitted only once because `activated_at` must still be `NULL`.

For a higher-throughput production system, the activation row would likely be locked with `select_for_update()` or emitted through an outbox pattern to guarantee exactly-once downstream publication semantics.

## Experiment assignment

Assignment is based on a SHA-256 hash of a stable visitor identifier. The first 32-bit segment is mapped to a 50/50 bucket.

This is deliberately deterministic rather than random-per-request. The goal is stable treatment membership, not cryptographic secrecy.

Production extensions would include:

- experiment ID and version in the hash input;
- configurable allocation percentages;
- mutually exclusive experiment layers;
- holdouts;
- persisted exposure timestamps;
- assignment-service audit logs.

## Event model

The MVP stores events in MySQL because it keeps the runnable system compact. In a larger platform, behavioral events would usually be separated from transactional application data and streamed to an analytics store.

A reasonable evolution path is:

```text
Django -> durable event outbox -> stream/queue -> event processors -> warehouse/OLAP store
```

The current `ProductEvent` table demonstrates event naming, metadata, timestamps, and analytics aggregation without requiring a separate warehouse to run the project.

## Import pipeline

Local mode processes uploads synchronously for low setup cost. Docker mode uses RabbitMQ and Celery so an HTTP request does not remain open while potentially large customer files are parsed.

The state machine is:

```text
pending -> processing -> completed
                     \-> failed
```

Import rows use upsert semantics on `(session, external_id)` so replaying a customer record updates rather than duplicates it.

## Redis responsibility

Redis is used as Celery's result backend in the Docker profile. It is intentionally not the primary customer database. Customer profiles need durable relational constraints and transactional behavior, so MySQL is the source of truth.

## AI boundary

The copilot receives product state and returns recommendations only. The model path is not given tools that can mutate product state. This is a deliberate least-privilege design:

```text
user goal + product state -> recommendation provider -> JSON recommendations -> human decision
```

The rules engine provides a deterministic fallback when no external provider is configured.

## Production topology

The Terraform directory documents an AWS-oriented target topology using:

- ECS/Fargate for stateless web/API/worker compute;
- RDS MySQL for transactional state;
- ElastiCache Redis for task/result/cache workloads;
- Amazon MQ-compatible RabbitMQ endpoint or equivalent managed broker;
- ALB for ingress;
- Secrets Manager/SSM for secrets;
- CloudWatch for logs/metrics.

The Terraform is a reference deployment blueprint, not a claim that a public production environment is currently running.
