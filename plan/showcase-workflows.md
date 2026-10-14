## goal: Make the public showcase useful for choosing data, reproducing a request and assessing evidence

Done-condition: FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash ../tools/check_repo.sh "$PWD"

- [x] 1. Document a researcher workflow, evidence boundaries and an executable public arithmetic example | ctx: docs/research-workflow.md | owner: codex-01a13a2e-4bb4-7f91-ad76-f1541c3b24c1 | gate: FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash ../tools/check_repo.sh "$PWD"
      2026-10-14T11:40:14Z released — Held at unchanged document-check false positive; human correction required; proposal un-applied.
      2026-10-14T12:01:36Z released — Held at preserved-patch checker-expression false positive; follow-up correction awaits coordinator decision.
      2026-10-14T12:10:23Z exit 0 in 2s [f0310ab2] — PASS  private-code / PASS  history / qts-platform-showcase: PASS (0 failed)

- [x] 2. Add a structured public evidence report with bounded input, provenance, refusal and recovery checks | needs: 1 | ctx: docs/evidence-report.md | owner: codex-01a13a2e-4bb4-7f91-ad76-f1541c3b24c1 | gate: FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash ../tools/check_repo.sh "$PWD"
      2026-10-14T13:39:39Z exit 0 in 4s [f0310ab2] — PASS  private-code / PASS  history / qts-platform-showcase: PASS (0 failed)

- [x] 3. Prepare the accepted public report for a review branch | needs: 2 | ctx: review/pr-finalization/preparation.md | owner: codex-01a13a2e-4bb4-7f91-ad76-f1541c3b24c1 | gate: FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash ../tools/check_repo.sh "$PWD"
      2026-10-14T18:17:14Z released — Held on exact public actor-field scan decision; no branch push or PR creation.
      2026-10-14T18:47:27Z released — Held on exact public identifier decision; actor-field scope implemented, full scan not passed.
      2026-10-14T19:01:28Z exit 0 in 5s [f0310ab2] — PASS  private-code / PASS  history / qts-platform-showcase: PASS (0 failed)
- [>] 4. Verify the open PR with CI and Codex review at its final revision | needs: 3,5,6,7 | ctx: review/pr-finalization/preparation.md | owner: codex-01a13a2e-4bb4-7f91-ad76-f1541c3b24c1 | lease: 2026-10-14T20:49:21Z | gate: python3 -c 'import json,re,subprocess; s=lambda a:json.loads(subprocess.check_output(a,text=True)); repo="oscar-chw/qts-platform-showcase"; branch="codex/qts-showcase-pr-20261015"; h=subprocess.check_output(["git","rev-parse",branch],text=True).strip(); p=s(["gh","pr","view",branch,"--repo",repo,"--json","headRefOid,baseRefName,state,number"]); assert p["headRefOid"]==h and p["baseRefName"]=="main" and p["state"].lower()=="open"; runs=s(["gh","api","repos/"+repo+"/actions/runs?head_sha="+h+"&event=pull_request"])["workflow_runs"]; latest=[next((r for r in runs if r["name"]==n),None) for n in ("check","lint")]; assert all(r and r["head_sha"]==h and r["status"]=="completed" and r["conclusion"]=="success" for r in latest); endpoint="repos/"+repo+"/pulls/"+str(p["number"]); reviews=s(["gh","api",endpoint+"/reviews"]); bot="chatgpt-codex-connector[bot]"; assert any(r["user"]["login"]==bot and r["commit_id"]==h and r["state"].lower() in ("commented","approved") for r in reviews); comments=s(["gh","api",endpoint+"/comments"]); assert not any(r["user"]["login"]==bot and r["commit_id"]==h and re.search(r"\[P[01]\]",r["body"]) for r in comments); print("PASS current PR revision, both CI workflows and completed Codex review")'
      2026-10-14T19:21:13Z released — Hosted review completed at ae8cc39 with two valid input-refusal findings; source repair and fresh review required.
      2026-10-14T20:05:36Z released — Second hosted review at0dc found later-table ambiguity and missing cleansing-removal reference binding; ordinary repair and fresh review required.
      2026-10-14T20:31:58Z released — Third hosted review at85f found code headings truncating section scans and missing required auxiliary citations; ordinary repair and fresh review required.

