# U05 API and Operations Notes

## API

- `POST /api/v1/recommendations`: create a bounded recommendation request.
- `POST /api/v1/recommendations/{session_id}/refine`: apply a versioned conversational refinement.
- `POST /api/v1/recommendations/{session_id}/reset`: create a new session epoch.
- Requests require an authenticated owner boundary and `Idempotency-Key`; schemas reject unknown and oversized fields.

## Degraded Operation

- Missing/withdrawn U02 features: continue without personalization.
- AI timeout, circuit, malformed output or budget exhaustion: deterministic intent and evidence-template output.
- U03 approved catalog or U04 compatible validation unavailable: fail closed without exposed items.
- Failed candidate or Claim validation: discard the failed output; no raw draft reaches serialization.

## Operations

- Prometheus rules: `infra/prometheus/u05-alerts.yml`.
- Grafana dashboard: `infra/grafana/provisioning/dashboards/u05-recommendation.json`.
- Maintenance profile: `docker compose --profile maintenance run recommendation-maintenance`.
- AI remains disabled until HTTPS endpoint, read-only credential, pricing/usage cap and versioned evaluation pass.
