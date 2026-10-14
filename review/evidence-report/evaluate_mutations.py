"""Evaluate isolated implementation defects; never change the acceptance cases."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[2]
SOURCE = Path("scripts/evidence_report.py")
TESTS = Path("tests/test_evidence_report.py")
MUTATIONS = [
    ("drop_crypto", '"total": ashare + crypto', '"total": ashare',
     "test_published_counts_and_digest_match_independent_sum"),
    ("constant_digest", "hashlib.sha256(blob).hexdigest()", '"0" * 64',
     "test_content_digest_changes_on_editorial_change"),
    ("claim_private_verified", '"source_data_verified": False', '"source_data_verified": True',
     "test_published_counts_and_digest_match_independent_sum"),
    ("reread_caller", "computed = derive(str(snapshot))", "computed = derive(str(path))",
     "test_digest_and_arithmetic_use_captured_bytes_if_caller_file_changes"),
    ("ignore_arithmetic", "if bad:", "if False and bad:",
     "test_inconsistent_computed_sum_is_refused"),
    ("ignore_result_source", "if stored[3] != stored_source or read_row[3] != reads_source:",
     "if False and (stored[3] != stored_source or read_row[3] != reads_source):",
     "test_headline_date_must_match_raw_counts"),
]


def main():
    source = (REPO / SOURCE).read_text()
    tests_hash = hashlib.sha256((REPO / TESTS).read_bytes()).hexdigest()
    results = []
    with tempfile.TemporaryDirectory(prefix="evidence-mutations-") as directory:
        for label, old, new, witness in [("control", None, None, None)] + MUTATIONS:
            tree = Path(directory) / label
            shutil.copytree(REPO, tree, ignore=shutil.ignore_patterns(".git", "__pycache__", ".ruff_cache"))
            altered = source
            if old is not None:
                assert source.count(old) == 1, label
                altered = source.replace(old, new, 1)
                (tree / SOURCE).write_text(altered)
            assert hashlib.sha256((tree / TESTS).read_bytes()).hexdigest() == tests_hash
            command = [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                       "-p", "test_evidence_report.py"]
            run = subprocess.run(command, cwd=tree, capture_output=True, text=True, timeout=20)
            caught = run.returncode == 1 and ("FAIL: " + str(witness) in run.stderr or
                                            "ERROR: " + str(witness) in run.stderr)
            assert run.returncode == 0 if witness is None else caught, (label, run.returncode, run.stderr)
            results.append({"case": label, "exit_code": run.returncode, "witness": witness,
                            "expected_outcome": "pass" if witness is None else "caught",
                            "test_source_unchanged": True,
                            "implementation_sha256": hashlib.sha256(altered.encode()).hexdigest()})
    assert (REPO / SOURCE).read_text() == source
    out = {"source_sha256": hashlib.sha256(source.encode()).hexdigest(), "tests_sha256": tests_hash,
           "python_version": sys.version.split()[0], "cases": results,
           "scope": "six isolated report defects and same-run unmodified control; acceptance cases unchanged"}
    (REPO / "review/evidence-report/mutations.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"control": "pass", "mutants_caught": len(MUTATIONS), "acceptance_unchanged": True}))


if __name__ == "__main__":
    main()
