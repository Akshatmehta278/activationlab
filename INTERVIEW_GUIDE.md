# ActivationLab Interview Guide

Use this after you have run the project yourself. The goal is to be able to explain the tradeoffs, not memorize buzzwords.

## 1. One-sentence explanation

ActivationLab is a full-stack SaaS onboarding experiment platform that assigns visitors to stable variants, instruments activation events, imports customer data, and measures whether a guided onboarding flow changes first-value conversion.

## 2. What problem does it solve?

New SaaS customers frequently sign up but never reach the first meaningful product outcome. ActivationLab makes that problem measurable. It defines a four-step activation path and records the funnel:

1. `workspace_created`
2. `integration_connected`
3. `data_imported`
4. `campaign_created`
5. derived event: `onboarding_completed`

The final event is not a page view. It is generated only after all required product milestones exist.

## 3. Why deterministic A/B assignment?

`assign_variant(visitor_id)` hashes the visitor ID and maps it into a 50/50 bucket.

Benefits:
- the same visitor stays in the same experience after refreshes;
- assignment does not require a separate randomization table before session creation;
- testing is deterministic;
- experiment contamination is reduced.

At larger scale, I would add an explicit experiment/exposure table so one user can participate in many experiments with versioned allocation rules.

## 4. Why session state and ProductEvent are separate

`OnboardingSession` answers: **What is true now?**

`ProductEvent` answers: **What happened, and when?**

If I stored only the current state, I could not reconstruct the path a user took, compute time between milestones, debug event delivery, or re-run analytics later.

## 5. Why OnboardingStep has a uniqueness constraint

The database guarantees one `(session, step)` pair. That means clicking an action twice cannot create two completed-step rows and inflate conversion counts.

Application logic also uses `get_or_create`, but the database constraint is the final protection against races.

## 6. CSV import lifecycle

The user uploads a CSV to Django.

Fast local mode:

```text
HTTP request -> CustomerImport -> process_customer_import() -> Customer rows -> data_imported event
```

Docker mode:

```text
HTTP request -> CustomerImport -> RabbitMQ -> Celery worker -> Customer rows -> data_imported event
                                      |
                                      +-> Redis stores Celery result state
```

The request returns an import-job ID. The React UI polls the status endpoint until the job is completed or failed.

## 7. Why RabbitMQ and Celery?

CSV parsing can become slow and unpredictable as files grow. Keeping it inside the web request ties up the Django worker and increases request timeouts.

RabbitMQ provides durable message delivery between the API and workers. Celery executes the task. This also makes retries and independent worker scaling possible.

For the local demo, the same business function runs synchronously so the project stays easy to start.

## 8. Why Redis is not the main customer database

Customer profiles need durable relational persistence and uniqueness constraints, so MySQL is the source of truth. Redis is used as infrastructure for fast ephemeral task-result state. It can later be added as a cache, but the project does not pretend cache state is durable customer truth.

## 9. Experiment statistics

The dashboard calculates:

- activation rate per variant;
- absolute difference in percentage points;
- relative uplift;
- two-proportion z-score;
- two-sided p-value;
- 95% confidence interval for the rate difference;
- sample-ratio-mismatch check.

### Example interview explanation

> If Guided converts at 55% and Control at 40%, the observed difference is +15 percentage points. That is not automatically proof that the design is better. I calculate uncertainty around the difference and a p-value. I also check sample-ratio mismatch because a broken allocator can make downstream significance calculations misleading.

### What the p-value does NOT mean

It does not mean "there is a 95% probability the variant is better." It measures how surprising an observed difference would be under the null model used by the test.

## 10. Sample-ratio mismatch (SRM)

The experiment expects roughly 50/50 assignment. The dashboard uses a chi-square check for whether the observed split is implausible under that expectation.

SRM can reveal bugs such as:
- one variant failing to load;
- assignment depending on a missing browser property;
- selective event loss;
- routing/caching problems.

## 11. Why the seeded data is synthetic

The seed command creates realistic demo traffic so the analytics screen is not empty. It intentionally gives Guided a healthier synthetic funnel.

Never describe the resulting uplift as a real customer result. On a resume, describe what you implemented, not a fabricated performance improvement.

## 12. Copilot safety model

The copilot has two providers:

- `rules`: deterministic local recommendations and zero external dependency;
- `openai`: optional server-side model call when an API key is configured.

The endpoint is advisory-only. Recommendations are returned to the UI, but the copilot does not automatically import data, send campaigns, delete customers, or mutate a production integration.

Other guardrails:
- the API key remains server-side;
- only limited onboarding context is sent;
- the model is instructed not to request secrets;
- model failures fall back to deterministic rules;
- interactions are logged with the provider used.

## 13. Database models to know

### OnboardingSession
Visitor identity, variant, company context, and activation timestamp.

