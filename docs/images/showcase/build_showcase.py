#!/usr/bin/env python3
"""Build the original Solstice Court study using only public SketchyUp commands.

Emits readable phase batches and executes each with sketchyup-cli. Textures are
injected from repository resources; no generated geometry or base64 is committed.
Coordinates are metres in an invented local site. No external model inputs.
"""

import argparse
import base64
import json
import math
import resource
import subprocess
import time
from pathlib import Path

from detail_showcase import add_details
from terrazzo_texture import texture_png

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))

ROOT = Path(__file__).resolve().parents[3]


class Builder:
    def __init__(self, out):
        self.out = out
        out.mkdir(parents=True, exist_ok=True)
        self.commands = []
        self.body = self.material = self.definition = 0
        self.phase = 0
        self.model = None
        self.tags = {}
        self.mats = {}
        self.hide = []
        self.roofs = []
        self.annotations = []
        self.front_posts = []
        self.section_hide = []
        self.start = time.monotonic()

    def add(self, command, **kw):
        self.commands.append(dict(command=command, **kw))

    def new(self):
        self.body += 1
        return str(self.body)

    def flush(self, name):
        if not self.commands:
            return
        if len(self.commands) > 100:
            pending = self.commands
            for start in range(0, len(pending), 100):
                self.commands = pending[start : start + 100]
                self.flush(name + f"-{start // 100 + 1}")
            return
        self.phase += 1
        stem = f"{self.phase:02d}-{name}"
        path = self.out / (stem + ".json")
        path.write_text(json.dumps(self.commands, indent=2) + "\n")
        model = self.out / (stem + ".sketchyup")
        args = ["sketchyup-cli", "--script", str(path), "--output", str(model)]
        if self.model:
            args += ["--input", str(self.model)]
        with (self.out / (stem + ".log")).open("w") as log:
            result = subprocess.run(
                args, stdout=log, stderr=subprocess.STDOUT, timeout=300, check=False
            )
        if result.returncode:
            raise RuntimeError(
                f"{stem}: {(self.out / (stem + '.log')).read_text()[-7000:]}"
            )
        self.model = model
        self.commands = []
        print(stem, f"{time.monotonic() - self.start:.1f}s", flush=True)

    def sync_ids(self):
        desc = json.loads(
            subprocess.check_output(
                [
                    "sketchyup-cli",
                    "--input",
                    str(self.model),
                    "--query",
                    "document.describe",
                ],
                timeout=30,
            )
        )
        self.body = max(int(x["id"]) for x in desc["bodies"])

    def paint(self, body, mat):
        self.add("material.assign", body=body, material=self.mats[mat], side="both")

    def tag(self, body, tag):
        self.add("tag.assign", body=body, tag=self.tags[tag])

    def face(self, name, points, mat=None, holes=None):
        body = self.new()
        self.add("geometry.face", name=name, loops=[points] + (holes or []))
        if mat:
            self.paint(body, mat)
        return body

    def box(self, name, x, y, z, w, d, h, mat, tag=None):
        body = self.face(
            name, [[x, y, z], [x + w, y, z], [x + w, y + d, z], [x, y + d, z]]
        )
        self.add("geometry.push_pull", body=body, face="5", distance=h)
        self.paint(body, mat)
        if tag:
            self.tag(body, tag)
        return body

    def group(self, name, members, tag=None):
        body = self.new()
        self.add("group.create", name=name, members=members)
        if tag:
            self.tag(body, tag)
        return body

    def component(self, name, members, tag):
        body = self.group(name, members, tag)
        self.definition += 1
        self.add("component.create", body=body, name=name)
        return body, str(self.definition), len(members) + 1, tag

    def move(self, body, xyz):
        self.add("geometry.translate", body=body, delta=xyz)

    def instance(self, comp, xyz, angle=0, mirror=False):
        _, definition, count, tag = comp
        a = math.radians(angle)
        c = math.cos(a)
        s = math.sin(a)
        m = -1 if mirror else 1
        body = self.new()
        self.body += count - 1
        self.add(
            "component.instance",
            definition=definition,
            matrix=[m * c, m * s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, *xyz, 1],
        )
        self.tag(body, tag)
        return body

    def wire(self, a, b, name="Reference"):
        body = self.new()
        self.add("geometry.wire", body="0", start=a, end=b)
        self.add("scene.rename", body=body, name=name)
        return body

    def library(self, source, xyz, tag):
        """Rebase the repository assembly commands, including canonical members."""
        data = json.loads(
            (ROOT / "resources/assemblies" / (source + ".json")).read_text()
        )
        offset = self.body
        mo = self.material
        de = self.definition

        def remap(v, key=""):
            if isinstance(v, dict):
                return {k: remap(w, k) for k, w in v.items()}
            if isinstance(v, list):
                return [remap(w, "body" if key == "members" else key) for w in v]
            if isinstance(v, str) and v.isdigit() and v != "0":
                if key in ("body", "member"):
                    return str(int(v) + offset)
                if key == "definition":
                    return str(int(v) + de)
                if key == "material":
                    return str(int(v) + mo)
            return v

        commands = remap(data["commands"])
        root = next(c["body"] for c in commands if c["command"] == "component.create")
        self.commands.extend(commands)
        self.move(root, xyz)
        self.tag(root, tag)
        self.flush(source)
        desc = json.loads(
            subprocess.check_output(
                [
                    "sketchyup-cli",
                    "--input",
                    str(self.model),
                    "--query",
                    "document.describe",
                ],
                timeout=30,
            )
        )
        self.body = max(int(b["id"]) for b in desc["bodies"])
        self.definition = max(int(d["id"]) for d in desc["definitions"])
        self.material += sum(c["command"] == "material.create" for c in commands)
        return (
            root,
            str(self.definition),
            next(
                d["members"]
                for d in desc["definitions"]
                if d["id"] == str(self.definition)
            ),
            tag,
        )


