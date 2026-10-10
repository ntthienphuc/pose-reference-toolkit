# Natural-data case study protocol

Protocol date: 2026-10-11. This document specifies work to perform, not completed natural-data results. Freeze a reviewed copy, its settings and software commit before evaluating held-out samples.

The software contribution is a reusable workflow from an authorized collection to a versioned reference bank, calibrated target comparison and temporally aligned geometric feedback. Reference construction, comparison, calibration, inspection and integration are all part of the contribution. Existing extraction libraries and DTW are credited components. The study must show that an independent developer can use this workflow, including its observable failures.

The current public examples are generated motions. Passing them demonstrates implemented behavior, not sign-language quality, learner proficiency or pedagogical benefit. This protocol does not require a new classifier or a large learning application.

## Questions and claim boundaries

1. Can a documented real collection be imported, audited and turned into a usable bank, with every included and excluded source accounted for?
2. On independent held-out attempts, what target-match behavior and scoring coverage does the frozen bank and policy produce?
3. Does each displayed exemplar, alignment and joint state explain the reported geometric score?
4. How do alignment choice, reference multiplicity, missing observations and timing changes affect coverage, false matches and comparison cost?
5. Can another developer reproduce the workflow through the Python API or CLI and inspect a complete exported receipt?

Source-label agreement measures target matching. It does not establish whether a learner performed a linguistically acceptable sign. Expert ratings are a separate requirement for that stronger claim. Existing application results are not results of this independently implemented package.

## 1. Establish an eligible collection

Record the collection owner, source location, applicable permission or license, permitted transformations and whether source videos, derived poses and examples may be redistributed. Research access and public redistribution are separate permissions. Keep restricted assets local; a public reproduction recipe may describe obtaining them from their authorized distributor without republishing them. `authorized: true` records an operator declaration and does not create permission.

Locate original recordings or documented precomputed poses. For a legacy collection, recover source IDs, extraction settings and acquisition metadata before conversion. A file named as a public dataset is insufficient evidence of either license or participant consent. Do not silently reinterpret legacy arrays as the current named-joint contract.

Start with a small development collection that includes several visually confusable glosses, natural duration differences and examples with incomplete tracking. A pilot of roughly 5–10 glosses may reveal integration failures; it is not a prescribed sample size or proof of publication readiness. Select the final vocabulary for a documented intended use rather than choosing only easily separated words after seeing results.

Include independently confirmed labels, one pretrimmed attempt per sample, and all acquisition metadata that can be supported. Record camera/view, source recording, clip boundaries, available signer identity and how the label was established. Trimming rules must be applied without selecting the highest-scoring attempt. Keep failed extraction and unreadable declared samples in the outcome ledger.

The current optional adapter extracts 49 joints using 2D pixel coordinates and frame-index/FPS timing. It assumes constant frame rate and uses detection presence for hand confidence. Check compatibility, image orientation and hand assignments on representative clips. The default profile requires both hands and body tracking; a one-handed sign can therefore still fail if the other hand is unobserved. Choose and document required groups on development data, use the same bank contract at inference, and do not quietly relax them per evaluation sample.

## 2. Freeze roles and independence

Use three explicit roles in the source manifest:

| Role | Permitted use | Not permitted |
|---|---|---|
| Reference | Construct exemplars, tolerance and bank artifacts | Include held-out attempts to improve coverage |
| Calibration | Choose score threshold and inter-gloss margin for a fixed bank and alignment | Report fitted operating-point behavior as independent evaluation |
| Evaluation | Estimate frozen system behavior and inspect failures | Tune thresholds, groups, vocabulary or reference selection and retain the same hold-out claim |

Assign entire source recordings/acquisition groups to one role before generating clips or perturbations. Multiple clips, frames, camera views or perturbations of one source are related observations. Preserve their parent ID and group; they are not independent replicates. Byte/canonical-pose duplicate checks do not detect every overlapping or re-encoded video.

