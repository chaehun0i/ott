# U05 Recommendation and AI Grounding Business Rules

## Intent and Precedence Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| INT-01 | Canonical intent values are language-neutral and versioned | Unsupported schema version is rejected |
| INT-02 | Safety/legal/eligibility rules outrank all user and profile signals | Conflicting lower-priority value is ignored with a code |
| INT-03 | Latest explicit request and confirmed patch outrank retained session state | Stale state cannot overwrite the new turn |
| INT-04 | Consented stored preferences are soft signals and cannot become hard filters implicitly | Preference is omitted from hard conditions |
| INT-05 | Ambiguous, low-confidence or contradictory hard values require confirmation | State is `confirmation_required`; ranking does not run |
| INT-06 | Equivalent Korean/English meaning yields equivalent canonical hard conditions | Locale regression blocks the parser version |

## Eligibility and Candidate Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| ELG-01 | Every candidate originates from one immutable U03 approved-catalog snapshot | Reject candidate |
| ELG-02 | Approval, non-withdrawal, region, OTT, runtime, age and explicit exclusions are hard filters | Reject candidate before scoring |
| ELG-03 | AI output cannot add, approve or rank a candidate | Ignore AI candidate reference and record boundary violation |
| ELG-04 | Soft-condition broadening cannot relax safety, approval, availability, age or explicit hard constraints | Use empty/degraded result if no candidate remains |
| ELG-05 | Every surviving candidate retains a verifiable hard-filter proof and catalog version | Reject incomplete proof |
| ELG-06 | Replacement candidates come only from the already eligible reserve set and are revalidated | Reject invalid replacement |

## Scoring and Diversity Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| RNK-01 | Request fit, consented affinity, freshness, popularity and novelty components are each in `[0, 1]` | Reject scoring run |
| RNK-02 | Active non-negative policy weights sum to one after permitted missing-component normalization | Reject policy version |
| RNK-03 | Withdrawn/absent consent removes behavior-derived components immediately | Recompute non-personalized score |
| RNK-04 | Same intent, features, catalog and policy versions yield identical base scores and tie order | Mark run non-reproducible and block activation |
| RNK-05 | Final tie order is request fit, freshness, popularity, then canonical content ID | Apply deterministic ordering |
| RNK-06 | Diversity may reorder or omit only candidates in the eligible ranked set | Reject reranking output |
| RNK-07 | Exact content and franchise-equivalent duplication is removed; genre/provider repetition follows a versioned cap | Continue with fewer results if needed |
| RNK-08 | Diversity never reintroduces a candidate removed by a hard filter | Reject the complete reranking output |

## Grounding and Validation Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| GRD-01 | Evidence fields are allowlisted and belong to one approved candidate/version | Exclude invalid evidence |
| GRD-02 | Each atomic claim references content ID, metadata version, field path and source reference | Replace or remove claim |
| GRD-03 | A claim cannot cite another candidate's evidence | Reject claim and record `evidence_content_mismatch` |
| GRD-04 | Unsupported facts are omitted; missing evidence is never completed by model inference | Use approved template or omit sentence |
| GRD-05 | Reasons connect to confirmed conditions; summaries are concise, localized and spoiler-minimized | Regenerate within budget or use template |
| GRD-06 | AI-drafted text is identifiable in the response contract | Reject unlabeled draft |
| VAL-01 | Candidate eligibility is checked before drafting and again before serialization | Reject candidate |
| VAL-02 | Missing, unknown, incompatible or error U04 rule results fail closed | Reject exposure |
| VAL-03 | Failed draft text is never serialized, logged or used as a template input | Discard draft |
| VAL-04 | Item/claim failure remains isolated from safe siblings | Backfill, replace or return fewer items |
| VAL-05 | If no validated AI item remains, deterministic eligible ranking and approved templates replace the response | Set `response_fallback` |

## Conversation Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| CON-01 | Every turn records retained, added, changed and removed fields as one immutable patch | Reject malformed patch |
| CON-02 | Patch application uses expected session version | Return version conflict on stale write |
| CON-03 | Unmentioned confirmed conditions remain unchanged | Restore previous value if parser omits it |
| CON-04 | Explicit removal wins over retention and stored preference for that turn | Remove the condition |
| CON-05 | Reset closes the current epoch and produces empty conversation state | Prior epoch cannot be read by the new session |
| CON-06 | Every refined turn reruns eligibility, ranking, grounding and final validation | No partial-pipeline shortcut |

## Consent, Trace and Failure Rules

