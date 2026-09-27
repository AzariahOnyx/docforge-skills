---
name: demo-studio
description: Run the Studio Approval Checkpoints PDF live demo in this repository, from safe branch and PDF preflight through the existing generate-docs workflow. Use when explicitly invoked for the Studio demo.
---

# Studio documentation demo

Work from the repository root. This is a thin demo entry point. Use `.agents/skills/generate-docs/SKILL.md` for the actual documentation workflow; do not duplicate or change its rules.

## Inputs and boundaries

- Source: `input/Neo-Studio-Approval-Checkpoints-Dummy-PRD.pdf`.
- Output: `output/studio-approval-checkpoints/`.
- Treat the PDF as the authority for this fictional feature. Do not use the existing Tracks or Quiet Hours outputs as product evidence.
- Do not commit, push, delete, overwrite another output set, or modify the PDF.

## Run

1. Read `AGENTS.md` and check Git status and the current branch. The desired branch is `demo-studio-approval-checkpoints`, based on `main`. If already on it, stay there. If on `main` and it is safe to switch, use an existing local/remote branch or create the branch from `main` if neither exists. If switching would disturb work, stop and report the state; never reset, stash, or discard changes automatically.
2. Verify that the PDF exists and text can be extracted; report its page count. Inspect every page, including tables, figures, notes, and layout. If extraction omits important content, render and inspect it. If unreadable, stop before drafting and report the limitation.
3. Check whether `output/studio-approval-checkpoints/` already contains files. If so, report that this demo has already run and ask for a fresh output slug before generating again. Never overwrite a previous run.
4. Read `.agents/skills/generate-docs/SKILL.md` and run its entire Analyzer → structured handover → Drafter → independent source-first Proofreader sequence. Follow the repository templates and `standards/documentation.md`. Create a fresh output set in the specified output directory. Preserve both sides of source contradictions and all material unknowns; do not choose a side or invent UI behavior.
5. Run `python3 scripts/check_outputs.py output/studio-approval-checkpoints`. Fix structural defects supported by source evidence and rerun the check. A structural PASS alone does not prove source fidelity.
6. Report the created file paths, source page count, CREATE/UPDATE/DEFER scope, QA and checker results, material unanswered questions, and assignment versus publication readiness. Leave all changes uncommitted and unpushed.
