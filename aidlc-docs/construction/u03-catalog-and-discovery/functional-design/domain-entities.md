# U03 Catalog and Discovery Domain Entities

## Aggregate Boundaries

### ApprovedContent Aggregate

`ApprovedContent` is the authoritative visibility boundary for one canonical work.

| Field | Meaning and constraint |
|---|---|
| `content_id` | Stable internal identifier; never reused |
| `current_revision_id` | References the visible immutable revision |
| `catalog_version` | Monotonic version assigned when visibility or approved content changes |
| `visibility` | `visible` or `withdrawn`; only `visible` is queryable |
| `validation_rule_version` | Rule version that produced the passed decision |
| `validated_at` | Timestamp of the passed validation |
| `created_at`, `updated_at` | Audit timestamps |

The aggregate owns revisions, localization references, verified availability references and source provenance. A revision cannot become current without a passed validation decision and at least one source record.

### FeedProjection Aggregate

| Field | Meaning and constraint |
|---|---|
| `projection_version` | Immutable snapshot identifier |
| `applied_catalog_version` | Highest contiguous CatalogVersion included |
| `policy_version` | Feed category, freshness and score rule version |
| `content_id` | Approved content reference |
| `categories` | Non-empty subset of `new`, `upcoming`, `popular`, `leaving_soon` |
| `feed_score` | Finite normalized score used with deterministic tie-breakers |
| `release_date` | Secondary ordering value |
| `built_at` | Snapshot creation timestamp |

A content item may have one row per section or one row with a category set, but it must be unique within a section and projection version.

### SearchProjection Aggregate

| Field | Meaning and constraint |
|---|---|
| `projection_version` | Immutable search snapshot identifier |
| `applied_catalog_version` | Highest contiguous CatalogVersion included |
| `content_id` | Approved content reference |
| `locale_documents` | Normalized title, alternate title, synopsis and people terms by locale |
| `embedding` | Optional vector tied to an embedding model/version |
| `embedding_version` | Required when an embedding exists |
| `popularity_score` | Deterministic tie-breaker input |
| `built_at` | Snapshot creation timestamp |

Search projection membership is an optimization only. Every result is revalidated against `ApprovedContent` and regional availability.

## Entities

### CatalogRevision

An immutable approved snapshot containing content type, original locale/title, synopsis, genres, runtime, people, release date/year, age rating, poster reference and normalized provider attributes. It carries the source validation decision and never contains raw or quarantined payloads.

### ContentLocalization

| Field | Constraint |
|---|---|
| `content_id`, `revision_id`, `locale` | Composite identity; one localization per locale/revision |
| `title` | Required and non-blank |
| `synopsis` | Optional; absence is distinct from an empty string |
| `translation_source_id` | Required provenance reference |
| `is_original` | Exactly one title localization is original |

### Availability

| Field | Constraint |
|---|---|
| `availability_id` | Stable identifier |
| `content_id`, `revision_id` | Must reference the approved revision |
| `ott_provider` | Canonical provider code |
| `region` | Canonical region code; never wildcard on public read paths |
| `access_type` | Subscription, rent, buy or free |
| `starts_at`, `ends_at` | Optional bounded interval with start before end |
| `verification_status` | Only `verified` is externally eligible |
| `direct_watch_url`, `official_detail_url` | Validated HTTPS destinations; at least one exists for an active link |
| `license_source_id` | Provenance for legal availability |
| `verified_at` | Verification timestamp |

### CatalogSource

Links an approved revision to provider, original provider ID, source record version, license assertion, last successful update and provenance metadata. Provider differences remain traceable after canonical merge.

### ProjectionReceipt

Stores `(consumer, event_id, catalog_version, applied_at)`. Event ID is unique per consumer. The consumer's applied catalog version advances only contiguously.

## Value Objects

### CatalogVersion and ProjectionVersion

Positive monotonically increasing identifiers. `ProjectionVersion` also records its source `CatalogVersion` and rule/model versions, making query snapshots reproducible.

### FeedQuery

Contains required region, requested locale, requested sections, filter sets, sort policy, page size and optional cursor. Page size is bounded. Filters are canonicalized so logically equivalent queries have the same fingerprint.

### FeedCursor

Opaque authenticated serialization of schema version, query fingerprint, projection version, section, last score, last release date, last content ID and expiry. Clients cannot alter its fields. A cursor cannot be reused with another query.

### SearchQuery

Contains original text, normalized text, locale, required region, structured conditions, filters, search mode, page size and optional cursor. Korean and English produce the same structured-condition schema.

### StructuredSearchConditions

Fields include genres, moods, maximum runtime, companion context, included/excluded terms and OTT providers. Unknown or ambiguous tokens remain displayable as unresolved terms; they do not silently become hard filters.

### LocalizedText

Contains requested locale, actual locale, fallback level and value. Title and synopsis resolve independently using requested locale, original locale, English and deterministic first available locale.

### FreshnessStatus

Contains `fresh` or `stale`, last successful update, threshold, policy version and evaluation time. Calculation is deterministic for those inputs.

### VerifiedLink

Contains provider, region, link kind, URL, access type, active window, verification timestamp and source. Direct-watch is preferred over official-detail within the same provider and region.

### SearchHit

Contains content ID, match class, relevance score, matched locale/field, projection version and approved localized summary. It never embeds an unverified catalog payload.

## Relationships

- One `ApprovedContent` has many immutable `CatalogRevision` records and exactly one current revision while visible.
- One revision has one or more `CatalogSource` records, one original localization, zero or more translated localizations and zero or more availability records.
- A feed/search projection references `content_id` and revision/version metadata but does not own content truth.
- U04 provides passed decisions; U03 owns publication. U05 and U01 consume U03 read ports. U06 invokes an authorized U03 override command rather than writing catalog tables.

## State Transitions

| Current state | Command | Preconditions | Next state |
|---|---|---|---|
| Absent | Publish | Passed decision, complete provenance, newer version | Visible revision 1 |
| Visible | Replace | Passed decision and version newer than current | Visible new revision |
| Visible | Withdraw | Validated withdrawal or authorized override | Withdrawn |
| Withdrawn | Publish | New passed decision and explicit reactivation | Visible new revision |
| Any | Replay same decision/version | Existing receipt matches | No state change |

No transition exists from raw, normalized or quarantined data directly into a U03 read response.

## Data Ownership and Consistency

- Only U03 writes approved catalog and projection tables.
- Publication, CatalogVersion advancement and outbox creation are atomic.
- Projection updates are eventually consistent, but public reads are strongly closed over current approval and availability through final revalidation.
- Withdrawals are visible immediately at the authoritative boundary and asynchronously removed from projections.
- Projection rebuild uses a captured CatalogVersion and is published only after all projected IDs pass closure validation.

## Domain Invariants

1. Every visible content aggregate points to exactly one passed, immutable current revision.
2. Every returned item belongs to the current approved set at response assembly time.
3. Every returned availability is verified, active and equal to the requested region.
4. Every enabled outbound link is derived from returned verified availability.
5. Each content ID occurs at most once per feed section and at most once per search page.
6. Result ordering is total and deterministic for a fixed query and projection version.
7. Applied projection versions never skip a CatalogVersion.
8. Reapplying the same catalog event does not change observable projection state.
9. Localization fallback always reports the locale actually returned.
10. Failed or stale ingestion does not erase the last valid approved revision.

