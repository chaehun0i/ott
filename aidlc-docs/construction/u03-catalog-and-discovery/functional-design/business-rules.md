# U03 Catalog and Discovery Business Rules

## Rule Catalog

| Rule | Business rule | Failure behavior |
|---|---|---|
| CAT-01 | Only the current visible revision produced by a passed validation decision is externally queryable. | Exclude or return not found |
| CAT-02 | Publication requires source identity, license assertion, validation rule version and validation timestamp. | Reject publication |
| CAT-03 | A repeated publication decision/version is idempotent; an older version cannot replace a newer one. | Return existing result or version conflict |
| CAT-04 | Withdrawal blocks authoritative reads immediately, independent of projection lag. | Exclude or return not found |
| CAT-05 | Every response item is rechecked against authoritative approval and current regional availability. | Drop item; fail closed if authoritative check is unavailable |
| FEED-01 | An approved item may belong to multiple feed sections but appears at most once per section. | Deduplicate deterministically |
| FEED-02 | Category and score calculations use a recorded `FeedPolicyVersion`. | Reject unversioned projection |
| FEED-03 | Fixed-snapshot ordering uses score descending, release date descending and content ID ascending. | Reject malformed projection/cursor |
| FEED-04 | Different filter dimensions use AND; multiple values within one dimension use OR. | Validation error for unknown dimension/value |
| FEED-05 | Cursor query fingerprint and projection version must match the current request. | Cursor validation error |
| AVAIL-01 | Region is mandatory for public feed, detail, search and candidate-read queries. | Validation error |
| AVAIL-02 | Only verified, active availability for the exact requested region is eligible. | Exclude availability/content |
| AVAIL-03 | Prefer verified direct-watch link over verified official-detail link for the same provider and region. | Return no active link if neither exists |
| FRESH-01 | Freshness uses the category/provider policy threshold, with a 24-hour default. | Mark stale when threshold exceeded |
| FRESH-02 | Ingestion failure preserves the last valid revision and exposes its last successful update and status. | Serve approved stale data with status |
| LOC-01 | Fallback order is requested locale, original locale, English, deterministic first available locale. | Omit only the unavailable optional field |
| LOC-02 | Every localized field reports its actual returned locale and fallback level. | Reject malformed response model |
| SEARCH-01 | Text match precedence is exact title, title prefix, title full-text, then person match. | No hit when no supported match |
| SEARCH-02 | Locale match and normalized popularity break equal relevance; content ID supplies final total ordering. | Deterministic order |
| SEARCH-03 | Korean and English search parsers emit the same structured-condition schema. | Parser validation error or text-only fallback |
| SEARCH-04 | Unknown/ambiguous parsed terms are displayed as unresolved and cannot silently become hard filters. | Preserve as unresolved term |
| SEARCH-05 | Semantic candidates must pass all hard filters and authoritative approval closure. | Remove candidate |
| SEARCH-06 | Semantic failure or incompatible projection falls back to approved text/filter search and marks degradation. | Safe degraded response |
| PROJ-01 | Catalog events apply only in contiguous CatalogVersion order. | Pause and replay/rebuild on gap |
| PROJ-02 | Reapplying an event ID/version is a no-op with equivalent observable state. | Return already-applied receipt |
| PROJ-03 | A rebuilt projection is published only after all IDs pass approved-closure validation. | Keep prior projection; reject rebuild |

## Validation Rules

### Query Validation

- Region must be a supported canonical region code.
- Locale must be supported or safely canonicalizable; fallback does not change the requested locale stored in the response.
- Page size must be positive and within the configured maximum.
- Filter values must exist in the corresponding versioned vocabulary.
- Runtime and year ranges must be ordered and within domain bounds.
- Cursor schema, integrity, expiry, query fingerprint and projection version must validate before data access.
- Empty text with no filters is a feed query, not an unbounded search.

### Publication Validation

- `PassedValidation.status` must be passed and its rule version recognized.
- Canonical content ID and original provider identifiers must be present and consistent.
- Required fields, source attribution, license state and validation time must be present.
- Availability included in the approved revision must have region, provider, status and provenance.
- A source decision/version may advance the aggregate once only.

### Response Validation

- No content ID is duplicated within a section or result page.
- Each item resolves to a current visible approved revision.
- All returned availability matches the exact requested region and is currently active and verified.
- Every link belongs to one of those availability records.
- Sort tuples are monotonic according to the selected order.
- Returned localized values include actual locale and fallback level.

## Resiliency Rules

- Catalog storage failure is fail-closed because approval cannot be revalidated.
- Search/embedding failure is isolated from catalog reads and degrades to text/filter search.
- Projection lag is tolerated only with authoritative approval and availability rechecks.
- Version gaps stop projection advancement; they never trigger best-effort out-of-order application.
- The last valid approved revision survives provider ingestion failure and is marked stale according to policy.
- External semantic calls require an explicit time budget; unbounded waits are forbidden.
- Degraded responses carry stable reason codes and projection/catalog versions without exposing internal error text.

## Testable Properties — PBT-01

