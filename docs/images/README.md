# Repository images

The README shows **Solstice Court**, an original midcentury modern home designed
and built with SketchyUp's public modeling commands. It is an architectural study,
not a surveyed site or a construction document. No external project models,
real addresses, house numbers, city names or branded furniture were used.

All eight screenshots are actual SketchyUp 1.7.0 windows captured under a private
Xvfb **inside Docker**. Each is 1440×900, stripped of metadata and below 500 KB.

| Image | What it shows |
| --- | --- |
| `hero-light.png` | Post-and-beam home, deep flat canopies, glass, pool, breeze blocks and palms; light theme and Outliner. |
| `hero-dark.png` | The same model, camera and sunlight in the dark UI theme. |
| `components.png` | The library dining table selected, with its editable placement parameters visible. |
| `sheets.png` | A-101: dimensioned and labeled 1:50 floor plan on A2; four pages in the Pages tree. |
| `terrain.png` | Sloped, stamped and lightly sculpted site, with the Sun and shadows panel. |
| `commands.png` | Ctrl+K palette with `export` typed over the home. |
| `section.png` | Saved section perspective through the furnished house, with roofs and glazing hidden. |
| `interior.png` | Living room, stone fireplace, walnut ceiling and furniture, teal sofa and mustard lounge chair. |
| `social-preview.jpg` | 1280×640 brand panel beside an actual Blender Cycles CPU render of the same model; under 1 MB, metadata stripped. |

## Model sources

[`showcase/build_showcase.py`](showcase/build_showcase.py) emits bounded, readable
JSON command batches and executes them through `sketchyup-cli --script`. The old
monolithic `showcase.json` and `showcase-sheet.json` have been replaced.
Generated batches, native documents, logs and render manifests belong in `.local/`.

The generator uses only this repository's sources:

- Seven textures in `resources/textures/`: wood-dark-oak, stone-rubble-wall,
  gravel, grass, asphalt, metal-corrugated and fabric-wool-herringbone. Texture
  bytes are injected at generation time, never checked in again as base64.
- The dining table, bookshelf, base cabinet and cutting casement window from
  `resources/assemblies/`. Their public command sources are rebased into this
  document; no catalog import or GUI placement is needed.
- Original generic furniture and geometry, including a width-driven credenza,
  50 shared pierced breeze blocks, 10 posts, 7 beams and 6 dining chairs.

There are 10 shared definitions and 84 placements. Five definitions are
configurable (nine placements): four library assemblies plus the original
credenza. The model has 3,665 materialized vertices and 2,468 faces, far below the
150,000-vertex target. `stats.json` records the actual build duration and counts.

The model demonstrates push/pull, offset, Follow Me, solid subtraction, an arc,
a linear array, mirrored placement, groups, components, parameters, a hosted
window cutting a solid wall, tag folders, transparent materials, terrain stamping,
sculpting and a draped overlay. Eight saved scenes include an eye-level terrace,
an interior, section perspective, monochrome plan and elevation. Four A2 sheets
contain a cover, 1:50 plan, elevation/terrace views and section perspective.

Sun coordinates are generic (32° N, 110° W; UTC−07), with no geographic site
origin or address. The study uses 15 April 2026 at 10:00 local time.

## Regenerate

Run from the repository root. Check memory and disk first; run only one capture
container at a time. The Dockerfile installs the release package, verifies its
SHA256SUMS, and includes Python, Xvfb, xdotool, ImageMagick and fonts.

```sh
ulimit -c 0
timeout 10 free -g
timeout 10 df -h .
timeout 600 docker build -f scripts/screenshots.Dockerfile \
  --build-arg SKETCHYUP_VERSION=1.7.0 \
  -t sketchyup-shots:1.7.0 packaging/arch
```

Build the model separately with an installed SketchyUp 1.7.0 CLI:

```sh
timeout 300 python3 docs/images/showcase/build_showcase.py .local/showcase-build
```

The capture builds the model itself, starts a fresh app/profile for each shot,
and regenerates **all eight PNGs in one run**. It refuses to run outside Docker.
An optional mount preserves the native model and build statistics:

