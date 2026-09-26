# Technical-writing case study

## Sources and evidence
- `input/` contains the authoritative PRD and supporting artifacts.
- Never invent product behavior. Keep unsupported details explicit rather than filling gaps.
- Classify source claims in analysis as **FACT**, **ASSUMPTION**, **INFERENCE**, **UNKNOWN**, or **CONTRADICTION**.
- Cite source locations in analysis using file paths and sections, pages, or line numbers where available.
- Surface contradictions with citations to each conflicting claim; do not choose a side.

## Reusable workflow
Use this workflow for any PRD: **Analyzer → structured handover → Drafter → independent Proofreader**.

1. **Analyzer:** Review the PRD and supporting artifacts; identify requirements, evidence, gaps, and contradictions with claim classifications and citations.
2. **Structured handover:** Record scope, classified claims, source locations, unresolved questions, and contradictions for the Drafter.
3. **Drafter:** Draft the requested deliverable from the handover and sources, preserving uncertainty and unresolved contradictions.
4. **Independent Proofreader:** Use a reviewer separate from the Drafter to check source fidelity, unsupported behavior, completeness, clarity, and consistency; report issues for revision.

Keep this workflow generic across future PRDs. For the three-document workflow, use
`output/<slug>/analysis/`, `feature/`, `how-to/`, `release-note/`, and `qa/`.
Write an evidence-based content plan that distinguishes new content, updates to
existing content, and deferred work; never assume an existing document exists
without inspecting it. Do not create extra reader-facing articles without a
specific supported need.
After drafting, map every material handover claim in `analysis/COVERAGE.md`.
For revised PRDs, compare two source versions before changing documentation;
preserve the earlier output and record affected sections in `analysis/CHANGE-IMPACT.md`.
