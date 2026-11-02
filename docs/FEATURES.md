# Desktop feature reference

A compact reference for the desktop app's tools, shortcuts and optional services. For step-by-step
instructions, start with the [user guide](USER_GUIDE.md); for what is supported and tested, see the
[support matrix](SUPPORT_MATRIX.md); for scripting, see the [command-line reference](COMMAND_LINE.md).
Where this page and the user guide or [release notes](RELEASE_NOTES.md) differ, they are current.

This reference moved here from the project README.

## Modeling tools and shortcuts

- `L`: line. Click–move–click or press–drag–release; movement continues a chain.
  Escape disconnects it while keeping committed edges. Closed chains form faces.
- `R`: rectangle. Click the first corner, then the second; or enter `width, depth`
  in Measurements and press Enter. Values default to meters; `mm`, `cm`, `ft`, `in`,
  feet/inches and fractions override units. Unconstrained grid fallback is 0.1 m; acquired directions use continuous coordinates.
- Hover a point or edge for 450 ms to arm a reference. Move away for axis,
  parallel, perpendicular, analytic tangent, or from-point alignment. `Tab`
  cycles point and direction alternatives. `Shift` holds the current inference;
  release it to unlock. Right/Left/Up toggle world X/Y/Z locks; Down cycles
  parallel/perpendicular/off for the reference edge. Planar shapes reject axes
  outside their construction plane; Line can follow Z out of the starting plane.
  Numeric lengths honor locks. Focus transfer releases held Shift; arrow locks
  persist until toggled, committed, canceled, or the document changes.
- `C`: circle. Click center, then radius; or enter the radius. `24s` sets segments.
- Draw menu: Freehand, Regular polygon (`6s` sets sides), and Rotated rectangle
  (first corner, baseline endpoint, height).
- `A`: center arc. Draw → Center arc / Pie: center, radius point, end direction; or enter
  `radius, angle` such as `2m,90deg`. With a radius point set, a single value is
  the angle. Angles default to degrees; `rad` is supported. Pointer sweeps go
  counterclockwise around the plane normal; type a negative angle to reverse.
- Draw → Two-point arc: endpoints, then bulge point; or type a signed bulge.
  Three-point arc: start, a point on the arc, then end. Coordinates work at each
  phase. `24s` changes segmentation for all curves, including immediate re-entry.
- Draw → Drawing plane: automatic from the first hovered face, ground, selected
  face or custom origin/normal/horizontal direction. Drawing on an existing face
  subdivides its editing context.
- `T`: tape measure. Start on an edge or guide line for a parallel offset guide;
  start on a point for a distance and guide point. Enter `900mm` for an exact sill
  height. Draw → Protractor: center, baseline endpoint, then angle point or `45deg`.
  Numeric re-entry revises the last guide as one undoable operation.
- Tap `Ctrl` while measuring, or uncheck Draw → Create guides when measuring, to
  measure without editing the document. View → Show guides controls both display
  and snapping. Edit → Delete all guides clears them in one undo step.
- Guides appear as dotted overlays through faces and never form model faces.
  Guide points, lines and true 3D intersections can be acquired by drawing tools;
  guide lines also supply parallel/perpendicular references.
- `Space`: select. `P`: select a face, move to preview, then click/drag to finish
  or enter a signed world distance along its transformed local normal. Numeric
  re-entry revises the last operation. Double-click a face to repeat that distance
  as a new undo step. Tap `Ctrl` to retain the starting face while creating a new
  cap and sides; Draw exposes the same mode. Retaining intermediate faces can
  create non-manifold internal boundaries; turn it off to cut a through opening.
- With Select active, click faces/edges/guides; `Ctrl` adds and `Shift` toggles.
  Drag left-to-right to select fully enclosed visible entities, right-to-left to
  select touched visible entities. Occluded geometry is excluded in both modes.
  Double-click a face for its boundaries; triple-click for connected geometry.
- `Tab` / `Shift+Tab` traverses visible entities; `Ctrl+A` selects eligible geometry.
  The Outliner selects whole contexts and supports `Ctrl` multi-selection.
  `Enter` on a context opens it; `Escape` clears selection, then exits one level.
- Edit offers temporary hide/reveal and context lock/unlock. View → Show hidden
  geometry exposes hidden entities but does not bypass locks or the active context.
  These view states are session-only. Persistent group visibility and locks are separate.
