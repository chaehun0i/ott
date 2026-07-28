# U03 Catalog and Discovery Business Logic Model

## Scope and Boundary

U03 owns the approved catalog read model and feed/search projections. U04 alone decides whether incoming metadata passes validation; U04 publishes a passed decision through `ApprovedCatalogWritePort`. U03 persists the approved representation and guarantees that only the current approved version is observable through feed, detail, search, availability and U05 candidate-read ports.

U03 does not ingest raw provider data, decide quarantine, generate recommendation prose, rank personalized recommendations or write user profiles.

## Decision Summary

| Concern | Selected policy |
|---|---|
| Feed layout | New, upcoming, popular and leaving-soon sections; one content item may appear in multiple sections |
| Category calculation | Provider state, dates and normalized provider popularity under versioned rules |
| Ordering | Versioned freshness/popularity score, with deterministic tie-breakers |
| Pagination | Opaque cursor bound to a catalog/projection snapshot version |
| Filters | AND across filter kinds; OR among values of the same kind |
| Availability | Region is required; unverified availability and links are excluded |
| Freshness | Versioned category/provider policy; 24-hour default if no specific policy exists |
| Localization | Requested locale, original locale, English, then deterministic first available translation |
| Search ownership | U03 owns Korean/English search parsing and embedding search; schema contract is shared with U05 |
| Search fallback | Revalidated approved-catalog text/filter search with `degraded=true` |
| Projection updates | Versioned outbox events; replay is idempotent; withdrawn content is blocked synchronously |

## Approved Catalog Lifecycle

### Publish or Replace

1. U04 submits `PassedValidation` containing canonical content ID, normalized fields, source provenance, availability, validation rule version and validation time.
2. U03 verifies the command is complete, its validation status is passed, its source/license assertions are present and its version is not older than the current aggregate version.
3. U03 writes a new immutable `CatalogRevision` and atomically advances `ApprovedContent.current_revision` and the monotonically increasing `CatalogVersion`.
4. U03 writes a `CatalogChanged` outbox record in the same transaction. Repeating the same source decision/version returns the existing result without creating another revision or event.
5. Feed and search projection consumers apply the event only if its version is newer than their applied version. Gaps cause replay/rebuild instead of partial advancement.

### Withdraw

1. A validated withdrawal or authorized U06 override marks the aggregate non-visible and advances `CatalogVersion` transactionally.
2. All authoritative read paths recheck current visibility, so the withdrawn record is blocked immediately even while projections lag.
3. A versioned withdrawal event removes the record from feed and search projections. Replay is idempotent.

### Closure Invariant

Every returned content ID must resolve at response assembly time to a visible `ApprovedContent` revision whose validation decision is passed and whose requested-region availability is verified. Projection membership alone is never sufficient proof.

## Feed Query Flow

1. Validate required region, locale, filter values, sort mode, page size and optional opaque cursor.
2. Decode the cursor and verify query fingerprint, projection version and expiry. A mismatch returns a cursor validation error rather than silently changing the result set.
3. Select one or more sections: `new`, `upcoming`, `popular`, `leaving_soon`.
4. Apply filters. Different dimensions are intersected; selected values within genre, OTT, country or release status are unioned.
5. Join verified availability for the requested region. Records without verified availability are excluded.
6. Evaluate membership and `feed_score` using the policy version stored with the projection snapshot. A content item may belong to multiple requested sections but appears once within each section.
7. Sort by `feed_score DESC`, `release_date DESC`, then `content_id ASC`; the score calculation combines versioned popularity and freshness weights.
8. Read `page_size + 1`, emit the requested page and construct the next cursor from the snapshot version, query fingerprint and last sort tuple.
9. Recheck every item against the authoritative approved aggregate and current regional availability before response assembly.
10. Localize display fields and include source attribution, last successful update, freshness status, actual returned locale and projection version.

## Category and Freshness Calculation

Category membership is a pure function of normalized provider state, release/end dates, normalized provider popularity, evaluation time and `FeedPolicyVersion`. Provider-specific rules take precedence over category defaults.

Freshness is computed from the last successful provider update and the applicable policy threshold. A category/provider policy can define its own threshold; otherwise 24 hours is used. Failed ingestion never deletes the last valid revision. A visible record may be marked `stale`, but it remains eligible only while its approval and verified availability are still valid.

