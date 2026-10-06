# GitHub three-run triage and bounded workflow pause

User confirmed the three main run IDs below; subsequent Dependabot runs are audited separately. All evidence is from authenticated read-only GitHub API queries except the explicitly authorized workflow disable calls. No run was rerun and no budget setting was changed.

Current remote main is `fba7e2fd64c0bbe5e384a618a0ce8b02a7449996`. Its legitimate web commit removes macOS from two `matrix.os` lists. It is retained; no reset, checkout, main commit or force-push was performed.

| Workflow / run | Event and SHA | Result | Required handling |
|---|---|---|---|
| [37457818388](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37457818388) / .github/workflows/deploy.yaml | push, `fba7e2fd64c0bbe5e384a618a0ce8b02a7449996` | BILLING_OR_BUDGET_BLOCKED | Paused under this instruction; no code repair or rerun justified by this error |
| [37457818326](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37457818326) / .github/workflows/codeql.yml | push, `fba7e2fd64c0bbe5e384a618a0ce8b02a7449996` | BILLING_OR_BUDGET_BLOCKED | Paused under this instruction; no code repair or rerun justified by this error |
| [37457818293](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37457818293) / .github/workflows/test.yml | push, `fba7e2fd64c0bbe5e384a618a0ce8b02a7449996` | BILLING_OR_BUDGET_BLOCKED | Paused under this instruction; no code repair or rerun justified by this error |
| [37458414024](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37458414024) / .github/workflows/codeql.yml | pull_request, `e83b7f96a06fc292bd0cb86bd86e0f537ac912b4` | BILLING_OR_BUDGET_BLOCKED | Paused under this instruction; no code repair or rerun justified by this error |
| [37458413932](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37458413932) / .github/workflows/test.yml | pull_request, `e83b7f96a06fc292bd0cb86bd86e0f537ac912b4` | BILLING_OR_BUDGET_BLOCKED | Paused under this instruction; no code repair or rerun justified by this error |

## Verified root cause

Every failed job in these five runs carries the annotation: ‘The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings’. They have no executed steps. MkDocs deploy and Test pixi jobs were skipped downstream.

This verifies the category BILLING_OR_BUDGET_BLOCKED. The API annotation does not distinguish exhausted free minutes, a zero budget, or failed payment. The reported zero budget / Stop usage settings are user-provided context, not independently read billing settings. Ubuntu migration and macOS capacity notices are separate annotations, not evidence of test/code failures. No CodeQL analysis, SARIF upload, MkDocs build or test execution failure is established by these runs.

## macOS configuration finding

The new main SHA, rather than an old rerun SHA, was used by run 37457818293. Its actual job list includes `OS (macos, envs/osx-arm64.lock.yaml)`. The frozen workflow at this SHA retains an explicit macOS matrix.include entry. Removing macOS only from matrix.os therefore did not remove this generated job. This is a configuration finding separate from the billing block. The workflow is paused; no CI file was changed in this turn. If the workflow is later re-enabled with an intended no-macOS boundary, review that include entry first.

Exact relevant lines at the run SHA:

```yaml
35:         os: [ubuntu, windows]
39:         - os: macos
268:         os: [ubuntu, windows]
```

## Workflow state and costs

| ID | Workflow path | Before | After |
|---|---|---|---|
| 368257323 | .github/workflows/codeql.yml | active | disabled_manually |
| 368257324 | .github/workflows/deploy.yaml | active | disabled_manually |
| 368257331 | .github/workflows/test.yml | disabled_manually | disabled_manually |

Queued/in-progress runs cancelled: 0. Only these three workflows were examined for cancellation. Local WSL work was not stopped. Other workflows, branch protections, security alerts, visibility and billing settings were not changed.

CodeQL is paused: no new cloud security scan is being produced. This is not a security PASS. No immediate further action is required while these workflows remain intentionally paused.

## Timing, attempts, steps and complete annotations

`RUN_TRIAGE_SUMMARY.json` preserves workflow ID/path, attempt, event, SHA, creation/start/end times, and all jobs/steps. End time is the latest job.completed_at; run.updated_at is retained separately and not called mail time. The five `checks_and_full_annotations_<run>.json` files contain complete unabridged check-run data and annotations, including line positions, raw messages and output text. Original run and attempt-job API responses are saved alongside them.

### Run 37457818388 / attempt 1

Created 2026-10-06T11:39:08Z; started 2026-10-06T11:39:08Z; jobs completed 2026-10-06T11:39:11Z; event push; branch main.

- build: failure, 2026-10-06T11:39:08Z → 2026-10-06T11:39:11Z, executed steps=0.
- deploy: skipped, 2026-10-06T11:39:11Z → 2026-10-06T11:39:11Z, executed steps=0.
### Run 37457818326 / attempt 1

Created 2026-10-06T11:39:08Z; started 2026-10-06T11:39:08Z; jobs completed 2026-10-06T11:39:11Z; event push; branch main.

- Analyze (python): failure, 2026-10-06T11:39:08Z → 2026-10-06T11:39:11Z, executed steps=0.
### Run 37457818293 / attempt 1

Created 2026-10-06T11:39:08Z; started 2026-10-06T11:39:08Z; jobs completed 2026-10-06T11:39:14Z; event push; branch main.

- Detect Pixi changes: failure, 2026-10-06T11:39:08Z → 2026-10-06T11:39:11Z, executed steps=0.
- OS (macos, envs/osx-arm64.lock.yaml): failure, 2026-10-06T11:39:08Z → 2026-10-06T11:39:14Z, executed steps=0.
- OS (ubuntu): failure, 2026-10-06T11:39:08Z → 2026-10-06T11:39:11Z, executed steps=0.
- OS (windows): failure, 2026-10-06T11:39:08Z → 2026-10-06T11:39:10Z, executed steps=0.
- OS (pixi): skipped, 2026-10-06T11:39:11Z → 2026-10-06T11:39:11Z, executed steps=0.
### Run 37458414024 / attempt 1

Created 2026-10-06T11:44:29Z; started 2026-10-06T11:44:29Z; jobs completed 2026-10-06T11:44:32Z; event pull_request; branch dependabot/github_actions/github-actions-547ce19ed8.

- Analyze (python): failure, 2026-10-06T11:44:30Z → 2026-10-06T11:44:32Z, executed steps=0.
### Run 37458413932 / attempt 1

Created 2026-10-06T11:44:29Z; started 2026-10-06T11:44:29Z; jobs completed 2026-10-06T11:44:35Z; event pull_request; branch dependabot/github_actions/github-actions-547ce19ed8.

- Detect Pixi changes: failure, 2026-10-06T11:44:30Z → 2026-10-06T11:44:32Z, executed steps=0.
- OS (ubuntu): failure, 2026-10-06T11:44:30Z → 2026-10-06T11:44:33Z, executed steps=0.
- OS (macos, envs/osx-arm64.lock.yaml): failure, 2026-10-06T11:44:30Z → 2026-10-06T11:44:35Z, executed steps=0.
- OS (windows): failure, 2026-10-06T11:44:30Z → 2026-10-06T11:44:35Z, executed steps=0.
- OS (pixi): skipped, 2026-10-06T11:44:33Z → 2026-10-06T11:44:32Z, executed steps=0.

Local scientific verification is independent. Gate5 run 03 remains FAILED_TIME_LIMIT with no accepted primal. Workflow pausing does not change or qualify any research result.
