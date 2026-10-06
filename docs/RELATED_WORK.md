# Related work and positioning

Targeted review, 2026-10-06. This is not an exhaustive novelty search. Code features below are based on the linked repositories/papers, not reproduced competitor benchmarks. No source from these projects is vendored or copied into this toolkit.

| Work | Relevant overlap | Pose Reference's proposed emphasis |
|---|---|---|
| [MediaPipe–DTW sign recognition](https://github.com/gabguerin/Sign-Language-Recognition--MediaPipe-DTW) | Imports reference videos, extracts hand-angle features, applies DTW and voting. `yt_download.py` automatically obtains/cuts source clips. | Audited, explicitly permission-declared bank construction; role separation; complete-exemplar feedback receipts; recapture versus similarity outcomes. Existing-video reference import is **not** a new idea. |
| [pose-evaluation](https://github.com/sign-language-processing/pose-evaluation), [Jiang et al., WMT 2025](https://aclanthology.org/2025.wmt-1.4/) | Reusable sign-pose metrics, DTW processing, missing-keypoint handling and varying pose lengths/formats; paper evaluates retrieval and human correlation. | Bank lifecycle plus target-practice decision/visualization tied to one selected exemplar. Do not claim pose comparison or missing-data processing is original, or equal human-validation evidence. |
| [SignBridge](https://github.com/mhmdtaha091/SignBridge) | Browser tutor, MediaPipe/TF.js, avatar imitation scored using DTW with targeted feedback, data-quality capture workflow. | Small independent Python API/CLI and artifact receipts for imported references rather than a full language-learning frontend. This is a design distinction, not demonstrated superiority. |
| [Holzknecht et al., 2024](https://doi.org/10.1080/15434303.2024.2364877) | Automated vocabulary assessment, handshape/movement feedback; compares machine and human ratings and studies learners' perceptions. | A transparent geometric software component with explicitly limited evidence. Human-rated validity and learning outcomes remain future work. |
| [Wen and Xu, 2024 preprint](https://arxiv.org/abs/2404.10383) | Two-stage sign-performance scoring with reconstruction, rotation and smoothing. | The contribution here is reference-artifact construction and engineering contracts, not a new learned scoring algorithm. |

Repository snapshots inspected: gabguerin `68948d87b1e57c3af41f5116728b3d264d6830d0`; pose-evaluation `2769b6f49693dd83e2ee81c09355d787afe775c6`; SignBridge `22000aae3e0cf9836178bd3c409a047b08f24d70`. Their source licenses were MIT at inspection. License permission over code does not establish permission over linked videos or bundled datasets. Absence of a feature from the inspected material is not proof that the feature has never been implemented elsewhere.

## Defensible contribution statement

“Pose Reference Toolkit provides an auditable workflow for constructing pose reference banks from authorized sources and producing quality-aware, complete-exemplar geometric feedback for isolated practice attempts. Source roles, pose contracts, bank assets, decision policies and selected alignment are exposed as inspectable artifacts through a reusable Python API, CLI and web adapter.”

Do not describe the software as the first automatic sign tutor, the first reference-video scorer, a novel DTW algorithm, or a validated substitute for sign-language instructors. The useful distinction is the combination of bank construction, coherent comparison and verifiable outcomes in a reusable release; whether that is sufficiently original for a journal is an editorial/reviewer judgment.

For release organization, [EmbedKD](https://github.com/hublinhdn/embedkd) and [AffectStream's SoftwareX repository](https://github.com/ElsevierSoftwareX/SOFTX-D-25-00173) provide examples of installation/reproduction, license/citation metadata, examples and software checks. They are packaging examples, not sign-language baselines or proof of journal acceptance.

See [references.bib](references.bib) for bibliographic records. Website/repository content can change after the snapshot.
