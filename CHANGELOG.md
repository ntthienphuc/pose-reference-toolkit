# Changelog

## 0.1.1 — 2026-10-06

- Rename the product and repository to Pose Reference Toolkit.
- Rename the distribution to `pose-reference-toolkit`, imports to `pose_reference`, and CLI to `pose-ref`.
- Update the web demo, container, citation metadata and reproduction commands to the new name.
- Preserve existing bank/pose schemas and comparison semantics. See README for migration.

## 0.1.0 — 2026-10-06

- Initial standalone Python API, CLI and local upload/pose visualization demo.
- Explicit pose and source schemas, role/group overlap audit, byte/canonical-pose duplicate checks.
- Versioned bank building with permissions, accepted/excluded source reports, hashes and quality/tolerance settings.
- Complete-exemplar linear/bounded-DTW matching, consistent feedback and quality-aware outcomes.
- Bank-bound calibration and disjoint evaluation diagnostics.
- Synthetic fixture generation, regression/HTTP tests, packaging and reproduction tools.
- Optional pinned MediaPipe Holistic video adapter; no private real references or recognition weights included.

This package is independent of the original practice application. It changes the scoring method and cannot inherit that application's evaluation results.
