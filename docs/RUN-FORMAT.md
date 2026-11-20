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

`docforge run start` also records each source's `kind`: `file`, or `jira` or `confluence` for a file written by `docforge sources fetch`. A fetched source also gets an `origin` with its issue key or page ID, title, URL, version, last update, space (Confluence) and fetch time, read from the file's provenance header. Sources given with `--context` have the authority `context`: supporting material, never a requirement source on its own.

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
- `docforge publish open <run> --docs-checkout <clone>` pushes the branch to the doc collection's `git_url` (default `https://github.com/<owner>/<repo>.git`; a `file:///` bare repository works for tests) and opens the pull request through `api_url`, as a draft while the source change is unmerged. It pushes only a `docforge/` branch whose tip is the commit in `pr.json`, never forced; the token reaches Git through an askpass helper, never the command line or URL. An existing pull request for the branch is found and updated, never duplicated. `pr.json` records `pr_number`, `pr_url`, `pr_node_id` and `pushed_commit`. After `publish update`, run `open` again to push the revision.
- `docforge publish ready <run> --source-state merged --apply` also marks the pull request ready on GitHub (GraphQL `markPullRequestReadyForReview`) and records `ready_applied`.
- `docforge pr handle <payload> --event <name> --runs <folder>` records one GitHub delivery about a DocForge pull request (found by repository and pull request number in `publish/pr.json`, up to four folders deep); `docforge serve --docs-runs <folder>` does the same for live deliveries. A review with state `changes_requested`, a line comment, or a comment mentioning `bot_login` counts when its `author_association` is in `reviewer_associations`; bots, DocForge itself, edits, deletions and anything after the pull request is merged or closed are ignored. A line comment becomes a change request once its review requested changes, or at once when it mentions DocForge. `pr.json` keeps `processed` delivery IDs, waiting `line_comments`, `requested_reviews`, `last_request_at`, `replies` (posted or not, and why), `github_state` and `automatic_revisions`. Change requests from GitHub have `"origin": "github"` in `review/feedback.jsonl`.
- `docforge pr run <run>` (or `--all --runs <folder>`) carries out a pending revision after `revision_delay_seconds`: with a `backend` section through the API (the answer may change only the pull request's pages, `analysis/COVERAGE.md` and `qa/QA-REPORT.md`; the claim gate and clean-up must pass, with one repair turn; on failure every file is restored and the status is `revision_failed` until new feedback arrives), otherwise it waits for a session to carry out `prompts/revise-N.md` and run `publish update`. A committed revision is pushed and answered on the pull request when `auto_create_pr` allows. After `max_revisions`, DocForge asks for a person.
- Answers in a pull request comment: `Qn:` lines answer the plan's open questions, `Xn:` lines answer cross-source questions in `analysis/cross-source.json`. They are saved as a new answer source (next to earlier answers, else `<run>/answers/A<n>.md`) and added to `run.json`. Each `Xn` answer adds `{claim_id, question_id, source_id, sha256, by, at}` to `analysis/resolutions.json`; the claim gate stops blocking that claim while the answer source in `run.json` still has that hash. Unknown question numbers record nothing.
- A merged source pull request (`run.json` `source_pr`) marks each matching docs pull request ready (`mark_ready`, and on GitHub with `auto_create_pr`).

Placement: without `--place`, `publish prepare` uses the pack's `placement` list. The first entry whose `applies_to` matches a page gives a path template with the fields `{product}` (the run's product key), `{category}` and `{slug}` (front matter; `slug` falls back to `title`) and `{month}` (front matter `release_month`, else the month the pull request is prepared). Values become lowercase slugs; a missing value is an error, never a guess. On the Jira route, the branch is named `docforge/<ticket key>` and the evidence manifest `_docforge/<ticket key>.evidence.json`.
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

## House packs

A pack is a folder with a `pack.yaml`:

```yaml
schema_version: 1
name: demo
version: 0.1.0
conventions: conventions.md
products:
  - key: alerts
    title: Pulseboard Alerts
references:
  - path: references/products/alerts.md
    title: Alerts product reference
    products: [alerts]               # only for runs started with --product alerts
  - path: references/voice.md
    title: Voice
    stages: [drafter, proofreader]   # default; analyzer is also allowed
    applies_to: [how-to/]            # deliverable folders or paths; empty means all
article_specs:
  - type: procedural
    path: specs/how-to.md
    applies_to: [how-to/]            # empty: the Analyzer chooses where it applies
cleanup_steps:                       # run in order; each kind has its own fields
  - id: em-dashes
    kind: replace                      # pattern, replacement, ignorecase
    description: Replace em dashes.
    pattern: "\u2014"
    replacement: " - "
  - id: support-links
    kind: marker_link                  # pattern with (?P<type>...) and (?P<phrase>...), address, templates
    description: Turn support markers into links.
    pattern: '\[SUPPORT (?P<type>INQUIRY|ENABLE)(?:: (?P<phrase>[^\]]*))?\]'
    address: support@example.com
    templates: {INQUIRY: {subject: "Question about {phrase}", line: "I have a question about {phrase}."}}
    default_type: INQUIRY
    applies_to: [how-to/]              # optional, like references
    skip: [release-note/]              # optional: deliverables the step never runs on
vale:
  styles_path: styles
  based_on: [House]
capture_profiles:
  - name: demo-app
    path: capture/profiles.yml
```

Unknown keys are errors. Every path must stay inside the pack, including through symlinks, and each file is limited to 1 MB. The pack's `sha256` covers `pack.yaml` and every file it names.

With `run start --pack`, `run.json` gets a `pack` entry with the name, version, hash, each file's path, role and hash, and `copied_to: "pack"`. The manifest, conventions, references and article specs are copied to the run's `pack/` folder, and work orders point there. Revision orders check the copied `pack.yaml` against its recorded hash. With `--product <key>`, the run records the product and work orders include only references for that product (and references with no `products`). Without it, product references are left out and the orders list the pack's products.

Vale style files are copied to the run too. `docforge lint` checks them against their recorded hashes and runs them with DocForge's house style and live learned rules; a pack style cannot use the names `DocForge`, `DocForgeLearned` or `Vale`. Capture profiles are checked and recorded but not used yet.

## API backend

`docforge run exec <run>` runs unfinished stages in order (or one with `--stage N`) through the Anthropic API. It never re-runs a stage whose outputs exist and refuses one whose outputs exist only in part. The Research stage still runs in a Claude Code session.

Each request has two system blocks and one user message. The first system block holds DocForge's backend rules and every pack file the run uses; it is the same for every stage and cached for an hour. The second holds the stage's skill and engine files. The user message holds the sources (checked against their recorded hashes, marked as data), earlier stage outputs, docs matches for the Analyzer, and the work order. The answer is JSON whose `path` values are limited to the stage's outputs.

`<run>/backend/calls.jsonl` gets one line per call: time, stage, attempt, model requested and served, effort, `max_tokens`, whether refusal fallback was on, request ID, stop reason, duration, token usage (with per-attempt `iterations` when a fallback ran), estimated cost, and the prompt's SHA-256. It never holds prompt text or credentials. `run.json` gets `backend` totals: calls, estimated cost, models, and the date of the price table. With `--dry-run`, `<run>/backend/dry-run/` holds each stage's assembled prompt and request settings instead, and no call is made.

## Flow sources

