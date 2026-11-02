"""Original shared garden and furnishing geometry for the Solstice Court study.

Every surface is made with public face/push-pull commands. Repeated plants,
joinery and furniture stay editable shared definitions rather than imported meshes.
"""

import json
import math
import subprocess

TAU = math.tau


def cylinder(b, name, x, y, z, radius, height, material, sides=16):
    body = b.face(
        name,
        [
            [
                x + radius * math.cos(i * TAU / sides),
                y + radius * math.sin(i * TAU / sides),
                z,
            ]
            for i in range(sides)
        ],
    )
    b.add("geometry.push_pull", body=body, face=str(sides + 1), distance=height)
    b.paint(body, material)
    return body


def lathe(b, name, rings, mat, sides=12, center=(0, 0), ribs=False):
    """Faceted surface of revolution; rings are (radius, height)."""
    parts = []
    for level in range(len(rings) - 1):
        for i in range(sides):
            points = []
            for j, k in [
                (i, level),
                (i + 1, level),
                (i + 1, level + 1),
                (i, level + 1),
            ]:
                r, z = rings[k]
                r *= 1.10 if ribs and j % 2 == 0 else 1
                a = j * TAU / sides
                points.append(
                    [center[0] + r * math.cos(a), center[1] + r * math.sin(a), z]
                )
            parts.append(b.face(name, points, mat))
    return parts


def blob(b, name, x, y, z, radius, height, mat, sides=10):
    return lathe(
        b,
        name,
        [
            (radius * 0.12, z - height * 0.45),
            (radius * 0.8, z - height * 0.28),
            (radius, z),
            (radius * 0.7, z + height * 0.35),
            (radius * 0.08, z + height * 0.5),
        ],
        mat,
        sides,
        (x, y),
    )


def place(b, name, parts, locations, tag="Landscape"):
    grounded = {
        "Stepping stones",
        "Garden agave",
        "Barrel cactus",
        "Low garden shrub",
        "Ornamental grass",
        "Garden boulder",
        "Garden shade tree",
        "Garden dining table",
        "Garden dining chair",
    }
    if name in grounded:
        meta = json.loads(
            subprocess.check_output(
                [
                    "sketchyup-cli",
                    "--input",
                    str(b.model),
                    "--inspect",
                    "document.describe",
                ],
                timeout=30,
            )
        )
        request = {
            "apiVersion": 1,
            "documentId": meta["documentId"],
            "expectedRevision": meta["revision"],
            "query": "terrain.elevation_at",
            "body": b.terrain,
            "points": [list(p[:2]) for p in locations],
        }
        path = b.out / "grounding-query.json"
        path.write_text(json.dumps(request))
        result = json.loads(
            subprocess.check_output(
                ["sketchyup-cli", "--input", str(b.model), "--inspect-file", str(path)],
                timeout=30,
            )
        )
        samples = result["data"]["points"]
        assert all(p["found"] for p in samples), result
        locations = [
            (*p[:2], sample["elevation"] + 0.035, *p[3:])
            for p, sample in zip(locations, samples, strict=True)
        ]
    comp = b.component(name, parts, tag)
    b.move(comp[0], locations[0][:3])
    for p in locations[1:]:
        b.instance(comp, p[:3], p[3] if len(p) > 3 else 0)
    b.flush(name.lower().replace(" ", "-"))
    return comp


