# Learned rules

Rules DocForge learned from review feedback. Each rule is one YAML file (`R001.yml`, ...) and moves through `proposed`, `tested`, and `live`, or ends as `rejected` or `retired`.

- `avoid` rules flag a word or phrase, optionally with a replacement. When live, `docforge lint` runs them with Vale.
- `guidance` rules are instructions that cannot be checked mechanically. When live, they appear in Drafter, Proofreader, and revision work orders.

A rule goes live only through `docforge rules approve`, which needs a test report (`docforge rules test`) that matches the rule's current wording. Editing a tested or live rule makes it `proposed` again.

This public folder holds fictional demonstration rules only. Keep rules learned from private feedback in a private repository and point DocForge at it with `--rules-dir` or `DOCFORGE_RULES_DIR`.