| Rule | Definition | Failure outcome |
|---|---|---|
| PRV-01 | U05 accepts only pseudonymous, purpose-limited feature snapshots | Reject direct identity input |
| PRV-02 | Consent absence/withdrawal excludes behavior features and raw behavior history | Use non-personalized ranking |
| PRV-03 | AI input contains only intent plus allowlisted candidate evidence | Reject oversized or disallowed context |
| TRC-01 | Trace records decision inputs/versions, bounded scores, codes and fallback path | Mark trace incomplete and alert |
| TRC-02 | Trace excludes direct identifiers, raw prompt/response, credentials and chain-of-thought | Drop prohibited field and raise privacy signal |
| FAL-01 | AI timeout/circuit never weakens hard filtering or C11 validation | Use deterministic fallback |
| FAL-02 | U03 unavailability cannot be replaced by model knowledge | Return bounded unavailable state |
| FAL-03 | Unknown U04 validation contract version cannot be treated as compatible | Fail closed |

## Testable Properties - PBT-01

| ID | Component | Category | Property |
|---|---|---|---|
| P-U05-01 | Intent codec | Round-trip | Encoding and decoding any valid intent preserves canonical constraints, origin and confirmation state |
| P-U05-02 | Bilingual interpreter contract | Oracle/invariant | Generated equivalent Korean/English phrases map to the same hard-condition oracle |
| P-U05-03 | Intent resolver | Invariant | A lower-precedence source never overwrites a higher-precedence confirmed value |
| P-U05-04 | Hard filter | Invariant/easy verification | Every output candidate is approved and satisfies every hard condition |
| P-U05-05 | Score policy | Range invariant | Every component/final score remains in `[0, 1]` and effective weights sum to one |
| P-U05-06 | Ranking | Idempotence | Repeating rank with identical versioned inputs yields the same ordered IDs and scores |
| P-U05-07 | Ranking | Oracle | Optimized ranking equals a simple filter-score-sort reference model |
| P-U05-08 | Diversity | Invariant | Diversity output is a duplicate-free subsequence/permutation of eligible inputs and never adds a filtered ID |
| P-U05-09 | Evidence builder | Invariant | Every evidence reference belongs to the same candidate and approved metadata version |
| P-U05-10 | Output validator | Easy verification | No failed/unknown claim or ineligible candidate appears in serialized output |
| P-U05-11 | Session patcher | Stateful/model | Random patch/reset sequences match a simple map-and-epoch reference state after every command |
| P-U05-12 | Fallback | Invariant | AI failure changes drafting/degradation status but never eligibility or validation requirements |

These properties require reusable domain generators for bilingual intents, conflicts, consent states, catalog snapshots, score policies, candidate permutations, evidence graphs, validation outcomes and patch sequences. Example tests remain mandatory for every primary story and failure family.

## Extension Compliance

### Resiliency Baseline

| Rule | Status | Functional-design evidence |
|---|---|---|
| RESILIENCY-01 | Compliant | Eligibility/grounding are high criticality; AI drafting is degradable |
| RESILIENCY-02 | Compliant | Inherited 99.0%, RTO 4 hours and RPO 24 hours are preserved for later NFR quantification |
| RESILIENCY-03 | N/A at this stage | Deployment change mechanics are not functional business logic; immutable versions support later change control |
| RESILIENCY-04 | N/A at this stage | Deployment/rollback automation belongs to Infrastructure Design and U07 |
| RESILIENCY-05 | Compliant | Dependency, validation, fallback and trace failure signals have explicit outcome codes |
| RESILIENCY-06 | Compliant | U03/U04 readiness and AI degradation are separable functional states |
| RESILIENCY-07 | Compliant | Eligibility failures, AI latency/circuit, fallback and validation rejection are observable decisions |
| RESILIENCY-08 | N/A | Approved single-server prototype; production topology is a later transition gate |
| RESILIENCY-09 | N/A | Fixed prototype capacity; NFR Requirements will define numeric load/review triggers |
| RESILIENCY-10 | Compliant | AI dependency is isolated and deterministic fallback preserves hard rules |
| RESILIENCY-11 | Compliant | Inherited Backup and Restore strategy covers durable session/trace state |
| RESILIENCY-12 | Compliant | Only minimized durable recommendation state requires backup; transient drafts do not |
| RESILIENCY-13 | Compliant | Versioned inputs allow session/trace recovery without replaying unsafe drafts |
| RESILIENCY-14 | Compliant handoff | Timeout, circuit, U03/U04 failure, consent withdrawal and trace failure scenarios are test requirements |
| RESILIENCY-15 | Compliant | Stable failure codes and versioned traces support investigation and correction |

### Property-Based Testing

- PBT-01: compliant through P-U05-01~12 with explicit categories and component mapping.
- PBT-02~08 and PBT-10: N/A for executable verification at Functional Design; the identified properties and generator needs are mandatory Code Generation handoff inputs.
- PBT-09: N/A until NFR Requirements confirms the existing Hypothesis stack for U05.

### Security Baseline

Disabled in `aidlc-state.md` and N/A as an extension. PRV-01~03 and TRC-02 retain core consent, data-minimization and trace privacy requirements.

No blocking enabled-extension finding remains at U05 Functional Design.
