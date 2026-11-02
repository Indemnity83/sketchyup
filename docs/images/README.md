# Repository screenshots

These PNGs show SketchyUp 1.7.0 for the README. They are all 1440×900 and come from
a small original showcase house, not from a real project.

- `hero-light.png`, `hero-dark.png`: the hero view (textured house, stairs to a
  timber deck, sun shadows, the Outliner), in the light and dark themes. The ground
  rises behind the house.
- `components.png`: the dining table, a configurable assembly, selected. Its width,
  depth, height, legs and apron are in the Info panel under "Parameters · this
  placement". It stands on the deck beside the recipe table.
- `sheets.png`: the Sheets workspace with sheet A-101 (plan view and perspective view).
- `terrain.png`: the site terrain with nothing selected and the Sun and shadows panel open.
- `commands.png`: the Ctrl+K command palette with "export" typed.

## Source

The model is built from two CLI scripts:

- `showcase.json`: the house, deck, stairs, recipe table, terrain, dimensions, textured
  materials (textures from `resources/textures/`, embedded as base64), saved scenes
  Hero, Plan, Site and Sheet perspective, and sun shadows. The terrain's back edge is
  5 m above its front edge, so the ground rises behind the house.
- `showcase-sheet.json`: sheet A-101 with its plan and perspective views and title text.
  Drawing sheet operations cannot share a batch with model operations, so this is a
  second batch.

The dining table is not in the scripts: `catalog.import` reads only `.sketchycat`
catalogs, not the bundled assembly library. The components shot places it in the app,
at (1.6, −0.95, 0.6) m, by choosing it in the Components list and typing that position
into the Measurements box.

The model shots use the Paint tool (B). The Select tool's hint line overlaps the scene
tabs, and Orbit and Pan draw a camera hint of their own, so Paint keeps the viewport
clean. Remove that workaround from `scripts/capture-screenshots.sh` when the Select hint
is fixed.

## Regenerate

Build the screenshot image from `scripts/screenshots.Dockerfile`. It installs the
SketchyUp 1.7.0 package from the GitHub release, checks it against that release's
`SHA256SUMS`, and adds Xvfb, xdotool and ImageMagick. The build needs network access.
Its context is `packaging/arch`, which supplies the pinned mirror list. Building with the
tag `sketchyup-shots:1.7.0` replaces any local image with that tag.

```sh
docker build -f scripts/screenshots.Dockerfile --build-arg SKETCHYUP_VERSION=1.7.0 \
  -t sketchyup-shots:1.7.0 packaging/arch
```

Then run the capture. `scripts/capture-screenshots.sh` builds both scripts into a
temporary directory, starts its own Xvfb with an isolated home directory for each shot,
drives SketchyUp through the shot list, and writes the PNGs:

```sh
docker run --rm --network none --memory 3g --cpus 2 --user "$(id -u):$(id -g)" \
  -v "$PWD":/src:ro -v "$PWD/docs/images":/out sketchyup-shots:1.7.0 \
  /src/scripts/capture-screenshots.sh /out
```

CI does not run this script. Rerun it after a change to the model or the UI, and
commit the new PNGs with the change.
