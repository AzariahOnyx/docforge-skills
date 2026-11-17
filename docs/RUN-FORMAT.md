# Custom run format

Use `scripts/create_manifest.py` to create `run.json`. Never silently overwrite a run. The source paths in this file are relative to the repository root. The deliverable paths are relative to the run folder.

## run.json example

```json
{
  "schema_version": 1,
  "profile": "custom",
  "audience": "administrators",
  "sources": [
    {
      "id": "S1",
      "path": "demo/mock-prd.md",
      "sha256": "<actual 64-character lowercase SHA-256 from create_manifest.py>",
      "authority": "primary"
    }
  ],
  "deliverables": ["guides/overview.md"],
  "review": {
    "method": "not_reviewed",
    "source_fidelity": "pending",
    "product_verification": "pending",
    "human_approval": "pending"
  }
}
```

The example hash placeholder is explanatory. Do not copy this example directly as a valid manifest. Run the manifest generator to calculate the real hash.

Review methods: `not_reviewed`, `same_agent_second_pass`, `independent_reviewer`, `human_reviewer`. Review statuses: `pending`, `passed`, `failed`, `blocked`, `not_applicable`.

## analysis/evidence.json example

```json
[
  {
    "claim_id": "C01",
    "source_id": "S1",
    "quote": "Quiet Hours lets a member pause their own in-app alerts for a selected period.",
    "status": "included",
    "destinations": ["guides/overview.md"]
  }
]
```

Evidence status values: `included`, `blocked`, `deferred`, `context`. Only included claims may list document destinations. Exact quotation matching checks that the quoted words occur in the referenced source file, not that a generated claim logically follows from those words. A reviewer must check entailment and contradictions.

### Claim class (optional)

An evidence row may carry `claim_class`: one of `FACT`, `ASSUMPTION`, `INFERENCE`, `UNKNOWN`, or `CONTRADICTION`. When present it must be one of these values, and an `UNKNOWN` or `CONTRADICTION` claim cannot have status `included`. Rows without `claim_class` are still valid.

### Code evidence

A row without `kind`, or with `"kind": "quote"`, is quote evidence as shown above. A row with `"kind": "code"` cites lines of a file at a specific commit of a code repository instead of a source listed in `run.json`:

```json
{
  "claim_id": "C02",
  "kind": "code",
  "repo": "example-org/product-web",
  "commit": "<full 40-character lowercase commit SHA>",
  "path": "src/quiet_hours.py",
  "lines": "L3-L5",
  "excerpt_sha256": "<SHA-256 of the cited lines>",
  "status": "included",
  "destinations": ["guides/overview.md"]
}
```

`excerpt_sha256` is the SHA-256 of the cited lines joined with a newline, without a trailing newline. The validator always checks the repository name, the full commit SHA, a relative path that stays inside the repository, and the line range. To verify the code itself, pass a local Git checkout of that repository:

```bash
python3 scripts/validate_run.py output/my-custom-run \
  --code-root example-org/product-web=../product-web
```

With a checkout, the validator confirms the commit exists, reads the file at that commit, checks that the cited lines exist and are not blank, and recomputes the excerpt hash. It runs `git` locally and never fetches, checks out, or changes anything. Without a checkout, code evidence is reported as not verified. Matching code proves only that the cited lines existed at that commit, not that they support the claim.

## PRD-vs-code research (claims.json)

A run started with `docforge run start --code owner/repo --base <sha> --head <sha>` has a Research stage after the Analyzer. `docforge research packet` lists the changed code with ready code citations. The research stage writes `analysis/claims.json`, using the handover's claim IDs:

```json
{
  "schema_version": 1,
  "claims": [
    {
      "claim_id": "C03",
      "statement": "The pause options are 1 hour and Until tomorrow.",
      "prd": [{"source_id": "S1", "quote": "Choose **1 hour** or **Until tomorrow**, then select **Confirm**."}],
      "code": [{"repo": "example-org/pulseboard-web", "commit": "<full 40-character SHA>",
                "path": "src/pulseboard/quiet_hours.py", "lines": "L5-L8",
                "excerpt_sha256": "<SHA-256 of the cited lines>", "relation": "contradicts",
                "note": "the code offers 2 hours, not 1 hour"}],
      "needs_engineering": null
    }
  ]
}
```

`relation` is `supports`, `contradicts`, or `context`. `docforge evidence code-ref` prints a verified citation for any lines. `docforge research check` verifies every quote and code citation, then gives each claim one status, checked in this order:

| Status | Rule |
| --- | --- |
| `conflicting` | PRD evidence and code marked `contradicts` |
| `needs_engineering` | `needs_engineering` holds a question the code cannot answer |
| `confirmed` | PRD evidence and code marked `supports` |
| `prd_only` | PRD evidence and no supporting code |
| `code_only` | Supporting code and no PRD evidence |
| `unknown` | Neither |

`conflicting`, `needs_engineering`, and `code_only` claims raise questions `X1`, `X2`, and so on. The check writes `analysis/CROSS-SOURCE.md` and `analysis/cross-source.json`, and adds the questions to a generated block at the end of `analysis/clarifications-and-assumptions.md`. Rerunning replaces only that block. Nothing is written when any quote or citation fails. A status compares what two sources say; it is not product verification, and a conflict is never resolved by the check.

