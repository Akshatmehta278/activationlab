# Contributing

Thanks for taking an interest in ActivationLab.

## Development setup

```bash
chmod +x setup.sh start.sh scripts/*.sh
./setup.sh
./start.sh
```

Before opening a pull request:

```bash
./scripts/test-local.sh
```

## Pull-request expectations

- keep product/domain logic in backend services rather than duplicating it in UI code;
- add or update tests for behavioral changes;
- do not commit `.env`, database files, uploaded customer data, or API keys;
- keep seeded data synthetic;
- document significant architectural decisions;
- avoid representing demo metrics as real customer outcomes.

## Commit style

Short imperative commits are preferred, for example:

```text
Add import retry state
Document experiment guardrails
Refactor activation service
```

## Reporting bugs

Use the bug issue template and include:

- execution profile (local or Docker);
- operating system;
- steps to reproduce;
- expected behavior;
- observed behavior;
- relevant logs with secrets removed.
