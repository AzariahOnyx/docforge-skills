#!/usr/bin/env python3
"""Exercise coverage gate against meaningful broken output cases."""

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = REPO / "output" / "quiet-hours"
CHECKER = REPO / "scripts" / "check_outputs.py"


def run(directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(directory)],
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    assert run(EXAMPLE).returncode == 0, "baseline example must pass"
    cases = {
        "missing claim": lambda s: s.replace(
            "| C08 | BLOCKED | — | Until tomorrow time and zone are undefined; no clock-time claim. | Q01 |\n", ""
        ),
        "duplicate claim": lambda s: s + "\n| C01 | CONTEXT | — | Duplicate. | None |\n",
        "invalid disposition": lambda s: s.replace("| C08 | BLOCKED |", "| C08 | VERIFIED |"),
        "missing destination": lambda s: s.replace(
            "| C01 | INCLUDED | feature/feature-guide.md |",
            "| C01 | INCLUDED | — |",
        ),
    }
    with TemporaryDirectory() as temporary:
        root = Path(temporary) / "quiet-hours"
        for name, mutate in cases.items():
            shutil.copytree(EXAMPLE, root)
            path = root / "analysis" / "COVERAGE.md"
            path.write_text(mutate(path.read_text(encoding="utf-8")), encoding="utf-8")
            result = run(root)
            if result.returncode == 0:
                print(f"FAIL: {name} passed unexpectedly")
                return 1
            shutil.rmtree(root)
            print(f"PASS: {name} rejected")
        shutil.copytree(EXAMPLE, root)
        impact = root / "analysis" / "CHANGE-IMPACT.md"
        impact.write_text(
            "# Change impact\n\n## Baseline\n\nBoth sources inspected.\n\n"
            "## Source changes\n\nFixed option changed.\n\n"
            "## Document actions\n\nUpdate the how-to.\n",
            encoding="utf-8",
        )
        if run(root).returncode != 0:
            print("FAIL: valid optional change impact rejected")
            return 1
        impact.write_text(impact.read_text(encoding="utf-8").replace("## Document actions", "## Actions"), encoding="utf-8")
        if run(root).returncode == 0:
            print("FAIL: incomplete change impact passed unexpectedly")
            return 1
        print("PASS: optional change-impact structure checked")
        impact.write_text(
            "# Change impact\n\n## Baseline\n\n"
            "## Source changes\n\n"
            "demo/mock-prd-v2.md, line 15 supports the changed option.\n\n"
            "## Document actions\n\nUpdate.\n",
            encoding="utf-8",
        )
        if run(root).returncode != 0:
            print("FAIL: valid source line citation rejected")
            return 1
        impact.write_text(
            impact.read_text(encoding="utf-8").replace("line 15", "line 14"),
            encoding="utf-8",
        )
        if run(root).returncode == 0:
            print("FAIL: blank source line citation passed unexpectedly")
            return 1
        print("PASS: blank source line citation rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