def architecture(b):
    for name, x, y, z, w, d in [
        ("Living", -0.9, -1.05, 3.65, 12.4, 9.65),
        ("Sleeping", 10.6, -2.75, 3.32, 6.15, 11.35),
        ("Carport", -6.1, 2, 3.12, 6.1, 6.5),
    ]:
        for xx, yy, ww, dd in [
            (x, y, w, 0.06),
            (x, y + d - 0.06, w, 0.06),
            (x, y, 0.06, d),
            (x + w - 0.06, y, 0.06, d),
        ]:
            b.box(
                name + " white fascia", xx, yy, z + 0.05, ww, dd, 0.23, "White", "Roof"
            )
    outrigger = [b.box("Exposed walnut beam end", 0, 0, 0, 0.14, 0.65, 0.24, "Walnut")]
    place(
        b,
        "Walnut outriggers",
        outrigger,
        [(x, -1.5, 3.39) for x in [0.1, 1.9, 3.7, 5.5, 7.3, 9.1, 10.9]],
        "Roof",
    )
    for y in [0.06, 0.12, 0.19]:
        b.box(
            "Sliding door sill track",
            0.24,
            y,
            0.545,
            10.4,
            0.018,
            0.018,
            "Bronze",
            "Glazing",
        )
        b.box(
            "Sliding door head track",
            0.24,
            y,
            3.26,
            10.4,
            0.018,
            0.025,
            "Bronze",
            "Glazing",
        )
    for x in [0.25, 3.75, 7.35]:
        b.box(
            "Clerestory top rail", x, 0.10, 3.59, 3.32, 0.09, 0.04, "Bronze", "Glazing"
        )
        for xx in [x + 0.82, x + 2.48]:
            b.box(
                "Clerestory intermediate frame",
                xx,
                0.10,
                3.34,
                0.025,
                0.09,
                0.27,
                "Bronze",
                "Glazing",
            )
        for xx in [x + 1.55, x + 1.75]:
            b.box(
                "Sliding pull handle",
                xx,
                0.06,
                1.5,
                0.025,
                0.05,
                0.3,
                "Bronze",
                "Glazing",
            )
    # Entry occupies part of the west glass bay; opaque teal leaf and clear sidelight.
    b.box("Teal entry door", 0.065, 5.35, 0.55, 0.09, 1.05, 2.4, "Teal", "Structure")
    b.box("Entry pull", -0.01, 5.48, 1.48, 0.06, 0.03, 0.4, "Bronze", "Structure")
    for yy in [5.30, 6.42, 7.28]:
        b.box("Entry jamb", 0.03, yy, 0.54, 0.14, 0.045, 2.45, "Bronze", "Glazing")
    b.box("Entry door head", 0.03, 5.3, 2.95, 0.14, 2.02, 0.06, "Bronze", "Glazing")
    b.box("Entry sidelight", 0.075, 6.47, 0.58, 0.02, 0.8, 2.35, "Glass", "Glazing")
    for i in range(4):
        x = -5.65 + i * 0.85
        b.box("Carport storage", x, 7.5, 0.07, 0.8, 0.45, 1.85, "Walnut", "Structure")
        b.box(
            "Storage pull", x + 0.68, 7.45, 0.9, 0.02, 0.05, 0.22, "Bronze", "Structure"
        )
    sconce = [
        b.box("Sconce plate", 0, 0, 0, 0.18, 0.06, 0.35, "Bronze"),
        cylinder(b, "Opal sconce", 0.09, -0.08, 0.06, 0.075, 0.24, "Linen"),
    ]
    place(
        b,
        "Exterior sconces",
        sconce,
        [(15.55, -2.03, 2.0), (11.04, -2.03, 2.0), (-0.2, 7.68, 2.0)],
        "Structure",
    )
    for i in range(3):
        b.box(
            "Pool submerged step",
            1.02,
            -3.75 - i * 0.36,
            0.04 - i * 0.075,
            1.65,
            0.36,
            0.075,
            "Ivory",
            "Landscape",
        )
    # Expressed paving and coping joints, in the model rather than render effects.
    joint = [b.box("Coping joint", 0, 0, 0, 0.014, 0.20, 0.002, "Bronze")]
    place(
        b,
        "Coping joints",
        joint,
        [(x, -7.5, 0.381) for x in range(1, 10)]
        + [(x, -3.2, 0.381) for x in range(1, 10)],
    )
    b.flush("architectural-detail")