- `Ctrl+G`: make a group; `Ctrl+Shift+G`: explode selected groups/components.
  Enter or double-click opens a context; Escape or an outside click closes one level.
  The breadcrumb returns to an ancestor. `G` opens Make component from the viewport.
  Edit offers Make component, Place component,
  Replace component, Change component axes and Make unique. Raw face/edge/guide
  selections can become components in one undo step.
- A persistent banner names the active shared definition and counts its instances.
  Drawing, transforms, grouping, paint and deletion inside that scope update all
  instances. Make unique isolates the active placement, including nested ownership.
  A locked affected instance rejects the entire shared edit. Placement dialogs use
  world coordinates; the axes dialog uses component coordinates and preserves
  world geometry. The [native component evidence](verification/R033c-native-components.md)
  records tested workflows and limits.
- `M`: move; `Q`: rotate; `S`: scale. Select geometry, choose a pivot, then a
  destination (plus a baseline/reference for rotation or scale). Type exact
  displacement, angle or scale factors in Measurements. Re-entry revises the same
  undo item. With no selection, Move can target an inferred vertex.
- After a Move or Rotate copy, type `xN` for N new copies or `/N` for N equal
  intervals ending at the chosen destination. Counts are limited to 1–100;
  re-entering counts, distance or angle revises the same undo item.
- `Ctrl` toggles transform copy mode; Edit also provides copy/local-axis settings
  and X/Y/Z flips about the selection center. Raw copies stay in their editing
  context; whole-context copies duplicate the hierarchy. Local mode requires one
  context. `[x,y,z]` always denotes world coordinates. `B`: change context color.
  `Delete` erases the selected entities as one undo step. Mixed deletion is bounded
  to 100 subentities per operation; select a whole context for bulk deletion.
- Point inference acquires endpoints, midpoints, curve centers, intersections,
  edges and faces within 8 logical pixels. Marker shapes and labels identify the
  result; `Tab` cycles nearby alternatives. Drawing from loose geometry adopts
  its context. Locked planes exclude off-plane points. Index preparation runs in
  the background; the 0.1 m grid remains the fallback when no candidate is acquired.
- Middle drag or `O`: orbit. Right drag or `H`: pan. `Z`: drag to zoom.
  `Alt`+left drag temporarily orbits within a drawing tool; add `Shift` to pan.
  Wheel: zoom around the pointer on the camera target plane. `Shift+Z`: fit.
- View → Navigation → Trackpad enables two-finger scrolling to pan,
  `Alt`+scroll to orbit and `Ctrl`+scroll to zoom. Native pinch/pan/rotate events
  also navigate while preserving an anchored tool. Navigation mode is remembered.
- `1/2/3` with Select active: perspective/top/front. View adds orthographic,
  right/back/left/bottom/isometric presets and a remembered 5–120° vertical FOV.
  Projection changes preserve target-plane scale; fit accounts for FOV and aspect.
  `Escape`: cancel drawing.
- `Ctrl+Z` / `Ctrl+Shift+Z`: undo/redo. `Ctrl+K`: commands, objects and recent files.
- `F6` / `Shift+F6`: move between window regions. `Ctrl+Shift+T`: toggle the Model panel.
- `Ctrl+O` / `Ctrl+S`: native open/save dialogs. Unsaved changes prompt before replacement or close.

With a drawing tool active, typing a digit or `[` sends input to Measurements.
`[x,y,z]` sets an absolute point; `<x,y,z>` sets a relative point. Comma-decimal
locales use semicolons between dimensions/coordinates. The selected drawing plane constrains the point. Entering another value immediately after completion revises that operation
as one undo item; an intervening edit or undo/redo invalidates re-entry. Escape in
Measurements returns focus to the viewport. Invalid input remains selected and
marked with an explanation.

## Saving, recovery and themes

