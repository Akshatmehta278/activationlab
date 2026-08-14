# Run Me First

## 1. Check your machine

```bash
chmod +x setup.sh start.sh scripts/*.sh
./scripts/doctor.sh
```

Fast local mode requires Python 3.12+, Node.js 22+, and npm.

## 2. Fastest local run

From the repository root:

```bash
./setup.sh
./start.sh
```

Open `http://127.0.0.1:5173`.

The first setup installs Python/npm dependencies, creates the SQLite database, applies migrations, and seeds synthetic experiment data.

## 3. Full Docker run

```bash
cp .env.example .env
docker compose up --build
```

Open `http://127.0.0.1:5173`.

Docker mode runs MySQL, RabbitMQ, Redis, Django/Gunicorn, a Celery worker, and React/Nginx.

## 4. Best demo path

1. Finish workspace setup.
2. Connect `shopify-demo`.
3. Click **Use built-in demo CSV**.
4. Create **Welcome Series**.
5. Open **Experiments** and explain the Control vs Guided comparison.
6. Open **Copilot** and explain why it is advisory-only.
7. Run `./scripts/test-local.sh`.
8. Read `INTERVIEW_GUIDE.md` before discussing the project in an interview.

## 5. Stop local mode

Use `Ctrl+C` in the terminal running `./start.sh`.

For Docker:

```bash
docker compose down
```