def interiors(b):
    stool = [
        cylinder(b, "Upholstered stool seat", 0, 0, 0.68, 0.23, 0.09, "Mustard", 20)
    ]
    for x in [-0.15, 0.15]:
        for y in [-0.15, 0.15]:
            stool.append(b.box("Stool leg", x, y, 0, 0.035, 0.035, 0.69, "Walnut"))
    stool.append(
        b.box("Stool footrest", -0.15, -0.16, 0.23, 0.34, 0.025, 0.025, "Bronze")
    )
    place(
        b,
        "Island bar stool",
        stool,
        [(8.05, 3.93, 0.54), (8.8, 3.93, 0.54), (9.55, 3.93, 0.54)],
        "Furniture",
    )
    shade = lathe(
        b, "Pendant shade", [(0.32, 0), (0.27, 0.14), (0.08, 0.28)], "Mustard", 20
    )
    shade.append(cylinder(b, "Pendant diffuser", 0, 0, -0.01, 0.30, 0.015, "Linen", 20))
    shade.append(cylinder(b, "Pendant cord", 0, 0, 0.28, 0.012, 0.90, "Bronze", 8))
    # Tag hanging fixtures with Roof, so the cutaway and plan stay readable.
    place(b, "Island pendant", shade, [(8.05, 4.75, 2.35), (9.4, 4.75, 2.35)], "Roof")
    lamp = [
        cylinder(b, "Lamp base", 0, 0, 0, 0.25, 0.035, "Bronze", 20),
        cylinder(b, "Lamp stem", 0, 0, 0.035, 0.025, 1.40, "Bronze", 12),
    ]
    lamp += lathe(b, "Linen floor shade", [(0.33, 1.2), (0.24, 1.68)], "Linen", 20)
    place(b, "Floor lamp", lamp, [(4.8, 5.8, 0.54), (14.95, 6.2, 0.54)], "Furniture")
    for y in [-0.9, 4]:
        b.box(
            "Bedroom rug", 11.55, y - 0.25, 0.545, 3.2, 2.85, 0.015, "Wool", "Furniture"
        )
        b.box(
            "Walnut headboard",
            11.95,
            y + 2.02,
            0.78,
            2.5,
            0.09,
            0.65,
            "Walnut",
            "Furniture",
        )
        b.box(
            "Bedside table",
            14.6,
            y + 1.5,
            0.54,
            0.55,
            0.55,
            0.48,
            "Walnut",
            "Furniture",
        )
    for x in [5.1, 6.3]:
        b.box(
            "Art walnut frame", x, 7.72, 1.85, 0.9, 0.045, 1.15, "Walnut", "Furniture"
        )
        b.box(
            "Art canvas", x + 0.04, 7.68, 1.89, 0.82, 0.025, 1.07, "Linen", "Furniture"
        )
        b.box(
            "Art teal field",
            x + 0.11,
            7.65,
            1.97,
            0.30,
            0.02,
            0.87,
            "Teal",
            "Furniture",
        )
        b.box(
            "Art ochre field",
            x + 0.45,
            7.65,
            2.40,
            0.29,
            0.02,
            0.40,
            "Ochre",
            "Furniture",
        )
    # Small glazed ceramics and leaves, placed at the hearth and credenza ends.
    plant = lathe(b, "Indoor pot", [(0.15, 0), (0.22, 0.32), (0.22, 0.36)], "Clay", 16)
    for i in range(9):
        a = i * TAU / 9
        tip = [0.42 * math.cos(a), 0.42 * math.sin(a), 1.10]
        for side in [-1, 1]:
            plant.append(
                b.face(
                    "Indoor leaf",
                    [
                        [0, 0, 0.32],
                        [
                            0.28 * math.cos(a + side * 0.2),
                            0.28 * math.sin(a + side * 0.2),
                            0.65,
                        ],
                        tip,
                    ],
                    "Leaf",
                )
            )
    place(
        b,
        "Indoor plant",
        plant,
        [(0.65, 5.95, 0.54), (6.4, 7.23, 1.33), (15.15, 0.6, 0.54)],
        "Furniture",
    )
    b.flush("interior-detail")


