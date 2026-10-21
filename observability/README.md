# Observability

The authenticated console shows per-stream ages, late/overflow counts, posterior variance, commit-latency distribution and viewer drops. /api/metrics returns counters; /metrics exports Prometheus text behind the same session authentication. A production scraper needs an explicitly provisioned authentication flow rather than exposing the route publicly.

Run IDs correlate streamed packets and structured run-completion logs. HTTP responses have X-Trace-Id and logs include trace, method and status without payloads, cookies, paths or passwords. This is correlation, not an OpenTelemetry distributed trace implementation. SQLite is the event history; it is not an external telemetry backend.
