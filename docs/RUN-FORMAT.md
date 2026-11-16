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

## Source citations

Use `[S1#L9]` or `[S1#L9-L11]` for a source with stable line numbers. Page and section references such as `[S1#p2]` or `[S1#section:Authentication]` are recorded but require manual verification. The checker cannot inspect a PDF image or infer section boundaries from these references. A citation can exist and still fail to support the claim.

## Structural checks

```bash
python3 scripts/validate_run.py output/my-custom-run
```

The validator checks file paths, hashes, local links, Markdown structure, declared evidence, source quotations, and review statuses. It does not generate documents, extract PDFs, or approve publication.
