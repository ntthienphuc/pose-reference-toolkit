# Reproduction

Use a fresh checkout and environment. Keep generated data and receipts outside version control. See README for installation. The core package needs only NumPy; server and extraction dependencies are separate extras.

```sh
python -m pip install -e ".[server,dev]"
python -m unittest discover -s tests -v
pose-ref demo --out demo_run
pose-ref inspect --bank demo_run/bank
pose-ref evaluate --bank demo_run/bank --manifest demo_run/sources.json --policy demo_run/policy.json --out artifacts/evaluation.json
python scripts/benchmark.py --out artifacts/benchmark.json --repeats 30
python scripts/license_inventory.py --out artifacts/installed_licenses.json
python -m pip freeze > artifacts/environment.txt
python -m build
python scripts/check_wheel.py --wheel dist/pose_reference_toolkit-0.1.3-py3-none-any.whl --out artifacts/wheel.json
```

Create `artifacts` before writing shell redirections or custom output files. `demo` and receipt outputs refuse existing paths; use a new directory for a second run. Bank and manifest hashes can differ with NumPy version or binary ZIP writer details; compare semantic outcomes and source/artifact receipts within the declared environment, rather than claiming byte-identical artifacts across platforms.

To verify the actual browser, start `pose-ref serve --bank demo_run/bank --policy demo_run/policy.json --demo-root demo_run`, then in another terminal:

```sh
python -m pip install playwright
python -m playwright install chromium
python scripts/check_browser.py --out artifacts/browser.json
```

To exercise video decoding/extraction, use a Python 3.11 environment and:

```sh
python -m pip install -e ".[server,dev,extract]"
python -m pip check
python scripts/check_video_adapter.py --out artifacts/video_adapter.json
python -m unittest discover -s tests -v
```

The adapter check creates a blank video, verifies FPS sampling and unique joint schema, and confirms a tracking-quality failure. It does not demonstrate successful tracking of real signs. The six-joint synthetic demo bank deliberately differs from the 49-joint adapter contract; build a bank from your compatible real video/pose sources to use video comparison.

HTTP tests exercise FastAPI's in-process client. Browser checks exercise a real running server and Chromium. Synthetic benchmarks include checksum checking and feedback serialization, excluding extraction and network. Report runtime environment, repeats, vocabulary/reference counts, p50/p95 and this scope alongside numbers.

GitHub Actions runs core checks on Linux and Windows, packaging/source verification, optional adapter checks, a browser smoke and a Docker server smoke. Use the run attached to the exact release commit as evidence; workflow existence alone does not demonstrate a successful run. No CI result establishes linguistic validity or independent reuse.

Container demo (generate `demo_run` on the host first):

```sh
docker build -t pose-reference:0.1.3 .
docker run --rm -p 8010:8010 -v "ABSOLUTE_DEMO_FOLDER:/data:ro" pose-reference:0.1.3
```

The base container contains the server extra, not MediaPipe. It supports compatible pose uploads and generated synthetic fixtures. Bank folders created from an atomic temporary directory are private to their creating OS user. On Linux, add `--user "$(id -u):$(id -g)"` to run with the host bank owner's UID/GID; do not expose a real private bank to all users just to work around mount permissions. The default image user is `pose_reference` (UID 1000). Windows Docker mount permissions differ; verify `/health` with the intended host mount. CI verifies the Linux host-UID configuration.
