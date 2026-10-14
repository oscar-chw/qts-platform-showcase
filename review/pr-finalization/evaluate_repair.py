"""Probe report defects in isolated copies, using the same unmodified acceptance suite."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[2]
SOURCE = Path("scripts/evidence_report.py")
TESTS = Path("tests/test_evidence_report.py")


def main():
    spec = importlib.util.spec_from_file_location("previous_report_eval", REPO / "review/evidence-report/evaluate_mutations.py")
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    mutations = previous.MUTATIONS + [
        ("accept_duplicate_result_rows", "if len(matches) != 1 or len(matches[0]) != 4:",
         "if not matches or len(matches[0]) != 4:", "test_duplicate_consumed_aggregate_rows_are_refused"),
        ("accept_duplicate_result_sections",
         'if sum(line.strip() == "## " + heading for line in text.splitlines()) != 1:',
         'if sum(line.strip() == "## " + heading for line in text.splitlines()) < 1:',
         "test_duplicate_consumed_aggregate_sections_are_refused"),
        ("accept_missing_source_name", " or not parts[0].strip()", "",
         "test_source_names_cannot_be_empty_with_valid_matching_dates"),
    ]
    source = (REPO / SOURCE).read_text()
    tests_hash = hashlib.sha256((REPO / TESTS).read_bytes()).hexdigest()
    results = []
    with tempfile.TemporaryDirectory(prefix="report-repair-eval-") as directory:
        for label, old, new, witness in [("control", None, None, None)] + mutations:
            tree = Path(directory) / label
            shutil.copytree(REPO, tree, ignore=shutil.ignore_patterns(".git", "__pycache__", ".ruff_cache"))
            altered = source
            if old is not None:
                assert source.count(old) == 1, label
                altered = source.replace(old, new, 1)
                (tree / SOURCE).write_text(altered)
            assert hashlib.sha256((tree / TESTS).read_bytes()).hexdigest() == tests_hash
            run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                                  "-p", "test_evidence_report.py"], cwd=tree,
                                 capture_output=True, text=True, timeout=20)
            caught = run.returncode == 1 and ("FAIL: " + str(witness) in run.stderr or
                                            "ERROR: " + str(witness) in run.stderr)
            assert run.returncode == 0 if witness is None else caught, (label, run.returncode, run.stderr)
            results.append({"case": label, "exit_code": run.returncode, "witness": witness,
                            "expected_outcome": "pass" if witness is None else "caught",
                            "test_source_unchanged": True,
                            "implementation_sha256": hashlib.sha256(altered.encode()).hexdigest()})
    assert (REPO / SOURCE).read_text() == source
    result = {"source_sha256": hashlib.sha256(source.encode()).hexdigest(), "tests_sha256": tests_hash,
              "python_version": sys.version.split()[0], "cases": results,
              "scope": "six preserved defects plus three hosted-review regression defects; same-run control"}
    (REPO / "review/pr-finalization/repaired-mutations.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"control": "pass", "mutants_caught": len(mutations), "acceptance_unchanged": True}))


if __name__ == "__main__":
    main()