### OnboardingStep
Materialized funnel milestones with an idempotency constraint.

### ProductEvent
Append-style behavioral instrumentation.

### Integration
The connected source for the current onboarding session.

### Customer / CustomerImport
Imported customer profiles and the status of each ingestion job.

### Campaign
The first-value output created during onboarding.

### CopilotInteraction
Audit record of recommendation requests and provider output.

## 14. Request path example

For CSV import:

```text
React uploadCustomerCsv()
    -> POST /api/sessions/:id/imports/
    -> serializer checks file type/size
    -> CustomerImport persisted
    -> customer_import_started event
    -> synchronous processor OR Celery task
    -> CSV rows validated/upserted
    -> data_imported step
    -> customer_import_completed event
    -> React polls status
    -> React refreshes session state
```

## 15. Why MySQL in Docker but SQLite locally?

This is a developer-experience decision.

SQLite gives a reviewer a one-command demo without installing infrastructure. Docker demonstrates that the exact same Django model layer can run against MySQL in a more realistic multi-service environment.

## 16. What would you change for production?

Good answer:

- real authentication/authorization and organizations/workspaces;
- versioned Experiment and Exposure models;
- schema validation and quarantine for bad import rows;
- object storage for uploaded files instead of a shared Docker volume;
- encrypted secrets and a secret manager;
- observability with traces, structured logs, and SLOs;
- rate limits and abuse controls;
- exactly-once-like idempotency keys for external webhooks;
- experiment power calculations and sequential-testing policy;
- CI/CD and infrastructure-as-code for cloud deployment;
- background deletion/retention policies for customer data;
- explicit consent/privacy controls.

## 17. Failure scenarios you should be able to discuss

### User uploads same CSV twice
Current design upserts each customer by `(session, external_id)`, so customer rows are not duplicated. Import jobs and import events are still separate attempts.

### Worker crashes halfway through
Celery is configured for late acknowledgement and rejection on worker loss, so broker redelivery can replay the task after an actual worker crash. Some rows may already have been upserted; `(session, external_id)` upsert semantics make customer-row replay safe. Permanent validation/domain failures are recorded as failed jobs rather than blindly retried. A stricter production system would add row checkpoints and explicit retry classification.

### RabbitMQ is unavailable
Docker async imports cannot be queued. The API should surface queue failure. The local mode avoids this dependency by processing synchronously.

### OpenAI API is unavailable
The copilot falls back to the local rules provider, so onboarding still works.

### The same onboarding button is clicked twice
The unique `(session, key)` constraint prevents duplicate step completion.

## 18. Five strong interview questions you can answer from this project

1. How would you design an A/B testing platform for product onboarding?
2. How do you prevent duplicate analytics events from corrupting a funnel?
3. When should work move from an HTTP request into a queue?
4. How would you detect a broken experiment allocation?
5. How do you make an AI assistant useful without giving it unsafe autonomy?

## 19. 60-second project pitch

> I built ActivationLab to model the engineering behind SaaS activation. A React/TypeScript client guides a user through workspace setup, integration, CSV customer import, and a first campaign. Django persists product state and append-style events, and assigns a stable A/B variant from the visitor ID. The analytics endpoint computes the funnel by variant, a two-proportion significance test, confidence interval, and sample-ratio-mismatch guardrail. For local demos, CSV processing is synchronous with SQLite; in Docker the same import moves through RabbitMQ to Celery, persists to MySQL, and uses Redis for task results. I also added a human-in-the-loop onboarding copilot that defaults to explainable local rules and can optionally use a server-side model without giving it automatic destructive actions.

## 20. How the AWS/Terraform blueprint maps the system

The `infra/terraform` directory maps the Docker topology to managed infrastructure:

- Application Load Balancer routes normal traffic to the frontend and `/api/*` to Django.
- React/Nginx, Django/Gunicorn, and Celery run as independently scalable ECS/Fargate services.
- RDS MySQL stores transactional application/customer state.
- ElastiCache Redis stores Celery result/cache-style state.
- Amazon MQ provides a managed RabbitMQ-compatible broker.
- CloudWatch receives container logs.

The important interview point is independent scaling: HTTP containers scale with request traffic while worker containers scale with queue depth and import latency.

The Terraform is a reference architecture. Do not claim it is a live production deployment unless you actually deploy it.

## 21. Why I did not add every possible database/tool

A strong architecture does not add technologies simply to match a keyword list. MySQL is appropriate for the current transactional customer/onboarding model, RabbitMQ decouples async jobs, and Redis serves ephemeral task state. If event volume grew beyond what the transactional database should handle, I would introduce a dedicated streaming/analytics path based on measured requirements rather than adding another datastore without a workload that needs it.

That answer is stronger than saying "I used five databases because the job description mentioned them."
