# Data contracts

## Pose sequence v1

Each JSON document has exactly `schema_version`, `xy`, `confidence`, `timestamps_ms`, `names`, `groups`, `coordinate_space`, and `mirror`. Use `PoseSequence.to_dict()` to produce it. `xy` is T×J×2, confidence is T×J in [0,1], and timestamps are strictly increasing milliseconds. Supported bounds are 1–2000 frames and 3–128 joints. Positive-confidence coordinates must be finite; missing values may be `null` with zero confidence. Never encode missing detections as observed zeros.

Joint names are ordered and unique. `pose_left_shoulder` and `pose_right_shoulder` are required anchors. Groups explicitly partition all joint indices exactly once. The default required groups are `body`, `left_hand`, `right_hand`; for an intentionally one-handed task, declare the corresponding required groups at bank build time, rather than silently omitting a missing hand later.

`coordinate_space` is `pixel_xy` or `cartesian_xy`. `mirror` is `unmirrored` or `mirrored`; there is no automatic handedness swapping. The query must exactly match the bank's contract. The video adapter assumes an unmirrored input; confirm capture settings before using that declaration.

For NPZ import, store numeric `xy`, `confidence`, `timestamps_ms` arrays and a scalar Unicode `metadata` containing JSON for the remaining pose fields. Object arrays and pickle are refused. `.pose` files from pose-format are not directly accepted by v0.1.1; convert them with a separately validated mapping instead of assuming fixed joint offsets.

## Source manifest v1

The top-level fields are `schema_version: 1` and `samples`. Each row requires:

| Field | Meaning |
|---|---|
| id | Unique source sample ID |
| gloss | Operator-confirmed label; not inferred from filenames |
| path | Relative file path contained within the manifest folder |
| kind | `pose` or `video` |
| role | `reference`, `calibration`, or `evaluation` |
| source_group | Acquisition/source group supplied by the operator |
| license | Documented source permission/license description |
| authorized | Explicit `true` operator declaration |
| speaker_id, speaker_verified | Optional signer identity and boolean assertion that it was verified |

Role separation is enforced using declared acquisition groups and, where provided, declared verified speaker IDs. The software does not verify identities or legal rights. Exact byte duplicates and canonical pose duplicates are refused; canonicalization includes the complete pose contract, coordinates and confidences, with timestamps shifted to zero. It is not perceptual video deduplication and is not invariant to coordinate transforms or timestamp rounding.

## Bank v1

`manifest.json` hashes `profile.json`, `build_report.json` and per-gloss NPZ assets. The profile locks the pose contract, required groups, normalization, resampling length, quality gates, tolerance settings and metric. The build report preserves accepted sources and excluded reasons, source hashes, group declarations, permissions and extraction recipe/version information. Each bank gloss records complete templates, medoid ID, source byte/canonical-pose hashes and tolerance clipping/support diagnostics.

The builder consumes only `reference` rows. A gloss requires 2–64 accepted references. Existing destinations are never overwritten. CLI build failures save a separate `.failure.json`; no partial valid bank is published. Checksums detect modification relative to a loaded manifest; they are not digital signatures or proof of authenticity.

## Receipts and HTTP

Comparison receipts identify the bank SHA-256, canonical query-pose SHA-256, target, full decision policy, input-quality assessment, outcome, score, selected reference, ranking, alignment pairs and optional per-joint feedback. The query hash covers the parsed pose document, including absolute timestamps; it is not the original video's byte hash. Unknown joints remain `unknown` and numeric values are serialized as `null`. JSON rejects duplicate keys and non-finite constants.

The demo serves `GET /`, `/health`, `/bank`, allowlisted synthetic `/demo/{name}`, `POST /compare` with `{target,pose}`, and optional multipart `POST /compare-video` with `target` and `video`. Pose uploads are bounded at 2 MB, video uploads at 30 MB and extraction at 2000 sampled frames. These are application limits, not a complete public-service resource/security policy. The server defaults to loopback and serializes comparison/extraction work in one process.
