# U03 PostgreSQL Verification

## Environment

- Docker Engine 29.6.2 and Compose 5.3.1
- `pgvector/pgvector:0.8.2-pg17-bookworm`
- Image digest `sha256:feb68f4f15446397d8cac7f4fe48fe4586de83160d1fc48b46283312d1a33966`
- PostgreSQL 17.10, pgvector 0.8.2, pg_trgm 1.6 and unaccent 1.1
- Alembic head `0003_u03_catalog_expand`; 15 U03 tables

## Gate Results

- `pytest -m integration`: 19 passed, 115 deselected, zero skipped
- HNSW index: actual index scan selected and nearest-vector row verified
- Publication/outbox: atomic publish and withdrawal, decision idempotency and rollback injection passed
- Projection: receipt deduplication, gap state, compare-and-set version and generation pointer rollback passed
- Vector: compatible model/dimension HNSW and exact-oracle queries passed
- Capacity: 100,000-row fixture, ordered index plan and sub-60-second local gate passed
- Quality: Korean and English Recall@10/NDCG@10 exceeded 0.85/0.80
- PBT: PBT-U03-01 through 16 plus the stateful projection reference model passed with seed 260728

No PostgreSQL integration test was counted as complete while skipped.
