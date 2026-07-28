# U03 Dependency Validation

## Python

- Runtime constraint: Python `>=3.12.13,<3.13`
- Package: `pgvector==0.5.0`
- Wheel SHA-256: `fedc9800894e6da2be51358d7b7c574bf34f247ca741a5a09513622135f5964f`
- Source SHA-256: `07a9dcf735696879406983afc6eba9a787cef7c0cf6c367ca1a5779f036dee74`
- Resolver: uv resolved 55 packages and installed the pinned package successfully with SQLAlchemy `Vector(3)` import validation.

## PostgreSQL

- Image: `pgvector/pgvector:0.8.2-pg17-bookworm`
- Digest: `sha256:feb68f4f15446397d8cac7f4fe48fe4586de83160d1fc48b46283312d1a33966`
- Server: PostgreSQL 17.10
- Extensions: `pg_trgm` 1.6, `unaccent` 1.1, `vector` 0.8.2
- HNSW: index scan selected for a cosine nearest-neighbor query and returned the exact expected row.

## Decision

The plain `postgres:17-bookworm` fallback was rejected because it does not provide a version-pinned vector extension. Unpinned `latest` images were rejected because they cannot reproduce migration or ranking behavior.
