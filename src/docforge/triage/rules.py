"""Layer 1 of the "docs needed?" decision: path rules, free and deterministic.

Each changed file gets a category from its path. The outcome follows the adopted rules:

- quiet when every file is a test, CI or build file, a dependency or lock file, logging, monitoring or
  infrastructure configuration, repository-internal docs, or in an undocumented repo or area;
- act when a mapped spec.md changed (new or changed acceptance criteria);
- confirm when UI text (locale files) or feature-flag configuration changed, and nothing needs the model;
- undecided when product code changed: the model decides, or, without one, a person confirms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from docforge.config import CodeArea, CodeRepo, Triage
from docforge.sources.diff import ChangedFile

DEFAULT_PATHS: dict[str, tuple[str, ...]] = {
    "tests": ("test/**", "tests/**", "**/test/**", "**/tests/**", "**/__tests__/**", "**/*.test.*", "**/*.spec.*",
              "**/*_test.go", "**/test_*.py", "**/*_test.py", "e2e/**", "**/e2e/**", "cypress/**", "**/fixtures/**"),
    "ci_build": (".github/**", ".gitlab-ci.yml", ".circleci/**", "Jenkinsfile", "**/Jenkinsfile", "Dockerfile",
                 "**/Dockerfile", "Makefile", "**/*.gradle", "build/**", "scripts/ci/**", ".buildkite/**",
                 "tsconfig*.json", "**/tsconfig*.json", ".eslintrc*", "**/.eslintrc*", "babel.config.*",
                 "webpack.config.*", "vite.config.*", "jest.config.*"),
    "dependencies": ("package-lock.json", "**/package-lock.json", "yarn.lock", "**/yarn.lock", "pnpm-lock.yaml",
                     "**/pnpm-lock.yaml", "poetry.lock", "uv.lock", "Gemfile.lock", "go.sum", "**/go.sum",
                     "Cargo.lock", "requirements*.txt", "**/requirements*.txt", ".nvmrc", ".python-version"),
    "infra": ("infra/**", "terraform/**", "**/*.tf", "helm/**", "charts/**", "k8s/**", "deploy/**", "monitoring/**",
              "**/logback*.xml", "**/log4j*.*", "**/logging.*", "alerts/**", "**/prometheus*.yml"),
    "repo_docs": ("README.md", "**/README.md", "CHANGELOG.md", "CONTRIBUTING.md", "docs/adr/**", "**/adr/**",
                  "CODEOWNERS", ".github/CODEOWNERS"),
    "ui_text": ("**/locales/**", "**/locale/**", "**/i18n/**", "**/*.po", "**/messages*.json", "**/strings.xml",
                "**/*.strings", "**/translations/**"),
    "feature_flags": ("**/feature-flags/**", "**/feature_flags/**", "**/featureflags/**", "**/flags.json",
                      "**/*feature-flag*", "**/*feature_flag*"),
}
QUIET = ("tests", "ci_build", "dependencies", "infra", "repo_docs", "undocumented")
CONFIRM = ("ui_text", "feature_flags")
LABELS = {
    "tests": "tests", "ci_build": "CI or build files", "dependencies": "dependency or lock files",
    "infra": "logging, monitoring or infrastructure", "repo_docs": "repository-internal docs",
    "undocumented": "undocumented code", "ui_text": "UI text", "feature_flags": "feature-flag configuration",
    "spec": "spec.md", "code": "product code",
}


def glob_regex(pattern: str) -> re.Pattern:
    """`**/` matches any number of folders (including none), `*` anything but `/`, `?` one character."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def matches(path: str, patterns) -> bool:
    return any(glob_regex(p).match(path) for p in patterns)


def area_for(repo: CodeRepo, path: str) -> CodeArea | None:
    """The most specific area whose path prefix contains `path`."""
    found = [a for a in repo.areas if not a.path or path == a.path.rstrip("/") or path.startswith(a.path.rstrip("/") + "/")]
    return max(found, key=lambda a: len(a.path), default=None)


@dataclass
class RuleResult:
    outcome: str  # quiet, act, confirm, undecided
    category: str
    reasons: list[str]
    files: dict[str, str] = field(default_factory=dict)  # path -> category
    products: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)


def classify(path: str, repo: CodeRepo, triage: Triage) -> str:
    area = area_for(repo, path)
    if not repo.documented or (area is not None and not area.documented):
        return "undocumented"
    if matches(path, repo.spec_paths):
        return "spec"
    for category, defaults in DEFAULT_PATHS.items():
        if matches(path, (*defaults, *triage.paths.get(category, ()))):
            return category
    return "code"


def apply_rules(repo: CodeRepo, triage: Triage, changed: list[ChangedFile] | None) -> RuleResult:
    if changed is None:
        return RuleResult("undecided", "unknown", ["the changed files are unknown (no diff)"])
    if not changed:
        return RuleResult("quiet", "empty", ["the pull request changes no file"])
    files = {}
    for item in changed:
        paths = [p for p in (item.path, item.old_path) if p]
        categories = [classify(p, repo, triage) for p in paths]
        # A rename counts as the more significant of its two paths.
        order = ["spec", "code", "ui_text", "feature_flags", *QUIET]
        files[item.path] = min(categories, key=order.index)
    areas = [a for a in (area_for(repo, p) for p in files) if a is not None and a.documented]
    result = RuleResult("undecided", "code", [], files,
                        sorted({p for a in areas for p in a.products}),
                        sorted({a.feature for a in areas if a.feature}),
                        sorted({a.owner for a in areas if a.owner}))
    kinds = set(files.values())
    specs = sorted(p for p, c in files.items() if c == "spec")
    if specs:
        result.outcome, result.category = "act", "spec_acceptance_criteria"
        result.reasons = [f"spec.md changed: {', '.join(specs)} (new or changed acceptance criteria)"]
    elif kinds <= set(QUIET):
        result.outcome, result.category = "quiet", "+".join(sorted(kinds))
        result.reasons = ["only " + ", ".join(LABELS[k] for k in sorted(kinds)) + " changed"]
    elif "code" not in kinds:
        flagged = sorted(kinds & set(CONFIRM))
        result.outcome, result.category = "confirm", flagged[0]
        result.reasons = [f"{LABELS[k]} changed: " + ", ".join(sorted(p for p, c in files.items() if c == k))
                          for k in flagged]
    else:
        code = sorted(p for p, c in files.items() if c == "code")
        result.reasons = [f"product code changed ({len(code)} file(s), for example {code[0]})"]
        result.reasons += [f"{LABELS[k]} changed too" for k in sorted(kinds & set(CONFIRM))]
    return result
