# Public-evidence report: local handoff

Implementation: `032329842bad90611b14a83158c7b2dcd21c3a1a`, branch `codex/qts-evidence-report-20261014`.
Accepted documentation baseline `9ce249e8f7d592f85f8f9d3c30dcd32be3767c39` is preserved on its own branch.

## Useful behavior

A reviewer or notebook can obtain stable structured public counts, dated source references and a digest without parsing terminal prose. The command captures a bounded input once, validates required counts and matching sources, and reuses the existing arithmetic on that captured copy. Invalid input emits a named error on standard error with no successful report on standard output. Correcting the input recovers without state reset.

```bash
python3 scripts/evidence_report.py
python3 scripts/evidence_report.py --results edited-results.md
```

The runnable normal/failure/recovery example is in [the guide](../../docs/evidence-report.md#input-and-failure-contract). Its recorded statuses are zero, one and zero; the recovered report equals the initial report. [Fresh-clone evidence](fresh-clone.json) also runs the actual command and this example with site packages disabled.

## Local verification

| Command or instrument | Observed result |
|---|---|
| `python3 -m unittest discover -s tests -p test_evidence_report.py` | 27 cases pass on Python 3.9.6. |
| `../_venvs/ctp/bin/python -m unittest discover -s tests -p test_evidence_report.py` | 27 cases pass on Python 3.11. |
| `python3 review/evidence-report/evaluate_mutations.py` | Same-run control passes; six isolated defects are caught without changing acceptance cases. |
| `FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash scripts/check.sh` | Original checks, original planted-defect controls, demo and added report suite pass. |
| `../_venvs/ctp/bin/python -m ruff check --config ruff.toml .` | Pass. |
| Existing node-two full repository gate | All sixteen checks pass; plan tool records exit zero. |

[Verification pins](verification.json), [local commands](local-checks.json), [mutations](mutations.json), [recovery](recovery.json), [original-check preservation](preserved-checks.json) and [review status](review-status.json) are separate receipts. Red-before-implementation and subsequent numeric, duplicate-section, scale-source and temporary-storage reproductions remain in this directory and separate commits. No acceptance assertion was weakened. Commit author identity matches the configured Oscar address.

## Contribution and limits

The engineering lesson is to bind an evidence digest and checked statements to the same captured bytes. A deterministic caller-file-change test catches a second-read mismatch. Independent integer sums, source-date disagreement, malformed input, numeric limits, temporary-storage failure and cleanup checks protect the reporting contract. This is useful public-document tooling, with an explicit boundary around the private implementation.

The report computes 704009291430 stored rows and 1111 dated fixture reads from existing published aggregates. It does not re-query private records, establish unique rows or today's operational health. Those verification flags remain false; the existing cleansing-removal reconciliation remains open. No new performance, trading or library-integration claim follows.

Independent coordinator source review and acceptance are pending. The candidate routing evaluation did not permit dispatch, so no extra reviewer was launched through it. Local source review and author checks are not independent acceptance. Remote checks have not run; nothing was pushed or published. The inherited figure reader emits a resource warning under direct warning-enabled tests; it remains recorded, not suppressed or edited.
