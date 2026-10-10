# Software metadata

Metadata for Pose Reference Toolkit 0.1.3, following the C1–C8 fields in the SoftwareX original-software template (March 2026, version 6).

| Field | Description | Value |
|---|---|---|
| C1 | Current code version | 0.1.3 |
| C2 | Permanent link to code/repository used for this version | [Version 0.1.3 source](https://github.com/ntthienphuc/pose-reference-toolkit/tree/v0.1.3) |
| C3 | Legal code license | MIT; [LICENSE](../LICENSE) and [Licence.txt](../Licence.txt) contain identical terms. Third-party dependencies and supplied data retain their own rights. |
| C4 | Code versioning system | Git |
| C5 | Software languages, tools and services used | Python library and CLI; HTML, CSS and JavaScript browser demo; NumPy; optional FastAPI/Uvicorn server and MediaPipe/OpenCV extraction adapter; GitHub Actions CI. No hosted service is required to run the local toolkit. |
| C6 | Compilation requirements, operating environments and dependencies | Python >=3.10; NumPy >=1.26,<3. Build: setuptools >=77 and wheel. Exact optional dependency constraints are in [pyproject.toml](../pyproject.toml). The legacy video adapter is checked separately on Python 3.11 and requires supported platform wheels. Core CI targets Linux and Windows; workflow configuration is not evidence that a particular run passed. |
| C7 | Developer documentation/manual | [README](../README.md), [reproduction instructions](../REPRODUCE.md), [contracts](CONTRACTS.md), [method](METHOD.md), [limitations](LIMITATIONS.md) and [contribution guide](../CONTRIBUTING.md). |
| C8 | Support email for questions | No support email is declared in this repository. Use [GitHub Issues](https://github.com/ntthienphuc/pose-reference-toolkit/issues) for repository support. The manuscript must supply the author's actual corresponding/support email before submission. |

The public example data are generated synthetic motions. This version supplies engineering validation and does not establish accuracy on real signs, proficiency grading, educational benefit or independent reuse. See the [software paper evidence plan](SOFTWAREX_PLAN.md) for the remaining evidence.
