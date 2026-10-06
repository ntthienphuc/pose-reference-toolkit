# Software paper plan and evidence ledger

Working title: **Signova Reference Toolkit: Auditable pose reference banks and coherent geometric feedback for isolated sign practice**.

This is a writing/evidence plan, not a submitted or accepted paper. Check the current [SoftwareX author guide](https://www.sciencedirect.com/journal/softwarex/publish/guide-for-authors) and template before submission. The guide page returned HTTP 403 during the 2026-10-06 inspection, so exact current word limits and mandatory metadata are not asserted here.

## Motivation and contribution

Existing video and pose comparison software already covers extraction, DTW and feedback. A reusable component still needs consistent input contracts, versioned reference selection, observable exclusions, role-specific diagnostics and a result whose displayed exemplar explains its score. Explain those software problems with concrete failure cases, rather than claiming a new sign-language recognition algorithm.

## Suggested manuscript structure

1. Motivation and significance: bank-building burden, permitted source reuse, coherent feedback, existing sign-assessment software and explicit evidence boundaries.
2. Software description: library, CLI, source/bank/policy schemas, build audit, normalization, quality gates, bounded alignment, whole-reference selection and web adapter.
3. Illustrative examples: synthetic controlled cases plus an authorized real reference collection if available. Show the rejected/missing/reference-mixing cases and receipts, not only ideal successes.
4. Evaluation: functional checks, package and interface reproducibility, extraction smoke, runtime/bank-size measurements; separate engineering evidence from target retrieval and human-rated assessment.
5. Impact, reuse and limitations: how an independent developer can supply compatible poses and integrate results; what the current 2D metric does not assess.
6. Software metadata, license/data permissions, citation/version and availability.

## Results to collect

| Result | Current release capability | Claim supported |
|---|---|---|
| Synthetic positive/different-motion and missing/degenerate cases | Reproducible `demo` receipts | Expected engineered decisions only |
| Whole-exemplar versus per-cell reference mixture | Regression counterexample | Score/feedback coherence under that constructed case |
| Invalid JSON, timestamps, contracts, overlap, pickle, tampering | Automated tests | Tested input/artifact checks |
| Build inclusion/exclusion and source roles | Manifest/build report and diagnostic receipts | Traceable bank construction, based on operator metadata |
| API/CLI/wheel/browser parity | Reproduction scripts and CI | Software installation and interface behavior |
| Latency p50/p95 with repeated runs | `scripts/benchmark.py` | Host-specific synthetic comparison time, excluding video extraction |
| Real held-out target/distractor retrieval | Diagnostic tool exists; new public real results not supplied | Requires authorized data, disjoint groups and frozen calibration policy |
| Human score/feedback agreement | Not established | Requires expert ratings and an appropriate agreement protocol |
| Educational benefit and independent reuse | Not established | Requires learner study and an independent integration/use case |

Before stronger domain claims, prioritize one real-data bank use case, threshold sensitivity, confusable negatives, recapture coverage and feedback inspection by a sign-language expert. Preserve signer and acquisition grouping. Do not report synthetic fixture rates as real accuracy or reuse old application numbers as results of this new package. A successful CI run cannot replace that evidence.

## Efficient next improvements

First collect authorized real pose sequences and evaluate the current mechanism. Add angular/handshape features only if observed errors justify them, with metric versioning, common-reference/path feedback and separate calibration. Add a validated pose-format importer if it reduces actual reuse burden. Add camera integration only when needed by a use case; the independent upload demo is sufficient to exercise this library's existing API. Jetson benchmarking is optional and currently unverified; do not make it the headline of this CPU-oriented reference component.
