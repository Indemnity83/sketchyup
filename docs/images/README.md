# Repository screenshots

These PNGs show SketchyUp 1.7.0 for the README. They are all 1440×900 and come from
a small original showcase house, not from a real project.

- `hero-light.png`, `hero-dark.png`: the hero view (textured house, stairs to a
  timber deck, sun shadows, the Outliner), in the light and dark themes.
- `components.png`: the four-leg table selected, with its recipe parameters in the
  Entity info panel.
- `sheets.png`: the Sheets workspace with sheet A-101 (plan view and perspective view).
- `terrain.png`: the site terrain, selected, with its Entity info panel open.
- `commands.png`: the Ctrl+K command palette with "sec" typed.

## Source

The model is built from two CLI scripts:

- `showcase.json`: the house, deck, stairs, table, terrain, dimensions, textured
  materials (textures from `resources/textures/`, embedded as base64), saved scenes
  Hero, Plan, Site and Sheet perspective, and sun shadows.
- `showcase-sheet.json`: sheet A-101 with its plan and perspective views and title text.
  Drawing sheet operations cannot share a batch with model operations, so this is a
  second batch.

## Regenerate

`scripts/capture-screenshots.sh` builds both scripts into a temporary directory,
starts its own Xvfb with an isolated home directory, drives SketchyUp through the
shot list, and writes the PNGs. Run it in the screenshot image, which provides Xvfb,
xdotool, ImageMagick and the SketchyUp 1.7.0 package (`sketchyup-shots:1.7.0`):

```sh
docker run --rm --network none --memory 3g --cpus 2 --user "$(id -u):$(id -g)" \
  -v "$PWD":/src:ro -v "$PWD/docs/images":/out sketchyup-shots:1.7.0 \
  /src/scripts/capture-screenshots.sh /out
```

CI does not run this script. Rerun it after a change to the model or the UI, and
commit the new PNGs with the change.
