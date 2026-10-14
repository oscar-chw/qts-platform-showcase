# Node 4 — Verify the open PR with CI and Codex review at its final revision

plan: showcase-workflows
gate: `python3 -c 'import json,re,subprocess; s=lambda a:json.loads(subprocess.check_output(a,text=True)); repo="oscar-chw/qts-platform-showcase"; branch="codex/qts-showcase-pr-20261015"; h=subprocess.check_output(["git","rev-parse",branch],text=True).strip(); p=s(["gh","pr","view",branch,"--repo",repo,"--json","headRefOid,baseRefName,state,number"]); assert p["headRefOid"]==h and p["baseRefName"]=="main" and p["state"].lower()=="open"; runs=s(["gh","api","repos/"+repo+"/actions/runs?head_sha="+h+"&event=pull_request"])["workflow_runs"]; latest=[next((r for r in runs if r["name"]==n),None) for n in ("check","lint")]; assert all(r and r["head_sha"]==h and r["status"]=="completed" and r["conclusion"]=="success" for r in latest); endpoint="repos/"+repo+"/pulls/"+str(p["number"]); reviews=s(["gh","api",endpoint+"/reviews"]); bot="chatgpt-codex-connector[bot]"; assert any(r["user"]["login"]==bot and r["commit_id"]==h and r["state"].lower() in ("commented","approved") for r in reviews); comments=s(["gh","api",endpoint+"/comments"]); assert not any(r["user"]["login"]==bot and r["commit_id"]==h and re.search(r"\[P[01]\]",r["body"]) for r in comments); print("PASS current PR revision, both CI workflows and completed Codex review")'`
ctx: review/pr-finalization/preparation.md

## Released 2026-10-14T19:21:13Z — local author

Hosted review completed at ae8cc39 with two valid input-refusal findings; source repair and fresh review required.

## Released 2026-10-14T20:05:36Z — local author

Second hosted review at0dc found later-table ambiguity and missing cleansing-removal reference binding; ordinary repair and fresh review required.

## Released 2026-10-14T20:31:58Z — local author

Third hosted review at85f found code headings truncating section scans and missing required auxiliary citations; ordinary repair and fresh review required.

## Released 2026-10-14T20:58:36Z — local author

Fourth review atbbbf found negated expected figures accepted and supported headings rejected by the arithmetic reader; ordinary repair required.

## Released 2026-10-14T21:30:17Z — local author

Fifth review at843 found marker-prefixed fence openers hiding later evidence rows; fail-closed format repair required.

## Released 2026-10-14T22:08:31Z — local author

Sixth review at3f4 found accepted table indentation rejected and marker-prefixed markup bypassing the format guard; ordinary repair required.