def build(out):
    b = Builder(out)
    style = {
        "mode": "textured",
        "background": [0.93, 0.94, 0.92],
        "ground": [0.8, 0.79, 0.72],
        "front": [0.86, 0.85, 0.8],
        "back": [0.65, 0.68, 0.67],
        "groundVisible": False,
        "groundHeight": 0,
        "gridVisible": False,
        "axesVisible": False,
        "edgesVisible": True,
        "edge": [0.23, 0.26, 0.24],
        "profiles": False,
        "profileWidth": 1,
        "xrayOpacity": 0.25,
    }
    solar = {
        "algorithm": "noaa-meeus-geometric-v1",
        "enabled": True,
        "shadows": True,
        "latitude": 32,
        "longitude": -110,
        "northDegrees": 0,
        "year": 2026,
        "month": 4,
        "day": 15,
        "hour": 16,
        "minute": 30,
        "second": 0,
        "utcOffsetMinutes": -420,
    }
    b.add("document.style", style=style)
    b.add("document.solar", solar=solar)
    for i, (name, parent, folder) in enumerate(
        [
            ("Architecture", "0", True),
            ("Structure", "1", False),
            ("Roof", "1", False),
            ("Glazing", "1", False),
            ("Furniture", "0", False),
            ("Landscape", "0", False),
            ("Annotation", "0", False),
        ],
        1,
    ):
        b.add("tag.create", name=name, parent=parent, folder=folder)
        b.tags[name] = str(i)
    textures = [
        ("Walnut", "wood-dark-oak", 2),
        ("Stone", "stone-rubble-wall", 2),
        ("Gravel", "gravel", 3),
        ("Grass", "grass", 3),
        ("Asphalt", "asphalt", 3),
        ("Metal", "metal-corrugated", 1),
        ("Wool", "fabric-wool-herringbone", 1),
    ]
    for i, (name, file, size) in enumerate(textures, 1):
        b.add(
            "asset.import",
            name=file + ".jpg",
            mediaType="image/jpeg",
            data=base64.b64encode(
                (ROOT / "resources/textures" / (file + ".jpg")).read_bytes()
            ).decode(),
        )
        b.material += 1
        b.mats[name] = str(b.material)
        b.add(
            "material.create",
            name=name,
            color=[0.62, 1, 0.65] if name == "Grass" else [1, 1, 1],
            asset=str(i),
            textureSize={"width": size, "height": size},
        )
    b.add(
        "asset.import",
        name="court-terrazzo.png",
        mediaType="image/png",
        data=base64.b64encode(texture_png()).decode(),
    )
    b.material += 1
    b.mats["Terrazzo"] = str(b.material)
    b.add(
        "material.create",
        name="Terrazzo",
        color=[1, 1, 1],
        asset="8",
        textureSize={"width": 1.2, "height": 1.2},
    )
    for name, color, opacity in [
        ("Ivory", [0.92, 0.91, 0.85], 1),
        ("White", [0.95, 0.95, 0.91], 1),
        ("Roof gray", [0.65, 0.67, 0.65], 1),
        ("Linen", [0.85, 0.79, 0.64], 1),
        ("Ochre", [0.68, 0.43, 0.15], 1),
        ("Concrete", [0.64, 0.63, 0.55], 1),
        ("Teal", [0.08, 0.38, 0.36], 1),
        ("Mustard", [0.88, 0.59, 0.16], 1),
        ("Bronze", [0.18, 0.22, 0.19], 1),
        ("Glass", [0.57, 0.78, 0.79], 0.10),
        ("Water", [0.12, 0.57, 0.62], 0.86),
        ("Sand", [0.65, 0.57, 0.41], 1),
        ("Sage", [0.48, 0.61, 0.36], 1),
        ("Leaf", [0.32, 0.48, 0.28], 1),
        ("Firebox", [0.07, 0.08, 0.07], 1),
        ("Clay", [0.61, 0.29, 0.17], 1),
    ]:
        b.material += 1
        b.mats[name] = str(b.material)
        b.add("material.create", name=name, color=color, opacity=opacity)
    b.flush("palette")

    # House 16 x 8 m, wing to the east; lower pool court to the south.
    b.box("Living pavilion slab", 0, 0, 0, 11, 8, 0.5, "Concrete", "Structure")
    b.box("Bedroom wing slab", 11, -2, 0, 5, 10, 0.5, "Concrete", "Structure")
    b.box(
        "Terrazzo living floor",
        0.15,
        0.15,
        0.5,
        10.7,
        7.7,
        0.04,
        "Terrazzo",
        "Structure",
    )
    b.box("Bedroom floor", 11.1, -1.9, 0.5, 4.8, 9.8, 0.04, "Walnut", "Structure")
    for name, x, y, w, d in [
        ("North wall", 0, 7.8, 11, 0.2),
        ("East wall", 15.8, -2, 0.2, 10),
        ("Bedroom divider", 11, 3.1, 4.8, 0.15),
        ("Bedroom west", 11, 0, 0.18, 3.1),
    ]:
        b.box(name, x, y, 0.5, w, d, 2.8, "Ivory", "Structure")
    # Feature hearth, visibly open front, stone piers and lintel.
    for name, x, z, w, h in [
        ("Hearth left", 0.4, 0.5, 0.65, 3.7),
        ("Hearth right", 3.25, 0.5, 0.65, 3.7),
        ("Stone lintel", 1.05, 1.65, 2.2, 2.55),
    ]:
        b.box(name, x, 6.65, z, w, 1, h, "Stone", "Structure")
    b.box("Fireplace recess", 1.05, 7.48, 0.6, 2.2, 0.12, 1.05, "Firebox", "Structure")
    b.box("Floating hearth", 0.2, 6.2, 0.54, 3.9, 1.3, 0.18, "Concrete", "Structure")
    b.box("Chimney cap", 0.25, 6.5, 4.2, 3.8, 1.3, 0.12, "Metal", "Roof")
    # Continuous wood soffits, staggered roofs and fine pale fascia.
    for name, x, y, z, w, d in [
        ("Living", -0.9, -1.05, 3.65, 12.4, 9.65),
        ("Sleeping", 10.6, -2.75, 3.32, 6.15, 11.35),
        ("Carport", -6.1, 2, 3.12, 6.1, 6.5),
    ]:
        roof = [
            b.box(name + " wood soffit", x, y, z, w, d, 0.12, "Walnut"),
            b.box(name + " roof", x, y, z + 0.12, w, d, 0.12, "Roof gray"),
        ]
        b.roofs.append(b.group(name + " canopy", roof, "Roof"))
    # Shared structural posts and beams; materials applied before component creation.
    post = b.component(
        "Bronze post", [b.box("Post", 0, 0, 0, 0.14, 0.14, 3.1, "Bronze")], "Structure"
    )
    locations = [
        (0.1, 0.1, 0.54),
        (3.6, 0.1, 0.54),
        (7.2, 0.1, 0.54),
        (10.8, 0.1, 0.54),
        (0.1, 7.6, 0.54),
        (5.4, 7.6, 0.54),
        (10.8, 7.6, 0.54),
        (-5.7, 2.4, 0),
        (-5.7, 7.7, 0),
        (-0.35, 2.4, 0),
    ]
    b.move(post[0], locations[0])
    b.front_posts.append(post[0])
    for p in locations[1:]:
        instance = b.instance(post, p)
        if p[1] == 0.1:
            b.front_posts.append(instance)
        if p[0] < 0:
            b.section_hide.append(instance)
    beam = b.component(
        "Exposed roof beam", [b.box("Beam", 0, 0, 0, 0.14, 9.2, 0.24, "Walnut")], "Roof"
    )
    b.move(beam[0], [0.1, -0.8, 3.39])
    for x in [1.9, 3.7, 5.5, 7.3, 9.1, 10.9]:
        b.instance(beam, [x, -0.8, 3.39])
    # Curtain walls; broad sheets of glass with transom and slim mullions.
    for x in [0.25, 3.75, 7.35]:
        b.box("Pool glazing", x, 0.14, 0.56, 3.32, 0.025, 2.76, "Glass", "Glazing")
        b.box("Clerestory", x, 0.14, 3.36, 3.32, 0.025, 0.27, "Glass", "Glazing")
        b.box("Transom", x, 0.1, 3.30, 3.32, 0.09, 0.06, "Bronze", "Glazing")
        for a in [x, x + 1.66, x + 3.29]:
            b.box("Mullion", a, 0.1, 0.54, 0.035, 0.09, 3.09, "Bronze", "Glazing")
    for y in [0.3, 2.75, 5.2]:
        b.box("West glass", 0.12, y, 0.54, 0.025, 2.35, 2.8, "Glass", "Glazing")
        b.box("West mullion", 0.08, y, 0.54, 0.08, 0.045, 2.85, "Bronze", "Glazing")
    b.box(
        "Bedroom court glass", 11.2, -1.86, 0.54, 4.5, 0.025, 2.74, "Glass", "Glazing"
    )
    for x in [11.2, 12.7, 14.2, 15.65]:
        b.box("Bedroom mullion", x, -1.9, 0.54, 0.05, 0.08, 2.78, "Bronze", "Glazing")
    b.flush("architecture")

    # Breeze blocks with real holes, shared 48 times, beside the arrival court.
    block = b.face(
        "Pierced block",
        [[0, 0, 0], [0.44, 0, 0], [0.44, 0, 0.44], [0, 0, 0.44]],
        holes=[[[0.08, 0, 0.08], [0.08, 0, 0.36], [0.36, 0, 0.36], [0.36, 0, 0.08]]],
    )
    b.add("geometry.push_pull", body=block, face="9", distance=0.16)
    b.paint(block, "White")
    screen = b.component("Breeze block", [block], "Structure")
    b.move(screen[0], [-5.5, 2, 0.15])
    for row in range(5):
        for col in range(10):
            if row or col:
                b.instance(screen, [-5.5 + col * 0.48, 2, 0.15 + row * 0.48])
    b.box("Screen footing", -5.65, 1.78, 0, 5.05, 0.45, 0.15, "Concrete", "Structure")
    b.box("Carport paving", -6, 2, -0.05, 6, 6, 0.1, "Asphalt", "Landscape")
    # Terrace built as four bands around a sunken pool; open water, no fake overpaint.
    for x, y, w, d in [
        (-1, -3, 12, 3),
        (1, -8.5, 11, 1.2),
        (-1, -8.5, 2, 5.5),
        (9, -7.3, 3, 4.3),
    ]:
        b.box("Limestone terrace", x, y, -0.1, w, d, 0.38, "Ivory", "Landscape")
    for x, y, w, d in [
        (0.8, -7.5, 8.4, 0.2),
        (0.8, -3.2, 8.4, 0.2),
        (0.8, -7.3, 0.2, 4.1),
        (9, -7.3, 0.2, 4.1),
    ]:
        b.box("Pool coping", x, y, 0.28, w, d, 0.10, "Concrete", "Landscape")
    b.box("Pool water", 1, -7.3, -0.05, 8, 4.1, 0.08, "Water", "Landscape")
    for i in range(3):
        b.box(
            "Broad terrace step",
            -0.8,
            -1.2 - i * 0.38,
            0.28 + i * 0.07,
            4,
            0.38,
            0.07,
            "Concrete",
            "Landscape",
        )
    # Dining chairs: a generic original slatted walnut chair, no branded design.
    parts = [
        b.box("Seat", 0, 0, 0.42, 0.5, 0.48, 0.08, "Mustard"),
        b.box("Back", 0, 0.43, 0.5, 0.5, 0.055, 0.4, "Walnut"),
    ]
    for x in [0.035, 0.415]:
        for y in [0.035, 0.395]:
            parts.append(b.box("Chair leg", x, y, 0, 0.05, 0.05, 0.43, "Walnut"))
    chair = b.component("Dining chair", parts, "Furniture")
    b.move(chair[0], [6.15, 3.05, 0.54])
    for x in [6.95, 7.75]:
        b.instance(chair, [x, 3.05, 0.54])
    for x in [6.65, 7.45, 8.25]:
        b.instance(chair, [x, 1.65, 0.54], 180)
    # Original parametrically stretchable credenza: top, carcass, sliding doors.
    parts = [
        b.box("Top", 0, 0, 0.72, 2.4, 0.5, 0.06, "Walnut"),
        b.box("Case", 0, 0.03, 0.2, 2.4, 0.44, 0.52, "Walnut"),
        b.box("Sliding teal door", 0.07, -0.015, 0.25, 1.05, 0.035, 0.42, "Teal"),
        b.box("Sliding ivory door", 1.17, -0.03, 0.25, 1.15, 0.035, 0.42, "Ivory"),
    ]
    for x in [0.12, 2.16]:
        parts.append(b.box("Credenza foot", x, 0.12, 0, 0.08, 0.28, 0.2, "Bronze"))
    cred = b.component("Court credenza", parts, "Furniture")
    b.add(
        "component_parameter.define",
        definition=cred[1],
        name="width",
        label="Width",
        type="length",
        mode="input",
        expression="2400 mm",
        min=1.8,
        max=3.6,
    )
    for member in parts[:2]:
        b.add(
            "component_parameter.drive",
            definition=cred[1],
            kind="stretch",
            member=member,
            expression="width",
            data={"axis": "x", "at": 1.2},
        )
    b.add(
        "component_parameter.drive",
        definition=cred[1],
        kind="position",
        member=parts[-1],
        expression="width - 240 mm",
        data={"axis": "x"},
    )
    for member, at, expression in [
        (parts[2], 0.6, "width / 2 - 150 mm"),
        (parts[3], 1.7, "width / 2 - 50 mm"),
    ]:
        b.add(
            "component_parameter.drive",
            definition=cred[1],
            kind="stretch",
            member=member,
            expression=expression,
            data={"axis": "x", "at": at},
        )
    b.add(
        "component_parameter.drive",
        definition=cred[1],
        kind="position",
        member=parts[3],
        expression="width / 2 - 30 mm",
        data={"axis": "x"},
    )
    b.move(cred[0], [4.3, 7.05, 0.54])
    b.flush("components")
    # Soft furniture, upholstered cushions, split seats, low coffee table.
    for name, x, y, w, d, mat in [
        ("Conversation sofa", 1.05, 3.9, 3.3, 1, "Teal"),
        ("Lounge chair", 4.35, 4.6, 0.9, 1, "Mustard"),
    ]:
        parts = [
            b.box("Walnut base", x, y, 0.67, w, d, 0.16, "Walnut"),
            b.box(
                "Seat cushion", x + 0.08, y + 0.05, 0.83, w - 0.16, d - 0.12, 0.23, mat
            ),
            b.box(
                "Back cushion", x + 0.08, y + d - 0.22, 1.06, w - 0.16, 0.22, 0.47, mat
            ),
        ]
        for xx in [x + 0.08, x + w - 0.18]:
            for yy in [y + 0.1, y + d - 0.2]:
                parts.append(
                    b.box("Splayed foot", xx, yy, 0.54, 0.09, 0.09, 0.14, "Bronze")
                )
        b.group(name, parts, "Furniture")
    b.box("Woven rug", 1.15, 2.2, 0.545, 3.9, 2.4, 0.015, "Wool", "Furniture")
    b.box("Coffee table", 2.0, 2.8, 0.84, 1.8, 0.68, 0.06, "Walnut", "Furniture")
    for x in [2.1, 3.6]:
        b.box("Coffee trestle", x, 2.9, 0.56, 0.08, 0.48, 0.28, "Bronze", "Furniture")
    for x, y in [(2.2, 2.95), (2.65, 3.0)]:
        b.box("Book", x, y, 0.9, 0.32, 0.23, 0.035, "Mustard", "Furniture")
    for x, y in [(12, 4), (12, -0.9)]:
        b.box("Bed plinth", x, y, 0.54, 2.4, 2.1, 0.26, "Walnut", "Furniture")
        b.box(
            "Linen mattress",
            x + 0.1,
            y + 0.1,
            0.8,
            2.2,
            1.9,
            0.22,
            "Ivory",
            "Furniture",
        )
        b.box(
            "Woven bed throw",
            x + 0.1,
            y + 0.15,
            1.02,
            2.2,
            0.65,
            0.03,
            "Wool",
            "Furniture",
        )
        for xx in [x + 0.25, x + 1.3]:
            b.box("Pillow", xx, y + 1.4, 1.02, 0.8, 0.45, 0.13, "Mustard", "Furniture")
    # Pool loungers with tilted backs, cushions and hardwood rails.
    loungerparts = [
        b.box("Cushion", 0, 0, 0.25, 0.7, 1.7, 0.12, "Wool"),
        b.box("Rail", -0.05, -0.04, 0.16, 0.8, 1.8, 0.08, "Walnut"),
    ]
    back = b.box("Raised back", 0, 1.25, 0.37, 0.7, 0.55, 0.10, "Wool")
    b.add(
        "geometry.transform_selection",
        entities=[{"body": back, "kind": "context", "entity": "0"}],
        matrix=[1, 0, 0, 0, 0, 0.866, 0.5, 0, 0, -0.5, 0.866, 0, 0, 0, 0, 1],
        pivot=[0, 1.25, 0.37],
        space="world",
    )
    loungerparts.append(back)
    lounger = b.component("Terrace lounger", loungerparts, "Furniture")
    b.move(lounger[0], [10, -6.8, 0.28])
    b.instance(lounger, [11.8, -6.8, 0.28], mirror=True)
    b.flush("interiors")

    # Library sources built into this document; parameter panels work on reopen.
    table = b.library("dining-table", [6.2, 1.9, 0.54], "Furniture")
    b.library("bookshelf", [8.6, 7.1, 0.54], "Furniture")
    cabinet = b.library("base-cabinet", [5.1, 6.7, 0.54], "Furniture")
    for x in [5.7, 6.3, 6.9, 7.5]:
        b.instance(cabinet, [x, 6.7, 0.54])
    b.box("Kitchen counter", 5.05, 6.65, 1.4, 3.1, 0.7, 0.05, "Ivory", "Furniture")
    b.box("Island", 7.8, 4.35, 0.54, 2.1, 0.85, 0.82, "Teal", "Furniture")
    b.box("Island stone top", 7.7, 4.25, 1.36, 2.3, 1.05, 0.06, "Ivory", "Furniture")
    b.flush("kitchen")
    # A hosted library casement cuts an ordinary north-facing wall panel.
    wall = b.face(
        "Hosted bedroom window wall",
        [[11, 7.8, 0.5], [16, 7.8, 0.5], [16, 7.8, 3.3], [11, 7.8, 3.3]],
        "Ivory",
    )
    b.add("geometry.push_pull", body=wall, face="5", distance=0.18)
    b.tag(wall, "Structure")
    b.flush("host-wall")
    window = b.library("casement-window", [0, 0, 0], "Glazing")
    b.add(
        "component.attach",
        body=window[0],
        host=wall,
        face="5",
        anchor=[13.5, 7.8, 2],
        tangent=[1, 0, 0],
    )
    b.flush("hosted-window")

    # Desert landscaping from faceted native geometry, plus sloped terrain.
    for x, y in [(-3, -3), (-3, 5), (17, 3), (14, -5)]:
        b.box(
            "Raised planter",
            x - 0.65,
            y - 0.65,
            0,
            1.3,
            1.3,
            0.55,
            "Concrete",
            "Landscape",
        )
        b.box(
            "Gravel mulch",
            x - 0.55,
            y - 0.55,
            0.55,
            1.1,
            1.1,
            0.02,
            "Grass" if x == 14 else "Gravel",
            "Landscape",
        )
        for j in range(9):
            a = j * 2 * math.pi / 9
            p = [
                [x, y, 0.55],
                [x + 0.25 * math.cos(a - 0.35), y + 0.25 * math.sin(a - 0.35), 1.05],
                [x + 1.0 * math.cos(a), y + 1.0 * math.sin(a), 0.85],
                [x + 0.25 * math.cos(a + 0.35), y + 0.25 * math.sin(a + 0.35), 1.05],
            ]
            body = b.face("Agave leaf", p[:3], "Sage")
            b.tag(body, "Landscape")
            body = b.face("Agave leaf fold", [p[0], p[2], p[3]], "Leaf")
            b.tag(body, "Landscape")
    # Palms: tapered octagonal trunks and folded leaf fans.
    for x, y, h in [(-4, -6, 5.4), (17, 7, 6.2), (-4, 10, 5.8)]:
        ring = [
            [
                x + 0.17 * math.cos(a * math.pi / 4),
                y + 0.17 * math.sin(a * math.pi / 4),
                0,
            ]
            for a in range(8)
        ]
        trunk = b.face("Palm trunk", ring)
        b.add("geometry.push_pull", body=trunk, face="9", distance=h)
        b.paint(trunk, "Walnut")
        b.tag(trunk, "Landscape")
        for j in range(9):
            a = j * 2 * math.pi / 9
            base = [x, y, h]
            mid = [x + 1.3 * math.cos(a), y + 1.3 * math.sin(a), h + 0.5]
            tip = [x + 2.5 * math.cos(a), y + 2.5 * math.sin(a), h - 0.4]
            for sign in [-1, 1]:
                side = [
                    mid[0] + sign * 0.4 * math.sin(a),
                    mid[1] - sign * 0.4 * math.cos(a),
                    mid[2] - 0.1,
                ]
                for points in [[base, mid, side], [mid, tip, side]]:
                    body = b.face("Palm frond", points, "Leaf" if sign == 1 else "Sage")
                    b.tag(body, "Landscape")
    b.flush("planting")
    sources = []
    for y, z in [(-12, -0.7), (-9, -0.45), (0, -0.1), (9, 0.5), (13, 0.9)]:
        edge = b.wire([-9, y, z], [21, y, z], "Terrain source")
        sources.append({"body": edge, "edge": "1"})
        b.hide.append(edge)
    terrain = b.new()
    b.add(
        "terrain.create_from_edges",
        name="Gently sloping desert site",
        edges=sources,
        steinerFill=True,
    )
    b.paint(terrain, "Grass")
    b.tag(terrain, "Landscape")
    b.add(
        "terrain.stamp_pad",
        terrain=terrain,
        footprint={"polygon": [[-6.5, -9], [16.7, -9], [16.7, 8.6], [-6.5, 8.6]]},
        elevation=-0.15,
        mode="width",
        width=1.5,
    )
    b.add(
        "terrain.sculpt",
        terrain=terrain,
        mode="raise",
        path=[[18, 10]],
        radius=3,
        amount=0.25,
    )
    b.paint(terrain, "Grass")
    b.flush("terrain-grading")
    b.sync_ids()
    # Terrain is a container: paint its generated tile bodies through the public API.
    desc = json.loads(
        subprocess.check_output(
            ["sketchyup-cli", "--input", str(b.model), "--query", "document.describe"],
            timeout=30,
        )
    )
    for tile in desc["bodies"]:
        if tile["parent"] == terrain:
            b.paint(tile["id"], "Grass")
    path = b.face(
        "Driveway drape source",
        [
            [-8, 12, 2],
            [-4, 12, 2],
            [-4, 8, 2],
            [-0.3, 7.7, 2],
            [-0.3, 3, 2],
            [-5.9, 3, 2],
            [-5.9, 8, 2],
            [-8, 9, 2],
        ],
        "Asphalt",
    )
    b.add(
        "terrain.drape",
        terrain=terrain,
        mode="overlay",
        faces=[{"body": path, "face": "9"}],
        lift=0.025,
    )
    b.hide.append(path)
    b.flush("terrain")
    b.sync_ids()
    desc = json.loads(
        subprocess.check_output(
            ["sketchyup-cli", "--input", str(b.model), "--query", "document.describe"],
            timeout=30,
        )
    )
    for body in desc["bodies"]:
        if body["name"] == "Drape" and body["parent"] == "0":
            b.tag(body["id"], "Landscape")
            for tile in desc["bodies"]:
                if tile["parent"] == body["id"]:
                    b.paint(tile["id"], "Asphalt")

    # Follow Me creates a pool handrail from a hexagonal section.
    profile = b.face(
        "Handrail profile",
        [
            [
                9.35 + 0.028 * math.cos(i * math.pi / 3),
                -5.3 + 0.028 * math.sin(i * math.pi / 3),
                0.35,
            ]
            for i in range(6)
        ],
    )
    rail = b.new()
    b.add(
        "geometry.sweep",
        body=profile,
        face="7",
        path=[
            [9.35, -5.3, 0.35],
            [9.35, -5.3, 1.15],
            [9.35, -5.0, 1.4],
            [9.35, -4.5, 1.4],
            [9.35, -4.2, 1.15],
            [9.35, -4.2, 0.35],
        ],
    )
    b.paint(rail, "Bronze")
    b.tag(rail, "Landscape")
    b.hide.append(profile)
    # Offset outlines on a ceramic tray retain the original face coverage.
    tray = b.face(
        "Ceramic tray",
        [
            [2.95, 2.92, 0.903],
            [3.45, 2.92, 0.903],
            [3.45, 3.28, 0.903],
            [2.95, 3.28, 0.903],
        ],
        "Ivory",
    )
    b.add("geometry.offset", body=tray, face="5", distance=-0.025)
    b.tag(tray, "Furniture")
    # Solid subtraction forms a shallow stone wash basin on the island.
    basin = b.box("Basin outer", 8.05, 4.45, 1.42, 0.7, 0.5, 0.12, "Concrete")
    cutter = b.box("Basin cutter", 8.10, 4.50, 1.45, 0.6, 0.4, 0.2, "Concrete")
    b.add(
        "geometry.boolean",
        body=basin,
        tool=cutter,
        context="0",
        operation="subtract",
        keepOperands=False,
    )
    b.flush("sweep-offset-basin")
    b.sync_ids()
    # Circular native arc outlines a table bowl; repeated linear slats form a mat.
    arc = b.new()
    b.add(
        "geometry.arc_center",
        body="0",
        center=[6.8, 2.35, 1.30],
        normal=[0, 0, 1],
        xAxis=[1, 0, 0],
        radius=0.16,
        startAngle=0,
        sweepAngle=1.8 * math.pi,
        segments=24,
    )
    b.tag(arc, "Furniture")
    slat = b.box(
        "Timber entry slat", -0.6, 0.7, 0.30, 0.65, 0.04, 0.025, "Walnut", "Landscape"
    )
    b.add(
        "geometry.array_selection",
        entities=[{"body": slat, "kind": "context", "entity": "0"}],
        mode="linear",
        delta=[0, 0.09, 0],
        count=12,
    )
    b.flush("arc-array")
    b.sync_ids()

    add_details(b, terrain)

    # Dimensions and named section planes. Annotations are scene selective.
    for name, a, c, offset in [
        ("Pavilion width", [0, -0.6, 0.55], [11, -0.6, 0.55], [0, -0.7, 0]),
        ("House depth", [16.5, -2, 0.55], [16.5, 8, 0.55], [0.7, 0, 0]),
    ]:
        edge = b.wire(a, c, name)
        b.annotations.append(edge)
        b.tag(edge, "Annotation")
        b.add(
            "annotation.create",
            name=name,
            kind="distance",
            anchors=[
                {"kind": "edge", "body": edge, "edge": "1", "fraction": t}
                for t in [0, 1]
            ],
            offset=offset,
        )
    for name, x, y in [
        ("LIVING", 2.8, 1.4),
        ("DINING", 7.2, 0.7),
        ("KITCHEN", 7.2, 5.8),
        ("SLEEPING", 13.4, 1.5),
        ("SLEEPING", 13.4, 6.8),
        ("CARPORT", -3, 5),
    ]:
        anchor = b.wire([x, y, 0.55], [x + 0.01, y, 0.55], name + " label anchor")
        b.tag(anchor, "Annotation")
        b.add(
            "annotation.create",
            name=name + f" {x} {y}",
            kind="label",
            anchors=[{"kind": "edge", "body": anchor, "edge": "1", "fraction": 0}],
            text=name,
            leader=False,
            textSize=10,
        )
    b.add(
        "section.create",
        name="Living cut",
        context="0",
        space="world",
        plane={"normal": [0, 1, 0], "offset": -2.6},
        fill=True,
        edges=True,
        color=[0.74, 0.52, 0.28],
    )
    b.add(
        "section.create",
        name="Plan cut",
        context="0",
        space="world",
        plane={"normal": [0, 0, -1], "offset": 1.7},
        fill=True,
        edges=True,
    )
    b.flush("annotations-sections")
    cameras = [
        ("Hero", [5, 1, 1.0], -117, 29, 44, 40, False),
        ("Terrace", [6, 2.5, 1.8], -102, 6, 23, 55, False),
        ("Living", [2.8, 6.1, 1.7], -72, 2, 5.5, 70, False),
        ("Section", [5.5, 4.7, 1.55], -100, 32, 13.2, 47, False),
        ("Plan", [5, 3, 0.5], -90, 90, 28, 40, True),
        ("Site", [5, 1, 0], -55, 42, 47, 40, False),
        ("Furniture", [6.8, 2.8, 1.1], -100, 34, 8.5, 45, False),
        ("Elevation", [5, 3, 1], -90, 0, 34, 40, True),
    ]
    for i, (name, target, yaw, pitch, dist, fov, ortho) in enumerate(cameras, 1):
        vis = [{"id": h, "visible": False} for h in b.hide]
        vis += [{"id": h, "visible": name != "Furniture"} for h in b.front_posts]
        vis += [{"id": h, "visible": name != "Section"} for h in b.section_hide]
        vis += [
            {
                "id": h,
                "visible": name in ("Hero", "Terrace", "Living", "Site", "Elevation"),
            }
            for h in b.roofs
        ]
        tags = [
            {"id": b.tags["Annotation"], "visible": name == "Plan"},
            {
                "id": b.tags["Glazing"],
                "visible": name not in ("Furniture", "Plan", "Section"),
            },
            {
                "id": b.tags["Roof"],
                "visible": name not in ("Plan", "Furniture", "Section"),
            },
            {
                "id": b.tags["Landscape"],
                "visible": name not in ("Plan", "Furniture", "Section", "Elevation"),
            },
        ]
        snapshot = {
            "camera": {
                "target": target,
                "yaw": yaw,
                "pitch": pitch,
                "distance": dist,
                "fieldOfView": fov,
                "orthographic": ortho,
            },
            "section": {
                "plane": None,
                "active": (
                    [{"context": "0", "section": "1"}]
                    if name == "Section"
                    else [{"context": "0", "section": "2"}]
                    if name == "Plan"
                    else []
                ),
            },
            "visibility": {
                "bodies": vis,
                "tags": tags,
                "hidden": [],
                "showHidden": False,
            },
            "style": dict(style, mode="monochrome" if name == "Plan" else "textured"),
            "solar": dict(
                solar, enabled=name not in ("Living", "Furniture", "Plan", "Section")
            ),
        }
        b.add("saved_scene.create", name=name, snapshot=snapshot)
    b.add("saved_scene.recall", scene="1")
    b.add(
        "render_preset.create",
        name="Court late afternoon",
        width=1440,
        height=900,
        samples=64,
        seed=17,
        engine="cycles",
    )
    b.flush("scenes")

    # Four sheets, separate transaction. A2 fits the full 16 m plan at 1:50.
    def text(sheet, x, y, w, h, value, size=12):
        b.add(
            "drawing_item.create",
            sheet=sheet,
            kind="text",
            data={
                "frame": {"xMm": x, "yMm": y, "widthMm": w, "heightMm": h},
                "text": value,
                "font": {"family": "DejaVu Sans", "sizePt": size},
                "align": "left",
            },
        )

    for sheet, name, number in [
        ("1", "Court house / study", "A-000"),
        ("2", "Floor plan", "A-101"),
        ("3", "Elevations", "A-201"),
        ("4", "Section perspective", "A-301"),
    ]:
        b.add(
            "drawing_sheet.create",
            name=name,
            number=number,
            paper={"widthMm": 594, "heightMm": 420},
            marginMm=12,
        )
        text(sheet, 20, 15, 550, 18, "SOLSTICE COURT  /  " + name.upper(), 20)
        text(
            sheet,
            20,
            390,
            550,
            12,
            "ORIGINAL DESIGN STUDY     /     SKETCHYUP     /     " + number,
            10,
        )
    for sheet, scene, x, y, w, h, content, scale, title in [
        ("1", "1", 20, 45, 554, 325, "rasterAppearance", 100, "Courtyard pavilion"),
        ("2", "5", 40, 55, 510, 300, "technicalLines", 50, "Floor plan / 1:50"),
        ("3", "8", 20, 55, 554, 145, "technicalLines", 50, "Pool elevation / 1:50"),
        ("3", "2", 20, 215, 554, 160, "rasterAppearance", 100, "Pool terrace"),
        ("4", "4", 20, 45, 554, 325, "rasterAppearance", 100, "Living section"),
    ]:
        b.add(
            "drawing_view.create",
            name=title,
            sheet=sheet,
            source={"kind": "scene", "scene": scene},
            frame={"xMm": x, "yMm": y, "widthMm": w, "heightMm": h},
            scaleDenominator=scale,
            content=content,
            hiddenLines=False,
        )
    text(
        "2",
        25,
        365,
        530,
        15,
        "LIVING + DINING    /    KITCHEN    /    TWO SLEEPING ROOMS    /    COURTYARD",
        12,
    )
    b.add("drawing_view.accept", all=True)
    b.flush("sheets")
    final = out / "showcase.sketchyup"
    final.write_bytes(b.model.read_bytes())
    desc = json.loads(
        subprocess.check_output(
            ["sketchyup-cli", "--input", str(final), "--query", "document.describe"],
            timeout=30,
        )
    )
    (out / "document.json").write_text(json.dumps(desc, indent=2) + "\n")
    stats = {
        "vertices": sum(x["vertices"] for x in desc["bodies"]),
        "faces": sum(len(x["faces"]) for x in desc["bodies"]),
        "bodies": len(desc["bodies"]),
        "definitions": len(desc["definitions"]),
        "instances": len(desc["instances"]),
        "buildSeconds": round(time.monotonic() - b.start, 2),
        "componentShotBody": table[0],
    }
    assert stats["bodies"] < 9500, (
        "Keep headroom below the 10000-body measured drawing limit"
    )
    assert 25000 <= stats["vertices"] <= 60000, "Showcase detail budget changed"
    # CLI cannot render the three perspective sheet viewports, but it can validate
    # every measured view. Refuse broken sheets before an expensive GUI capture.
    preflight = json.loads(
        subprocess.check_output(
            [
                "sketchyup-cli",
                "--input",
                str(final),
                "--export-sheets",
                str(out / "preflight.pdf"),
                "--preflight-only",
            ],
            timeout=60,
        )
    )
    (out / "sheet-preflight.json").write_text(json.dumps(preflight, indent=2) + "\n")
    unexpected = [
        f
        for f in preflight["preflight"]["findings"]
        if f["severity"] == "blocking" and f["code"] != "rasterUnavailable"
    ]
    assert not unexpected, unexpected
    (out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(stats)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    build(args.output.resolve())
