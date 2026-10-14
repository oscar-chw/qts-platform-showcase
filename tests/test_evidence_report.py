"""Public evidence must bind one document and refuse contradictory records."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parent.parent
DOCUMENT = REPO / "docs/results.md"
PROGRAM = REPO / "scripts/evidence_report.py"


class EvidenceReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "results.md"
        self.original = DOCUMENT.read_bytes()
        self.path.write_bytes(self.original)

    def run_report(self, path=None):
        return subprocess.run([sys.executable, str(PROGRAM), "--results", str(path or self.path)],
                              capture_output=True, text=True, timeout=10, cwd=REPO)

    def success(self):
        run = self.run_report()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, "")
        return json.loads(run.stdout)

    def reject(self, code):
        run = self.run_report()
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout, "")
        result = json.loads(run.stderr)
        self.assertEqual(result["error"]["code"], code)
        self.assertEqual(result["error"]["document"], "results.md")
        self.assertTrue(result["error"]["message"])

    def edit(self, old, new):
        text = self.path.read_text()
        self.assertIn(old, text)
        self.path.write_text(text.replace(old, new, 1))

    def test_published_counts_and_digest_match_independent_sum(self):
        report = self.success()
        ashare = sum([293894477866, 228609088757, 43446124248])
        crypto = sum([137221906250, 698762007, 138932302])
        self.assertEqual(report["schema"], "qts-public-evidence/v1")
        self.assertEqual(report["stored_rows"]["ashare_cleansed"], ashare)
        self.assertEqual(report["stored_rows"]["crypto_stored"], crypto)
        self.assertEqual(report["stored_rows"]["total"], ashare + crypto)
        self.assertEqual(report["concurrency_reads"]["total"], sum([282, 410, 419]))
        self.assertEqual(report["provenance"]["sha256"], hashlib.sha256(self.original).hexdigest())
        self.assertEqual(report["provenance"]["document"], "results.md")
        self.assertEqual(report["stored_rows"]["source_date"], "2026-10-05")
        self.assertEqual(report["concurrency_reads"]["source_date"], "2026-09-23")
        self.assertIsNone(report["stored_rows"]["distinct_count"])
        self.assertFalse(report["source_data_verified"])
        self.assertFalse(report["operational_health_verified"])
        self.assertIn("source-snapshot reconciliation", " ".join(report["limits"]))

    def test_default_document_is_independent_of_working_directory(self):
        run = subprocess.run([sys.executable, str(PROGRAM)], capture_output=True,
                             text=True, timeout=10, cwd=self.temp.name)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["stored_rows"]["total"], 704009291430)

    def test_repeat_is_deterministic_and_does_not_change_input(self):
        first, second = self.run_report(), self.run_report()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_content_digest_changes_on_editorial_change(self):
        first = self.success()
        with self.path.open("a") as file:
            file.write("\nPublic editorial note.\n")
        second = self.success()
        self.assertEqual(first["stored_rows"], second["stored_rows"])
        self.assertNotEqual(first["provenance"]["sha256"], second["provenance"]["sha256"])

    def test_inconsistent_computed_sum_is_refused(self):
        self.edit("704,009,291,430", "704,009,291,431")
        self.reject("inconsistent_arithmetic")

    def test_changed_raw_count_without_changed_total_is_refused(self):
        self.edit("| 43,446,124,248 |", "| 43,446,124,249 |")
        self.reject("inconsistent_arithmetic")

    def test_missing_raw_section_is_refused(self):
        self.edit("## Raw counts", "## Other counts")
        self.reject("invalid_counts")

    def test_missing_required_row_is_refused(self):
        self.edit("A-share cleansed orders", "Other observations")
        self.reject("invalid_counts")

    def test_duplicate_raw_row_is_refused(self):
        row = "| A-share cleansed orders | 293,894,477,866 | table counts, 2026-10-05 |"
        self.edit(row, row + "\n" + row)
        self.reject("invalid_counts")

    def test_duplicate_raw_section_is_refused(self):
        with self.path.open("a") as file:
            file.write("\n## Raw counts\n\n| Count | Value | Source |\n|---|---|---|\n"
                       "| A-share cleansed orders | 1 | table counts, 2026-10-05 |\n")
        self.reject("invalid_counts")

    def test_non_integer_negative_or_bad_grouping_is_refused(self):
        for value in ["not-a-count", "-1", "1.5", "29,38"]:
            with self.subTest(value=value):
                self.path.write_bytes(self.original)
                self.edit("| 293,894,477,866 |", "| " + value + " |")
                self.reject("invalid_counts")

    def test_source_dates_cannot_mix_snapshots(self):
        row = "| A-share cleansed orders | 293,894,477,866 | table counts, 2026-10-05 |"
        self.edit(row, row.replace("2026-10-05", "2026-10-06"))
        self.reject("inconsistent_sources")

    def test_headline_date_must_match_raw_counts(self):
        headline = "| 700B+ | Live | table counts, 2026-10-05 |"
        self.edit(headline, headline.replace("2026-10-05", "2026-10-06"))
        self.reject("inconsistent_sources")

    def test_scale_result_date_must_match_raw_counts(self):
        row = next(line for line in self.path.read_text().splitlines()
                   if line.startswith("| Sum of the two, stored rows |"))
        self.edit(row, row.replace("2026-10-05", "2026-10-06"))
        self.reject("inconsistent_sources")

    def test_digest_and_arithmetic_use_captured_bytes_if_caller_file_changes(self):
        spec = importlib.util.spec_from_file_location("public_evidence_under_test", PROGRAM)
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(PROGRAM.parent))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        original_derive = module.derive

        def change_caller_after_capture(snapshot):
            self.path.write_bytes(self.original.replace(b"| 43,446,124,248 |", b"| 43,446,124,249 |", 1))
            return original_derive(snapshot)

        with patch.object(module, "derive", side_effect=change_caller_after_capture):
            result = module.report(self.path)
        self.assertEqual(result["provenance"]["sha256"], hashlib.sha256(self.original).hexdigest())
        self.assertEqual(result["stored_rows"]["total"], 704009291430)
        self.assertNotEqual(self.path.read_bytes(), self.original)

    def test_invalid_source_date_is_refused(self):
        row = "| A-share cleansed orders | 293,894,477,866 | table counts, 2026-10-05 |"
        self.edit(row, row.replace("2026-10-05", "2026-99-05"))
        self.reject("inconsistent_sources")

    def test_typed_count_cannot_be_smaller_than_cleansed(self):
        self.edit("| 566,464,087,478 |", "| 1 |")
        self.reject("invalid_count_relationship")

    def test_zero_crypto_denominator_is_refused(self):
        for value in ["137,221,906,250", "698,762,007", "138,932,302"]:
            self.edit("| " + value + " |", "| 0 |")
        self.reject("invalid_count_relationship")

    def test_zero_typed_denominator_is_refused(self):
        for value in ["293,894,477,866", "228,609,088,757", "43,446,124,248", "566,464,087,478"]:
            self.edit("| " + value + " |", "| 0 |")
        self.reject("invalid_count_relationship")

    def test_counts_above_supported_integer_range_are_refused(self):
        for value in ["9" * 40, "9223372036854775808"]:
            with self.subTest(value=value):
                self.path.write_bytes(self.original)
                self.edit("| 293,894,477,866 |", "| " + value + " |")
                self.reject("invalid_counts")

    def test_missing_source_file_is_named(self):
        missing = Path(self.temp.name) / "missing.md"
        run = self.run_report(missing)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout, "")
        error = json.loads(run.stderr)["error"]
        self.assertEqual(error["code"], "input_read_error")
        self.assertEqual(error["document"], "missing.md")

    def test_invalid_encoding_is_refused(self):
        self.path.write_bytes(b"\xff\xfe")
        self.reject("invalid_encoding")

    def test_empty_input_is_refused(self):
        self.path.write_bytes(b"")
        self.reject("invalid_counts")

    def test_input_limit_is_enforced_before_parsing(self):
        self.path.write_bytes(b"x" * 524289)
        self.reject("input_too_large")

    def test_correcting_input_recovers_without_state(self):
        self.edit("| 43,446,124,248 |", "| 43,446,124,249 |")
        self.reject("inconsistent_arithmetic")
        self.path.write_bytes(self.original)
        report = self.success()
        self.assertEqual(report["stored_rows"]["total"], 704009291430)


def load_tests(loader, tests, pattern):
    suite = loader.loadTestsFromTestCase(EvidenceReportTests)
    if suite.countTestCases() == 0:
        raise RuntimeError("Evidence report suite collected no cases")
    return suite


if __name__ == "__main__":
    unittest.main()
