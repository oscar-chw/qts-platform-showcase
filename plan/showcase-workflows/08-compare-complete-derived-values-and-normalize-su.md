# Node 8 — Compare complete derived values and normalize supported headings at the arithmetic seam

plan: showcase-workflows
gate: `FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash ../tools/check_repo.sh "$PWD"`
ctx: review/pr-finalization/fourth-repair.md

## Attempt 2026-10-14T21:11:24Z — local author — 12s — exit 1

```
FAIL  committed: uncommitted changes:
M docs/evidence-report.md
 M review/pr-finalization/current-status.md
 M review/pr-finalization/fourth-repair.md
 M review/pr-finalization/pr-body.md
 M scripts/evidence_report.py
?? plan/showcase-workflows/08-compare-complete-derived-values-and-normalize-su.md
?? review/pr-finalization/evaluate_fourth_repair.py
?? review/pr-finalization/fourth-checks.json
?? review/pr-finalization/fourth-execution.json
?? review/pr-finalization/fourth-mutations.json
  PASS  readme
  PASS  tidy
  PASS  attribution
  PASS  links
  PASS  check.sh
  PASS  ignored-source
  PASS  license
  PASS  decisions
  PASS  ci
  PASS  fresh-demo
  PASS  meta
  PASS  size
  PASS  todos
  PASS  private-code
  PASS  history
qts-platform-showcase: FAIL (1 failed)
```

## Attempt 2026-10-14T21:12:11Z — local author — 13s — exit 0

```
PASS  committed
  PASS  readme
  PASS  tidy
  PASS  attribution
  PASS  links
  PASS  check.sh
  PASS  ignored-source
  PASS  license
  PASS  decisions
  PASS  ci
  PASS  fresh-demo
  PASS  meta
  PASS  size
  PASS  todos
  PASS  private-code
  PASS  history
qts-platform-showcase: PASS (0 failed)
```
