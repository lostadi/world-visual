#!/usr/bin/env python3
"""Verify the published capture without requiring Ostadix or a browser."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent


def verify():
    data = json.loads((ROOT / "capture.json").read_text())
    source = (ROOT / "world.O").read_bytes()
    assert hashlib.sha256(source).hexdigest() == data["source_sha256"], "source identity mismatch"
    result = data["result"]
    assert (result["world_count"], result["side"], result["steps"]) == (4, 64, 128)
    assert result["cell_updates"] == 2_097_152
    assert result["sqlite_score"] == 721_489_843_996
    assert len(result["worlds"]) == len(data["visuals"]) == 4
    expected_hashes = [
        "9ef06471ff562bb079bd9f6a4627afbf7aa39c27edf1283e9c49d6587682e227",
        "09698dc576f5375242fcf07cfd85e06c47c87220f72d72dce80df7ffa6053f2b",
        "6be406a939b8c431f2c0c8b9141dad8b7ba5a4a66433c94530246aabd7ca2491",
        "8bf03787ef457d9909a291b42cc577e73c0328b0c339292198de14bce7e3a0ac",
    ]
    expected_collisions = [65780, 66378, 66323, 65608]
    frame_count = 0
    for i, (world, visual) in enumerate(zip(result["worlds"], data["visuals"])):
        assert world["world"] == i and world["ticks"] == 128
        assert len(visual["frames"]) == len(visual["collisions"]) == 129
        assert visual["collisions"][0] == 0
        assert visual["collisions"] == sorted(visual["collisions"])
        assert visual["collisions"][-1] == world["collision_events"] == expected_collisions[i]
        for tick, encoded in enumerate(visual["frames"]):
            cells = bytes.fromhex(encoded)
            assert len(cells) == 4096 and all(c < 16 for c in cells), (i, tick, "cell encoding")
            particles = sum(c.bit_count() for c in cells)
            px = sum(bool(c & 1) - bool(c & 4) for c in cells)
            py = sum(bool(c & 2) - bool(c & 8) for c in cells)
            assert (particles, px, py) == (world["particles"], world["px"], world["py"]), (i, tick, "conservation")
            frame_count += 1
        assert hashlib.sha256(cells).hexdigest() == world["sha256"] == expected_hashes[i]
    template = (ROOT / "template.html").read_text()
    assert template.count("__WORLD_DATA__") == 1
    encoded = json.dumps(data, separators=(",", ":"))
    assert (ROOT / "index.html").read_text() == template.replace("__WORLD_DATA__", encoded), "page/capture mismatch"
    scripts = re.findall(r"<script>(.*?)</script>", template, re.S)
    assert len(scripts) == 1
    assert scripts[0].strip() == (ROOT / "dashboard.js").read_text().strip(), "dashboard source mismatch"
    print(f"PASS: {frame_count} frames; particle/momentum conservation; four oracle hashes; capture, source and page agree.")


if __name__ == "__main__":
    verify()
