"""Optional blank-video extraction check: decoding/tracking gates, not sign accuracy."""
import argparse
import json
from pathlib import Path
import tempfile
import cv2
import numpy as np
from pose_reference.video import extract_video, NAMES, GROUPS
from pose_reference.pose import prepare_pose

parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args = parser.parse_args()
with tempfile.TemporaryDirectory() as directory:
    clip = Path(directory) / "blank.avi"
    writer = cv2.VideoWriter(str(clip), cv2.VideoWriter_fourcc(*"MJPG"), 20, (320,240))
    if not writer.isOpened():
        raise RuntimeError("Test codec unavailable")
    for _ in range(20):
        writer.write(np.zeros((240,320,3),dtype=np.uint8))
    writer.release()
    seq = extract_video(clip)
    assert seq.xy.shape == (10,49,2)
    assert len(set(NAMES)) == 49
    np.testing.assert_allclose(seq.timestamps_ms, np.arange(10)*100)
    tensor, quality = prepare_pose(seq,32,tuple(GROUPS))
    assert tensor is None and not quality["passed"]
    try:
        extract_video(Path(directory)/"missing.avi")
    except ValueError:
        unreadable = "rejected"
    else:
        raise AssertionError("Unreadable video accepted")
receipt = {"status":"passed","scope":"blank-video adapter engineering check, not actual sign tracking quality",
           "sampled_frames":10,"unique_joints":49,"tracking_gate":quality,"unreadable_video":unreadable}
Path(args.out).parent.mkdir(parents=True,exist_ok=True)
Path(args.out).write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
print("Video adapter passed: 10 frames, 49 unique joints; blank input fails tracking quality; unreadable input rejected")
