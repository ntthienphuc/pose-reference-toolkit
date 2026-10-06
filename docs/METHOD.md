# Comparison method v1

The method operates on one isolated, pretrimmed attempt. It does not segment continuous signing, discover labels, translate sentences or estimate proficiency.

1. Validate the input's ordered names, explicit groups, dimensions, timestamps, observation masks, coordinate and mirror contracts. Check that bank files still match the loaded checksums.
2. Check tracking before scoring. Defaults: at least eight frames, confidence ≥0.5, anchor and required-group coverage ≥0.8, no required joint missing for more than 25% of source frames, and no source timestamp gap over 250 ms. A failure produces `needs_recapture` with no score.
3. Center each valid frame at the shoulder midpoint and scale by the median valid shoulder width of that attempt. Degenerate shoulders do not receive a fallback scale. Resample to the bank's length, default 32, using source timestamps. Interpolate only between adjacent observed frames; do not fill a detection gap with invented observations.
4. Build per-frame/per-joint tolerance from **reference rows only**: coordinatewise median template, 0.85 quantile of Euclidean deviations plus 0.03, clipped to [0.08,0.25] shoulder-width units. Minimum required-cell support is 0.5. Report cap clipping so heterogeneous references do not silently widen tolerances indefinitely. These values are heuristics, not linguistically derived tolerances.
5. Compare every complete exemplar. The default uses equal normalized-time indices; optional DTW uses a single Sakoe–Chiba band (default 20% of resampled length), a joint-aggregate cost and one monotone path shared by all required joints. Distances divided by tolerance are capped at 5 in selection cost; missing cells have cost 5. DTW minimizes accumulated cost, not normalized-path cost, and no path-length invariance is claimed.
6. Select the whole template with lowest mean clipped cost; score and index break ties deterministically. The geometric score is 100 times the fraction of required path cells that are observed and within tolerance. Missing cells remain in the denominator. There is no independent choice of the best reference at each joint/frame.
7. Compare the requested target score with the best alternative gloss. Default score threshold is 85 and margin is 5. Calibrated policies are tied to a bank hash and alignment mode. Render the selected target exemplar and exactly the same path/cell states used for its score.

| Outcome | Condition |
|---|---|
| reject | Invalid request, incompatible contract, unknown target or modified bank |
| needs_recapture | Input tracking/anchors/timing do not pass quality gates |
| low_similarity | Target score below threshold or substantially below an alternative |
| inconclusive | Score is high but the target is not uniquely supported by the configured margin |
| match | Target passes score threshold and available inter-gloss margin |

Single-gloss banks have no alternative margin. Use multiple plausible distractor glosses when calibrating a decision intended to distinguish signs.

The calibration grid uses scores 70–95 in steps of 5 and margins 0,5,10,15. It maximizes the empirical balanced positive/negative target-match rate on observable calibration pairs; stricter settings break ties. Evaluation uses only evaluation rows and refuses overlap with references or supplied calibration receipts. Source-gloss agreement assesses target retrieval, not expert-rated correctness of learner form. Invalid inputs and recapture outcomes must be reported alongside rates rather than silently removed.
