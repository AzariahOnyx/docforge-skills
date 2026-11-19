"""Owner answers to a plan's open questions: read them from a comment, write them as a run source.

An answer is a comment line that starts with a question number, for example
`Q3: Only workspace admins` or `A3 - Only workspace admins`. `X2: ...` answers a
cross-source question from `docforge research check` (on a docs pull request). Lines that are not
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


CROSS_LINE = re.compile(r"^\s*X\s?0*([1-9][0-9]{0,3})\s*[:.)\-–]\s*(\S.*)$", re.I)


def split_answers(text: str) -> tuple[dict[int, str], dict[int, str], str]:
    """({Qn: answer}, {Xn: answer to a cross-source question}, the remaining feedback).

    `Qn` (or `An`) answers the plan's open question n; `Xn` answers cross-source question n from
    `docforge research check`. A later line for the same number is added to it."""
    plan: dict[int, str] = {}
    cross: dict[int, str] = {}
    feedback: list[str] = []
    for line in text.splitlines():
        for pattern, target in ((ANSWER_LINE, plan), (CROSS_LINE, cross)):
            match = pattern.match(line)
            if match:
                number, answer = int(match.group(1)), match.group(2).strip()
                target[number] = f"{target[number]} {answer}" if number in target else answer
                break
        else:
            if line.strip():
                feedback.append(line.strip())
    return plan, cross, "\n".join(feedback)


def split_comment(text: str) -> tuple[dict[int, str], str]:
    """({question number: answer}, the remaining feedback), for the plan's Qn questions only."""
    plan, cross, feedback = split_answers(text)
    rest = [f"X{n}: {a}" for n, a in cross.items()]
    return plan, "\n".join([*rest, feedback] if feedback else rest)


def question_ids(questions: list[str]) -> dict[int, str]:
    """{number: label as the register writes it, for example 3: "Q03"} for open questions "Qn: text"."""
    ids = {}
    for question in questions:
        match = re.match(r"^Q0*([1-9][0-9]*)\b", question)
        if match:
            ids[int(match.group(1))] = question.split(":", 1)[0].strip()
    return ids


def next_source_id(folder: Path, taken: set[str] = frozenset()) -> str:
    names = [p.stem for p in folder.glob("A*.md")] + list(taken)
    used = [int(m.group(1)) for name in names if (m := SOURCE_ID.match(name))]
    return f"A{max(used, default=0) + 1}"


def write_answers(folder: Path, *, key: str, answers: dict[int, str], labels: dict[int, str],
                  questions: dict[str, str], by: str | None, comment_id: str | None,
                  created: str | None, taken: set[str] = frozenset()) -> tuple[str, Path]:
    """Write a new answer source into folder; returns (source ID, path). Never overwrites a file."""
    return write_labelled_answers(folder, key=key, answers={labels[n]: a for n, a in answers.items()},
                                  questions=questions, by=by, comment_id=comment_id, created=created, taken=taken)


def write_labelled_answers(folder: Path, *, key: str, answers: dict[str, str], questions: dict[str, str],
                           by: str | None, comment_id: str | None, created: str | None,
                           taken: set[str] = frozenset(), role: str = "the ticket owner") -> tuple[str, Path]:
    """Write answers keyed by question label (Q03, X2) as a new source; IDs skip those in `taken`."""
    folder.mkdir(parents=True, exist_ok=True)
    source_id = next_source_id(folder, taken)
    path = folder / f"{source_id}.md"
    meta = {"kind": "answer", "id": f"{key} {source_id}", "title": f"Answers from {role} ({source_id})",
            "version": comment_id or "unknown", "updated": created or "", "author": by or "unknown",
            "fetched_at": now()}
    lines = [f"Answers posted on {key} by {role} (account {by or 'unknown'}), "
             f"comment {comment_id or 'unknown'}, {created or 'time unknown'}.", ""]
    for label in sorted(answers, key=lambda q: (q[0], int(re.sub(r"\D", "", q) or 0))):
        lines += [f"## {label}", ""]
        if questions.get(label):
            lines += [f"Question: {neutralise(questions[label])}", ""]
        lines += ["Answer: " + neutralise(answers[label]).replace("\n", " "), ""]
    with path.open("x", encoding="utf-8") as handle:
        handle.write(render(meta, meta["title"], "\n".join(lines)))
    return source_id, path
