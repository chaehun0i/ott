# U02 Property-Based Test Evidence

## Coverage

| Property | Automated Evidence |
|---|---|
| PBT-U02-01 | Repeated save produces one saved item and one version increment. |
| PBT-U02-02 | Ratings 1–5 are accepted; all other integers fail without mutation. |
| PBT-U02-03 | Each genre has only its final liked, disliked or unspecified state. |
| PBT-U02-04 | Session revocation is terminal under generated command sequences. |
| PBT-U02-05 | Retried Google-subject links cannot add a second active link. |
| PBT-U02-06 | Collection and disclosure fail closed without current consent. |
| PBT-U02-07 | Repeated idempotency keys produce one event identity. |
| PBT-U02-08 | Withdrawal cleanup leaves no source events or derived features. |
| PBT-U02-09 | Feature snapshots contain allow-listed prefixes and no UserId. |
| PBT-U02-10 | Deleted users cannot return to an active authorization state. |
| PBT-U02-11 | Versioned feature snapshots preserve semantic equality through JSON. |

## Reproduction and Regression Promotion

The verified deterministic command uses `--hypothesis-seed=270727`. Hypothesis shrinking remains
enabled. When a minimized counterexample is found, preserve the failing seed and generated blob in
the CI artifact, add the minimized example as a named example-based regression test, and keep the
original property so broader generation continues. Do not replace the property with only the
regression example.
