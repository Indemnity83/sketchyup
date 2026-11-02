"""Small deterministic terrazzo tile, injected into the model at build time."""

import random
import struct
import zlib


def texture_png():
    size = 256
    rng = random.Random(17)
    pixels = bytearray([221, 216, 200] * size * size)
    colors = [(174, 169, 151), (194, 187, 166), (239, 234, 216), (131, 150, 141)]
    for _ in range(1300):
        x, y = rng.randrange(size), rng.randrange(size)
        radius = rng.choice([1, 1, 1, 2, 3])
        color = bytes(rng.choice(colors))
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    offset = ((y + dy) % size * size + (x + dx) % size) * 3
                    pixels[offset : offset + 3] = color

    def chunk(kind, data):
        return (
            struct.pack("!I", len(data))
            + kind
            + data
            + struct.pack("!I", zlib.crc32(kind + data))
        )

    raw = b"".join(
        b"\0" + pixels[y * size * 3 : (y + 1) * size * 3] for y in range(size)
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!2I5B", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
