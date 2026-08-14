# ActivationLab API Examples

Backend local URL: `http://127.0.0.1:8000`

## Health

```bash
curl http://127.0.0.1:8000/api/health/
```

## Create/get a session

```bash
curl -X POST http://127.0.0.1:8000/api/sessions/ \
  -H 'Content-Type: application/json' \
  -d '{"visitor_id":"demo-manual-1"}'
```

## Workspace

```bash
curl -X PATCH http://127.0.0.1:8000/api/sessions/demo-manual-1/profile/ \
  -H 'Content-Type: application/json' \
  -d '{"company_name":"Northstar Commerce","business_type":"Ecommerce"}'
```

## Integration

```bash
curl -X POST http://127.0.0.1:8000/api/sessions/demo-manual-1/integration/ \
  -H 'Content-Type: application/json' \
  -d '{"provider":"shopify-demo","external_store_id":"store-123"}'
```

## Customer CSV

```bash
curl -X POST http://127.0.0.1:8000/api/sessions/demo-manual-1/imports/ \
  -F 'file=@sample-data/customers.csv'
```

If the response returns import ID `1`:

```bash
curl http://127.0.0.1:8000/api/sessions/demo-manual-1/imports/1/
```

## Create campaign

```bash
curl -X POST http://127.0.0.1:8000/api/sessions/demo-manual-1/campaigns/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"Welcome Series","channel":"email"}'
```

## Copilot

```bash
curl -X POST http://127.0.0.1:8000/api/sessions/demo-manual-1/copilot/ \
  -H 'Content-Type: application/json' \
  -d '{"goal":"Help the merchant reach first value safely"}'
```

## Experiment metrics

```bash
curl http://127.0.0.1:8000/api/metrics/
```

## Recent events

```bash
curl http://127.0.0.1:8000/api/events/recent/
```
