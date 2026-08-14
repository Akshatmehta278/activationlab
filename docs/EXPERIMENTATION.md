# Experimentation Design

## Question

Does a guided onboarding experience improve the probability that a new SaaS visitor reaches the defined activation milestone compared with the standard onboarding experience?

## Primary metric

**Activation rate**

```text
activated sessions / assigned sessions
```

Activation requires all four milestones:

1. workspace created;
2. integration connected;
3. customer data imported;
4. campaign draft created.

This is stronger than measuring a click because it represents completion of a meaningful product setup sequence.

## Secondary diagnostic metrics

- step completion by funnel stage;
- time to activation;
- import success/failure state;
- event volumes by type.

## Assignment

The project performs deterministic 50/50 assignment from `visitor_id`.

A production system should include an `experiment_id` and allocation version in the hash input so the same visitor can be independently assigned across experiments while remaining stable within each one.

## Statistical comparison

The dashboard uses a pooled two-proportion z-test for the difference in activation rates between Control and Guided.

For variant conversion rates `p1` and `p2`, the application reports:

- absolute difference in percentage points;
- relative uplift;
- z-score;
- two-sided p-value;
- 95% confidence interval for the difference.

## Interpretation

A small p-value is evidence against the null hypothesis under the test assumptions; it is **not** the probability that the treatment is good or the probability that the null hypothesis is true.

The confidence interval communicates the plausible range of the treatment effect under the model. Product decisions should consider effect size and business relevance, not statistical significance alone.

## Sample-ratio mismatch

The dashboard includes a basic sample-ratio mismatch guardrail. A severe departure from the expected 50/50 allocation can indicate assignment, logging, routing, bot, or instrumentation problems.

In a mature experimentation platform, SRM checks would be performed using a chi-square or exact method with an explicit threshold and would alert before results were trusted.

## Biases this demo does not solve

- novelty effects;
- cross-device identity resolution;
- cookie deletion;
- bot traffic;
- seasonality;
- interference between users;
- repeated peeking / optional stopping;
- multiple-comparison correction;
- treatment noncompliance;
- heterogeneous treatment effects.

## Production experiment lifecycle

A production-ready workflow would add:

1. written hypothesis and expected mechanism;
2. primary metric and guardrails selected before launch;
3. minimum detectable effect;
4. power/sample-size calculation;
5. experiment owner and rollout plan;
6. exposure logging;
7. quality checks such as SRM;
8. fixed analysis window or sequential-testing framework;
9. documented decision and follow-up.

## Synthetic data policy

The seed command generates artificial sessions and outcomes to make the dashboard usable immediately. Those outcomes are test/demo fixtures only and must not be reported as a real conversion lift.