```sh
mkdir -p .local/capture-build
timeout 900 docker run --rm --network none \
  --memory 4g --memory-swap 4g --cpus 2 --user "$(id -u):$(id -g)" \
  -v "$PWD":/src:ro -v "$PWD/docs/images":/out \
  -v "$PWD/.local/capture-build":/build -e SHOWCASE_BUILD_OUT=/build \
  sketchyup-shots:1.7.0 /src/scripts/capture-screenshots.sh /out
```

For capture development only, `SHOWCASE_SHOTS=components,sheets` selects a subset.
Release the full image set only after a clean run without this filter and a visual
inspection of every output.

Render through SketchyUp's GLB snapshot exporter and its unchanged Blender adapter,
then compose the social preview with ImageMagick:

```sh
timeout --foreground 1450 scripts/render-showcase.sh .local/showcase-render
timeout 60 scripts/make-social-preview.sh \
  .local/showcase-render/image.png docs/images/social-preview.jpg
```

Use a **new render directory** for each run: the exporter refuses to overwrite a
snapshot. `/usr/bin/blender` must be Blender 5.2 LTS. The script uses Cycles CPU,
4 threads, 160 fixed samples, seed 17, 1344×1024, Standard view transform, no
denoising, and the model's solar lighting. Blender is bounded by a user systemd
scope with `MemoryMax=8G`, `MemorySwapMax=0`, and a 20-minute timeout. It writes
`image.png`, `result.json`, `elapsed.txt`, `snapshot/manifest.json` and logs.
The social script adapts the supplied brand-panel layout, including its drawn
cube icon; it does not retouch or fabricate the rendered geometry.

## Released-product limitations

No product code was changed. These observations and workarounds are relevant
when reproducing this model:

- D-094: Select hints overlap the scene/status line. Capture clicks the Paint
  tool before model shots. A scene-tab click retains keyboard focus, so a bare
  `B` keystroke is not reliable there.
- Under bare Xvfb, the separate command-palette dialog may not acquire X input
  focus. Capture waits for its window and explicitly focuses it before typing.
- Animated scene recall sometimes left the camera between views during capture.
  The isolated profile uses the existing `reducedMotion=true` setting and zero
  transition duration. The saved camera itself is unchanged.
- Painting a resolved component member returns **"Resolved component member
  disagrees with its definition"**. Paint primitive members before creating the
  shared definition, as this generator does.
- Attaching a cutting component to an open host returns **"Opening requires
  validated closed geometry: open_boundary"**. Extrude the wall first.
- Creating a section and a scene referencing it in one batch returns **"New scene
  snapshots require existing body, tag, geometry and section references"**.
  Create sections before the scene batch. Sheet operations also use a separate batch.
- Imprinting a drape across a stamped pad returns **"Drape on terrain refused;
  nothing was changed: inside-pad (6)"**, with **"A building pad protects this
  area; drape around it or remove its stamp first."** Use an overlay for this drive.
- A full-turn `geometry.arc_center` returns **"Invalid curve radius, angle or
  segment count"**. The table ornament uses a supported partial arc.
- Assigning a material to nonexistent body 1 in an otherwise empty document
  returns **"map::at"**. This is a poor diagnostic; the generator tracks allocated IDs.
- Sparse terrain sources with `maxEdgeLength=3` produced **"Stamp pad refused;
  nothing was changed: outside-outline (1)"**, with **"A footprint point is outside
  the terrain; pads stay inside the terrain's outline and outside its holes."**
  The generator leaves the optional edge-length limit unset for this sparse site.
- More than 100 commands returns **"Batch must contain 1–100 commands"**. The
  generator splits phases into batches of at most 100.
- `asset.import` takes `mediaType`, not `mimeType`; the latter returns **"Unknown
  command parameter"**. The generator uses the published schema.
- Annotation names must be unique, even when their displayed text is identical:
  **"Annotation names must be bounded, trimmed and unique"**.
- Terrain containers do not supply an inherited material to their generated tiles.
  Assign material to the tile bodies through the public API after grading.

The render transfer report explicitly records omitted wire geometry and annotations
and the tessellated/omitted analytic curve. There are no missing texture assets.
Intersect, schedules, 3D text and a sunken conversation pit were not used. This is
an architectural visualization study with generic furniture, not a permit-ready plan.
CI does not run these documentation capture scripts.
