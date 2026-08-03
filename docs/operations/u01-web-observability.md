# U01 Web Observability

Docker `json-file` stdout/stderr with 10 MB × 5 rotation is the authoritative local log source. Loki is an optional, access-controlled search replica and is not the system of record. Browser events are allowlisted, bounded, anonymous outcomes; prompts, query/body values, credentials, cookies and direct user identifiers are rejected.

Prometheus probes the public root through Caddy and a known web target. A container that remains running but unhealthy is alerted for operator investigation; `restart: unless-stopped` is not described as a health-based restart controller.
