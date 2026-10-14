# PR preparation and evidence scope

Current local technical acceptance covers the frozen report candidate `e3028e0c4f94c664b560b98c99f29869479ee83a`, implementation `032329842bad90611b14a83158c7b2dcd21c3a1a`. The previous `9ce249e` documentation candidate remains preserved. [Acceptance pins](accepted-source.json) bind the scoped coordinator review to all thirteen source/evidence files. Earlier handoffs retain the status they had when frozen.

The public report returns exact integer totals, dated source references and a digest of one bounded captured input. It rejects malformed or contradictory inputs and recovers after correction. [Report guide](../../docs/evidence-report.md) contains the runnable normal/failure/recovery example; [case/mutation/recovery evidence](../evidence-report/handoff.md) describes its controls. No new code behavior or private measurement is part of this preparation.

The coordinator independently read the program, twenty-seven-case suite, arithmetic dependency and additive check/license deltas, then ran the original full script with the configured private pattern list. Actual report normal/wrong-total/corrected statuses were zero, one and zero; the corrected result was identical. All thirteen pins stayed unchanged. The separate author full sixteen-check repository audit remains author evidence.

The two public identifier corrections were explicitly approved and applied before the accepted documentation candidate. The exact [working-directory patch](../working-directory-proposal.patch), [checker-expression patch](../checker-expression-proposal.patch), original failures and twenty original rejection controls remain. No additional checker correction is proposed here.

New release condition: use a review branch and PR with both existing CI workflows successful and a completed hosted Codex review bound to its final revision. Missing or unfinished remote evidence stays unverified. Resolve consequential review findings through a source fix and a new checked revision. Keep main merge, deployment and any further release action for Oscar review.

The report verifies consistency of public aggregate statements only. Private records and today's service state were not checked; distinct rows remain unknown and the existing cleansing-removal reconciliation remains open. The inherited figure reader's resource warning is retained. [Results and dated scope](../../docs/results.md) remain the evidence source; no new performance or trading claim follows.
