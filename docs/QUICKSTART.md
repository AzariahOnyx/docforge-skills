# Quickstart: use your own specification

This workflow runs in a compatible coding-agent environment that can read local files and write Markdown. It is **not** a hosted upload service or a one-click application. Source inspection, QA, and publication approval remain necessary.

## Option A — Reproduce the tested three-document demo

1. Clone the repository in a compatible agent workspace.
2. Read `AGENTS.md` and `.agents/skills/generate-docs/SKILL.md`.
3. Use the fictional `demo/mock-prd.md` as the source, and choose a new output directory to preserve existing examples.
4. Ask the agent:

```text
Read AGENTS.md, docs/INPUT-CONTRACT.md, and .agents/skills/generate-docs/SKILL.md.
Run the default three-document profile on demo/mock-prd.md.
Audience: signed-in Pulseboard members.
Output: output/my-quiet-hours-run/.
Generate the Analyzer handover, clarifications, content plan, feature guide,
one supported how-to, release note, coverage ledger, and source-first QA report.
Do not invent an end time or time zone for "Until tomorrow".
Run python3 scripts/check_outputs.py output/my-quiet-hours-run/.
Report blockers and distinguish structural PASS from publication readiness.
```

5. Inspect `analysis/`, `feature/`, `how-to/`, `release-note/`, and `qa/`. Compare the claims with the original fictional source.

## Option B — Request a different documentation type

Provide an accessible source file and a clear reader goal. For example:

```text
Read AGENTS.md, docs/INPUT-CONTRACT.md, and .agents/skills/generate-docs/SKILL.md.
Source: input/my-approved-api-spec.md.
Audience: developers integrating the API.
Deliverable: one API reference draft only, not a feature guide/how-to/release-note package.
Output: output/my-api-reference/.
Use the Analyzer -> HANDOVER -> Drafter -> source-first Proofreader process.
Cite every material technical claim in review artifacts.
Do not invent endpoints, request parameters, auth, error codes, or examples.
Mark unsupported sections BLOCKED. Create a coverage ledger and QA report.
Record a manual API-reference structure review; the legacy checker does not
validate this custom profile. Do not claim publication approval.
```

This custom-profile route is **newly generalized instruction behavior**, not yet validated by a reproducible automated end-to-end test. Verify its outputs manually before relying on it.

## If the source is incomplete

The agent should produce explicit clarification questions, leave unsafe procedures blocked, and state which sources or sections it could not inspect. It must not fill missing technical facts with plausible content.

## Public demonstration and privacy

Use the fictional `demo/` sources for portfolio demonstrations. Do not upload confidential or proprietary specifications to a public repository. The original historical interview PDF is not the recommended sample and its redistribution rights have not been verified.
