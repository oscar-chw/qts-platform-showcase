"""Probe normalized pipe rows and shared markup-prefix refusal with unchanged cases."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
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
    mutations = [(*mutation, 1) for mutation in previous.MUTATIONS]
    mutations[-1] = (
        "ignore_result_source",
        "if stored[3] != stored_source or removed[3] != stored_source or read_row[3] != reads_source:",
        "if False and (stored[3] != stored_source or removed[3] != stored_source or read_row[3] != reads_source):",
        "test_headline_date_must_match_raw_counts", 1,
    )
    validity = ('parts = plain.rsplit(", ", 1)\n        try:\n'
                '            if len(parts) != 2 or not parts[0].strip() or date.fromisoformat(parts[1]).isoformat() != parts[1]:')
    mutations += [
        ("accept_duplicate_result_rows", "if len(matches) != 1 or len(matches[0]) != 4:",
         "if not matches or len(matches[0]) != 4:", "test_duplicate_consumed_aggregate_rows_are_refused", 1),
        ("accept_duplicate_result_sections", "if len(starts) != 1:", "if len(starts) < 1:",
         "test_duplicate_consumed_aggregate_sections_are_refused", 1),
        ("accept_missing_source_name", " or not parts[0].strip()", "",
         "test_source_names_cannot_be_empty_with_valid_matching_dates", 2),
        ("stop_after_first_table", "    for line in lines[start + 1:stop]:\n",
         "    for line in lines[start + 1:stop]:\n        if rows and not line.lstrip().startswith(\"|\"):\n            break\n",
         "test_later_tables_cannot_hide_duplicate_consumed_rows", 1),
        ("ignore_headline_removal_source", " or removed[3] != stored_source", "",
         "test_cleansing_removal_result_sources_must_match_contributing_counts", 1),
        ("ignore_scale_removal_source", "    removal_source(scale_removed[3], stored_source)",
         "    pass", "test_cleansing_removal_result_sources_must_match_contributing_counts", 1),
        ("ignore_auxiliary_source_validity", validity,
         validity.replace('if len(parts) != 2 or not parts[0].strip() or date.fromisoformat(parts[1]).isoformat() != parts[1]:',
                          'if False and (len(parts) != 2 or not parts[0].strip() or date.fromisoformat(parts[1]).isoformat() != parts[1]):'),
         "test_removal_reference_role_does_not_excuse_missing_name_or_date", 1),
        ("ignore_fenced_code", 'if opening and not (opening[1][0] == "`" and "`" in opening[2]):',
         'if False and opening and not (opening[1][0] == "`" and "`" in opening[2]):',
         "test_code_headings_cannot_hide_later_duplicate_rows", 1),
        ("ignore_indented_code", 'if len(re.match(r"[ \\t]*", line)[0].expandtabs(4)) >= 4:',
         'if False and len(re.match(r"[ \\t]*", line)[0].expandtabs(4)) >= 4:',
         "test_examples_inside_consumed_sections_cannot_override_arithmetic", 1),
        ("allow_missing_removal_roles", 'if set(references) != roles or references.get("counts") != expected:',
         'if references.get("counts") != expected:', "test_removal_citations_require_each_role_exactly_once", 1),
        ("allow_repeated_removal_roles", " or match[2] in references", "",
         "test_removal_citations_require_each_role_exactly_once", 1),
        ("arithmetic_reads_literal_code", 'snapshot.write_bytes("\\n".join(markdown_lines(text)).encode("utf-8"))',
         "snapshot.write_bytes(blob)", "test_examples_inside_consumed_sections_cannot_override_arithmetic", 1),
    ]
    mutations += [
        ("mention_instead_of_complete_value", "actual != value for actual, value in expected",
         "value not in actual for actual, value in expected", "test_negated_or_obsolete_result_values_do_not_verify", 1),
        ("ignore_rounded_measure", '        (stored[0], f"Stored market-data rows: A-share cleansed ({ashare / 1e9:.1f}B) plus crypto stored ({crypto / 1e9:.1f}B)"),\n',
         "", "test_rounded_headline_components_cannot_be_negated", 1),
        ("ignore_threshold_wording", ' or " ".join(paragraphs[0].split()) != why', "",
         "test_threshold_prose_cannot_negate_or_obsolete_values", 1),
        ("skip_heading_normalization", "if heading:", "if False and heading:",
         "test_supported_heading_spelling_keeps_report_values", 1),
    ]
    mutations += [
        ("accept_marker_prefixed_fences", 'if prefixed and not (prefixed[1][0] == "`" and "`" in prefixed[2]):',
         'if False and prefixed and not (prefixed[1][0] == "`" and "`" in prefixed[2]):',
         "test_container_fences_cannot_hide_contradictory_reads", 1),
        ("accept_raw_markup_blocks", r'if re.match(MARKER_PREFIX + r"* {0,3}<(?:!--|[!?]|/?[A-Za-z][A-Za-z0-9-]*(?:[ \t/>]|$))", line):',
         r'if False and re.match(MARKER_PREFIX + r"* {0,3}<(?:!--|[!?]|/?[A-Za-z][A-Za-z0-9-]*(?:[ \t/>]|$))", line):',
         "test_raw_markup_cannot_hide_later_evidence_rows", 1),
    ]
    mutations += [
        ("skip_pipe_row_normalization", 'if line.lstrip().startswith("|"):',
         'if False and line.lstrip().startswith("|"):', "test_indented_consumed_tables_preserve_report_values", 1),
        ("skip_markup_marker_prefix", 'MARKER_PREFIX + r"* {0,3}<', 'r" {0,3}<',
         "test_marker_prefixed_raw_markup_has_a_named_refusal", 1),
    ]
    source = (REPO / SOURCE).read_text()
    tests_hash = hashlib.sha256((REPO / TESTS).read_bytes()).hexdigest()
    results = []
    with tempfile.TemporaryDirectory(prefix="report-sixth-repair-") as directory:
        for label, old, new, witness, occurrences in [("control", None, None, None, 0)] + mutations:
            tree = Path(directory) / label
            shutil.copytree(REPO, tree, ignore=shutil.ignore_patterns(".git", "__pycache__", ".ruff_cache"))
            altered = source
            if old is not None:
                assert source.count(old) == occurrences, label
                altered = source.replace(old, new)
                if label == "ignore_arithmetic":
                    call = "    arithmetic_values(text, counts, stored, removed, scale, read_row)"
                    assert altered.count(call) == 1
                    altered = altered.replace(call, "    pass", 1)
                (tree / SOURCE).write_text(altered)
            assert hashlib.sha256((tree / TESTS).read_bytes()).hexdigest() == tests_hash
            command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_evidence_report.py"]
            if witness is not None:
                command += ["-k", witness]
            run = subprocess.run(command, cwd=tree, capture_output=True, text=True, timeout=20)
            count = re.search(r"Ran (\d+) tests?", run.stderr)
            assert count and int(count[1]) == (50 if witness is None else 1), (label, run.stderr)
            caught = run.returncode == 1 and ("FAIL: " + str(witness) in run.stderr or
                                            "ERROR: " + str(witness) in run.stderr)
            assert run.returncode == 0 if witness is None else caught, (label, run.returncode, run.stderr)
            results.append({"case": label, "exit_code": run.returncode, "witness": witness,
                            "expected_outcome": "pass" if witness is None else "caught",
                            "test_source_unchanged": True, "case_count": int(count[1]),
                            "mutation_sites": 2 if label == "ignore_arithmetic" else occurrences,
                            "implementation_sha256": hashlib.sha256(altered.encode()).hexdigest()})
    assert (REPO / SOURCE).read_text() == source
    result = {"source_sha256": hashlib.sha256(source.encode()).hexdigest(), "tests_sha256": tests_hash,
              "python_version": sys.version.split()[0], "cases": results,
              "scope": "twenty-four earlier defect classes plus two pipe-row/markup-prefix defects; full same-run control and one unchanged causal test per defect; arithmetic bypass changes both validating sites"}
    (REPO / "review/pr-finalization/sixth-mutations.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"control": "pass", "mutants_caught": len(mutations), "acceptance_unchanged": True}))


if __name__ == "__main__":
    main()
