# Software paper plan and evidence ledger

Working title: **Pose Reference Toolkit: Reference-bank construction, temporal pose comparison and inspectable geometric feedback**.

The 2026-10-11 review defines the complete contribution in [software positioning](SOFTWAREX_POSITIONING.md) and a staged [natural-data protocol](CASE_STUDY_PROTOCOL.md). Use those documents to freeze the case study before drafting stronger domain-performance claims.

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

Readiness review, 2026-10-09: the release and its GitHub CI are usable software evidence, but the current illustrative collection remains synthetic and the optional extraction check uses a blank video. The original application's constructed scoring counterexample does not establish this toolkit's accuracy on people. Draft the software description now; before a sign-practice submission, prioritize one documented, authorized real collection with reference/calibration/evaluation roles and report exclusion counts, scoring coverage, all-pair and conditional target-match rates. Human ratings are needed for claims about linguistic correctness or proficiency, not for the narrower claim that a developer can construct and inspect a geometric comparison workflow.

The evaluation bug found in this review was corrected: unreadable inputs previously disappeared from rate denominators. Freeze the corrected revision and rerun all quantitative results before copying them into a manuscript. The earlier fully readable synthetic demo rates are unaffected; mixed valid/invalid evaluation rates can change. See [method](METHOD.md#diagnostic-denominators-and-coverage).

For a compact paper result set, collect (1) build acceptance/exclusion and partition audits on the real collection, (2) held-out target matching with coverage and uncertainty intervals at the independent acquisition-group level, (3) the constructed mixed-exemplar failure case, (4) linear/DTW sensitivity under the same reference and calibration roles, and (5) runtime versus vocabulary, reference count and sequence length, with environment and raw measurements. The existing two-gloss microbenchmark supports only that fixed small fixture; it is not a scalability study. An independent installation/integration example would strengthen the reuse evidence.

First collect authorized real pose sequences and evaluate the current mechanism. Add angular/handshape features only if observed errors justify them, with metric versioning, common-reference/path feedback and separate calibration. Add a validated pose-format importer if it reduces actual reuse burden. Add camera integration only when needed by a use case; the independent upload demo is sufficient to exercise this library's existing API. Jetson benchmarking is optional and currently unverified; do not make it the headline of this CPU-oriented reference component.
