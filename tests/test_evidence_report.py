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

    def test_duplicate_consumed_aggregate_rows_are_refused(self):
        prefixes = ["Stored market-data rows", "A-share rows cleansing removed",
                    "A-share rows, cleansed", "Crypto rows, stored", "Sum of the two, stored rows",
                    "A-share rows removed by cleansing", "Reads |"]
        for prefix in prefixes:
            for contradict in [False, True]:
                with self.subTest(prefix=prefix, contradict=contradict):
                    self.path.write_bytes(self.original)
                    row = next(line for line in self.path.read_text().splitlines()
                               if line.startswith("| " + prefix))
                    duplicate = row
                    if contradict:
                        cells = row.split("|")
                        cells[2] = " contradictory value "
                        duplicate = "|".join(cells)
                    self.edit(row, row + "\n" + duplicate)
                    self.reject("inconsistent_arithmetic")

    def test_duplicate_consumed_aggregate_sections_are_refused(self):
        for heading in ["Headline numbers", "Scale", "Concurrency"]:
            with self.subTest(heading=heading):
                self.path.write_bytes(self.original)
                with self.path.open("a") as file:
                    file.write("\n## " + heading + "\n\n")
                self.reject("inconsistent_arithmetic")

    def test_later_tables_cannot_hide_duplicate_consumed_rows(self):
        cases = [("Raw counts", "A-share cleansed orders", "invalid_counts"),
                 ("Headline numbers", "Stored market-data rows", "inconsistent_arithmetic"),
                 ("Headline numbers", "A-share rows cleansing removed", "inconsistent_arithmetic"),
                 ("Scale", "A-share rows, cleansed", "inconsistent_arithmetic"),
                 ("Scale", "Crypto rows, stored", "inconsistent_arithmetic"),
                 ("Scale", "Sum of the two, stored rows", "inconsistent_arithmetic"),
                 ("Scale", "A-share rows removed by cleansing", "inconsistent_arithmetic"),
                 ("Concurrency", "Reads |", "inconsistent_arithmetic")]
        for heading, prefix, code in cases:
            for indent in ["", "   "]:
                with self.subTest(heading=heading, prefix=prefix, indent=indent):
                    self.path.write_bytes(self.original)
                    lines = self.path.read_text().splitlines()
                    start = lines.index("## " + heading)
                    stop = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
                    row = next(line for line in lines[start + 1:stop] if line.startswith("| " + prefix))
                    cells = row.split("|")
                    cells[2] = " contradictory value "
                    later = ["", "Additional observations:", "", indent + "| Measure | Value | Label | Source |",
                             indent + "|---|---|---|---|", indent + "|".join(cells), ""]
                    lines[stop:stop] = later
                    self.path.write_text("\n".join(lines) + "\n")
                    self.reject(code)

    def test_cleansing_removal_result_sources_must_match_contributing_counts(self):
        for prefix in ["A-share rows cleansing removed", "A-share rows removed by cleansing"]:
            for source in ["unknown", "table counts, 2026-10-06", ", 2026-10-05"]:
                with self.subTest(prefix=prefix, source=source):
                    self.path.write_bytes(self.original)
                    row = next(line for line in self.path.read_text().splitlines() if line.startswith("| " + prefix))
                    self.assertIn("table counts, 2026-10-05", row)
                    self.edit(row, row.replace("table counts, 2026-10-05", source))
                    self.reject("inconsistent_sources")

    def test_source_names_cannot_be_empty_with_valid_matching_dates(self):
        sources = ["table counts, 2026-10-05", "concurrency gate results, 2026-09-23"]
        for source in sources:
            for name in ["", " ", "\t"]:
                with self.subTest(source=source, name=name):
                    self.path.write_bytes(self.original)
                    text = self.path.read_text()
                    self.assertIn(source, text)
                    self.path.write_text(text.replace(source, name + ", " + source.rsplit(", ", 1)[1]))
                    self.reject("inconsistent_sources")

    def test_removal_auxiliary_references_require_named_valid_dates(self):
        references = ["table counts, 2026-10-03 (day ranges)",
                      "data platform design, 2026-09-28 (only exact duplicates are removed)"]
        for reference in references:
            for invalid in ["unknown", ", 2026-10-03", "table counts, 2026-99-03"]:
                with self.subTest(reference=reference, invalid=invalid):
                    self.path.write_bytes(self.original)
                    row = next(line for line in self.path.read_text().splitlines()
                               if line.startswith("| A-share rows removed by cleansing"))
                    self.assertIn(reference, row)
                    self.edit(row, row.replace(reference, invalid))
                    self.reject("inconsistent_sources")

    def test_code_headings_cannot_hide_later_duplicate_rows(self):
        cases = [("Raw counts", "A-share cleansed orders", "invalid_counts"),
                 ("Headline numbers", "Stored market-data rows", "inconsistent_arithmetic"),
                 ("Scale", "Sum of the two, stored rows", "inconsistent_arithmetic"),
                 ("Concurrency", "Reads |", "inconsistent_arithmetic")]
        code_lines = ["    ## note", "\t## note", "```text\n## note\n```",
                      "~~~text\n## note\n~~~", "````text\n## note\n`````",
                      "   ```text\n## note\n   ```"]
        for heading, prefix, code in cases:
            for example in code_lines:
                with self.subTest(heading=heading, example=example):
                    self.path.write_bytes(self.original)
                    lines = self.path.read_text().splitlines()
                    start = lines.index("## " + heading)
                    stop = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
                    row = next(line for line in lines[start + 1:stop] if line.startswith("| " + prefix))
                    cells = row.split("|")
                    cells[2] = " contradictory value "
                    lines[stop:stop] = ["", example, "", "| Measure | Value | Label | Source |",
                                        "|---|---|---|---|", "|".join(cells), ""]
                    self.path.write_text("\n".join(lines) + "\n")
                    self.reject(code)

    def test_code_examples_do_not_count_as_tables_or_sections(self):
        row = "| A-share cleansed orders | 1 | table counts, 2026-10-05 |"
        literal = "## Raw counts\n\n| Count | Value | Source |\n|---|---|---|\n" + row
        examples = ["\n".join("    " + line for line in literal.splitlines()),
                    "\n".join("\t" + line for line in literal.splitlines()),
                    "```text\n" + literal + "\n```", "~~~text\n" + literal + "\n~~~",
                    "````text\n" + literal + "\n`````", "   ```text\n" + literal + "\n   ```"]
        for example in examples:
            with self.subTest(example=example):
                self.path.write_bytes(self.original)
                with self.path.open("a") as file:
                    file.write("\n\n" + example + "\n")
                report = self.success()
                self.assertEqual(report["stored_rows"]["total"], 704009291430)
                self.assertEqual(report["provenance"]["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_removal_citations_require_each_role_exactly_once(self):
        reference = "table counts, 2026-10-05 (counts)"
        day_ranges = "table counts, 2026-10-03 (day ranges)"
        rule = "data platform design, 2026-09-28 (only exact duplicates are removed)"
        sources = ["table counts, 2026-10-05", reference, reference + "; " + day_ranges,
                   reference + "; " + rule, reference + "; " + day_ranges + "; " + day_ranges + "; " + rule,
                   reference + "; " + day_ranges + "; " + rule + "; " + rule,
                   reference + "; " + day_ranges + "; " + rule.replace("only exact duplicates are removed", "other rule")]
        for source in sources:
            with self.subTest(source=source):
                self.path.write_bytes(self.original)
                row = next(line for line in self.path.read_text().splitlines()
                           if line.startswith("| A-share rows removed by cleansing"))
                cells = row.split("|")
                cells[4] = " " + source + " "
                self.edit(row, "|".join(cells))
                self.reject("inconsistent_sources")

    def test_removal_reference_role_does_not_excuse_missing_name_or_date(self):
        for reference in ["table counts, 2026-10-03 (day ranges)",
                          "data platform design, 2026-09-28 (only exact duplicates are removed)"]:
            plain, role = reference.rsplit(" (", 1)
            for invalid in ["unknown", ", " + plain.rsplit(", ", 1)[1], "table counts, 2026-99-03"]:
                with self.subTest(reference=reference, invalid=invalid):
                    self.path.write_bytes(self.original)
                    row = next(line for line in self.path.read_text().splitlines()
                               if line.startswith("| A-share rows removed by cleansing"))
                    self.assertIn(reference, row)
                    self.edit(row, row.replace(reference, invalid + " (" + role))
                    self.reject("inconsistent_sources")

    def test_examples_inside_consumed_sections_cannot_override_arithmetic(self):
        for heading in ["Raw counts", "Headline numbers", "Scale", "Concurrency"]:
            literal = ("## " + heading + "\n\n| Count | Value | Source |\n|---|---|---|\n"
                       "| A-share cleansed orders | 1 | table counts, 2026-10-05 |")
            examples = ["\n".join("    " + line for line in literal.splitlines()),
                        "\n".join("\t" + line for line in literal.splitlines()),
                        "```text\n" + literal + "\n```", "~~~text\n" + literal + "\n~~~"]
            for example in examples:
                with self.subTest(heading=heading, example=example):
                    self.path.write_bytes(self.original)
                    self.edit("## " + heading + "\n", "## " + heading + "\n\n" + example + "\n")
                    report = self.success()
                    self.assertEqual(report["stored_rows"]["total"], 704009291430)
                    self.assertEqual(report["concurrency_reads"]["total"], 1111)
                    self.assertEqual(report["provenance"]["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_negated_or_obsolete_result_values_do_not_verify(self):
        prefixes = ["Stored market-data rows", "A-share rows cleansing removed",
                    "A-share rows, cleansed", "Crypto rows, stored", "Sum of the two, stored rows",
                    "A-share rows removed by cleansing", "Reads |"]
        for prefix in prefixes:
            for wording in ["not ", "obsolete "]:
                with self.subTest(prefix=prefix, wording=wording):
                    self.path.write_bytes(self.original)
                    row = next(line for line in self.path.read_text().splitlines()
                               if line.startswith("| " + prefix))
                    cells = row.split("|")
                    cells[2] = " " + wording + cells[2].strip() + " "
                    self.edit(row, "|".join(cells))
                    self.reject("inconsistent_arithmetic")

    def test_rounded_headline_components_cannot_be_negated(self):
        for value in ["565.9B", "138.1B"]:
            for wording in ["not ", "obsolete "]:
                with self.subTest(value=value, wording=wording):
                    self.path.write_bytes(self.original)
                    row = next(line for line in self.path.read_text().splitlines()
                               if line.startswith("| Stored market-data rows"))
                    self.assertIn(value, row)
                    self.edit(row, row.replace(value, wording + value))
                    self.reject("inconsistent_arithmetic")

    def test_threshold_prose_cannot_negate_or_obsolete_values(self):
        for value in ["2.9%", "39.1%"]:
            for wording in ["not ", "obsolete "]:
                with self.subTest(value=value, wording=wording):
                    self.path.write_bytes(self.original)
                    self.edit(value, wording + value)
                    self.reject("inconsistent_arithmetic")

    def test_supported_heading_spelling_keeps_report_values(self):
        for heading in ["Raw counts", "Headline numbers", "Scale", "Concurrency"]:
            for spelling in ["## " + heading + " ##", "   ## " + heading + " ####", "##\t" + heading + "\t##"]:
                with self.subTest(heading=heading, spelling=spelling):
                    self.path.write_bytes(self.original)
                    self.edit("## " + heading + "\n", spelling + "\n")
                    report = self.success()
                    self.assertEqual(report["stored_rows"]["total"], 704009291430)
                    self.assertEqual(report["concurrency_reads"]["total"], 1111)
                    self.assertEqual(report["provenance"]["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_container_fences_cannot_hide_contradictory_reads(self):
        for marker, close in [("- ", "  "), ("+ ", "  "), ("* ", "  "),
                              ("1. ", "   "), ("1) ", "   "), ("> - ", ">   ")]:
            with self.subTest(marker=marker):
                self.path.write_bytes(self.original)
                lines = self.path.read_text().splitlines()
                start = lines.index("## Concurrency")
                stop = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
                row = next(line for line in lines[start + 1:stop] if line.startswith("| Reads |"))
                cells = row.split("|")
                cells[2] = " contradictory value "
                lines[stop:stop] = ["", marker + "```text", close + "a literal example", close + "```", "",
                                    "| Measure | Result | Label | Source |", "|---|---|---|---|", "|".join(cells), ""]
                self.path.write_text("\n".join(lines) + "\n")
                self.reject("inconsistent_arithmetic")

    def test_marker_prefixed_fence_openers_have_a_named_format_refusal(self):
        for marker in ["- ", "+ ", "* ", "1. ", "1) ", "> ", ">- ", "- > "]:
            with self.subTest(marker=marker):
                self.path.write_bytes(self.original)
                with self.path.open("a") as file:
                    file.write("\n" + marker + "```text\n  an example\n  ```\n")
                self.reject("inconsistent_arithmetic")

    def test_literal_marker_fences_inside_supported_code_remain_opaque(self):
        for marker in ["- ", "1. ", "> ", ">- "]:
            with self.subTest(marker=marker):
                self.path.write_bytes(self.original)
                self.edit("## Raw counts\n", "## Raw counts\n\n````text\n" + marker + "```text\n"
                          "  ## Raw counts\n  ```\n````\n")
                report = self.success()
                self.assertEqual(report["stored_rows"]["total"], 704009291430)
                self.assertEqual(report["provenance"]["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_raw_markup_cannot_hide_later_evidence_rows(self):
        for opening, closing in [("<!--", "-->"), ("<pre>", "</pre>"), ("<div>", "</div>")]:
            with self.subTest(opening=opening):
                self.path.write_bytes(self.original)
                lines = self.path.read_text().splitlines()
                start = lines.index("## Concurrency")
                stop = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
                row = next(line for line in lines[start + 1:stop] if line.startswith("| Reads |"))
                cells = row.split("|")
                cells[2] = " contradictory value "
                lines[stop:stop] = ["", opening, "## note", closing, "",
                                    "| Measure | Result | Label | Source |", "|---|---|---|---|", "|".join(cells), ""]
                self.path.write_text("\n".join(lines) + "\n")
                self.reject("inconsistent_arithmetic")

    def test_literal_markup_in_supported_code_is_not_report_data(self):
        for fence in ["```", "~~~"]:
            with self.subTest(fence=fence):
                self.path.write_bytes(self.original)
                literal = fence + "text\n<pre>\n## Raw counts\n</pre>\n" + fence + "\n"
                self.edit("## Raw counts\n", "## Raw counts\n\n" + literal)
                report = self.success()
                self.assertEqual(report["stored_rows"]["total"], 704009291430)
                self.assertEqual(report["provenance"]["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_indented_consumed_tables_preserve_report_values(self):
        for heading in ["Raw counts", "Headline numbers", "Scale", "Concurrency"]:
            for width in [1, 2, 3]:
                with self.subTest(heading=heading, width=width):
                    self.path.write_bytes(self.original)
                    lines = self.path.read_text().splitlines()
                    start = lines.index("## " + heading)
                    stop = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
                    for index in range(start + 1, stop):
                        if lines[index].startswith("|"):
                            lines[index] = " " * width + lines[index]
                    self.path.write_text("\n".join(lines) + "\n")
                    report = self.success()
                    self.assertEqual(report["stored_rows"]["total"], 704009291430)
                    self.assertEqual(report["concurrency_reads"]["total"], 1111)
                    self.assertEqual(report["provenance"]["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_marker_prefixed_raw_markup_has_a_named_refusal(self):
        for marker in ["> ", ">", "- ", "+ ", "* ", "1. ", "1) ", ">- ", "- > "]:
            for markup in ["<!-- note -->", "<div></div>", "<?note?>"]:
                with self.subTest(marker=marker, markup=markup):
                    self.path.write_bytes(self.original)
                    with self.path.open("a") as file:
                        file.write("\n" + marker + markup + "\n")
                    self.reject("inconsistent_arithmetic")

    def test_literal_prefixed_markup_in_supported_code_remains_opaque(self):
        for marker in ["> ", "- ", "1. ", ">- "]:
            with self.subTest(marker=marker):
                self.path.write_bytes(self.original)
                literal = "```text\n" + marker + "<!-- note -->\n" + marker + "<div></div>\n```\n"
                self.edit("## Raw counts\n", "## Raw counts\n\n" + literal)
                report = self.success()
                self.assertEqual(report["stored_rows"]["total"], 704009291430)
                self.assertEqual(report["provenance"]["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

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

    def test_unavailable_temporary_storage_is_named(self):
        spec = importlib.util.spec_from_file_location("public_evidence_io_test", PROGRAM)
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(PROGRAM.parent))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        with patch.object(module.tempfile, "TemporaryDirectory", side_effect=OSError("storage unavailable")):
            with self.assertRaises(module.ReportError) as caught:
                module.report(self.path)
        self.assertEqual(caught.exception.code, "report_io_error")

    def test_failed_snapshot_write_cleans_up_and_preserves_input(self):
        spec = importlib.util.spec_from_file_location("public_evidence_cleanup_test", PROGRAM)
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(PROGRAM.parent))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        real_directory = module.tempfile.TemporaryDirectory
        created = []

        def track_directory(*args, **kwargs):
            directory = real_directory(*args, **kwargs)
            created.append(Path(directory.name))
            return directory

        with patch.object(module.tempfile, "TemporaryDirectory", side_effect=track_directory):
            with patch.object(module.Path, "write_bytes", side_effect=OSError("snapshot write failed")):
                with self.assertRaises(module.ReportError) as caught:
                    module.report(self.path)
        self.assertEqual(caught.exception.code, "report_io_error")
        self.assertTrue(created)
        self.assertTrue(all(not directory.exists() for directory in created))
        self.assertEqual(self.path.read_bytes(), self.original)


def load_tests(loader, tests, pattern):
    suite = loader.loadTestsFromTestCase(EvidenceReportTests)
    if suite.countTestCases() == 0:
        raise RuntimeError("Evidence report suite collected no cases")
    return suite


if __name__ == "__main__":
    unittest.main()
