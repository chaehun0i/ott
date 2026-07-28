# GitHub Actions Automatic Trigger Pause

Automatic GitHub Actions triggers are temporarily paused while the workflow
suite is stabilized. Every workflow remains available through
`workflow_dispatch` for controlled manual verification.

## Paused triggers

| Workflow | Paused automatic trigger | Restore after |
|---|---|---|
| `ci.yml` | Pull requests and pushes to `main` | Quality, PostgreSQL integration and security jobs pass manually |
| `release.yml` | Tags matching `v*` | Image publication succeeds manually with the required package permission |
| `recovery-validation.yml` | Daily backup and quarterly restore schedules | Required secrets and isolated restore target are validated |
| `synthetic.yml` | Every 15 minutes | Prototype base URL and synthetic check are stable |

## Reactivation gate

Restore automatic triggers only after all four workflows have completed a
successful manual run. Reactivate one workflow per commit so a regression can
be isolated and reverted without affecting the other gates.
