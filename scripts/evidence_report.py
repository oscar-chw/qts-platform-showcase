#!/usr/bin/env python3
"""Audit one captured public results document; never query the private platform."""

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

from figures import LINK, derive


DEFAULT = Path(__file__).resolve().parent.parent / "docs/results.md"
INPUT_LIMIT = 524288
MAX_COUNT = 9223372036854775807
ASHARE = ["A-share cleansed orders", "A-share cleansed trades", "A-share cleansed quotes"]
TYPED = "A-share typed layer, all three tables"
CRYPTO = ["Crypto trades, stored", "Crypto L3 order-book events, stored",
          "Crypto incremental L2 book updates, stored"]
READS = ["Concurrency gate, reads by the first reader kind", "Concurrency gate, reads by the second reader kind",
         "Concurrency gate, reads by the third reader kind"]
REQUIRED = ASHARE + [TYPED] + CRYPTO + READS
INTEGER = re.compile(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)")


class ReportError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def read_snapshot(path):
    try:
        with path.open("rb") as file:
            blob = file.read(INPUT_LIMIT + 1)
    except OSError as error:
        raise ReportError("input_read_error", "Cannot read results document: " + str(error.strerror)) from error
    if len(blob) > INPUT_LIMIT:
        raise ReportError("input_too_large", "Results document exceeds the 524288-byte input limit")
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ReportError("invalid_encoding", "Results document must be valid UTF-8 text") from error
    return blob, text


def section_rows(text, heading, code):
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == "## " + heading]
    if len(starts) != 1:
        raise ReportError(code, "Section must appear exactly once: " + heading)
    start = starts[0]
    stop = next((i for i in range(start + 1, len(lines)) if lines[i].strip().startswith("## ")), len(lines))
    rows = []
    for line in lines[start + 1:stop]:
        if not line.lstrip().startswith("|"):
            continue
        cells = [LINK.sub(r"\1", cell).replace("**", "").strip()
                 for cell in line.strip().strip("|").split("|")]
        if not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            rows.append(cells)
    return rows


def raw_counts(text):
    rows = section_rows(text, "Raw counts", "invalid_counts")
    if not rows or len(rows[0]) != 3 or rows[0][0] in REQUIRED:
        raise ReportError("invalid_counts", "Raw-count table needs a three-cell header")
    counts = {}
    for index, row in enumerate(rows[1:], 1):
        if len(row) != 3 or row[0] not in REQUIRED or row[0] in counts:
            raise ReportError("invalid_counts", "Missing, duplicate or unsupported raw count at row " + str(index))
        if not INTEGER.fullmatch(row[1]):
            raise ReportError("invalid_counts", "Raw count must be a nonnegative integer: " + row[0])
        digits = row[1].replace(",", "")
        if len(digits) > 19 or int(digits) > MAX_COUNT:
            raise ReportError("invalid_counts", "Raw count exceeds the supported integer range: " + row[0])
        parts = row[2].rsplit(", ", 1)
        try:
            if len(parts) != 2 or not parts[0].strip() or date.fromisoformat(parts[1]).isoformat() != parts[1]:
                raise ValueError("missing source name or date")
        except ValueError as error:
            raise ReportError("inconsistent_sources", "Raw source needs a name and valid date: " + row[0]) from error
        counts[row[0]] = {"count": int(digits), "source": row[2], "date": parts[1]}
    missing = [name for name in REQUIRED if name not in counts]
    if missing:
        raise ReportError("invalid_counts", "Required raw count missing: " + missing[0])
    return counts


def group_source(counts, names):
    references = {counts[name]["source"] for name in names}
    if len(references) != 1:
        raise ReportError("inconsistent_sources", "Counts in one result refer to different source snapshots")
    first = counts[names[0]]
    return first["source"], first["date"]


def result_table(text, heading):
    return section_rows(text, heading, "inconsistent_arithmetic")


def result_row(rows, name, prefix=False):
    matches = [row for row in rows if row and (row[0].startswith(name) if prefix else row[0] == name)]
    if len(matches) != 1 or len(matches[0]) != 4:
        raise ReportError("inconsistent_arithmetic", "Result row must appear once with four cells: " + name)
    return matches[0]


