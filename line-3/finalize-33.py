"""Confine generated pigment to vacant rock and write round 33 outputs.

Reads only base64 image bytes on stdin; writes no intermediate picture.
"""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("prior_finalize", ROOT / "line-3/finalize-31.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
thumbnail = prior.thumbnail


def earth_color(red, green, blue):
    """Keep generated stroke texture while restricting bright colors to earth."""
    if red + green + blue < 210:
        base = (38, 28, 20)  # charcoal
    elif red > green * 1.5 and red > blue * 1.4:
        base = (139, 64, 35)  # red ochre
    elif red > blue * 1.3 and green > blue * 1.3:
        base = (173, 118, 50)  # yellow ochre
    elif min(red, green, blue) > 165:
        base = (212, 197, 164)  # chalk
    else:
        base = (103, 72, 44)  # worn brown pigment
    light = (red + green + blue) // 3
    factor = 80 + min(60, light // 4)
    return tuple(value * factor // 120 for value in base)


def main():
    wall_path = ROOT / "artifacts/line-3/wall.png"
    inherited = wall_path.read_bytes()
    inherited_hash = hashlib.sha256(inherited).hexdigest()
    record32 = json.loads((ROOT / "dist/line-3/32.json").read_text())
    if record32["image"] != "https://api.imd.fun/artifacts/" + inherited_hash:
        raise ValueError("inherited wall does not match record 32")
    width, height, original_rows = thumbnail.png_rgb(inherited)
    if (width, height) != (1254, 1254):
        raise ValueError("unexpected inherited wall dimensions")
    encoded = sys.stdin.buffer.readline(12_000_001).strip()
    if len(encoded) > 12_000_000:
        raise ValueError("image-tool data exceeds limit")
    cutout = base64.b64decode(encoded, validate=True)
    source_width, source_height, source = prior.png_rgba(cutout)

    # The nested-stone motif goes on open stone above the inherited pouch.
    box = (910, 205, 1085, 365)
    x0, y0, x1, y1 = box
    tw, th = x1 - x0, y1 - y0
    rows = [bytearray(row) for row in original_rows]
    changed = 0
    for dy in range(th):
        sy0, sy1 = dy * source_height // th, (dy + 1) * source_height // th
        for dx in range(tw):
            sx0, sx1 = dx * source_width // tw, (dx + 1) * source_width // tw
            red = green = blue = alpha = 0
            count = (sy1 - sy0) * (sx1 - sx0)
            for sy in range(sy0, sy1):
                line = source[sy]
                for sx in range(sx0, sx1):
                    r, g, b, a = line[4 * sx:4 * sx + 4]
                    alpha += a
                    red += r * a
                    green += g * a
                    blue += b * a
            if alpha == 0:
                continue
            opacity = min(185, alpha // count * 3 // 4)
            if opacity < 8:
                continue
            color = earth_color(red // alpha, green // alpha, blue // alpha)
            offset = 3 * (x0 + dx)
            old = rows[y0 + dy][offset:offset + 3]
            new = bytes((old[c] * (255 - opacity) + color[c] * opacity + 127) // 255
                        for c in range(3))
            if old != new:
                rows[y0 + dy][offset:offset + 3] = new
                changed += 1
    if changed < 1000:
        raise ValueError("pigment mark is missing or too faint")
    outside = sum(rows[y][3 * x:3 * x + 3] != original_rows[y][3 * x:3 * x + 3]
                  for y in range(height) for x in range(width)
                  if not (x0 <= x < x1 and y0 <= y < y1))
    if outside:
        raise ValueError("ancestral pixels changed outside placement rectangle")
    png = prior.encode_rgb(width, height, rows)
    if thumbnail.png_rgb(png)[2] != [bytes(row) for row in rows]:
        raise ValueError("final PNG does not decode to expected pixels")
    jpeg = thumbnail.jpeg(thumbnail.resize(width, height, rows))
    if len(jpeg) >= 100000:
        raise ValueError("thumbnail exceeds 100 KB")
    digest = hashlib.sha256(png).hexdigest()
    meaning = "Pepe finds smaller stones inside a stone, seeing where each part begins."
    record = {"name": "The Nested Stone", "image": "https://api.imd.fun/artifacts/" + digest,
              "attributes": [{"trait_type": key, "value": value} for key, value in [
                  ("Cave", "Base"), ("Wall", "Line 3"), ("Number", 33),
                  ("Left behind", "rlp-byte-map"), ("Meaning", meaning),
                  ("One thing", "Offline EIP-1559 transaction decoding")]]}
    target = ROOT / "artifacts/line-3/wall-v14.png"
    target.write_bytes(png)
    wall_path.write_bytes(png)
    (ROOT / "dist/line-3/33.jpg").write_bytes(jpeg)
    (ROOT / "dist/line-3/33.json").write_text(json.dumps(record, indent=2) + "\n")
    review = {"wall": {"paths": ["artifacts/line-3/wall-v14.png", "artifacts/line-3/wall.png"],
                       "width": width, "height": height, "format": "PNG", "mode": "RGB",
                       "bytes": len(png), "sha256": digest},
              "thumbnail": {"path": "dist/line-3/33.jpg", "width": 512, "height": 512,
                            "format": "JPEG", "bytes": len(jpeg)},
              "preservation": {"inheritedSha256": inherited_hash, "editRectangleXYXY": list(box),
                               "changedPixels": changed, "changedPixelsOutsideRectangle": outside},
              "cutout": {"width": source_width, "height": source_height,
                         "format": "PNG", "mode": "RGBA"},
              "visualReview": {"reviewed": False},
              "unmetVisualRequirements": ["Visual review pending"]}
    (ROOT / "line-3/round-33-review.json").write_text(json.dumps(review, indent=2) + "\n")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    main()