Automatic recovery copies are enabled every 30 seconds; File → Recovery settings
changes the interval (5–3,600 seconds) or disables it. The recovery status shows
only the last verified copy and identifies newer edits still in memory. A write
failure pauses automatic attempts; File → Save recovery now retries.
Recovery never overwrites your saved file. Startup and File → Recover work let
you open a verified copy as Edited, open the last saved file, or discard selected
recovery data. Recovered work first saves to a new native path.
The CLI can inspect copies with `--recovery-list ROOT` and reopen one with
`--recover ROOT/SESSION --output copy.sketchyup`.
Save explicitly for durable named files: explicit saves use a
checksummed container and preserve the previous valid file as `.sketchyup.bak`.
Files and the containing directory are synced before showing Saved. Open a backup
through the file dialog's all-files filter or the CLI if you need the previous save. Light, Dark and System
themes are available in View. Groups and reusable components support nested, mirrored
and nonuniform transforms through both native tools and the headless command API.

## Formline import

Formline v1 files can be imported through File → Import Formline or
`sketchyup-cli --import-formline source.formline --output copy.sketchyup`.
Imports become editable boxes and 48-sided cylinders in a new unsaved model,
with names, colors, visibility and source identities retained. The report explains
conversion details; the original file stays unchanged. See the
[format decision](decisions/0014-formline-import.md).

## Assistant and rendering

Press `Ctrl+J` or choose View → Assistant. In Preferences, choose OpenAI and
**ChatGPT subscription**, then **Continue with ChatGPT**. Finish browser sign-in,
choose an account-specific model, and Save. Eligible requests use your ChatGPT
plan; Manage ChatGPT usage opens its usage/access settings. You can select saved
accounts or add another account/workspace. Sign out removes the selected session.

Alternatively, select **API key (separate API billing)**, enter an explicit model
ID and store an API key. Both connections require `secret-tool` (Arch package
`libsecret`) and an available, unlocked Secret Service on Linux. Credentials are
never stored in preferences or native files. Subscription sessions are separate
from API keys; SketchyUp does not read Codex's credential files.
The first request asks you to approve sending model context to OpenAI. “What is
sent” explains attachments and the bounded document inspection tools available
to the provider. Keys do not belong in chat, terminal arguments or model files.

Preview first is the default. Review the hatched geometry, changed objects and
host-measured bounds/area, then Apply (`Ctrl+Return`) or Discard. Apply adds one
undo entry. Refine / re-plan starts a fresh request on the current model. A manual
edit makes an older proposal stale. Direct mode uses the same validated commit
path. Deletion and shared-definition edits require the corresponding per-request
checkbox. If an outcome is unknown, use Reconcile before editing or saving.
Escape returns focus to the model. Without a configured provider, ordinary
modeling, saving and rendering remain available.

The optional local provider uses an explicitly configured numeric loopback
endpoint and model. The measured Ollama 0.35.1 / `qwen3:4b-instruct` CPU profile is
experimental: all four live corpus tasks reached the five-minute limit. It has
no automatic download or cloud fallback. See [provider evidence](verification/R045-local-provider.md).

Choose Camera → Render to set an explicit Blender executable, camera, resolution,
samples and CPU or supported GPU device. Blender 5.2 LTS is supported; CPU is the
default. The job renders an immutable snapshot while editing continues. Results
identify the source revision, show when the model has changed, and can be saved
as PNG. Blender is optional. See [render evidence](verification/R050-native-render-ui.md).

The [M5 acceptance procedure](M5_ACCEPTANCE.md) describes the reproducible
room/window workflow, retained evidence, live provider corpus and package setup.
The [M5 gate](verification/M5.md) and [M6 gate](verification/M6.md) are complete, and the [M7 checkpoint](verification/M7-accepted.md) is accepted. The [M8 gate](verification/M8.md) and the [M9 gate](verification/M9.md) are accepted.
The [M6 acceptance procedure](M6_ACCEPTANCE.md) reproduces the integrated
roof/stair/joinery/furniture study, site placement and live assistant checks.

## Optional Blender rendering

In the native editor, choose **Camera → Render…**, select an installed Blender
5.2 LTS executable (or leave the path blank to discover `blender`), and check its
devices. Choose Cycles or Eevee preview, the current camera or fit the visible
model, resolution and samples. Cycles supports an explicitly selected compute
device with optional CPU fallback. Eevee uses the reported active OpenGL renderer;
changing the engine requires a new device check. Eevee's approximate indirect
lighting appears in the transfer report. Blender remains optional for editing and
saving native models.

Enabled sun studies carry into the captured render. An optional 2:1 Radiance HDR
panorama supplies the environment, with strength and rotation controls; its bytes
are captured so moving or deleting the original file cannot change queued work.