def removal_source(reference, expected):
    citations = [part.strip() for part in reference.split(";")]
    for citation in citations:
        plain = re.sub(r" \([^()]*\)$", "", citation)
        parts = plain.rsplit(", ", 1)
        try:
            if len(parts) != 2 or not parts[0].strip() or date.fromisoformat(parts[1]).isoformat() != parts[1]:
                raise ValueError("missing source name or date")
        except ValueError as error:
            raise ReportError("inconsistent_sources", "Removal references need named, valid dated sources") from error
    count_refs = [citation for citation in citations if citation.endswith(" (counts)")]
    if reference != expected and count_refs != [expected + " (counts)"]:
        raise ReportError("inconsistent_sources", "Removal count reference differs from its contributing counts")


def report(path):
    blob, text = read_snapshot(path)
    counts = raw_counts(text)
    stored_source, stored_date = group_source(counts, ASHARE + [TYPED] + CRYPTO)
    reads_source, reads_date = group_source(counts, READS)
    ashare = sum(counts[name]["count"] for name in ASHARE)
    crypto = sum(counts[name]["count"] for name in CRYPTO)
    if counts[TYPED]["count"] < ashare or counts[TYPED]["count"] == 0 or crypto == 0:
        raise ReportError("invalid_count_relationship", "Typed rows must cover cleansed rows; percentage denominators cannot be zero")
    headlines = result_table(text, "Headline numbers")
    stored = result_row(headlines, "Stored market-data rows", prefix=True)
    removed = result_row(headlines, "A-share rows cleansing removed", prefix=True)
    concurrency = result_table(text, "Concurrency")
    read_row = result_row(concurrency, "Reads")
    if stored[3] != stored_source or removed[3] != stored_source or read_row[3] != reads_source:
        raise ReportError("inconsistent_sources", "Result and raw counts refer to different source snapshots")
    scale = result_table(text, "Scale")
    for prefix in ["A-share rows, cleansed", "Crypto rows, stored", "Sum of the two, stored rows"]:
        row = result_row(scale, prefix, prefix=True)
        if row[3] != stored_source:
            raise ReportError("inconsistent_sources", "Scale result and raw counts refer to different source snapshots")
    scale_removed = result_row(scale, "A-share rows removed by cleansing", prefix=True)
    removal_source(scale_removed[3], stored_source)
    # Existing arithmetic code reads a path. Give it only our captured bytes so the digest and
    # computed statements cannot refer to two different reads of a mutable caller file.
    try:
        with tempfile.TemporaryDirectory(prefix="public-evidence-") as directory:
            snapshot = Path(directory) / "results.md"
            snapshot.write_bytes(blob)
            computed = derive(str(snapshot))
    except OSError as error:
        raise ReportError("report_io_error", "Temporary public snapshot storage is unavailable") from error
    bad = [statement for statement, _, agrees in computed if not agrees]
    if bad:
        raise ReportError("inconsistent_arithmetic", "Published arithmetic disagrees: " + bad[0])
    return {
        "schema": "qts-public-evidence/v1",
        "provenance": {"document": path.name, "sha256": hashlib.sha256(blob).hexdigest(),
                       "scope": "captured public aggregate document"},
        "stored_rows": {"ashare_cleansed": ashare, "crypto_stored": crypto, "total": ashare + crypto,
                        "source_ref": stored_source, "source_date": stored_date, "distinct_count": None},
        "concurrency_reads": {"total": sum(counts[name]["count"] for name in READS),
                              "source_ref": reads_source, "source_date": reads_date,
                              "scope": "dated small correctness fixture"},
        "arithmetic_verified": True,
        "source_data_verified": False,
        "operational_health_verified": False,
        "limits": ["Published arithmetic only; private source data were not queried or verified.",
                   "Stored rows do not establish a distinct-row count.",
                   "Cleansing-removal source-snapshot reconciliation remains open.",
                   "No new throughput, cold-query latency, uptime or backtest-library claim."],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT, help="Public results Markdown document")
    arguments = parser.parse_args(argv)
    try:
        result = report(arguments.results)
    except ReportError as error:
        print(json.dumps({"error": {"code": error.code, "document": arguments.results.name,
                                   "message": str(error)}}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