## Evidence markers and the claim gate

Pages that will be published (runs started with `--publish-to owner/repo`) mark every statement. A statement is a paragraph, a list item, a block quote, or a table data row; headings, table header rows, code blocks and front matter are not statements. Each one ends with an invisible marker:

```markdown
Pausing requires an online connection. <!-- evidence: C06 -->

See [Pause in-app alerts for 1 hour](../how-to/how-to.md).
<!-- evidence: none (navigation link) -->
```

`docforge gate <run>` fails when a statement has no marker, a marker is malformed, a cited claim is unknown, a cited claim is not INCLUDED for that page in `analysis/COVERAGE.md` (or `included` for it in `analysis/evidence.json` for a custom profile), or a cited claim's cross-source status is `conflicting`, `unknown`, or `needs_engineering`. Exemptions pass but are listed for reviewers. The result is saved to `qa/gate.json`.

`docforge publish prepare` runs the gate, then commits the pages to a new local branch `docforge/<run>` in a docs checkout, together with an evidence manifest (`<docs folder>/_docforge/<run>.evidence.json`). It rewrites links between the placed pages, never changes the checkout's working tree or current branch, and never pushes. It writes `publish/pr.json` and `publish/pr-body.md` and prints the `git push` and `gh pr create` commands for a person to run after review. The pull request is a draft unless the run's `--source-pr` is recorded as merged; `docforge publish ready <run> --source-state merged` records the merge and prints `gh pr ready`. A docs repository can run the gate in CI with `templates/ci/docforge-gate.yml`.

## Review loop

Each prepared suggestion has a status in `publish/pr.json`: `open`, `changes_requested`, `revised`, or `closed`. Every review action appends one record to `review/feedback.jsonl` (never rewritten) with the reviewer, time, action, comment, optional page and line, and the commit and revision it applies to.

- `docforge review request-changes <run> --comment ... --reviewer ...` records a change request and writes `prompts/revise-N.md`, a work order that lists every request since the last revision.
- `docforge publish update <run> --docs-checkout <clone>` re-runs the claim gate and adds a follow-up commit to the same suggestion branch, only if no one else moved it. It never pushes.
- `docforge review close <run> --reason <reason> --reviewer ...` closes the suggestion with one of six reasons: `inaccurate`, `not_needed`, `already_documented`, `wrong_place`, `quality`, or `source_changed`.
- `docforge review serve --runs output` opens a local web page on 127.0.0.1 with Diff, Analysis, and History views and the same two actions.

Actions only change local files. Each prints the matching `gh pr comment` or `gh pr close` command for a person to run. Stored commands use the placeholders `<docs-checkout>` and `<run>`, so run files hold no local paths.

## Style linting (Vale)

`docforge lint <run>` runs [Vale](https://vale.sh) with DocForge's house style (`.vale.ini` and `styles/DocForge/`) on the run's pages and saves `qa/vale.json`. Once a suggestion exists, only lines that changed since DocForge last committed the page are reported; `--all` reports every line. The rules flag internal claim or question IDs in reader-facing text, placeholders, generic link text, subjective words, non-inclusive terms, mouse-only wording, and wordy phrases. Evidence markers and code blocks are not linted.

`--fix` shows the replacements Vale offers for single-replacement rules; `--apply` writes them. A fix is never made in front matter, an evidence marker, inline code, a link target, or an HTML tag, or where it overlaps an alert that needs a person. For runs meant for publishing, the claim gate runs again afterwards, and every page is restored if it fails. `docforge run check` includes the Vale result and fails on error-level alerts; if Vale is not installed, it says so and does not fail.

## Learned rules

Review feedback can become rules, each a YAML file in a rules folder (`--rules-dir`, else `DOCFORGE_RULES_DIR`, else `knowledge/rules`). A rule is `proposed`, then `tested`, then `live`, or ends as `rejected` or `retired`.

- `avoid` rules name a word or regular expression (Vale/RE2 syntax), optionally with a replacement. `docforge rules test` runs the rule alone through Vale over past runs' pages and the pages DocForge committed, and records every hit. When live, `docforge lint` applies it.
- `guidance` rules are instructions that cannot be checked mechanically. Their test report lists the pages they would apply to and quotes the feedback they came from, for a person to judge. When live, they appear in Drafter, Proofreader, and revision work orders.

`docforge rules approve` needs a test report that matches the rule's current wording. Editing a tested or live rule makes it `proposed` again, and lint and work orders stop using it until it is tested and approved again. `docforge rules suggest` gathers close reasons and change requests across runs for drafting new rules. Keep rules learned from private feedback in a private repository.

## Source citations

Use `[S1#L9]` or `[S1#L9-L11]` for a source with stable line numbers. Page and section references such as `[S1#p2]` or `[S1#section:Authentication]` are recorded but require manual verification. The checker cannot inspect a PDF image or infer section boundaries from these references. A citation can exist and still fail to support the claim.

## Structural checks

```bash
python3 scripts/validate_run.py output/my-custom-run
```

The validator checks file paths, hashes, local links, Markdown structure, declared evidence, source quotations, and review statuses. It does not generate documents, extract PDFs, or approve publication.
