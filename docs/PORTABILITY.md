# Installing and using the skills

These skills are Markdown instructions. They are not a standalone executable application and they do not provide a hosted API.

## Repository-local installation

Clone this repository into a coding-agent workspace that can read local files and run Python 3.10 or later. Keep `.agents/skills/`, `templates/`, `standards/`, `docs/`, and `scripts/` together. Read `AGENTS.md` and `.agents/skills/generate-docs/SKILL.md` before starting.

Some coding agents discover skills from `.agents/skills/`. Others require you to point the assistant at the SKILL.md file explicitly. Follow the installation instructions of your agent. Do not assume all agents support the same discovery conventions.

## Portable copy

Copy the four skill folders into your agent's supported skills directory. Also copy `templates/`, `standards/`, `docs/INPUT-CONTRACT.md`, and `scripts/` into the working project. The current instructions use repository-relative paths, so these supporting resources must remain available or the paths must be updated.

## Using ChatGPT Work

Open a Work task with access to your authorized source files and this repository. Ask it to read `AGENTS.md`, the master skill, and the intake contract, then execute the stages. Work may not automatically discover repo-local skills in every environment, so reference the files explicitly. Review the evidence handover and generated documents before publishing.

## Using another agent

Supply the source file paths, audience, desired deliverables, and output directory. Ask the agent to follow the master skill and explicitly invoke the Analyzer, Drafter, and Proofreader instructions. Record whether proofreading was independent.

## Validation

The legacy checker supports the default three-document profile. The newer `scripts/validate_run.py` checks a `run.json` manifest, custom deliverables, source SHA-256 hashes, source locators, exact evidence quotations, and review status. Neither checker proves technical correctness. See `docs/QUICKSTART.md`.
