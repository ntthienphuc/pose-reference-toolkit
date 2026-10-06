# Pose Reference Toolkit

[![CI](https://github.com/ntthienphuc/pose-reference-toolkit/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntthienphuc/pose-reference-toolkit/actions/workflows/ci.yml)

Build an audited reference bank from authorized video clips or precomputed poses, then compare one isolated practice attempt against a target gloss. The same selected reference and temporal alignment produce the score, joint feedback and web visualization.

This is a reusable Python library, CLI and small local web demo. It is a new, independent implementation of reference-bank and comparison logic, separated from the original practice application. It does not reproduce that application's coordinate/angular scores, classifier, account system or private reference dataset.

**The output is geometric similarity under a declared configuration. It is not a validated sign-language proficiency grade.** The public fixtures are synthetic motions, not signs performed by people.

## Quick start

Python 3.10 or newer; the optional legacy MediaPipe video adapter is tested separately on Python 3.11.

```sh
git clone https://github.com/ntthienphuc/pose-reference-toolkit.git
cd pose-reference-toolkit
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[server,dev]"
pose-ref demo --out demo_run
pose-ref serve --bank demo_run/bank --policy demo_run/policy.json --demo-root demo_run
```

Open <http://127.0.0.1:8010>. Try the four synthetic examples: matching motion, different motion, missing hand tracking, and degenerate shoulder anchors. Upload a compatible pose JSON for your own test. The synthetic bank has six joints; a video-extracted 49-joint pose requires a separate matching bank.

```sh
pose-ref compare --bank demo_run/bank --pose demo_run/example_same.json --target SYNTHETIC_HORIZONTAL --policy demo_run/policy.json
python -m unittest discover -s tests -v
```

The demo generates 16 independent synthetic files with declared reference/calibration/evaluation roles, builds eight references for two motion classes, calibrates on four files and evaluates on the other four. Generated rates verify the engineered fixture only. They are not VSL recognition or learner-assessment results.

## Own reference collection

Supply pretrimmed, single-attempt clips with confirmed labels and permission. Keep reference, calibration and evaluation acquisition groups separate. A source-group ID is not automatically a verified signer identity.

```json
{"schema_version": 1, "samples": [
  {"id":"hello_ref_01", "gloss":"HELLO", "path":"clips/hello_01.mp4",
   "kind":"video", "role":"reference", "source_group":"capture_01",
   "license":"YOUR documented permission or license", "authorized":true}
]}
```

This snippet shows one row; a build needs **2–64 accepted references per gloss**. Add disjoint `calibration` and `evaluation` rows before fitting and assessing policy thresholds. Paths resolve within the manifest folder. No automatic internet download or claim of rights verification is provided.

```sh
# Use Python 3.11 for this optional adapter.
python -m pip install -e ".[server,extract]"
pose-ref audit --manifest collection/sources.json
pose-ref build --manifest collection/sources.json --out collection/bank_v1
pose-ref calibrate --manifest collection/sources.json --bank collection/bank_v1 --out collection/policy.json
pose-ref evaluate --manifest collection/sources.json --bank collection/bank_v1 --policy collection/policy.json --out collection/evaluation.json
pose-ref serve --bank collection/bank_v1 --policy collection/policy.json
```

The server then accepts video uploads against this bank. Use `pose-ref extract --video clip.mp4 --out pose.json` to inspect extraction separately. The adapter uses MediaPipe Holistic, 49 uniquely named joints and frame-index/FPS timestamps; variable-frame-rate timing is not supported. Hand confidence is a detection-presence indicator, not a calibrated per-joint probability. See [data contracts](docs/CONTRACTS.md).

## Python API

```python
from pose_reference import ReferenceBank, compare
from pose_reference.pose import load_pose

bank = ReferenceBank("demo_run/bank")
result = compare(load_pose("demo_run/example_same.json"), bank, "SYNTHETIC_HORIZONTAL")
print(result["status"], result["score"], result.get("matched_reference_id"))
```

The default policy is explicitly heuristic. `linear` alignment is the default; `dtw` uses one bounded, shared path for all required joints. Policies calibrated for one alignment must not be transferred to another without validation.

## What the toolkit adds

- Manifest-based reference construction, explicit names/groups/mirror contract, source hashes, inclusion/exclusion reports, immutable versioned bank outputs.
- Checks for duplicate bytes and canonical pose content, source-group and declared verified-signer overlap across roles; additional guards against overlap with deployed references and calibration samples during evaluation.
- Quality gates before scoring; missing observations remain unknown during adjacent-frame resampling and count against the score's fixed required-cell denominator.
- Whole-reference selection and one alignment path for scoring and feedback; no minimum independently selected across different exemplars at each joint/frame.
- Explicit `match`, `low_similarity`, `inconclusive`, `needs_recapture` and `reject` outcomes with JSON receipts, plus a standalone browser adapter.

Reference import, MediaPipe extraction, pose distances and DTW have prior art. The proposed software contribution is this auditable workflow and its tested behavior. See [related work](docs/RELATED_WORK.md), [method](docs/METHOD.md), [reproduction](REPRODUCE.md), [limitations](docs/LIMITATIONS.md) and [paper plan](docs/SOFTWAREX_PLAN.md).

## Distribution and rights

Toolkit source and generated synthetic fixtures are MIT licensed, copyright Nguyễn Trần Thiên Phúc. Libraries retain their own licenses; [third-party notices](THIRD_PARTY_NOTICES.md) identifies direct dependencies. No private participant video, reference bank, model checkpoint, survey or application credential is redistributed. Public availability of a video does not establish permission to download, transform or redistribute it.

This release is standalone software. It is not a published SoftwareX article. Citation metadata is in [CITATION.cff](CITATION.cff).

## Migration from the initial prototype

Version 0.1.1 uses the distribution `pose-reference-toolkit`, Python package `pose_reference`, and command `pose-ref`. Install it in a fresh environment and update imports and launch commands. Existing toolkit v1 JSON/NPZ bank schemas and comparison semantics are unchanged; no legacy import/CLI alias is installed. The previous release remains in history with its original assets. This naming change does not alter the separate original practice application.
