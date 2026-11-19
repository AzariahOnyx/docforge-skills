"""Owner answers to a plan's open questions: read them from a comment, write them as a run source.

An answer is a comment line that starts with a question number, for example
`Q3: Only workspace admins` or `A3 - Only workspace admins`. Lines that are not
answers are revision feedback. A comment's answers are saved as one source file
that is never changed afterwards (`sources/answers/A1.md`, `A2.md`, ...), so its
hash in the run stays valid and the drafts can cite it like any other source.
"""

from __future__ import annotations

from pathlib import Path
import re

from docforge.sources.adf import neutralise
from docforge.sources.provenance import now, render

ANSWER_LINE = re.compile(r"^\s*[QA]\s?0*([1-9][0-9]{0,3})\s*[:.)\-–]\s*(\S.*)$", re.I)
SOURCE_ID = re.compile(r"^A([1-9][0-9]{0,3})$")


def split_comment(text: str) -> tuple[dict[int, str], str]:
    """({question number: answer}, the remaining feedback). A later line for the same number is added to it."""
    answers: dict[int, str] = {}
    feedback: list[str] = []
    for line in text.splitlines():
        match = ANSWER_LINE.match(line)
        if match:
            number, answer = int(match.group(1)), match.group(2).strip()
            answers[number] = f"{answers[number]} {answer}" if number in answers else answer
        elif line.strip():
            feedback.append(line.strip())
    return answers, "\n".join(feedback)


def question_ids(questions: list[str]) -> dict[int, str]:
    """{number: label as the register writes it, for example 3: "Q03"} for open questions "Qn: text"."""
    ids = {}
    for question in questions:
        match = re.match(r"^Q0*([1-9][0-9]*)\b", question)
        if match:
            ids[int(match.group(1))] = question.split(":", 1)[0].strip()
    return ids


def next_source_id(folder: Path) -> str:
    used = [int(m.group(1)) for p in folder.glob("A*.md") if (m := SOURCE_ID.match(p.stem))]
    return f"A{max(used, default=0) + 1}"


def write_answers(folder: Path, *, key: str, answers: dict[int, str], labels: dict[int, str],
                  questions: dict[str, str], by: str | None, comment_id: str | None,
                  created: str | None) -> tuple[str, Path]:
    """Write a new answer source into folder; returns (source ID, path). Never overwrites a file."""
    folder.mkdir(parents=True, exist_ok=True)
    source_id = next_source_id(folder)
    path = folder / f"{source_id}.md"
    meta = {"kind": "answer", "id": f"{key} {source_id}", "title": f"Answers from the ticket owner ({source_id})",
            "version": comment_id or "unknown", "updated": created or "", "author": by or "unknown",
            "fetched_at": now()}
    lines = [f"Answers posted on {key} by the ticket owner (account {by or 'unknown'}), "
             f"comment {comment_id or 'unknown'}, {created or 'time unknown'}.", ""]
    for number in sorted(answers):
        label = labels[number]
        lines += [f"## {label}", ""]
        if questions.get(label):
            lines += [f"Question: {neutralise(questions[label])}", ""]
        lines += ["Answer: " + neutralise(answers[number]).replace("\n", " "), ""]
    with path.open("x", encoding="utf-8") as handle:
        handle.write(render(meta, meta["title"], "\n".join(lines)))
    return source_id, path
