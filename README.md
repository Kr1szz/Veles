# Veles Shield

Veles Shield is a local demonstration app for verification risk scoring, review workflows, audit records, and bounded company-site crawling. It is a prototype; it has not been independently validated for fraud accuracy, regulatory compliance, or production readiness.

## Current capabilities

- KYC and transaction verification endpoints with rule-based and anomaly signals.
- A React dashboard for recent decisions, metrics, review queue, rules, and audit records.
- A website crawler that extracts public page metadata and short text excerpts. It follows same-origin links, honors `robots.txt`, applies page and response limits, and saves results in the configured database.
- SQLite by default, with optional Redis velocity counters and optional native C++ scoring acceleration. The actual active components are shown in the metrics response.
- No sign-in in local development/demo mode. Production startup requires `AUTH_ENABLED=true` and valid production secrets.

## Run locally

Requirements: Python 3.12+, Node.js, npm, and a C++ compiler if you want the optional native engine.

```bash
make init
make run
```

Open <http://localhost:8000>. The API documentation is at <http://localhost:8000/docs>.

Local demo mode accepts API calls without login. Keep it bound to localhost and use synthetic data. To enable authentication, set `AUTH_ENABLED=true` and provision an operator account. Production startup refuses to run unless authentication is enabled and production secrets are configured.

## Company website crawler

Open **Site crawler**, enter a public company URL, choose a page limit, and start the crawl. Results include crawl status, HTTP status, title, description, headings, internal links, and a short text excerpt. Crawl runs are stored in the database.

The crawler is sequential and intended for small, authorized website evaluations. It blocks local/private network targets and cross-origin redirects. It does not crawl authenticated pages, download full page source or media, or guarantee complete site coverage. Follow the website's terms and obtain permission where required.

## Design and operational notes

- [System design principles](docs/SYSTEM_DESIGN_PRINCIPLES.md) describes current boundaries, constraints, and production gaps.
- [Architecture](docs/ARCHITECTURE.md) covers the modules and data flow.
- [API reference](docs/API_REFERENCE.md) lists implemented routes and payloads.
- [Deployment guide](docs/DEPLOYMENT.md) documents the included deployment templates; these templates need environment-specific review.
- [Benchmarking notes](docs/BENCHMARKS.md) explains the in-process measurement script and its limits; no verified production SLA result is claimed.

## Demo data

The verification simulator uses fictional values and reserved/example addresses. Keep real customer data out of demos unless you have an approved data handling plan.

## Development checks

```bash
npm --prefix frontend run build
make test
```

Tests and builds report the current code state only; they do not certify security, model quality, throughput, or compliance.
