"""The three stages of a documentation run and the files each one produces."""

from __future__ import annotations

from dataclasses import dataclass

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
    skill: str
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


def stage_outputs(stage: Stage, profile: str, deliverables: list[str]) -> list[str]:
    """Run-relative files a stage must produce."""
    if stage.key == "analyzer":
        return list(ANALYSIS_FILES)
    if stage.key == "drafter":
        outputs = list(deliverables) + ["analysis/COVERAGE.md"]
        if profile == "custom":
            outputs.append("analysis/evidence.json")
        return outputs
    return ["qa/QA-REPORT.md"]
