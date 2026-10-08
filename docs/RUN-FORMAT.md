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

## Source citations

Use `[S1#L9]` or `[S1#L9-L11]` for a source with stable line numbers. Page and section references such as `[S1#p2]` or `[S1#section:Authentication]` are recorded but require manual verification. The checker cannot inspect a PDF image or infer section boundaries from these references. A citation can exist and still fail to support the claim.

## Structural checks

```bash
python3 scripts/validate_run.py output/my-custom-run
```

The validator checks file paths, hashes, local links, Markdown structure, declared evidence, source quotations, and review statuses. It does not generate documents, extract PDFs, or approve publication.
