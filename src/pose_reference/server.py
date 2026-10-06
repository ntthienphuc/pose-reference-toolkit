"""Small local web adapter over the same reference toolkit API."""
import asyncio
import importlib.util
from pathlib import Path
import tempfile
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from .bank import ReferenceBank
from .compare import ComparePolicy, compare
from .evaluation import load_policy
from .pose import PoseSequence, strict_json
from . import __version__


def create_app(bank_path, policy_path=None, demo_root=None):
    bank = ReferenceBank(bank_path)
    policy = load_policy(policy_path, bank) if policy_path else ComparePolicy()
    app = FastAPI(title="Pose Reference Toolkit", version=__version__)
    gate = asyncio.Semaphore(1)
    extraction = importlib.util.find_spec("mediapipe") is not None and importlib.util.find_spec("cv2") is not None

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return Path(__file__).with_name("web.html").read_text(encoding="utf-8")

    @app.get("/health")
    async def health():
        try:
            bank.assert_integrity()
        except (ValueError, OSError):
            return JSONResponse({"status": "invalid_bank"}, status_code=503)
        return {"status": "ready", "version": __version__, "bank_sha256": bank.digest, "video_extraction": extraction}

    @app.get("/bank")
    async def bank_info():
        return {"glosses": list(bank.entries), "contract": bank.profile["contract"], "required_groups": bank.profile["required_groups"],
                "target_len": bank.profile["target_len"], "policy": policy.__dict__}

    @app.get("/demo/{name}")
    async def fixture(name: str):
        if demo_root is None or name not in {"same", "wrong", "missing", "degenerate"}:
            raise HTTPException(404, "Fixture not available")
        return strict_json((Path(demo_root) / ("example_" + name + ".json")).read_text(encoding="utf-8"))

    @app.post("/compare")
    async def compare_pose(request: Request):
        # Bound the actual stream, not only Content-Length supplied by a client.
        raw = bytearray()
        async for block in request.stream():
            raw.extend(block)
            if len(raw) > 2_000_000:
                raise HTTPException(413, "Pose request exceeds 2 MB")
        try:
            document = strict_json(raw.decode("utf-8"))
            if not isinstance(document, dict) or set(document) != {"target", "pose"} or not isinstance(document["target"], str):
                raise ValueError("Expected exactly target and pose")
            seq = PoseSequence.from_dict(document["pose"])
            async with gate:
                return await asyncio.to_thread(compare, seq, bank, document["target"], policy)
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            return JSONResponse({"status": "reject", "score": None, "reasons": ["invalid_pose_request"], "error": str(error)}, status_code=400)

    @app.post("/compare-video")
    async def compare_video(target: str = Form(...), video: UploadFile = File(...)):
        try:
            if not extraction:
                raise HTTPException(503, "Install the extract extra to enable video input")
            async with gate:
                with tempfile.TemporaryDirectory(prefix="pose-reference-upload-") as directory:
                    path = Path(directory) / "clip.mp4"
                    total = 0
                    with path.open("wb") as stream:
                        while True:
                            chunk = await video.read(1_000_000)
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > 30_000_000:
                                raise HTTPException(413, "Video exceeds 30 MB")
                            stream.write(chunk)
                    from .video import extract_video
                    seq = await asyncio.to_thread(extract_video, path)
                    return await asyncio.to_thread(compare, seq, bank, target, policy)
        except (ValueError, RuntimeError, OSError, ImportError) as error:
            return JSONResponse({"status": "reject", "score": None, "reasons": ["video_extraction_error"], "error": str(error)}, status_code=400)
        finally:
            await video.close()
    return app
