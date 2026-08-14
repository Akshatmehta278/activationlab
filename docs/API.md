# API Guide

Base path: `/api/`

## Health

### `GET /api/health/`

Returns service mode and dependency configuration.

Example:

```json
{
  "status": "ok",
  "service": "activationlab-api",
  "database": "sqlite3",
  "async_imports": false,
  "copilot": "rules"
}
```

## Sessions

### `POST /api/sessions/`

Create or retrieve a visitor session.

```json
{
  "visitor_id": "4fe823d8-3dd1-4d27-ae42-792f805c9dfa"
}
```

The server determines the experiment variant; the client does not choose it.

### `GET /api/sessions/{visitor_id}/`

Read current onboarding state.

### `PATCH /api/sessions/{visitor_id}/profile/`

Create/update the workspace profile and complete the workspace milestone.

```json
{
  "company_name": "Northstar Commerce",
  "business_type": "Ecommerce"
}
```

## Integration

### `POST /api/sessions/{visitor_id}/integration/`

```json
{
  "provider": "shopify-demo",
  "external_store_id": "demo-store-42"
}
```

## Customer import

### `POST /api/sessions/{visitor_id}/imports/`

Multipart form upload with field name `file`.

Returns `202 Accepted` because Docker mode may process the file asynchronously.

### `GET /api/sessions/{visitor_id}/imports/{import_id}/`

Poll import state.

## Campaign

### `POST /api/sessions/{visitor_id}/campaigns/`

```json
{
  "name": "Welcome Series",
  "channel": "email"
}
```

## Copilot

### `POST /api/sessions/{visitor_id}/copilot/`

```json
{
  "goal": "Help a new ecommerce merchant reach first value faster"
}
```

The response contains a provider indicator and advisory recommendations.

## Analytics

### `GET /api/metrics/`

Returns:

- overall sessions and activation;
- per-variant conversion;
- experiment statistics;
- funnel completion;
- event counts;
- import-state summary;
- average time to activation.

### `GET /api/events/recent/`

Returns recent product events for debugging/demo inspection.

## Error behavior

DRF serializer validation returns `400` with field-specific errors. Missing session/import resources return `404`. File-import domain failures are persisted on the `CustomerImport` record so clients can distinguish transport acceptance from background processing success.
