# Security Policy

ActivationLab is a demonstration/portfolio project and should not be used to store sensitive production customer data without additional hardening.

## Supported version

Security fixes target the current `main` branch.

## Reporting a vulnerability

Please avoid opening a public issue for a vulnerability that would expose secrets, customer data, or a practical exploit path. Use a private GitHub security advisory if the repository has that feature enabled.

Include:

- affected component;
- reproduction steps;
- impact;
- suggested mitigation if known.

Do not include real credentials or customer PII in a report.

## Secrets

Never commit:

- `.env`;
- API keys;
- database passwords used outside local development;
- private keys;
- real customer CSVs.