If signer identity is verified, use signer-disjoint roles and document verification. Otherwise use acquisition-group-disjoint roles and say that signer independence is unknown. Do not replace missing signer metadata with one invented signer ID per clip. The toolkit deliberately refuses a declared verified signer appearing across roles; retain this protection. A same-signer application study would need an explicit separately implemented and documented protocol, rather than false metadata that bypasses the current guard.

Store a split ledger and hashes of source manifest, bank, policy, software revision and evaluation inputs. Report the number of independent groups and samples per role and gloss. Some source groups may lack some glosses; disclose the resulting coverage instead of manufacturing balanced counts.

## 3. Build, calibrate and run the primary case

Run `pose-ref audit`, `build`, `calibrate` and `evaluate` on new output paths. Archive the command arguments, environment, source audit, build report, bank profile/manifest, calibration receipt and complete evaluation report. Record accepted and excluded reference counts by gloss and reason, tracking coverage and tolerance-cap clipping. Every gloss needs 2–64 accepted references; a failed build is an outcome to diagnose, not a reason to hide the excluded sources.

Use one frozen primary alignment setting. If both linear and DTW are compared, construct comparable banks and fit a separate policy for each alignment on the same calibration role. Never apply a linear policy to DTW and call the difference an unbiased method comparison. Record the DTW band and the fact that accumulated path cost and repeated path cells can affect temporal weighting.

The current calibrator chooses a score threshold and margin by empirical balanced target-match behavior on scored calibration pairs. Archive total and scored calibration counts and exclusions. Do not change the search grid after observing held-out results without making it a new development iteration and reserving a new evaluation set.

Evaluate each declared sample against each bank gloss. Include preselected confusable negative targets in a separate reported subgroup as well as the complete vocabulary comparison; aggregate negative rates can look good when most alternatives are easy. Declare subgroup membership before looking at the results. Samples of unrepresented glosses have no in-bank positive pair and should be reported as a separate out-of-vocabulary experiment if used.

## 4. Report outcomes with their denominators

For every sample-target pair, retain its expected target status, observed outcome, score if available, reasons and source identity. The five decision outcomes are `match`, `low_similarity`, `inconclusive`, `needs_recapture` and `reject`.

| Quantity | Denominator or interpretation |
|---|---|
| All-pair true-match rate | Matched positive pairs / all declared positive pairs, including failed extraction and recapture |
| All-pair false-match rate | Matched negative pairs / all declared negative pairs, including failures |
| Conditional true-/false-match rates | The corresponding rates restricted to pairs with a numeric score |
| Sample scoring coverage | Distinct samples with a score / declared samples |
| Comparison scoring coverage | Scored pairs / declared sample-target pairs |
| Comparison status counts | Mutually exclusive decision counts across pairs |
| Sample status counts | Distinct samples producing each status; these counts may overlap across target queries |

Always report counts beside rates, including scored positive and negative counts. Conditional rates are undefined when their denominator is zero. A system rejecting all inputs has zero all-pair false matches and no useful coverage; report both facts. State any operational false-reject definition explicitly, since low similarity, ambiguity, recapture and malformed input imply different next actions.

Report rates per gloss and predeclared confusable subgroup where counts support interpretation. Pairs from one query share that query and the bank, so the number of pairs is not the number of independent experimental units. If verified independent signer or acquisition groups are available in adequate number, a cluster bootstrap can resample whole groups with all their samples and pairs intact. Declare the resampling unit, repetitions, seed and interval method. These intervals describe the fixed trained/calibrated system on sampled groups; they do not include uncertainty from rebuilding the bank or refitting calibration unless that process is explicitly resampled.

Do not report confident group-level intervals when identities or independent groups are unknown or too few. Give descriptive counts, per-group outcomes and the limitation instead. No arbitrary number of clips automatically makes a signer-level claim valid.

## 5. Examine the mechanisms without changing the task

**Feedback coherence.** For successful comparisons, recompute the score from exported required-cell states and verify that the displayed reference ID, coordinates and alignment are those used by the scorer. Include a small number of real examples inspected by a competent sign-language reviewer for interpretable failure descriptions. Distinguish geometric disagreement from a confirmed linguistic error. Keep the existing synthetic mixed-exemplar counterexample as a controlled engineering illustration; it is not a human-performance experiment.

