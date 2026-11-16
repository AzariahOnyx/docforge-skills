import pytest
from conftest import CODE_REPO

from docforge.evidence.code import verify_code_evidence
from docforge.evidence.models import CodeEvidence, parse_line_range
from docforge.research import ResearchError, build_packet, code_ref


def as_evidence(ref):
    first, last = parse_line_range(ref.lines)
    return CodeEvidence("C99", None, [], ref.repo, ref.commit, ref.path, first, last, ref.excerpt_sha256)


def test_packet_lists_changed_files_and_hunks(research_repo):
    root, base, head = research_repo
    packet = build_packet(root, CODE_REPO, base[:10], head[:10])
    assert (packet.base, packet.head) == (base, head)
    assert {(f.path, f.status, f.additions, f.deletions) for f in packet.files} == {
        ("src/pulseboard/notifications.py", "modified", 4, 0),
        ("src/pulseboard/quiet_hours.py", "added", 28, 0),
    }
    assert [(h.path, h.side, h.ref.lines) for h in packet.hunks] == [
        ("src/pulseboard/notifications.py", "added", "L9-L12"),
        ("src/pulseboard/quiet_hours.py", "added", "L1-L28"),
    ]
    assert packet.hunks[0].text.endswith('return ["Email alerts", "In-app alerts", "Quiet Hours"]')


def test_packet_citations_verify_with_evidence_core(research_repo):
    root, base, head = research_repo
    for hunk in build_packet(root, CODE_REPO, base, head).hunks:
        assert hunk.ref.commit == head
        assert verify_code_evidence(as_evidence(hunk.ref), root) == []


def test_removed_lines_are_cited_at_base(research_repo):
    from conftest import RESEARCH, git

    root, _, head = research_repo
    # A follow-up commit removes settings_sections() and deletes quiet_hours.py.
    (root / "src/pulseboard/quiet_hours.py").unlink()
    (root / "src/pulseboard/notifications.py").write_text(
        (RESEARCH / "base/src/pulseboard/notifications.py").read_text(encoding="utf-8"), encoding="utf-8")
    git(root, "commit", "-q", "-am", "Remove Quiet Hours")
    later = git(root, "rev-parse", "HEAD")
    packet = build_packet(root, CODE_REPO, head, later)
    assert {(f.path, f.status) for f in packet.files} == {
        ("src/pulseboard/notifications.py", "modified"), ("src/pulseboard/quiet_hours.py", "deleted")}
    assert [(h.path, h.side, h.ref.lines, h.ref.commit) for h in packet.hunks] == [
        ("src/pulseboard/notifications.py", "removed", "L9-L12", head),
        ("src/pulseboard/quiet_hours.py", "removed", "L1-L28", head),
    ]
    assert all(verify_code_evidence(as_evidence(h.ref), root) == [] for h in packet.hunks)


def test_code_ref_for_any_lines(research_repo):
    root, _, head = research_repo
    ref = code_ref(root, CODE_REPO, head[:8], "src/pulseboard/quiet_hours.py", "L21-23")
    assert (ref.commit, ref.lines) == (head, "L21-L23")
    assert verify_code_evidence(as_evidence(ref), root) == []


@pytest.mark.parametrize(
    "repo, commit, path, lines, message",
    [
        ("pulseboard-web", None, "src/pulseboard/quiet_hours.py", "L1", "owner/repo"),
        (CODE_REPO, None, "src/pulseboard/quiet_hours.py", "1-3", "L10 or L10-L24"),
        (CODE_REPO, None, "src/pulseboard/quiet_hours.py", "L2", "out of range or blank"),
        (CODE_REPO, None, "src/pulseboard/quiet_hours.py", "L27-L99", "out of range or blank"),
        (CODE_REPO, None, "src/pulseboard/missing.py", "L1", "does not exist at commit"),
        (CODE_REPO, "f" * 40, "src/pulseboard/quiet_hours.py", "L1", "not found"),
        (CODE_REPO, "HEAD", "src/pulseboard/quiet_hours.py", "L1", "expected a commit SHA"),
    ],
)
def test_code_ref_errors(research_repo, repo, commit, path, lines, message):
    root, _, head = research_repo
    with pytest.raises(ResearchError, match=message):
        code_ref(root, repo, commit or head, path, lines)


def test_packet_errors(research_repo, tmp_path):
    root, base, head = research_repo
    with pytest.raises(ResearchError, match="expected a commit SHA"):
        build_packet(root, CODE_REPO, "main", head)
    with pytest.raises(ResearchError, match="owner/repo"):
        build_packet(root, "pulseboard", base, head)
    with pytest.raises(ResearchError):
        build_packet(tmp_path / "not-a-repo", CODE_REPO, base, head)