- [x] 5. Repair duplicate aggregate and missing source-name refusals from hosted review | needs: 3 | ctx: review/pr-finalization/finding-repair.md | owner: codex-01a13a2e-4bb4-7f91-ad76-f1541c3b24c1 | gate: FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash ../tools/check_repo.sh "$PWD"
      2026-10-14T19:42:12Z exit 0 in 7s [f0310ab2] — PASS  private-code / PASS  history / qts-platform-showcase: PASS (0 failed)

- [x] 6. Bind all section tables and cleansing-removal references from second review | needs: 5 | ctx: review/pr-finalization/second-repair.md | owner: codex-01a13a2e-4bb4-7f91-ad76-f1541c3b24c1 | gate: FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash ../tools/check_repo.sh "$PWD"
      2026-10-14T20:24:09Z exit 0 in 10s [f0310ab2] — PASS  private-code / PASS  history / qts-platform-showcase: PASS (0 failed)

- [x] 7. Respect Markdown code boundaries and require all removal citation roles | needs: 6 | ctx: review/pr-finalization/third-repair.md | owner: codex-01a13a2e-4bb4-7f91-ad76-f1541c3b24c1 | gate: FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" bash ../tools/check_repo.sh "$PWD"
      2026-10-14T20:47:44Z exit 0 in 10s [f0310ab2] — PASS  private-code / PASS  history / qts-platform-showcase: PASS (0 failed)

## Evidence-report scope

Directly requested follow-up on 14 October: the coordinator accepted the scoped documentation candidate9ce249e and asked for meaningful development with evaluation. Preserve that branch head. The next user is a reviewer or researcher who wants a machine-readable audit record of the public raw-count table. The report will carry a source digest and dated references, computed stored totals and fixture read counts, with explicit unverified-private-source and operational-status fields. It must reject missing/duplicate/malformed counts, conflicting source dates and contradictory arithmetic, handle missing/invalid/oversized files, and recover after correcting the input. Use the existing figures parser and arithmetic checks; no third-party package or private input. Add acceptance cases first, commit them separately, then implement a small read-only command-line tool. Existing document/privacy/self-test checks remain; the full check will additionally run the new report cases. No current count, private platform runtime, speed or new public claim is inferred.

existing: scripts/figures.py already parses the public tables and validates their computed statements; scripts/check.sh and current CI run the document checks and planted-defect controls. The source linked public importer is a separate release-held dependency, not needed for this report. The original input and new report must use one captured byte snapshot so the digest and checked numbers cannot refer to different reads.

## analysis

A reader can see the architecture but must infer which layer to choose, how to record a reproducible request and whether the historical numbers imply current service health. Done when the public workflow gives inputs, expected outputs, refusal/recovery behavior, dated coverage and a runnable arithmetic example, with all existing document, privacy, arithmetic and repository checks passing. Private implementation and current operations remain outside this repository.

## research

existing: the published README, data model, reliability and results pages; scripts/check_docs.py, scripts/figures.py and scripts/demo.sh; the separately owned public qts-platform-demo; work-loop, production-code and standards skills. The existing figure checker already performs the public computation needed for the example. No new package or executable tool is required. Private source snapshots are not reread. Current health and the reusable backtest library's detailed coverage are not established by this write-up; no such claim will be added.

## plan

Use the existing seven-section reading structure and checks. Add one workflow page, link it from the README and docs index, clarify historical labels without changing the checked tables or raw values, then run the existing checks. Save a local source/command/example handoff. Scope was directly authorized by Oscar through the dedicated repository dispatch on 14 October. Publication and independent acceptance stay with the coordinator.

## Review-branch finalization

15 October instruction: use a PR and CI; direct main push, merge, deployment and visibility changes await Oscar review. Preserve accepted9ce249e and e3028e0. Source reporting behavior is already independently accepted; reuse its pinned case, mutation and recovery evidence. Prepare a separate review branch with an up-to-date evidence index, then open a PR and request hosted Codex review once. Read both existing CI workflows and the submitted review against the branch revision. Missing, pending, failed or differently pinned evidence keeps node four pending. A Codex high-priority finding must be repaired on the review branch, checked and reviewed at the new revision. No existing checker, failed record or approved patch is removed or loosened.

existing: GitHub already has check and lint workflows; the accepted reporter and scoped coordinator review are reusable. The hosted review follows the documented mention workflow. No live platform input, new experiment, integration, service or paid extra usage is needed.
