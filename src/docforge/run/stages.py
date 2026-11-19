"""The stages of a documentation run and the files each one produces.

Every run has Analyzer, Drafter and Proofreader. A run started with product code
(`run.json` has a "code" entry) also has a Research stage after the Analyzer.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

DEFAULT_DELIVERABLES = (
    "feature/feature-guide.md",
    "how-to/how-to.md",
    "release-note/release-note.md",
)

ANALYSIS_FILES = (
    "analysis/HANDOVER.md",
    "analysis/clarifications-and-assumptions.md",
    "analysis/CONTENT-PLAN.md",
)


@dataclass(frozen=True)
class Stage:
    number: int
    key: str
    name: str
    skill: str | None
    reads: tuple[str, ...]  # repository files the stage reads, besides sources and earlier outputs

    @property
    def work_order(self) -> str:
        return f"prompts/{self.number}-{self.key}.md"


STAGES = (
    Stage(
        1, "analyzer", "Analyzer", ".agents/skills/analyzer/SKILL.md",
        ("AGENTS.md", "docs/INPUT-CONTRACT.md", ".agents/skills/generate-docs/SKILL.md",
         "templates/handover.md", "templates/content-plan.md"),
    ),
    Stage(
        2, "drafter", "Drafter", ".agents/skills/drafter/SKILL.md",
        ("standards/documentation.md", "templates/feature-doc.md", "templates/how-to.md",
         "templates/release-note.md", "templates/coverage.md", "docs/RUN-FORMAT.md"),
    ),
    Stage(
        3, "proofreader", "Proofreader", ".agents/skills/proofreader/SKILL.md",
        ("standards/documentation.md", "templates/qa-report.md", "docs/REVIEW-CHECKLIST.md"),
    ),
)


RESEARCH = Stage(
    0, "research", "Research", None,
    ("docs/RUN-FORMAT.md",),
)


def stages_for(manifest: dict) -> tuple[Stage, ...]:
    """The run's stages, numbered in order. Research is added only for runs with code."""
    stages = list(STAGES)
    if manifest.get("code"):
        stages.insert(1, RESEARCH)
    return tuple(replace(stage, number=i) for i, stage in enumerate(stages, start=1))


IA_PLAN = "analysis/ia-plan.md"


def stage_outputs(stage: Stage, profile: str, deliverables: list[str], *, ia_plan: bool = False) -> list[str]:
    """Run-relative files a stage must produce. `ia_plan`: the run proposes its plan as ia-plan.md."""
    if stage.key == "analyzer":
        return list(ANALYSIS_FILES) + ([IA_PLAN] if ia_plan else [])
    if stage.key == "research":
        return ["analysis/claims.json", "analysis/CROSS-SOURCE.md"]
    if stage.key == "drafter":
        outputs = list(deliverables) + ["analysis/COVERAGE.md"]
        if profile == "custom":
            outputs.append("analysis/evidence.json")
        return outputs
    return ["qa/QA-REPORT.md"]
