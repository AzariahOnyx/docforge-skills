# V2 acceptance test

V2 exists to make the repository generate reader-ready documentation through its own reusable workflow, not through post-generation manual rewriting.

## Clean-room rule

For a regression run, the executor may read only the supplied PRD/supporting artifacts, repository rules, standards, templates, and skills. Previously approved reader-facing outputs are not drafting input. They may be opened only after the fresh run is complete.

## Required run

Use the original Tracks case-study PDF as the source and a new unused output slug. Run the one-command `$demo-studio` skill or the master `generate-docs` skill.

The run must create:

- analysis/HANDOVER.md
- analysis/clarifications-and-assumptions.md
- analysis/CONTENT-PLAN.md
- analysis/EDITORIAL-BLUEPRINT.md
- analysis/COVERAGE.md
- feature/feature-guide.md
- how-to/how-to.md
- release-note/release-note.md
- qa/QA-REPORT.md

Then run `python3 scripts/check_outputs.py <fresh-output>`.

## Quality acceptance

The fresh set passes only when all of these are true:

1. No reader-facing product behavior is unsupported by the PRD.
2. The disable-Tracks contradiction remains unresolved and is handled without selecting either outcome.
3. The feature guide explains the task-versus-track mental model before lower-value detail and preserves material lifecycle, permission, offline, cross-project, and irreversible consequences.
4. The how-to uses a fully supported start/action/result path. It is not padded with inferred Start/Stop, bulk-selection, permission, or recovery steps.
5. The release note is short, change-oriented, and limited to the most useful distinct supported capabilities; it does not invent date, version, rollout, platform, or previous-state claims.
6. The three documents have distinct reader jobs and do not merely repeat the same content at different lengths.
7. Technical fidelity PASS, editorial/assignment-fit PASS, Draft challenge PASS, and structural checker PASS are all present.
8. Publication blockers remain explicit and separate from assignment readiness.

Exact wording and section names do not need to match the approved benchmark.

## Deterministic tests

GitHub Actions runs the structural checker and `scripts/test_checker.py`. The regression suite verifies that a valid baseline is accepted and that missing/incomplete editorial blueprints plus missing/duplicated coverage claims are rejected.

## Human/model quality test

The generative acceptance test must be executed by the target runtime (Codex in the repository) because GitHub Actions has no configured model credential. Do not represent deterministic CI as proof that an LLM will produce the desired prose. The clean-room run above is the final behavioral test.
