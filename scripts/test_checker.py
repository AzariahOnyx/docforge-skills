#!/usr/bin/env python3
"""Regression tests for structural, coverage, and V2 editorial-artifact gates."""

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = REPO / "output" / "tracks"
CHECKER = REPO / "scripts" / "check_outputs.py"


def run(directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(directory)],
        capture_output=True,
        text=True,
        check=False,
    )


def copy_example(temporary: str) -> Path:
    root = Path(temporary) / "tracks"
    shutil.copytree(EXAMPLE, root)
    return root


def expect_rejected(name: str, mutate) -> None:
    with TemporaryDirectory() as temporary:
        root = copy_example(temporary)
        mutate(root)
        result = run(root)
        if result.returncode == 0:
            raise AssertionError(f"{name} passed unexpectedly\n{result.stdout}")
        print(f"PASS: {name} rejected")


def main() -> int:
    baseline = run(EXAMPLE)
    if baseline.returncode != 0:
        print("FAIL: baseline Tracks output must pass")
        print(baseline.stdout)
        return 1
    print("PASS: baseline Tracks output accepted")

    expect_rejected(
        "missing editorial blueprint",
        lambda root: (root / "analysis" / "EDITORIAL-BLUEPRINT.md").unlink(),
    )

    expect_rejected(
        "incomplete editorial blueprint",
        lambda root: (root / "analysis" / "EDITORIAL-BLUEPRINT.md").write_text(
            "# Blueprint\n\n## Document contracts\n\nIncomplete.\n", encoding="utf-8"
        ),
    )

    def remove_first_coverage_row(root: Path) -> None:
        path = root / "analysis" / "COVERAGE.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if line.startswith("| C") and "Disposition" not in line:
                del lines[index]
                break
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    expect_rejected("missing claim coverage", remove_first_coverage_row)

    def duplicate_first_coverage_row(root: Path) -> None:
        path = root / "analysis" / "COVERAGE.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        row = next(line for line in lines if line.startswith("| C") and "Disposition" not in line)
        path.write_text(path.read_text(encoding="utf-8") + "\n" + row + "\n", encoding="utf-8")

    expect_rejected("duplicate claim coverage", duplicate_first_coverage_row)

    def partial_v22_artifacts(root: Path) -> None:
        (root / "analysis" / "TERMINOLOGY.md").write_text(
            "# Terminology\n\n## Canonical terms\n\nA deliberately partial V2.2 artifact.\n"
            "\n## Final terminology audit\n\nPASS\n",
            encoding="utf-8",
        )

    expect_rejected("partial V2.2 artifact set", partial_v22_artifacts)

    def invalid_traceability(root: Path) -> None:
        analysis = root / "analysis"
        (analysis / "TERMINOLOGY.md").write_text(
            "# Terminology\n\n## Canonical terms\n\nCanonical source-backed terminology for regression testing.\n"
            "\n## Final terminology audit\n\nPASS\n",
            encoding="utf-8",
        )
        (analysis / "RISK-REVIEW.md").write_text(
            "# Risk review\n\n## High-impact claims\n\nRegression fixture content.\n"
            "\n## Example safety\n\nRegression fixture content.\n"
            "\n## Cross-document ownership\n\nRegression fixture content.\n"
            "\n## Final risk audit\n\nPASS\n",
            encoding="utf-8",
        )
        (analysis / "TRACEABILITY.json").write_text(
            '{"schema_version":"1.0","claims":[],"readiness":"PUBLICATION-READY",'
            '"publication_blockers":["Q01"]}',
            encoding="utf-8",
        )

    expect_rejected("invalid V2.2 traceability/readiness", invalid_traceability)

    print("PASS: V2.2 checker regression suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
