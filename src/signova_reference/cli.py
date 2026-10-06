"""Build, audit, calibrate, compare and serve reference-bank workflows."""
import argparse
import json
from pathlib import Path
import sys
from .bank import ReferenceBank, audit_manifest, build_bank
from .compare import ComparePolicy, compare
from .evaluation import calibrate, diagnostics, load_policy
from .pose import load_pose, strict_json, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(prog="signova-ref", description=__doc__)
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("demo", help="Generate a synthetic bank, policy, queries and receipts")
    p.add_argument("--out", required=True)
    p = sub.add_parser("audit", help="Check source manifests, duplicates and role/group overlap")
    p.add_argument("--manifest", required=True)
    p = sub.add_parser("build", help="Extract reference samples and build an immutable versioned bank")
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--target-len", type=int, default=32)
    p.add_argument("--required-groups", default="body,left_hand,right_hand")
    p = sub.add_parser("extract", help="Optional video-to-canonical-pose adapter")
    p.add_argument("--video", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--frame-stride", type=int, default=2)
    p.add_argument("--start-ms", type=float, default=0)
    p.add_argument("--end-ms", type=float)
    for command in ("inspect", "compare", "calibrate", "evaluate", "serve"):
        p = sub.add_parser(command)
        p.add_argument("--bank", required=True)
        if command in {"calibrate", "evaluate"}:
            p.add_argument("--manifest", required=True)
            p.add_argument("--out", required=True)
        if command in {"compare", "evaluate", "serve"}:
            p.add_argument("--policy")
        if command in {"compare", "calibrate"}:
            p.add_argument("--alignment", choices=("linear", "dtw"), default="linear")
        if command == "compare":
            p.add_argument("--pose", required=True)
            p.add_argument("--target", required=True)
            p.add_argument("--out")
        if command == "serve":
            p.add_argument("--host", default="127.0.0.1")
            p.add_argument("--port", type=int, default=8010)
            p.add_argument("--demo-root")
    args = parser.parse_args(argv)
    try:
        if getattr(args, "out", None) and Path(args.out).exists():
            raise ValueError("Output already exists; choose a new path")
        if args.command == "demo":
            from .demo import create_demo
            result = create_demo(args.out)
        elif args.command == "audit":
            _, result = audit_manifest(args.manifest)
        elif args.command == "build":
            result = build_bank(args.manifest, args.out, args.target_len, tuple(args.required_groups.split(",")))
        elif args.command == "extract":
            from .video import extract_video
            pose = extract_video(args.video, args.frame_stride, args.start_ms, args.end_ms)
            write_json(args.out, pose.to_dict())
            result = {"status": "extracted", "frames": len(pose.xy), "out": args.out,
                      "timing": "source frame index divided by FPS; exact VFR timing unsupported"}
        else:
            bank = ReferenceBank(args.bank)
            if args.command == "inspect":
                result = {"status": "valid", "bank_sha256": bank.digest, "profile": bank.profile,
                          "glosses": [{"gloss": g, "references": len(e["reference_ids"]), "medoid_reference_id": e["medoid_reference_id"]} for g, e in bank.entries.items()]}
            elif args.command == "calibrate":
                result = calibrate(args.manifest, bank, args.alignment)
                write_json(args.out, result)
            elif args.command == "evaluate":
                policy = load_policy(args.policy, bank) if args.policy else ComparePolicy()
                receipt = strict_json(Path(args.policy).read_text(encoding="utf-8")) if args.policy else None
                result = diagnostics(args.manifest, bank, "evaluation", policy, receipt)
                write_json(args.out, result)
            elif args.command == "compare":
                policy = load_policy(args.policy, bank) if args.policy else ComparePolicy(alignment=args.alignment)
                result = compare(load_pose(args.pose), bank, args.target, policy)
                if args.out:
                    write_json(args.out, result)
            else:
                import uvicorn
                from .server import create_app
                uvicorn.run(create_app(args.bank, args.policy, args.demo_root), host=args.host, port=args.port, workers=1)
                return 0
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, ImportError, RuntimeError, KeyError, TypeError) as error:
        failure = {"status": "reject", "stage": args.command, "error": str(error)}
        if args.command == "build" and not Path(str(args.out) + ".failure.json").exists():
            report_path = Path(str(args.out) + ".failure.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(report_path, failure)
        print(json.dumps(failure, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
