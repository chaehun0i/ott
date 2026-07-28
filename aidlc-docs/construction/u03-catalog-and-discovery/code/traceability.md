# U03 Story Traceability

| Story | Implemented evidence | Verification |
|---|---|---|
| US-001 | Multi-section new/upcoming/popular/leaving feed and projection generation | Feed examples, PBT-03/05, PostgreSQL generation tests |
| US-002 | Multi-filter semantics, region-verified availability and lawful provider links | Catalog examples, PBT-02/06, API contract |
| US-003 | Source identifiers, last successful refresh and fresh/stale state | Detail/feed examples, PBT-08, API contract |
| US-004 | Exact/prefix/person/trigram/FTS text discovery | Text repository, parser/ranking tests, PostgreSQL indexes |
| US-005 | Korean natural-language parsing, semantic retrieval and locale fallback | Parser/locale/PBT tests and Korean quality gate |
| US-006 | English structured parsing with common schema and semantic fallback | Parser/hybrid tests and English quality gate |

All stories are implemented by U03 backend contracts; the U01 frontend remains a later unit.