def outdoor(b):
    # Round unbranded garden dining set on the east gravel court.
    table = [
        cylinder(b, "Garden table top", 0, 0, 0.72, 0.82, 0.065, "Ivory", 32),
        cylinder(b, "Garden table stem", 0, 0, 0.06, 0.10, 0.66, "Bronze", 12),
        cylinder(b, "Garden table foot", 0, 0, 0, 0.43, 0.06, "Bronze", 20),
    ]
    place(b, "Garden dining table", table, [(14.3, -6.2, 0.02)], "Landscape")
    parts = [b.box("Garden chair seat", -0.24, -0.22, 0.42, 0.48, 0.44, 0.06, "Teal")]
    for x in [-0.2, 0.17]:
        for y in [-0.18, 0.16]:
            parts.append(b.box("Garden chair leg", x, y, 0, 0.03, 0.03, 0.43, "Bronze"))
    for i in range(6):
        parts.append(
            b.box(
                "Chair back slat",
                -0.23 + i * 0.08,
                0.19,
                0.5,
                0.04,
                0.035,
                0.36,
                "Walnut",
            )
        )
    place(
        b,
        "Garden dining chair",
        parts,
        [
            (14.3, -5.03, 0.02),
            (15.47, -6.2, 0.02, -90),
            (14.3, -7.37, 0.02, 180),
            (13.13, -6.2, 0.02, 90),
        ],
    )
    umbrella = [
        cylinder(b, "Umbrella foot", 0, 0, 0, 0.33, 0.08, "Concrete", 20),
        cylinder(b, "Umbrella pole", 0, 0, 0.08, 0.035, 2.65, "Walnut", 12),
    ]
    for i in range(16):
        a = i * TAU / 16
        c = (i + 1) * TAU / 16
        umbrella.append(
            b.face(
                "Canvas umbrella panel",
                [
                    [0, 0, 2.75],
                    [1.45 * math.cos(a), 1.45 * math.sin(a), 2.18],
                    [1.45 * math.cos(c), 1.45 * math.sin(c), 2.18],
                ],
                "Linen" if i % 2 else "Mustard",
            )
        )
    place(b, "Terrace umbrella", umbrella, [(11.2, -4.05, 0.28)])
    pot = lathe(
        b,
        "Terrace planter",
        [(0.30, 0), (0.42, 0.5), (0.42, 0.55), (0.36, 0.55), (0.36, 0.49)],
        "Clay",
        20,
    )
    pot.append(cylinder(b, "Planter gravel", 0, 0, 0.48, 0.35, 0.01, "Gravel", 20))
    place(
        b,
        "Terrace pots",
        pot,
        [(-0.55, -2.65, 0.28), (10.6, -2.6, 0.28), (15.25, -2.5, 0.05)],
    )
    b.flush("outdoor-detail")


