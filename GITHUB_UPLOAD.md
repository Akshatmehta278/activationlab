# Publish to GitHub

The recommended approach is to extract the ZIP, verify the project locally, and push the repository with Git. Do **not** commit `.env`, `backend/.venv`, `node_modules`, database files, or real customer data; `.gitignore` is already configured for these.

## Option 1 — terminal

Create an empty GitHub repository named `activationlab`, then from this project folder run:

```bash
git init
git branch -M main
git add .
git commit -m "Build ActivationLab onboarding and experimentation platform"
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Option 2 — GitHub Desktop

1. Extract the ZIP.
2. Open GitHub Desktop.
3. Choose **Add Existing Repository** / create a repository from this folder.
4. Commit all tracked files.
5. Publish the repository.

## Recommended repository settings

- Description: `Full-stack SaaS onboarding, experimentation, customer-data ingestion, and AI-assisted activation platform.`
- Topics: `react`, `typescript`, `django`, `python`, `ab-testing`, `product-analytics`, `rabbitmq`, `celery`, `redis`, `mysql`, `docker`, `terraform`, `aws`
- Enable Issues and Actions.
- Enable Dependabot alerts if available.

## Before sharing with recruiters

- run the application yourself;
- run `./scripts/test-local.sh`;
- confirm GitHub Actions passes after the first push;
- replace any placeholder repository metadata you choose to add;
- do not claim synthetic demo uplift as a real customer result;
- be prepared to explain the architecture and tradeoffs in `INTERVIEW_GUIDE.md`.