## Detail and Availability Flow

1. Require `content_id`, region and requested locale.
2. Read the current approved revision and reject absent, withdrawn or non-approved content as not found.
3. Select only verified availability windows containing the evaluation time for the requested region.
4. For each OTT, prefer a verified direct-watch link; otherwise use the verified official detail link. Expired, unlicensed, unverified or mismatched-region links are excluded.
5. Apply locale fallback independently to title and description and return the actual locale for each localized field.
6. Return original title, poster, synopsis, genres, runtime, people, release year, age rating, OTT availability, source attribution, data-quality/freshness state and last successful update.

## Text Search Flow

1. Normalize Unicode, whitespace, locale and filters without discarding the original query for display.
2. Search approved projection fields using weighted match tiers: exact title, title prefix, title full-text, then person match.
3. Rank by match tier and text relevance; use requested-locale match and normalized popularity as deterministic tie-breakers, followed by content ID.
4. Apply the same region, availability, approval and filter closure used by feed queries.
5. Recheck authoritative approval before returning hits.

## Semantic Search Flow

1. The U03 search parser converts Korean or English search prose into the shared structured-query schema: free text, genre, mood, maximum runtime, companion, include/exclude terms and OTT filters.
2. The user-visible parsed conditions are preserved in the response contract. Search parsing is separate from U05 recommendation intent and does not produce personalized ranking inputs.
3. Execute hard filters against the approved catalog, then retrieve semantic candidates using the compatible embedding/projection version.
4. Combine semantic similarity with deterministic text evidence and apply authoritative approval/availability closure.
5. If the embedding dependency fails, the projection is incompatible/lagging, or the time budget is exhausted, execute approved-catalog text/filter fallback and set `degraded=true` with a non-sensitive reason code.
6. If neither semantic nor text/filter search can safely serve, return a retryable service error; never return unverified projection records.

## Projection Refresh Model

`CatalogChanged` events contain event ID, catalog version, content ID, change kind and revision reference, but no raw/quarantined payload. Feed and search consumers keep an applied version and event receipt. Duplicate or older events are no-ops. A contiguous next version is applied atomically. A version gap pauses advancement and requests replay or a snapshot rebuild. Rebuild creates a new projection version from authoritative approved aggregates and swaps it in only after closure validation.

## Error Model

| Error | Outcome |
|---|---|
| Invalid region/filter/cursor | Client validation error; no partial result |
| Content absent, withdrawn or non-approved | Not found |
| No verified regional availability | Omit from collections; detail reports unavailable/not found by contract |
| Projection lag | Authoritative recheck plus Catalog query fallback; `degraded=true` |
| Semantic dependency timeout/failure | Text/filter fallback; `degraded=true` |
| Catalog store unavailable | Retryable service-unavailable error; no stale unverified result |
| Version gap during refresh | Stop projection advancement and replay/rebuild |

## Component Responsibilities

| Component | Responsibilities | Exclusions |
|---|---|---|
| C04 Content Catalog | Approved aggregate, version transitions, feed/detail query, localization and verified availability | Raw ingestion, validation decision, personalized ranking |
| C07 Search | Query normalization, text/semantic retrieval, projection refresh and degraded fallback | Recommendation intent, free-form generation, approval mutation |
| S01 FeedQueryService | Orchestrate feed/detail response and closure checks | Projection mutation |
| S02 SearchService | Orchestrate parser, retrieval, filters, closure and fallback | AI recommendation ranking |

## Traceability

| Story | Functional coverage | Requirements |
|---|---|---|
| US-001 | Multi-section integrated feed and approved closure | FR-001, FR-002, AC-001, AC-014 |
| US-002 | Filter semantics, detail and legal regional link selection | FR-003~FR-005 |
| US-003 | Provenance, last successful update and stale state | FR-006, DR-006, AC-008 |
| US-004 | Weighted title/person search and filters | FR-003, FR-007 |
| US-005 | Korean parser, locale-aware text and semantic search | FR-008, FR-033~FR-034 |
| US-006 | English parser and shared structured-query schema | FR-008, FR-033~FR-034 |
| Supporting U05 | Approved regional candidate reads only | FR-013, DR-012, AC-012 |
| Supporting U04 | Passed-decision publication and quarantine exclusion | DR-003~DR-004, DR-009~DR-011, AC-014 |

