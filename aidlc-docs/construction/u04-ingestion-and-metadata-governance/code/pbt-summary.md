# U04 Property-Based Testing Summary

## Implemented Properties

| Property | Invariant |
|---|---|
| PBT-U04-01 | Raw envelope encode/decode round-trip preserves governed values |
| PBT-U04-02 | Versioned normalization is idempotent |
| PBT-U04-03 | Normalization preserves identifier source facts |
| PBT-U04-04 | Identity resolution matches the reference oracle |
| PBT-U04-05 | Merge result is independent of provider input order |
| PBT-U04-06 | Merge retains every candidate and selected provenance |
| PBT-U04-07 | A validation decision passes iff every mandatory result passes |
| PBT-U04-08 | A non-passed decision cannot map to U03 publication |
| PBT-U04-09 | Publication replay has one observable receipt |
| PBT-U04-10 | Random job commands match the state-machine model |
| PBT-U04-11 | One tombstone cannot remove another valid authoritative source |
| PBT-U04-12 | Durable cursor page replay is idempotent |

## Extension Compliance

| Rule | Status | Evidence |
|---|---|---|
| PBT-01 | Compliant | Functional Design identifies all twelve properties and categories |
| PBT-02 | Compliant | Raw codec round-trip property |
| PBT-03 | Compliant | Provenance, validation, merge and tombstone invariants |
| PBT-04 | Compliant | Normalization, publication and cursor idempotence |
| PBT-05 | Compliant | Identity reference-oracle comparison |
| PBT-06 | Compliant | Stateful job model checks every generated command transition |
| PBT-07 | Compliant | Reusable U04 domain strategies include Unicode and boundary values |
| PBT-08 | Compliant | Hypothesis shrinking remains enabled; seed `260728` is recorded |
| PBT-09 | Compliant | Locked Hypothesis 6.161.5 integrates with pytest 9.1.1 |
| PBT-10 | Compliant | Critical paths also have explicit example and contract tests |

No blocking PBT finding remains.
