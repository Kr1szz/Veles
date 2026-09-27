# API reference

Base URL for local development: `http://localhost:8000`. OpenAPI docs are available at `/docs` when enabled.

## Authentication behavior

Local development defaults to `AUTH_ENABLED=false`; role-protected API routes use a local demo administrator identity and require no token. This mode is intended for localhost synthetic-data demos only. With `AUTH_ENABLED=true`, protected endpoints require a JWT bearer token or the authentication cookie. Production startup requires authentication to be enabled.

## Verification

### `POST /api/v1/verify/kyc`

Required fields: `full_name`, `email`, `consent_given`. Optional fields include `phone`, `id_type` (`PAN`, `AADHAAR`, `PASSPORT`, `VOTER_ID`), `id_number`, `country_code`, `device_fingerprint`, `ip_address`, and `consent_purpose`.

### `POST /api/v1/verify/transaction`

Required fields: `user_id`, `amount`. Optional fields include `currency`, `device_fingerprint`, `ip_address`, `user_historical_mean`, `user_historical_var`, and `user_history_count`.

Both endpoints return `verification_id`, `entity_type`, `decision`, `risk_score`, `latency_ms`, `sla_met`, `triggered_rules`, `anomaly_breakdown`, `masked_identifiers`, `audit_hash`, and `timestamp`. A reported decision/latency is a prototype output, not a calibrated fraud conclusion or SLA guarantee.

### `GET /api/v1/verify/records`

Query parameters: `entity_type`, `decision`, `limit` (1–200), and `offset`. Returns masked record fields and pagination metadata.

## Company website crawler

### `POST /api/v1/crawler/crawl`

Example:

```json
{
  "url": "https://example.com",
  "max_pages": 10
}
```

`max_pages` defaults to 20 and must be between 1 and 50. The crawler is synchronous and returns a completed run with `id`, `origin`, status/counts, timestamps, and `pages`. Each page includes URL, HTTP status, title, description, headings, same-origin links, a short text excerpt, fetch time, and an optional error. Private/local targets and external redirects are rejected. The crawler respects `robots.txt` and is intended for small authorized crawls.

### `GET /api/v1/crawler/runs?limit=20`

Returns recent stored crawl summaries. `limit` must be 1–100.

### `GET /api/v1/crawler/runs/{run_id}`

Returns one stored crawl and its extracted pages, or `404` if it does not exist.

## Dashboard data

- `GET /api/v1/metrics` — stored decision counts, observed latency percentiles over at most the latest 5,000 records, the sample size, configured processing-time target, and infrastructure flags. `active_velocity_keys` is the in-process fallback map count, not a Redis-wide count.
- `GET /api/v1/events/recent` — process-local recent verification events.
- `GET /api/v1/events/stream` — process-local Server-Sent Events stream.
- `GET /api/v1/reviews/queue` — verification records in `REVIEW` status.
- `POST /api/v1/reviews/{verification_id}/override` — submit `override_decision` (`APPROVE`, `REJECT`, or `ESCALATE`) and `review_notes`.
- `GET /api/v1/rules` — active code/config rule descriptions.
- `GET /api/v1/dpdpa/audit-ledger` and `POST /api/v1/dpdpa/audit-ledger/verify` — audit entries and chain verification.
- `GET /api/v1/dpdpa/consents` — consent records.
- `POST /api/v1/dpdpa/erasure` — request field erasure by identifier and reason. It is destructive; production use requires authorization and an approved retention process.

## Authentication endpoints

When authentication is enabled, `POST /api/v1/auth/login` accepts `username` and `password`, and `GET /api/v1/auth/me` returns the current user. `POST /api/v1/auth/logout` clears the session cookie. Account provisioning is not exposed by this API.