**Reference multiplicity.** Use nested reference subsets chosen only from the reference role, with deterministic selection and documented IDs. Rebuild tolerances and recalibrate separately for each resulting bank. Compare matched evaluation groups for coverage, target-match rates, confusable false matches, selected-reference diversity, clipping and cost. More references may increase false acceptance. Do not pick the best subset on evaluation and retain a held-out performance claim. Use feasible counts within the implemented 2–64 limit; predeclare which sizes the collection supports.

**Missing observations.** Apply declared dropout patterns to held-out copies while preserving their parent groups: short missing runs, longer missing runs and hand-specific occlusions. Mark observations missing in the actual contract rather than replacing them with valid zero coordinates. Track whether the expected consequence is recapture, reduced observable coverage or changed comparison behavior. Report these as controlled perturbations of the same real sources, not new independent recordings or measured natural occlusion performance.

**Timing.** Predeclare resampling or timestamp perturbations and which property each tests. Speed variation with a consistent timestamp trajectory tests alignment behavior; invalid nonmonotone timestamps or excessive gaps test rejection/recapture. Keep these distinct. Do not use time reversal as automatically equivalent signing. Linear and DTW policies remain separately calibrated. Preserve original unmodified cases and record transformation parameters.

These analyses should explain a concrete failure or reuse decision. Add an angular, handshape or learned component only after consistent errors show that the existing geometry is the limiting factor and an independent evaluation is available for the revised metric.

## 6. Measure software cost and integration

Measure loading/build time, extraction time, comparison time, bank size and memory separately where feasible. The existing comparison microbenchmark includes integrity checking and feedback serialization; it excludes video extraction and network. Preserve that scope when extending it. Vary vocabulary size, references per gloss and normalized sequence length using declared fixtures and feasible real banks. Synthetic scaling inputs measure computational behavior, not sign accuracy. Report raw timings, warmups, repetitions, median/p95, hardware, OS, Python/dependency versions and whether disk-cache effects are controlled.

The current scorer evaluates every gloss to compute alternative-target margin and checks bank hashes on each comparison. Include these costs in end-to-end comparison claims. Do not call local CPU timings smartphone, Jetson or service-load results. A server benchmark needs its own concurrency, input, resource and failure protocol.

Demonstrate one independent installation or integration: a fresh environment builds or imports a permitted bank, compares a held-out pose, and inspects the full receipt through the API/CLI and web adapter. Separate author-run clean installation from genuinely independent external reuse. The downloaded web receipt should preserve the complete response, including feedback; a UI screenshot alone cannot reproduce its score.

## 7. Stop rules and submission decision

- If permission or source provenance is unresolved, stop redistribution and strong real-data claims; continue software tests and collection documentation.
- If extraction coverage is poor, identify its cause on development data before increasing the dataset size or training a model. Preserve failures in the final report.
- If the available vocabulary contains only easy negatives or no independent groups, narrow the empirical claim and collect the missing case instead of adding decorative features.
- If comparison outcomes are useful but expert correctness ratings are unavailable, retain the geometric workflow/target-matching claim. Do not present the score as validated proficiency.
- If a new feature or threshold is chosen after held-out inspection, designate the inspected set as development and obtain fresh evaluation evidence for the revised system.
- If the current workflow, observed failure modes and reuse case are adequately demonstrated, stop optional architecture expansion and write the paper. Extra model complexity is not a substitute for a complete, reproducible natural case.

The minimum credible natural-case package contains permitted inputs or an executable acquisition recipe, source and split ledger, build/exclusion reports, frozen bank and calibration identities, held-out outcome counts with coverage, inspectable feedback examples and scoped runtime evidence. Publicly share only artifacts covered by the applicable permissions. A SoftwareX submission can then describe the complete software contribution and its measured scope; acceptance remains an editorial decision.
