# U02 Dependency Validation

## Locked Runtime

- Python constraint remains `>=3.12.13,<3.13`.
- Existing U07 pins remain unchanged.
- `backend/pyproject.toml` and regenerated `backend/uv.lock` are the only dependency sources.

## Added Packages

| Package | Locked Version | Python 3.12 Evidence | Purpose |
|---|---:|---|---|
| argon2-cffi | 25.1.0 | resolver selected `argon2-cffi-bindings` 25.1.0 with Windows ABI3 wheel; import passed | Argon2id hash/verify/rehash |
| cryptography | 49.0.0 | Windows CPython 3.11+ ABI3 wheel downloaded and import passed | AES-GCM and envelope-key primitives |
| Authlib | 1.7.2 | Python 3 universal wheel and import passed; `joserfc` 1.7.4 resolved | Google OAuth/OIDC client validation |

## Resolver Evidence

1. A pip dry run against the configured Python 3.12 runtime resolved all three candidates without conflict.
2. `uv 0.11.32` resolved 54 packages with the existing project pins.
3. `uv sync` installed the locked set into `backend/.venv`.
4. Runtime imports and installed metadata returned the exact requested versions.

No lock file was edited manually. Exact transitive versions and artifact hashes are recorded in `backend/uv.lock`.

## Sources

- [argon2-cffi on PyPI](https://pypi.org/project/argon2-cffi/)
- [cryptography on PyPI](https://pypi.org/project/cryptography/)
- [Authlib on PyPI](https://pypi.org/project/Authlib/)

## Gate Result

Step 2 passed. Dependency resolution, Python 3.12.13 compatibility, synchronization and runtime imports are verified.
