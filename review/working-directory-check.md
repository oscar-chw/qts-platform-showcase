# Document check decision required

The unchanged document scan rejects the shell working-directory variable in the new local plan as a possible vendor or hardware name. The term is an ordinary shell variable, not operational hardware or access information. The links/fences, headline, arithmetic and number checks passed. No check source or gate has been changed.

Command: `FORBIDDEN_TERMS_FILE="$PWD/../_work/qts-forbidden.local.txt" python3 scripts/check_docs.py`
Result: exit 1; forbidden-terms check failed on the plan and its generated node record. Dependent full repository checks and independent acceptance are not run. The candidate is local and unpublished.

The prepared patch adds only the working-directory variable to the capitalized-word allowlist and adds a positive self-test control for it. All original rejection controls and private patterns remain. It is a proposal only and requires the human decision mandated by the repository's working rules.

Alternative: keep the strict scan and leave this local plan/document candidate held. Do not encode, rephrase, move or exclude the offending plan to evade the check.