| Property ID | Component | Category | Property |
|---|---|---|---|
| PBT-U03-01 | Approved Catalog | Invariant | Every returned content ID is a member of the current visible approved set. |
| PBT-U03-02 | Filter evaluator | Oracle | Optimized filtering equals a simple reference predicate using AND across dimensions and OR within a dimension. |
| PBT-U03-03 | Feed projection | Invariant | Projection and filtering never introduce IDs absent from the approved input set. |
| PBT-U03-04 | Feed deduplication | Idempotence | Deduplicating a section twice equals deduplicating it once. |
| PBT-U03-05 | Feed ordering | Invariant | Sorting preserves eligible elements, produces no duplicates and yields a total monotonic sort tuple. |
| PBT-U03-06 | Cursor codec | Round-trip | Encoding then decoding a valid cursor preserves its schema version, fingerprint, snapshot and last sort tuple. |
| PBT-U03-07 | Cursor pagination | Oracle | Concatenating pages from a fixed snapshot equals the reference fully sorted result without gaps or duplicates. |
| PBT-U03-08 | Availability filter | Invariant | Every returned availability is verified, active and matches the requested region. |
| PBT-U03-09 | Locale resolver | Easy verification | Resolution selects the first available value in the defined fallback chain and reports that exact locale. |
| PBT-U03-10 | Freshness evaluator | Invariant | A record is stale exactly when elapsed time exceeds the selected versioned threshold; the default is 24 hours. |
| PBT-U03-11 | Text ranking | Invariant | Exact title outranks prefix, prefix outranks full-text, and full-text outranks person match before tie-breakers. |
| PBT-U03-12 | Query normalization | Idempotence | Normalizing a canonical structured query again produces the same query and fingerprint. |
| PBT-U03-13 | Projection consumer | Stateful | Random publish, replace, withdraw, duplicate and out-of-order event sequences match a reference CatalogVersion model after each accepted command. |
| PBT-U03-14 | Projection replay | Idempotence | Replaying an already applied event leaves projection contents and applied version unchanged. |
| PBT-U03-15 | Projection rebuild | Invariant | Every rebuilt projection ID belongs to the captured approved snapshot and the applied version has no gap. |
| PBT-U03-16 | Semantic fallback | Invariant | Dependency failure cannot add an unapproved or hard-filter-violating result. |

Domain-specific generators must produce canonical content revisions, locale maps, regional availability windows, filter sets, fixed-snapshot sort tuples and ordered/disordered catalog event sequences. Code generation must implement these properties with Hypothesis plus example tests for US-001~US-006 critical scenarios.

## Traceability Matrix

| Rules | Stories | Requirements and acceptance criteria |
|---|---|---|
| CAT-01~CAT-05, PROJ-01~PROJ-03 | US-001~US-006, supporting US-020/US-022 | DR-009~DR-012, AC-012, AC-014 |
| FEED-01~FEED-05 | US-001, US-002 | FR-001~FR-003, AC-001 |
| AVAIL-01~AVAIL-03 | US-002, supporting US-008~US-011 | FR-004~FR-005, FR-013 |
| FRESH-01~FRESH-02 | US-003 | FR-006, DR-006, AC-008 |
| LOC-01~LOC-02 | US-005, US-006 | FR-033~FR-034 |
| SEARCH-01~SEARCH-06 | US-004~US-006 | FR-007~FR-008 |
| PBT-U03-01~16 | All U03 stories and supporting consumers | AC-009, AC-012, AC-014 |

## Extension Compliance

### Property-Based Testing

- **PBT-01 — Compliant**: Sixteen properties are identified by component and category and are explicitly handed to code generation.
- **PBT-02~PBT-10 — N/A at Functional Design**: The enabled extension assigns only PBT-01 enforcement to this stage. Framework configuration and executable tests are evaluated during NFR Requirements and Code Generation.

### Resiliency

- **RESILIENCY-01 — Compliant by prior design**: Feed and search are High workloads; U03 dependencies and outage impact are documented in requirements and Unit boundaries.
- **RESILIENCY-02~RESILIENCY-04 — Compliant by prior stages**: Project availability, recovery, change, deployment and rollback decisions are inherited unchanged; U03 introduces no conflicting decision.
- **RESILIENCY-05~RESILIENCY-07 — N/A for detailed Functional Design**: Metrics, health checks, dashboards and alarms are specified in U03 NFR stages.
- **RESILIENCY-08~RESILIENCY-09 — N/A for detailed Functional Design**: Topology and capacity are infrastructure/NFR concerns; no topology is selected here.
- **RESILIENCY-10 — Compliant**: Semantic dependency timeout, isolation, fail-closed catalog checks and approved text/filter degradation are explicit functional rules.
- **RESILIENCY-11~RESILIENCY-13 — Compliant by U07 baseline**: Backup/restore and recovery strategy are owned by U07 and apply to U03 persistence without alteration.
- **RESILIENCY-14~RESILIENCY-15 — N/A for detailed Functional Design**: Resiliency testing and incident-process integration are evaluated in NFR Design and Operations handoff.

### Security Baseline

The extension is disabled in `aidlc-state.md`, so it is not enforced. Core approval, source, license, cursor-integrity and fail-closed data boundaries remain mandatory.

No blocking extension finding remains for U03 Functional Design.
