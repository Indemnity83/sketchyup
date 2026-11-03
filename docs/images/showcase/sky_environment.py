"""Write a small original 2:1 scene-linear Radiance RGBE garden sky.

Clear blue zenith, warm late-afternoon horizon, muted ground. The panorama has no
sun disk: the document's solar study supplies the directional light and shadows.
Generated at render time; no binary environment is committed.
"""

import math
import sys
from itertools import pairwise
from pathlib import Path


def write_sky(path):
    width, height = 512, 256
    stops = [
        (0, (0.10, 0.28, 0.65)),
        (0.45, (0.32, 0.52, 0.78)),
        (0.495, (0.85, 0.69, 0.46)),
        (0.54, (0.50, 0.43, 0.31)),
        (1, (0.18, 0.22, 0.15)),
    ]
    data = bytearray(
        f"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y {height} +X {width}\n".encode()
    )
    for y in range(height):
        t = y / (height - 1)
        for (a, ca), (z, cz) in pairwise(stops):
            if a <= t <= z:
                w = (t - a) / (z - a)
                w = w * w * (3 - 2 * w)
                rgb = [(1 - w) * ca[i] + w * cz[i] for i in range(3)]
                mantissa, exponent = math.frexp(max(rgb))
                scale = mantissa * 256 / max(rgb)
                pixel = bytes([int(c * scale) for c in rgb] + [exponent + 128])
                data.extend(pixel * width)
                break
    Path(path).write_bytes(data)


if __name__ == "__main__":
    write_sky(sys.argv[1])
