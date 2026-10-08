# Documentation quality benchmark

This is a public-safe, fictional evaluation protocol. It is not a published accuracy result.

## Goal

Compare a direct drafting prompt against the staged Analyzer, Drafter, and Proofreader workflow on the same fixed source and task. Keep the model, temperature, tools, context budget, and source access identical where possible. Record differences, not just scores.

## Procedure

1. Read `cases.json` and the linked fictional source for each case.
2. Run each case twice: once using a direct drafting prompt and once using the documented skill workflow.
3. Save prompts, model version, source hashes, tool availability, outputs, and elapsed time for each run.
4. Have a reviewer who did not generate the output evaluate the assertions. Provide citations and counterexamples for failures.
5. Use the rubric below. Record `pass`, `fail`, or `uncertain` per assertion. Treat uncertain as unresolved, not a success.
6. Publish per-case evidence, denominator, and method before reporting any aggregate.

## Rubric

- **Source fidelity:** No product behavior absent from the provided source is asserted as fact.
- **Contradiction handling:** Incompatible source statements are surfaced and affected procedures blocked.
- **Completeness:** Supported reader goals and relevant warnings are addressed.
- **Traceability:** Material claims link to inspectable, supporting source passages.
- **Task quality:** Prerequisites, steps, and expected results are usable where supported.
- **Style and accessibility:** Descriptive headings, meaningful links, clear language, and accessible structure.
- **Review provenance:** Distinguish an independent reviewer from a same-agent second pass.

A validator can check file existence, hashes, locator bounds, and exact quotation matching. It cannot establish semantic entailment or judge the accuracy of a proposed procedure.

## Scoring

Report assertion pass rate as `passed / (passed + failed + uncertain)` and publish the raw counts. Also report unsupported-claim count, contradiction misses, and unresolved blockers separately. Do not present these numbers as human-reviewed until a reviewer actually performs the evaluation.

## Reproducibility

The cases and expected outcomes are in `cases.json`. No benchmark outcomes are supplied in this repository. Run and record evaluations before making impact claims.
