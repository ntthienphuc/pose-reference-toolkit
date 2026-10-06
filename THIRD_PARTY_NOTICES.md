# Third-party notices and release scope

The toolkit's own source, tests, browser page and synthetic fixture generator are copyright 2026 Nguyễn Trần Thiên Phúc and MIT licensed. No competitor implementation is vendored. Algorithms such as DTW and existing libraries are credited without claiming authorship of those algorithms/libraries.

Direct dependencies are installed separately; their code is not relicensed by this project's MIT license. Retain upstream license/notice files when distributing installed dependencies, containers or bundled binaries. This inventory describes source-license provenance, not a legal opinion over every transitive/binary component or user dataset.

| Dependency | Role | Upstream source license/reference |
|---|---|---|
| NumPy | Numerical arrays | [BSD-3-Clause](https://github.com/numpy/numpy/blob/main/LICENSE.txt); wheels also contain component notices |
| FastAPI | Optional web API | [MIT](https://github.com/fastapi/fastapi/blob/master/LICENSE) |
| Uvicorn | Optional server | [BSD-3-Clause](https://github.com/Kludex/uvicorn/blob/main/LICENSE.md) |
| python-multipart | Optional upload parsing | [Apache-2.0](https://github.com/Kludex/python-multipart/blob/main/LICENSE.txt) |
| MediaPipe 0.10.14 | Optional Holistic extraction | [Apache-2.0](https://github.com/google-ai-edge/mediapipe/blob/v0.10.14/LICENSE); shipped model/package components retain upstream notices |
| OpenCV / opencv-contrib-python | Optional decoding/extraction | [Apache-2.0 OpenCV](https://github.com/opencv/opencv/blob/4.x/LICENSE); [Python wrapper MIT and bundled-component notices](https://github.com/opencv/opencv-python/blob/4.x/LICENSE.txt) |
| JAX / jaxlib | MediaPipe import compatibility dependency | [Apache-2.0](https://github.com/jax-ml/jax/blob/main/LICENSE) |
| httpx | Development HTTP tests | [BSD-3-Clause](https://github.com/encode/httpx/blob/master/LICENSE.md) |
| build | Development packaging | [MIT](https://github.com/pypa/build/blob/main/LICENSE) |

Common server transitive components include Starlette (BSD-3-Clause), Pydantic (MIT), and AnyIO (MIT). Optional extraction pulls other upstream dependencies and native libraries; inspect installed distribution notices when redistributing that environment. `scripts/license_inventory.py` records available installed metadata and license files without pretending metadata is exhaustive. Preserve bundled codec/model notices; a permissive wrapper license alone is not a complete binary-license audit.

Redis, PyTorch, ONNX Runtime and pose-format are not dependencies of this release. They do not need replacement implementations for this workflow.

Reference/data rights are separate. `authorized: true` is an operator declaration, not a grant or legal verification. Obtain permission for identifiable participant recordings, transformations and redistribution. A GitHub source license does not automatically cover videos, linked datasets or pretrained assets. The public release contains no real participant/reference asset or private application credential. MediaPipe's optional installed package includes upstream components; this release does not publish a separately trained or extracted checkpoint.