`docforge sources flow <pdf> --id F1 --out <folder>` reads a step-per-page PDF. A page is a step when a line matches the profile's header pattern (default `Step 3/7` or `Step 3 of 7`); the step's action runs to its first sentence end and the rest of the page is its explanation, without noise lines such as page numbers. It writes `F1.json` (steps with page, action, explanation and the position of the page's largest image, for screenshot capture later) and `F1.md`:

```markdown
<!-- docforge-source
kind: flow
id: F1
title: Create an Alert
version: 1a2b3c4d5e6f
pdf: create-an-alert.pdf
pdf_sha256: <64 hex characters>
steps: 4
fetched_at: 2026-11-18T10:00:00+00:00
-->

## Step 1 of 4

Click New alert on the Alerts board.
```

`run start --flow F1.md` adds a source with `"kind": "flow"`, its `origin` (PDF name and hash, step count), and `"copy": "flows/F1.md"`, a copy kept in the run so the gate and checks work wherever the run folder goes. `run.json` also gets `"flow_steps": "required"` (or `"optional"`).

Citations: `[F1#step3]` or `[F1#step3-5]`. `scripts/check_outputs.py` and `scripts/validate_run.py` reject a citation of a step that does not exist, a step citation of a source that is not a flow, and a run copy whose hash does not match. A flow evidence row:

```json
{"claim_id": "C03", "status": "included", "destinations": ["guides/create-alert.md"],
 "kind": "flow", "source_id": "F1", "step": 3, "quote": "Enter a Threshold"}
```

The quote must appear in that step. With `flow_steps` required, the claim gate treats a claim as flow-backed when its row in `analysis/HANDOVER.md` cites an existing flow step (default profile) or it has a flow evidence row (custom profile), and every numbered list item in the pages must cite at least one flow-backed claim. `qa/gate.json` and the pull request body report how many numbered steps were backed.

## Clean-up

`docforge cleanup <run> [--apply]` runs the run's pack `cleanup_steps` (from the hash-checked copy of `pack.yaml`) over the deliverables, in order. Kinds: `replace`, `drop_sentences` (a matching sentence goes; a match in code, or a table cell that is only the match, stays and is reported), `marker_link` (a pre-filled `mailto:` link), `merge_alerts` (GitHub alerts of the same type that follow each other become one alert with a list and one combined evidence marker), `move_to_top` (an alert block below the page title) and `check` (findings only; `unless_linked` skips matches that are link text). Steps never change front matter, fenced or inline code, HTML comments including evidence markers, link targets or HTML tags.

With `--apply`, `qa/cleanup.json` and `qa/CLEANUP-REPORT.md` record every change (step, page, line, action, before, after) and finding. For runs that must pass the claim gate (meant for publishing, already proposed, or with required flow steps), the gate runs again and every page is restored if it fails.

## Jira front door

A `jira_ticket` trigger names a Jira context source, four status names (`plan` and `draft`, which DocForge reacts to; `bounce` and `planned`, which it only writes), the Work Types for net-new and enhancement tickets, and the environment variables holding the bot's account ID and the webhook secret. `docforge jira handle` verifies the delivery's `X-Hub-Signature` (HMAC-SHA256 of the exact body), then decides:

| Delivery | Ticket phase | Decision |
| --- | --- | --- |
| Moved to `plan` | new or failed | plan, or bounce to `bounce` with a comment when no PDF or Markdown attachment is usable or one is too large |
| Moved to `plan` | planned / drafted | a comment saying what still works |
| Moved to `draft` | new or planning | pull back to `plan` with a comment (one hop) |
| Moved to `draft` | planned | draft |
| Owner's comment mentioning the bot | planned | revise with the comment as feedback; a bare mention gets a request for specifics |
| Same mention | drafting or drafted | refused with a comment |

Mentions from anyone but the reporter, creator or assignee, and comments by the bot, are ignored.

`docforge jira run <KEY>` (or the `serve` worker) carries out pending work. Planning writes `<workspace>/tickets/<KEY>/sources/`: `issue.md` (the issue, with a provenance header), the attachments, a Markdown text file for each PRD PDF, and `F<n>.md` for each PDF that is mostly step pages. Attachments are downloaded only from the Jira host, or by HTTPS redirect to a host in `attachments.redirect_hosts` (the Authorization header is never sent on a redirect). The run is `<workspace>/tickets/<KEY>/run`. A revision moves the plan files to `analysis/revisions/r<N>/` and appends the feedback to `prompts/1-analyzer.md`; if the revision fails, the earlier plan is restored. Owner answers (comment lines such as `Q3: ...`) are written to `<workspace>/tickets/<KEY>/sources/answers/A<n>.md`, a file that is never changed afterwards, with a provenance header (`kind: answer`, the comment's author, ID and time). The run gets a source with `"kind": "answer"` and its hash, and each work order gets a "Sources added after the run started" section; earlier sources and hashes are not changed. Answers count only when every question number is open in the current plan. The ticket state's `answered` maps each answered question to its source. With `publish.plan_pr: true`, the run is started with `ia_plan` (run.json records the front matter values DocForge knows: mode, product, jira, docforge_run) and `publish`, and the Analyzer's outputs include `analysis/ia-plan.md`. After the Analyzer, `docforge plan check` must pass; then `publish/plan-pr.json` and `publish/plan-pr-body.md` record the plan pull request on branch `docforge/plan-<feature slug>`, with the file at the doc collection's `plan_path` (default `plans/{slug}/ia-plan.md`, allowed outside `filter`). It opens ready for review when `auto_create_pr` allows; otherwise the comment gives `docforge plan open`. The ticket state's `plan_pr` holds its link (or branch). While it is set, moving the ticket to the draft status and mentions on the ticket get a reply pointing to the pull request. Plan pull request review (`docforge pr handle` / `serve --docs-runs` route events for `plan-pr.json` too): reviews, line comments and mentions from reviewers become `requests` in `plan-pr.json`; after `revision_delay_seconds`, `docforge pr run` archives the plan to `analysis/revisions/r<N>/`, adds the requests to `prompts/1-analyzer.md`, runs the Analyzer (backend) or waits for a session, checks the new `ia-plan.md`, commits it to the plan branch and pushes it when `auto_create_pr` allows. If the remote plan branch has a commit DocForge did not push, the status becomes `hand_edited` and the file is not rewritten. A failed revision restores the previous plan (`revision_failed`). An approving review (its `commit_id`), a push by someone else that sets `status: approved` in the plan file (a `synchronize` event; the file is read at that commit, and a push without it counts as a hand edit), or a merge without a review (the head commit) sets `approved_commit`; `pr run` fetches the branch, reads the plan file at that commit and checks it (`approval_invalid` and a reply when it fails). A valid plan is saved as `analysis/ia-plan.approved.md`, with `status: approved` in its front matter whatever approved it; run.json gets `approved_plan` (`commit`, `pull_request`, `file`, `placements` from deliverable to docs path, `needs_own_run`) and `deliverables` becomes the drafts the plan asks for (overview -> feature guide, procedural -> how-to, release-notes -> release note; one of each, new articles only). The Drafter and Proofreader work orders are written again with an "Approved plan" section. With `pr run --jira-trigger --jira-state` (or `serve` with both endpoints), approval queues the ticket's drafting; the drafts pull request uses the approved docs paths, its body names the approved commit, and the plan pull request gets a reply with its link. `scripts/check_outputs.py` requires only the listed drafts for a run with `approved_plan`. With a trigger `publish` section (`collection`, `checkout` relative to the config, `base`), a passing draft is prepared as branch `docforge/<ticket key>`; with `auto_create_pr` it is also opened, and `pull_request` holds its link. A move to a `statuses.shipped` status after drafting records `shipped` and, with `auto_create_pr`, marks the pull request ready. A publish failure never undoes the drafts: it is reported in the comment. A failed plan leaves the ticket `failed`; a failed draft leaves it `planned`, so moving it to the draft status again retries. State lives in `<state>/<KEY>.json`: `phase` (new, planning, planned, drafting, drafted, failed), `run`, `revision`, `product`, `pending` work, the IDs of handled deliveries, an `outbox` of every comment and move (with whether it was sent and why not), and `history`.

## Docs needed? (code pull requests)

`docforge.triage` decides a code pull request in three outcomes, recorded in `.docforge/decisions.jsonl` as `outcome` (quiet, act, confirm), `category`, `reasons` and `triage` (`layer`: rules, model or none; the path category of each changed file; `products`, `features` and `owners` from the dependency map; the model's evidence, request ID and cost). `docs_needed` stays for older readers: act and confirm are `needs_research`.

- Path rules: each file's category comes from built-in patterns plus `triage.paths`. Quiet: tests, ci_build, dependencies, infra, repo_docs, and files in a repository or area with `documented: false`. Act: a file matching the repository's `spec_paths`. Confirm: ui_text, feature_flags. Any other file is product code, and the rules leave the decision to the model. A rename counts as the more significant of its two paths.
- Model: only when `triage.model` is set. The request holds the pull request's title and description, the file categories, the diff (at most `triage.max_diff_chars`) and up to five matches from the doc collection's checkout, all marked as data. The answer is an outcome and a category from the adopted table; an inconsistent pair becomes confirm, and a quiet answer becomes confirm when UI text or flags changed. Before the call, the worst-case cost must fit `max_cost_usd_per_pr` and what is left of `max_cost_usd_per_day` (a ledger, `triage-costs.jsonl`, next to the decision log). Over a cap, without a price, or when the call fails, the outcome is confirm.
- Without a model, product code changes are confirm: a person decides.
- Feedback (`source_pr_feedback` policy, off by default): a commit status with context `docforge/docs` and state `success` whatever the outcome, and, for act and confirm, one comment marked `<!-- docforge-docs-check -->` that later decisions edit (a later quiet decision corrects it). `suppress_source_pr_comments` stops the comment. The decision's `feedback` records what was posted, or why not.

## ia-plan.md format

One format for the engine and the docs-writer agent (`templates/ia-plan.md`). Front matter: `feature`, `mode` (Net-New or Enhancement), `product`, `category`, `owner`, `source_prs`, `engineering_spec`, `release`; optional `jira`, `docforge_run`, `decision` (act, confirm, quiet), `decision_reason` and `status` (proposed, approved). Tables: Existing articles - impact (Article, Docs path, Action: update / archive / none, Change needed, Outdated passage, Evidence), New articles (Title, Type, Docs path, Why, Evidence), Out of scope (Topic, Reason), Open questions (ID, Question, Why it matters), Spec-versus-code conflicts (ID, Spec says, Code says, Where, Question). Evidence is claim IDs (C03) or source tags (`SPEC:<section>`, `CODE:<path>:<line>`). The first engine format (Change / Why / Claims columns, conflicts with a Claim column) is still read and converted: deprecate and remove become archive. Rows with action none are listed but need no work.

## Outdated content finder

Switched on per doc collection (`find_outdated: true`, with `checkout`; `must_review` keywords; `outdated_cap`, default 25). It runs after the Analyzer and before the plan pull request, in the Jira and code routes, and writes:

- `analysis/change-note.json`: `strings` (old and new UI wording with where it came from: locale JSON keys, or quoted user-facing strings on removed and added code lines), `spec_changes` (removed and added spec lines), `terms` (the plan's feature, bold UI labels), `behaviour` (old and new, when a person or session writes them), `old_strings`. Without a code change, only terms from the sources' bold labels.
- `analysis/outdated-shortlist.json`: `pages` (path, title, `must_review`, reasons, matching lines, images in the matching sections), `must_review`, `cap`, `dropped`, `searched_pages`. A page with an old string (whole word) or a must-review keyword always stays; others are ranked by term matches up to the cap.
- `outdated/pass-1.json`, `pass-2.json`: `{"verdicts": [{path, verdict: affected | not_affected | unsure, passage, action: edit | archive | none, reason}]}`, from two separate backend calls (pages in reverse order for pass 2; `backend.stages.outdated` settings; the run's cost cap and `calls.jsonl`) or from `prompts/outdated-pass-<n>.md` work orders for two sessions.
- `analysis/outdated.json` and `analysis/OUTDATED.md`: the merged verdicts. An affected verdict whose passage is not in the article (ignoring emphasis and spacing) becomes unsure; agreeing passes stand; disagreement, or a must-review page without a verdict in a pass, is unsure.
- `analysis/ia-plan.md`: affected and unsure pages become existing-article rows (edit -> update, archive -> archive, unsure rows "(check) ..."); for rows already there, a missing or wrong passage takes the checked one, and an unsure verdict prefixes "(check: <reason>)". The plan pull request body lists the must-review pages and their verdicts.

`docforge outdated eval <cases> --docs <checkout>` scores shortlist recall (free) and, for cases pointing to an `outdated.json`, verdict recall, against the pages writers updated. `docforge outdated cases` drafts the cases file from the docs history (commits grouped by a Jira key or `#<pr>` in the message); a person fills in each change note, checks the expected pages and sets `checked_by`.

## Edits to existing articles

On approval, with a docs checkout, each Existing articles row with action `update` or `archive` becomes an entry in run.json `edits`: `src` (`existing/edited/<docs path>`), `dest`, `action`, `title`, `base_commit` and `sha256` of the article on the docs repository's base branch (copied to `existing/original/<docs path>`), `change` and `passage` from the plan. An article that is not on the base branch is named in `needs_own_run`. An archive is written at once: the original with `status: archived` added to (or replacing the status in) its front matter.

For updates, the Drafter's outputs include `analysis/fixes.json`: `{"fixes": [{"path", "find", "replace", "reason"}]}`. `docforge outdated fix <run>` (and the Drafter's checks with the API backend, with one repair turn; and drafting in both routes) applies them to `existing/original/` and writes `existing/edited/` and `analysis/edits.json` (per docs path: action, changed line ranges, the changes, problems). Checks: each `find` appears exactly once and stays inside one paragraph; a fix adds no heading and is at most three times its find plus 400 characters; the front matter and headings are unchanged; no list items, table rows or images are lost; at least 90% of the words remain; the plan's outdated passage and the change note's old UI strings are gone (an old string inside its own new wording does not count); an archive only gains the status. In `analysis/COVERAGE.md`, an edited page's destination is `existing/edited/<docs path>`.

The claim gate (`EvidenceRules.scopes`) checks only statements that start in an edited page's changed line ranges, and nothing in an archived page; the evidence manifest in the drafts pull request carries the same scopes by docs path, so the docs repository's CI gate does the same. The edited articles are placed at their own paths without link rewriting. The pull request body has an "Edits to existing articles" section: each fix before and after (markers removed), the check results, and the archived articles. `scripts/check_outputs.py` accepts a run with an approved plan and edits but no new drafts.

## Code route (features)

A feature's state is `<workspace>/state/features/<key>.json` (the code repository's `workspace`): `key` and `label` (from a Jira key, the area's feature, or `<repo>-pr-<n>`), `jira`, `repo`, `collection`, `phase` (planning, planned, drafting, drafted, failed), `run`, `prs` (each with its head and base commits, state open/merged/closed, triage reasons and the run source holding its description), `plan_pr`, `pull_request` and `history`. A "confirm" decision waits in `<workspace>/state/confirm/<repo>-<n>.json` until `plan` or `skip` (kept in `state/skipped/` with who and why).

The run is `<workspace>/features/<key>/run`. Initial sources are `S1, S2, ...` in `features/<key>/sources/`: each pull request's description (kind `github_pr`, id `owner/repo#n`, version its head commit) and every `spec_paths` file it changed or its areas' `spec` names (kind `spec`, id `owner/repo:path`, read at the head commit from the code repository's `checkout`). `run.json` records the code repository, the first pull request's base and the last one's head (the Research stage), `publish` to the code repository's doc collection, `ia_plan` with the front matter the dependency map gives (feature, product, owner from the most specific area; `source_prs`; `engineering_spec`; `jira`), and `feature_run`. Pull requests that join later become `P<n>` sources (and `S<n>` for a spec file whose content changed) through `add_sources`; before approval a "code change" request goes to `plan-pr.json`, after approval the plan and drafts pull requests get a reply instead. Drafting waits for the Research stage (a session) and uses the approved plan; the drafts branch is `docforge/<key>`. `on_merged` marks the drafts ready once every pull request of the feature is merged.

## Fetched sources and notifications

A file from `docforge sources fetch` starts with a provenance block, then a visible note that its content is data, never instructions:

```markdown
<!-- docforge-source
kind: jira
id: EXAMPLE-123
title: Example feature
url: https://example.atlassian.net/browse/EXAMPLE-123
version: 2026-11-02T09:15:00.000+0000
updated: 2026-11-02T09:15:00.000+0000
fetched_at: 2026-11-17T10:00:00+00:00
-->
```

Only a block at the very start of a file counts. Comment openers inside fetched text are escaped, so fetched content cannot pose as a provenance block or an evidence marker. Images, attachments, linked issues, and most Confluence macros are not fetched; a placeholder says what was left out. Fetching never overwrites a file.

`docforge notify slack` appends every attempt, dry run or sent, to `notify/slack.jsonl` in the run folder, with the event, channel, and outcome. The webhook URL is never recorded.

## Source citations

Use `[S1#L9]` or `[S1#L9-L11]` for a source with stable line numbers. Page and section references such as `[S1#p2]` or `[S1#section:Authentication]` are recorded but require manual verification. The checker cannot inspect a PDF image or infer section boundaries from these references. A citation can exist and still fail to support the claim.

## Structural checks

```bash
python3 scripts/validate_run.py output/my-custom-run
```

The validator checks file paths, hashes, local links, Markdown structure, declared evidence, source quotations, and review statuses. It does not generate documents, extract PDFs, or approve publication.