def garden(b, terrain):
    # Ground-cover polygons follow the actual terrain, including its graded apron.
    beds = [
        (
            "West gravel garden",
            [[-8.9, -11.9], [-1.2, -11.9], [-1.2, 1.6], [-8.9, 1.6]],
        ),
        (
            "East gravel garden",
            [
                [12.1, -11.9],
                [20.9, -11.9],
                [20.9, 8.6],
                [16.8, 8.6],
                [16.8, -2.9],
                [12.1, -2.9],
            ],
        ),
        ("North gravel garden", [[-3.5, 8.8], [20.9, 8.8], [20.9, 12.9], [-3.5, 12.9]]),
    ]
    for name, polygon in beds:
        body = b.face(name + " source", [[x, y, 3] for x, y in polygon], "Gravel")
        b.hide.append(body)
        b.add(
            "terrain.drape",
            terrain=terrain,
            mode="overlay",
            faces=[{"body": body, "face": str(len(polygon) + 1)}],
            lift=0.035,
        )
        b.flush("gravel-drape")
        b.sync_ids()
    desc = json.loads(
        subprocess.check_output(
            ["sketchyup-cli", "--input", str(b.model), "--query", "document.describe"],
            timeout=30,
        )
    )
    # Paint each new drape tile explicitly: containers do not inherit a material.
    drapes = [x for x in desc["bodies"] if x["name"] == "Drape" and x["parent"] == "0"]
    for drape in drapes[-3:]:
        b.tag(drape["id"], "Landscape")
        for tile in desc["bodies"]:
            if tile["parent"] == drape["id"]:
                b.paint(tile["id"], "Gravel")
    # A low perimeter and planted borders turn the rectangular extent into a garden.
    for x, y, w, d, z in [
        (-8.9, -11.8, 29.8, 0.20, -0.55),
        (-8.9, -11.8, 0.20, 13.5, -0.55),
        (20.7, -11.8, 0.20, 24.6, -0.55),
        (-3.4, 12.6, 24.3, 0.20, 0.7),
    ]:
        b.box("Low garden boundary", x, y, z, w, d, 0.9, "Concrete", "Landscape")
        b.box(
            "Garden wall cap",
            x - 0.03,
            y - 0.03,
            z + 0.9,
            w + 0.06,
            d + 0.06,
            0.06,
            "Ivory",
            "Landscape",
        )
    stone = [b.box("Concrete stepping slab", 0, 0, 0, 0.9, 0.60, 0.10, "Concrete")]
    place(
        b,
        "Stepping stones",
        stone,
        [(-1.9, -9.7 + i * 0.83, -0.12) for i in range(13)]
        + [(x, -9.5, -0.15) for x in [0, 1.2, 2.4, 3.6, 4.8, 6, 7.2, 8.4, 9.6, 10.8]],
    )
    # Folded lance leaves: two face planes per leaf with a pronounced ridge.
    agave = []
    for i in range(24):
        a = i * TAU / 9
        length = 0.60 if i < 9 else 0.90 if i < 18 else 0.42
        z = 0.45 if i < 18 else 0.92
        p = [0, 0, 0.05]
        tip = [length * math.cos(a), length * math.sin(a), z]
        mid = [length * 0.45 * math.cos(a), length * 0.45 * math.sin(a), 0.50]
        for side in [-1, 1]:
            edge = [
                mid[0] + side * 0.13 * math.sin(a),
                mid[1] - side * 0.13 * math.cos(a),
                mid[2] - 0.13,
            ]
            for triangle in [[p, edge, mid], [mid, edge, tip]]:
                agave.append(
                    b.face(
                        "Folded agave leaf", triangle, "Sage" if side == 1 else "Leaf"
                    )
                )
    positions = [
        (-6.6, -9.5),
        (-4.5, -8.5),
        (-6.7, -5),
        (-5.5, -1),
        (-3.5, 0.3),
        (14, -9.8),
        (16, -9),
        (18.5, -7),
        (18, -3),
        (19, 1),
        (18, 5),
        (18, 10),
        (12, 11),
        (6, 11),
    ]
    place(
        b,
        "Garden agave",
        agave,
        [(x, y, -0.05 if y < 8 else 0.6, i * 29) for i, (x, y) in enumerate(positions)],
    )
    cactus = lathe(
        b,
        "Ribbed barrel cactus",
        [(0.14, 0), (0.37, 0.18), (0.43, 0.48), (0.33, 0.76), (0.08, 0.88)],
        "Sage",
        24,
        ribs=True,
    )
    cactus += lathe(b, "Golden cactus crown", [(0.08, 0.88), (0.02, 0.91)], "Ochre", 12)
    place(
        b,
        "Barrel cactus",
        cactus,
        [
            (x, y, -0.08, i * 17)
            for i, (x, y) in enumerate(
                [
                    (-7, -8),
                    (-5.6, -7.5),
                    (-6, -3),
                    (-3.7, -10),
                    (14, -10.5),
                    (16.7, -7.8),
                    (18.8, -5),
                    (19.5, -1.5),
                    (17.7, 3.2),
                    (19.5, 6.3),
                    (13.7, -3.3),
                    (15.7, -4),
                ]
            )
        ],
    )
    shrub = []
    for x, y, z, r, h in [
        (-0.28, 0, 0.38, 0.45, 0.6),
        (0.3, 0.12, 0.46, 0.50, 0.65),
        (0, -0.25, 0.35, 0.42, 0.52),
    ]:
        shrub += blob(b, "Shrub foliage", x, y, z, r, h, "Leaf" if x < 0 else "Sage")
    locations = [
        (-7.5, -10.6),
        (-5, -10.6),
        (-2.8, -10.6),
        (-7.6, -6.3),
        (-7.6, -2),
        (-4.1, 1),
        (13, -10.6),
        (15.6, -10.6),
        (18.3, -10.5),
        (19.5, -8),
        (19.3, -3.3),
        (19.3, 2.5),
        (19.3, 7),
        (19, 11.5),
        (16, 11.6),
        (13, 11.6),
        (10, 11.6),
        (7, 11.6),
        (3, 11.6),
        (0, 11.6),
    ]
    place(
        b,
        "Low garden shrub",
        shrub,
        [(x, y, -0.10 if y < 8 else 0.7, i * 37) for i, (x, y) in enumerate(locations)],
    )
    grass = []
    for i in range(28):
        a = i * 2.39996
        r = 0.16 + (i % 5) * 0.04
        h = 0.45 + (i % 7) * 0.055
        base = [r * 0.4 * math.cos(a), r * 0.4 * math.sin(a), 0]
        mid = [r * math.cos(a), r * math.sin(a), h * 0.65]
        tip = [r * 1.8 * math.cos(a), r * 1.8 * math.sin(a), h]
        grass.append(
            b.face(
                "Arching grass blade",
                [
                    base,
                    [
                        mid[0] - 0.025 * math.sin(a),
                        mid[1] + 0.025 * math.cos(a),
                        mid[2],
                    ],
                    tip,
                ],
                "Sage" if i % 3 else "Ochre",
            )
        )
        grass.append(
            b.face(
                "Grass blade fold",
                [
                    base,
                    tip,
                    [
                        mid[0] + 0.025 * math.sin(a),
                        mid[1] - 0.025 * math.cos(a),
                        mid[2],
                    ],
                ],
                "Leaf",
            )
        )
    positions = [(-2.6, -10.8 + i * 0.85, -0.2) for i in range(13)] + [
        (12.5 + i * 0.85, -10.8, -0.2) for i in range(9)
    ]
    positions += [(19.8, -9 + i * 0.85, -0.05) for i in range(18)] + [
        (4 + i * 0.9, 12, 0.7) for i in range(12)
    ]
    place(b, "Ornamental grass", grass, positions)
    boulder = blob(b, "Faceted boulder", 0, 0, 0.28, 0.68, 0.65, "Concrete", 9)
    place(
        b,
        "Garden boulder",
        boulder,
        [
            (-5.5, -9, -0.05),
            (-7, -4, -0.1),
            (17.5, -8.5, -0.1),
            (19, 4.8, 0.1),
            (17, 10.7, 0.7),
        ],
    )
    # Two broad shade trees behind the pavilion; palms remain in the original model.
    tree = [cylinder(b, "Shade tree trunk", 0, 0, 0, 0.19, 3.4, "Walnut", 12)]
    for x, y, z, r, h in [
        (-1, 0, 3.8, 1.5, 1.65),
        (1, 0.2, 4.1, 1.6, 1.9),
        (0, -1, 4.4, 1.5, 1.8),
        (0, 1, 4.5, 1.6, 1.9),
        (0, 0, 5.3, 1.5, 1.4),
    ]:
        tree += blob(b, "Shade canopy", x, y, z, r, h, "Leaf" if x < 0 else "Sage", 12)
    place(b, "Garden shade tree", tree, [(1, 10.6, 0.6), (18.5, 8.5, 0.6)])
    b.flush("landscape-detail")


def add_details(b, terrain):
    b.terrain = terrain
    architecture(b)
    interiors(b)
    outdoor(b)
    garden(b, terrain)
