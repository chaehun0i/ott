# U03 Property-Based Testing Summary

PBT-U03-01 through PBT-U03-16 passed with Hypothesis seed `260728`, shrinking enabled and deterministic reproduction metadata. A stateful projection reference model also passed.

The properties cover approval closure, filter oracle, deduplication and order, cursor round-trip, keyset page partition, exact-region availability, locale fallback, freshness boundary, normalization idempotency, runtime parsing, RRF determinism/deduplication, circuit opening, semantic fallback, quality metric bounds and out-of-order replay convergence.

Shrinking found and reduced two defects during implementation: order-dependent duplicate selection and cursor corruption when raw signature bytes contained the separator. Both production implementations were corrected and the complete property suite passed afterward.
