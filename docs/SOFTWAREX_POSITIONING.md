# Software positioning and evidence

Assessment date: 2026-10-11. This document defines a proposed software contribution, not publication acceptance or experimentally established superiority.

## Problem and reusable product

Reference-based pose applications require more than a distance function. Developers must curate permitted examples, preserve their coordinate and timing conventions, distinguish poor observations from low similarity, select a reference whose visualization explains the reported result, and evaluate the resulting policy without dropping failures or reusing its calibration inputs.

**Pose Reference Toolkit provides a reusable workflow from reference collection to inspectable comparison and assessment.** Its functional sequence is manifest authoring, optional extraction, bank construction, policy calibration, isolated-attempt comparison, aligned visual review, full receipt export and held-out diagnostics. The Python API and CLI are the product; the local web demo demonstrates an integration. An Android application is not required to use this component.

Suggested paper title: **Pose Reference Toolkit: Reference-bank construction, temporal pose comparison and inspectable geometric feedback**.

The present application is isolated sign practice. The named-joint representation supports compatible pose collections without a trained sign recognizer. Broader dance, rehabilitation or clinical usefulness is not demonstrated and should not be added to the paper as established applications.

## Three connected software contributions

1. **A reference-bank lifecycle.** Source manifests declare roles, groups, label, mirror/coordinate conventions and permission. Builds record accepted and excluded sources, derive tolerances from references only, and write versioned banks with hashes. Calibration and evaluation enforce their declared role boundaries. Hashes establish consistency; they cannot establish rights or identity.
2. **A coherent temporal comparison.** Quality-gated poses are normalized and resampled without filling tracking gaps as observations. Linear or bounded-DTW matching selects a whole exemplar and one shared path for all required joints. The selected exemplar/path supplies both the fixed-denominator score and component feedback, rather than choosing a different favorable exemplar for each cell.
3. **Inspectable outcomes and reproducible assessment.** A comparison can match, show low similarity, remain inconclusive, request recapture or reject an input. Receipts preserve policy, bank/query identity, ranking, path and feedback. The local web review displays that same comparison and exports its complete JSON. Diagnostics retain failures and distinguish conditional rates from all-pair rates and coverage.

These mechanisms form one useful workflow. They are not three unrelated validation utilities, a new DTW algorithm, or proof that geometry measures proficiency. Their value must be illustrated by concrete reuse and measured behavior.

## Closest overlap and defensible difference

The actual SignBridge implementation already builds lesson references from existing video, uses MediaPipe and a DTW medoid, and provides DTW and heuristic geometric feedback. Learn2Sign already addresses explainable feedback for sign learning. The 2026 gesture-form validation study already covers normalization, timing alignment and hand/mirror policies. MotionPerfection and PyBodyTrack demonstrate relevant movement-analysis software in SoftwareX. See [the source-specific comparison](RELATED_WORK.md).

Consequently, neither reference reuse, DTW, MediaPipe integration nor sign feedback should be claimed as unprecedented. Our proposed contribution is the portable bank-to-assessment workflow and its explicitly tested behavior under reference multiplicity, missing observations, role contamination and uncertain matches. Alignment-conditioned feedback is an actionable comparison point; the present release establishes no competitor accuracy advantage. An implementation feature comparison must distinguish verified code from an unmeasured quality claim.

## Evidence ledger

| Paper statement | Evidence available | Evidence still required |
|---|---|---|
| Developers can construct and inspect a reference bank | Library/CLI, build reports, contracts and synthetic example | One independently reproduced authorized natural-data example |
| Score and visualization use the same selected exemplar/path | Implementation, constructed regression case, browser JSON checks | Practical frequency and importance of the issue on real inputs |
| Unusable observations are handled explicitly | Synthetic tracking/anchor cases and invalid-input tests | Natural extraction coverage and recapture frequency |
| Evaluation retains failures and partitions roles | Role/overlap tests and diagnostic definitions | Auditable natural collection with defensible independent units |
| Software is installable and reproducible | Built-wheel checks, environment records and commit-specific CI | Independent integration is helpful; CI alone is not reuse evidence |
| Comparison has a particular latency | Fixed synthetic host microbenchmark | Vocabulary/reference/sequence-size scaling; extraction and full upload timing if claimed |
| Feedback identifies sign-form errors | Geometric discrepancy output exists | Expert-annotated attempts and agreement/error analysis |
| Users learn better or receive valid proficiency grades | None | Appropriate expert and learner studies; outside the first software claim |

## Efficient route to a substantive paper

Use the current release to run one legally reproducible natural-data case before changing the metric. Collect bank acceptance/exclusions, held-out target/distractor decisions with coverage, reference-count and linear/DTW sensitivity, missingness perturbations and runtime scaling. Use the [case-study protocol](CASE_STUDY_PROTOCOL.md) to freeze roles and policy rules. Describe target-label retrieval as retrieval, not correctness of a learner's sign.

The author can write the software description and synthetic engineering example now. A submission centered on sign practice should add the natural case. If errors expose a specific deficiency, implement a versioned remedy and evaluate it under the same partition: for example, an importer that enables reuse or a handshape feature justified by inspected failures. More endpoints, Android UI or a Jetson demo alone would not resolve the central evidence gap.

The first useful stopping point is a documented external collection that another developer can build, compare and review with this release, accompanied by honest failure and operating-point results. A claim of teaching correctness is a separate, stronger study.