Keep modeling while captured snapshots render. The status chip opens **Jobs**, with
progress, elapsed time, logs, cancellation and retries. Up to two workers run at
once. The store permits at most eight pending captures and sixteen retained jobs,
subject to a conservative 2 GiB storage budget; remove finished jobs when it is full. **Retry capture**
uses the original model/settings. Use Render again for a fresh capture.

Verified images open beside the Model tab, with the original revision and a label
when the model has changed. **Save image as…** writes the PNG independently of
model Save. Two result tabs stay open at most; closing one keeps its image in Jobs.
Retained results survive restart and can be reopened there. Interrupted work is
available for explicit retry, while queued work resumes. **Remove** and **Remove all
finished jobs** delete their stored captures, images and logs; pending jobs remain.

**Open scene in Blender…** saves a packed `.blend` from that result's captured model
and then launches Blender. The file includes supported textures, HDR lighting,
camera/settings and a transfer manifest. This is one way: edits made in Blender do
not return to the native model. Any later import is a separate, potentially lossy
conversion. Scene creation can be canceled without changing the model or result.

See the [GLB material/geometry limitations](decisions/0032-glb-snapshots.md)
and each result's transfer report for unsupported scene details.

The optional local assistant adapter uses a measured Ollama 0.35.1 profile on a
numeric loopback endpoint. It sends no credentials or images, checks runtime and
model capabilities before document transfer, and rejects context overflow rather
than silently dropping history. See the [local profile and trial evidence](verification/R045-local-provider.md)
for the exact model digest, CPU limits, known failures and opt-in corpus runner.
Ordinary modeling does not require a provider.

## Walk and scene timing

The Camera menu includes **Look around** and **Walk**. Look around keeps the eye
fixed while dragging or pressing arrow keys; scroll changes the lens. Walk uses
WASD/arrows, Q/E for height, Shift for faster movement and scroll for speed. Escape
returns to Select. Navigation does not edit the model or its undo history.
The Scenes panel remembers a transition duration from zero to ten seconds; zero
or reduced motion recalls cameras immediately.

## Saved-scene animation

Render setup offers **Export scene animation** after checking Blender. Choose
saved camera scenes in their presentation order, frame rate, transition/hold times
and a new output folder. Export produces up to 240 PNG frames and a timing manifest;
Cancel keeps finished frames. Cameras, visibility, named sections and sun studies
come from an immutable capture, so modeling can continue during export. Transfer
limitations are recorded per frame. Temporary clipping/show-hidden overlays must
be disabled in saved scenes. The first exporter has no movie encoding or crash
resume; an unfinished manifest and any completed frames remain for inspection.
See [capture semantics](decisions/0106-immutable-animation-capture.md) and
[frame export](decisions/0107-native-animation-frame-export.md).

## Milestones and integrations

This summary was written at the M9 gate, before 1.0.0; the [roadmap](PR_ROADMAP.md) and the
[release notes](RELEASE_NOTES.md) carry the history since.

The [108-entry roadmap](PR_ROADMAP.md) has passed its M0 feasibility and
M1 native foundation, M2 editable geometry, M3 manual drawing, M4 editing/recovery, M5 automation and M6 advanced-modeling gates. The M7 presentation and rendering checkpoint is [accepted](verification/M7-accepted.md). The [M8 exchange and extensibility gate](verification/M8.md) is accepted, and the [M9 release-hardening gate](verification/M9.md) is accepted at the 1.0.0 release candidate. Shared components support native editing.
OpenAI and experimental loopback Ollama adapters, transactional previews and optional
Blender rendering are implemented. Live OpenAI acceptance passed the M5 and M6
workflow gates; the measured local CPU Ollama profile timed out on the initial
modeling corpus. Native
exchange covers GLB/glTF, OBJ/MTL and STL import/export, a documented 2D DXF subset and measured PDF/SVG views, with explicit conversion losses; see [Inspect and migrate native documents](COMMAND_LINE.md#inspect-and-migrate-native-documents) and the sections after it. Curves retain analytic parameters alongside configurable segmented editing geometry. The native storage contract is described in the [command-line reference](COMMAND_LINE.md#inspect-and-migrate-native-documents).

The original local Formline/Electron prototype was removed at the owner’s request. The native
application lives in the main project checkout; the supplied UX design references are preserved.
