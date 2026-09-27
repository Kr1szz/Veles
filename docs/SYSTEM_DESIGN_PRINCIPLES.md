# System design principles

This document describes the current prototype and the design rules for extending it. It distinguishes implemented behavior from production goals so that demo behavior is not presented as a guarantee.

## 1. Separate responsibilities

The system has four main paths:

1. **Ingestion:** FastAPI validates verification and crawl requests.
2. **Decisioning:** the verification pipeline applies deterministic rules and anomaly scoring.
3. **Persistence:** SQLAlchemy stores verification records, review outcomes, audit entries, and crawl results.
4. **Presentation:** the React dashboard reads operational data and receives verification events over Server-Sent Events.

Keep network fetching, decision rules, persistence, and UI rendering in their own modules. New crawlers and data sources should not place parsing or network logic in route handlers.

## 2. Bound work at every external boundary

Treat user input and remote systems as untrusted. Validate request schemas, cap request bodies, enforce page and response-size limits, set network timeouts, and reject unsupported URL schemes and ports. Return stable error messages without exposing stack traces.

The company-site crawler is deliberately bounded: it uses only HTTP(S) on ports 80/443, rejects hosts that resolve to non-public IP addresses, stays on the submitted origin, limits depth and page count, caps each response at 1 MB, respects `robots.txt`, disables environment proxy inheritance, and does not follow cross-origin redirects. It crawls sequentially with a short delay. These controls reduce risk; they do not replace network-level egress filtering or protection against DNS rebinding.

## 3. Be explicit about authority and deployment mode

Local development/demo mode has authentication disabled so the dashboard can be used without account setup. The application refuses to start with `ENVIRONMENT=production` unless `AUTH_ENABLED=true`; production must use the authentication flow and strong externally managed secrets. Never deploy the unauthenticated demo configuration to a shared or public network.

Destructive operations, including data erasure, must be protected by production authorization and leave an audit record. Treat the local demo database as disposable synthetic data.

## 4. Make writes auditable and transactional

Persist each verification decision and its audit entry in the same database transaction where practical. Keep identifiers masked in routine responses. Crawl records should retain source URL, run status, fetch time, HTTP outcome, and extracted fields so operators can inspect what the crawler observed.

The current crawler writes a completed run and its extracted pages together after fetching. A process crash during a crawl can leave no run record; a future queued crawler should create a durable run before work starts and support retry and cancellation states.

Verification records and audit entries are committed together in the storage service, and the event broadcast follows that commit. The event system is still process-local, and its per-subscriber queues are unbounded; use a bounded durable broker before multi-worker deployment.

## 5. Design for idempotency and bounded retries

Verification and crawl APIs can be retried by clients. Before adding automatic retries, define an idempotency key and ensure duplicate submissions do not create duplicate decisions, consent entries, or audit actions. Retry only transient failures, with a small bounded budget and backoff. Do not retry validation errors or robots denials.

The current crawler does not retry page failures. A later distributed version should use a durable queue, per-origin concurrency limits, retry budgets, and a dead-letter path.

## 6. Prefer observable, explainable outcomes

Return machine-readable status, counts, and reasons. Record the rules that influenced a risk decision. For crawls, separate discovered URLs, successfully fetched pages, failed pages, and robots exclusions; do not imply that page count equals site completeness. Keep timestamps and source URLs with extracted content.

Metrics should be computed from stored observations and display their time window and sample size. A configured latency target is not proof that the target is met. Benchmark claims need reproducible hardware, dataset, concurrency, and measurement methodology.

## 7. Scale only after measuring

The current crawler is a synchronous, sequential demo feature. It is appropriate for small sites and manual evaluation. Larger crawls need background workers, a durable job queue, per-domain scheduling, storage retention policy, and backpressure. Keep UI requests bounded and avoid unbounded in-memory queues.

The current app uses SQLAlchemy and defaults to local SQLite; Redis is optional for velocity controls. PostgreSQL, Redis clustering, horizontal scaling, and zero-downtime deployment require deployment-specific validation and are not implied by the included configuration files.

## 8. Privacy and data minimization

Collect only fields needed for the stated task. The crawler stores page title, description, headings, internal links, and a short text excerpt; it does not download or retain full HTML, images, scripts, or external pages. Avoid crawling authenticated, private, or personal-data areas without explicit authorization. Define retention and deletion policies before using real company data.

## 9. Accuracy and product claims

Describe what the code currently does, not a desired architecture. Label synthetic records and demo measurements clearly. Do not claim regulatory compliance, fraud-detection accuracy, a strict latency SLA, or production readiness without independent legal, security, and performance evidence.
