# From a research question to a reproducible data request

Use this guide when you need to inspect a trading day, compare cleansing rules or reproduce the
inputs to a study. It connects the [data model](data-model.md) to a researcher's choices. The call
shapes in that page use invented names; the private platform is not installed by cloning this
repository. Public computation available here is the evidence example below. The separately
owned [qts-platform-demo](https://github.com/oscar-chw/qts-platform-demo) runs the data concepts on
explicit synthetic inputs.

## Choose the task and its evidence

| You need to… | Read or run | What you can establish |
|---|---|---|
| Understand why a row changed | [Three layers](data-model.md#three-layers) and the correction/flag policy | The design retains supplier values and separates typing from cleansing. A local documentation check does not inspect the private rows. |
| Repeat a data request later | [Pinned datasets](data-model.md#versioned-pinned-datasets) and the request record below | Which version and request rules must stay fixed; the dated concurrency fixture is evidence for its tested scope. |
| Prevent a fill from using later observations | [Gap handling](data-model.md#one-interface-wherever-a-researcher-works) | Which policy to choose and when a request should be refused. Pinning a version alone does not make a transformation causal. |
| Verify the public scale arithmetic | `bash scripts/demo.sh` | The published raw counts agree with the page's derived figures. This does not re-query the private dataset. |
| Save a machine-readable audit record | [Evidence report](evidence-report.md) | Computed public counts with dated sources, a document digest and explicit unverified-private-source/current-health flags. |
| Exercise versioning and failure behavior | [Public demo](https://github.com/oscar-chw/qts-platform-demo#quick-start) | Independently written code on a small synthetic delivery; private scale and timings do not transfer to it. |

## Record the request before using its results

The following is an **ILLUSTRATIVE** research record, not an executable interface or a real dataset
identifier. Replace invented values in an authorized environment. Keep the record with the study
so that “the same data” has an explicit meaning.

```json
{
  "table": "equities.trades",
  "layer": "cleansed",
  "instruments": ["SYM_A"],
  "date_from": "2024-03-01",
  "date_to": "2024-03-01",
  "snapshot": "held-study-version",
  "frequency": "raw",
  "session_policy": "keep-labelled-sessions",
  "gap_policy": "none",
  "permit_future": false,
  "quality_policy": "retain-and-inspect-flags"
}
```

Choose these fields deliberately:

1. **Layer.** Use typed rows to inspect what the supplier delivered after type conversion. Use
   cleansed rows for reviewed labels and corrections. A flagged row remains available; filtering
   those flags is a study decision that belongs in the record.
2. **Version.** Pin one version before comparing reader routes or rerunning a study. Publishing a
   later version must not silently replace the earlier inputs. Keep the version identity with
   the request and result provenance.
3. **Time and sessions.** State the instrument/date range and whether you need raw events or
   session-aware bars. The documented bar behavior does not bridge the lunch break or two days.
   A request for stored bars and a query aggregating raw trades are not automatically the same
   workload; [the existing comparison](results.md#where-the-interface-is-slower) explains why.
4. **Missing observations.** Keep gaps visible unless the study needs a named fill policy.
   Carrying an earlier observation uses different information from choosing the nearest one.
   A forward-reading policy needs explicit opt-in and is unsuitable for a causal backtest input.

Expected output is the requested rows with the documented labels/flags and the selected version
held fixed. Compare row identities and values when checking two reader routes, rather than only
comparing row counts. This is a workflow recommendation; it does not report a new private gate.

## Treat refusal as part of the workflow

The errors below are the illustrative names already used in the [data-model examples](data-model.md#one-interface-wherever-a-researcher-works).

| Observation | What to investigate | How to continue without silently changing the study |
|---|---|---|
| Unknown instrument | Instrument identity and coverage on the requested date | Correct the request or record that the instrument is unavailable. Do not interpret an empty replacement as a successful read. |
| Missing day | The requested range and the dated coverage/issues record | Resolve the missing input or explicitly declare the missing-data policy. Do not manufacture a complete history with a future observation. |
| Forward-reading fill refused | Whether the named gap policy needs a later observation | Use no fill or a causal policy. If a non-causal analysis is intended, record the opt-in and do not present it as backtest-ready data. |
| Two runs differ | Version identity, layer, request rules and transformation settings | Reproduce the recorded request before attributing the difference to a strategy. |

The published [A-share gaps](results.md#scale) are dated source findings. This repository has no
current delivery/status feed. Operational recovery and present service health need separate
current evidence from the platform's operator.

## Run the public evidence example

Prerequisites: Python with its standard library and a shell. No platform access is required.
From a clone of this repository:

```bash
bash scripts/demo.sh
```

**Input:** the [Raw counts](results.md#raw-counts) table, not a remote dataset. In particular, the
three A-share cleansed counts are `293,894,477,866`, `228,609,088,757` and `43,446,124,248`.

**Expected output excerpts** from the existing figure checker:

```text
ok   565,949,690,871      A-share cleansed rows = orders + trades + quotes
ok   138,059,600,559      crypto stored rows = trades + L3 events + L2 book updates
ok   704,009,291,430      A-share cleansed + crypto stored
ok   1,111                concurrency gate reads, all three reader kinds
```

Spacing in the terminal may differ. The calculation is public and repeatable: it sums the
published counts and compares each derived value with its stated location in the page. The
command exits unsuccessfully on a disagreement. Run `bash scripts/check.sh` for the document
checks as well; their self-test deliberately introduces defects in scratch copies and requires
each applicable check to reject them.

If arithmetic fails, inspect the named count or derived statement and its source date. A passing
sum proves consistency of the public table, not accuracy or current availability of the private
data. The exact cleansing-removal source snapshots still need reconciliation before their derived
count is promoted to a separate achievement.

## Data and library coverage: what the record supports

| Component | Public evidence | Boundary |
|---|---|---|
| A-share and crypto stored data | [Scale](results.md#scale), table counts of 2026-10-05 and the stated ranges/issues | Historical stored rows, not a current unique-row count or complete market coverage. |
| Typed/cleansed layers and session rules | [Data model](data-model.md), design of 2026-09-28 and researcher documentation built 2026-10-01 | Published behavior and decisions; no private implementation or current re-run here. |
| Pinned reads through the query interface, Arrow and DuckDB | [Concurrency](results.md#concurrency), fixture of 2026-09-23 | Version correctness on the stated small fixture, not throughput, uptime or capacity certification. |
| DuckDB/Polars reading and query performance | [Researcher steps](results.md#researcher-steps-before-and-after) and [interface comparison](results.md#where-the-interface-is-slower) | Dated request shapes; warm-cache ratios and prose-derived observations have their stated exclusions. Cold queries on a new version were not timed. |
| Reusable backtest library, strategies, portfolio or execution | No coverage result for these components is supplied by this write-up | Data-platform evidence does not establish backtest correctness, alpha, live orders or a complete trading platform. |

Sources and their evidence types remain in [results.md](results.md#sources). This guide adds a
public reading/workflow aid, not a new platform measurement.
