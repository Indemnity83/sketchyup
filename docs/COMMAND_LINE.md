# Command-line and scripting reference

`sketchyup-cli` runs the same core operations as the desktop app, with no display. Run
`sketchyup-cli --help` for every option, `sketchyup-cli --capabilities` for the scripting commands, and
`sketchyup-cli --describe-command NAME` for one command's parameters. The
[generated tool reference](TOOL_REFERENCE.md) lists every command and query, and the
[modeling agent guide](AI_MODELING.md) describes the transports. Some sections below also describe the
matching desktop command. The examples run from the repository root against a development build.

This reference moved here from the project README.

## Inspection, sessions and transactions

Versioned bounded inspection is available through `--inspect document.describe --input MODEL`
for summary discovery, or `--inspect-file REQUEST.json --input MODEL` for typed
hierarchy, topology and measurement requests. The in-process inspection session
also supports bounded, expiring snapshots; see the [snapshot contract](decisions/0020-inspection-snapshots.md). Pages are limited to 100 rows and
256 KiB; stale references fail explicitly. File-only queries do not claim access
to desktop selection. See the [inspection contract and schemas](decisions/0019-bounded-inspection.md).
Native in-process inspection reads the actual window selection and captures a
bounded PNG with camera metadata. `sketchyup --inspection-capabilities` prints
its registry; see the [desktop inspection contract](decisions/0021-desktop-inspection.md).
Private transaction preparation and durable outcome reconciliation are implemented
in-process; see the [coordinator contract](decisions/0024-transaction-coordinator.md).
Incremental begin/apply/inspect/preview/commit dispatch uses versioned schemas,
immutable commit identities and cached append receipts; see the
[transaction contract](decisions/0025-transaction-dispatch.md).
Persistent headless sessions use `--session --input MODEL --outcomes DIRECTORY`,
with optional `--output MODEL` for an explicitly bound save destination. Create a
new baseline with `--session --new --output MODEL --outcomes DIRECTORY`.
`--session-capabilities` prints the shared schemas. Requests and replies use bounded
JSON lines; see the [session protocol](decisions/0026-headless-session.md).
Use `assert.measurement` inside an edit batch or transaction to require a final
body measurement to match an explicit expected value and absolute tolerance.
It supports local/world dimensions, bounds, edge length, face area and validated
solid volume. A failed assertion rolls back the whole edit; later steps in the
same draft must keep earlier assertions true. See the
[asserted-solid example](../examples/asserted-solid.json) and
[measurement contract](decisions/0055-geometric-assertions.md).

## Recipes, MCP and GLB snapshots

Versioned recipes pass typed results between those same requests:
`--recipe examples/transaction-face-recipe.json --new --output /tmp/face.sketchyup --outcomes /tmp/face-outcomes`.
The [room/window recipe](decisions/0031-room-window-recipes.md) creates a 6 × 4 m
room and widens one window from 1.2 to 1.4 m while preserving its sibling and frame
thickness:

```sh
sketchyup-cli --recipe examples/room-window-resize-recipe-v1.json --new \
  --output /tmp/recipe-room.sketchyup --outcomes /tmp/recipe-room-outcomes
```

Window dimensions are outer-frame dimensions. The room-only variant is
`examples/room-recipe-v1.json`; installed recipes live under
`/usr/share/doc/sketchyup/examples/`.

The [gable roof recipe](decisions/0056-gable-roof-recipe.md) adds an editable
closed slab with explicit pitch in degrees, overhang and vertical thickness.
`assembly.roof` preserves existing room/window content and verifies its volume,
area and bounds before publication. Run `examples/roof-recipe-v1.json` to create
and save the default room with its roof; native before/after files are also shipped.

The [straight stair recipe](decisions/0057-straight-stair-recipe.md) creates a
filled flight with equal risers and explicit tread depth, width and final elevation.
`examples/stair-recipe-v1.json` places the default flight beside the room and roof;
each tread, the closed volume and preservation of the scene are verified.

The [table and cabinet recipes](decisions/0058-furniture-recipes.md) build
measured solid members with shared component legs or panels. Their examples are
`examples/table-recipe-v1.json` and `examples/cabinet-recipe-v1.json`. Member dimensions,
clearances and volumes are verified; ordinary shared and instance-only edits remain
available afterward.

The [site placement recipe](decisions/0059-site-placement-recipe.md) moves an
existing assembly with explicit position units, a world or parent frame and a yaw
delta. Local geometry, materials, shared components and complete hosted assemblies
are preserved. `examples/site-recipe-v1.json` builds and places the full study in
one transaction; adopted native before/after fixtures are also included.

See the [recipe contract](decisions/0027-transaction-recipes.md) and
`--recipe-capabilities`. A local MCP stdio client can use `--mcp` with the same
explicit document/outcome options. It targets protocol 2026-07-28; see the
[MCP contract](decisions/0028-local-mcp.md) and `--mcp-capabilities`.
For actual desktop selection and camera inspection, launch an explicit native
model with `--mcp-inspection-socket` and connect using
`sketchyup-cli --mcp-connect SOCKET`; see the
[native MCP binding](decisions/0029-native-mcp.md).
Export a fixed render snapshot with
`sketchyup-cli --input MODEL --export-glb NEW_DIRECTORY`, optionally adding
`--render-settings examples/render-settings-v1.json`. The directory contains
`scene.glb` and its revision/settings/hash manifest. Export works without Blender;
Distinct front/back colors, opacity and PNG/JPEG textures are preserved in GLB and
Cycles, including independent projections, reversed faces and mirrored instances.
Managed PNG/JPEG images also appear in the modeling viewport, with independent
side projections and selection through fully transparent pixels; see the
[native preview contract](decisions/0065-viewport-textures.md) for filtering,
background decoding and preview limits.
Original image bytes remain packaged alongside normalized render images. Missing,
invalid or unsupported images retain the swatch color and report their status;
see [textured transfer](decisions/0064-textured-glb-export.md),
[two-sided transfer](decisions/0050-two-sided-export.md) and the
[GLB subset and loss policy](decisions/0032-glb-snapshots.md).
The headless binding reports desktop selection as unavailable. The native binding
exposes inspection only; staged mutation tools are currently available headlessly.


## Scripting examples

```sh
./build/dev/sketchyup-cli --capabilities
./build/dev/sketchyup-cli --describe-command geometry.translate
./build/dev/sketchyup-cli --script examples/room-shell.json --output /tmp/room.sketchyup
./build/dev/sketchyup-cli --input /tmp/room.sketchyup
./build/dev/sketchyup /tmp/room.sketchyup
./build/dev/sketchyup-cli --input /tmp/room.sketchyup --query geometry.inspect --context 1
./build/dev/sketchyup-cli --script examples/split-wire.json --output /tmp/wire.sketchyup
./build/dev/sketchyup-cli --script examples/planar-grid.json --output /tmp/grid.sketchyup
./build/dev/sketchyup-cli --preview --script examples/through-opening.json
./build/dev/sketchyup-cli --script examples/tilted-drawing.json --output /tmp/tilted.sketchyup
./build/dev/sketchyup-cli --script examples/curves.json --output /tmp/curves.sketchyup
./build/dev/sketchyup-cli --script examples/guides.json --output /tmp/guides.sketchyup
./build/dev/sketchyup-cli --script examples/transforms.json --output /tmp/transforms.sketchyup
./build/dev/sketchyup-cli --script examples/copy-arrays.json --output /tmp/arrays.sketchyup
./build/dev/sketchyup-cli --script examples/components.json --output /tmp/components.sketchyup
./build/dev/sketchyup-cli --script examples/tags.json --output /tmp/tags.sketchyup
./build/dev/sketchyup-cli --input /tmp/tags.sketchyup --query tags.describe
./build/dev/sketchyup-cli --script examples/entity-info.json --output /tmp/entity-info.sketchyup
./build/dev/sketchyup-cli --input /tmp/entity-info.sketchyup --query entity.inspect --context 1
./build/dev/sketchyup-cli --input /tmp/curves.sketchyup --query-file examples/inference-query.json
```

## Geometry, guides, tags, materials and assets

`geometry.transform_selection` accepts typed context/face/edge/vertex/guide
entities, a column-major affine `matrix`, an optional `pivot`, `space` (`world`
or `local`) and boolean `copy`. Shared vertices move once; incident geometry
stays attached, and invalid nonplanar or collapsed results reject atomically.
Raw copies receive fresh geometry IDs inside their existing context; whole-context
copies duplicate the hierarchy. The result includes typed copy mappings. Preview
geometry includes world transforms, including children moved by a parent.
The [transform contract](verification/R030a-scoped-transforms.md) records
limits; the [native tool evidence](verification/R030b-native-transforms.md)
describes pointer input, numeric amendment and frame semantics.

Guide points and infinite guide lines are available through `guide.point`,
`guide.line`, `guide.angle`, `guide.offset`, `guide.erase` and `guide.clear`.
Guides remain separate from faces/edges. `guide.clear` with body `"0"` removes
all guides in one undo step; a body ID scopes cleanup. Creation accepts local or
world coordinates, angles use radians, and offsets use meters in the selected
space. `geometry.measure_distance` and `geometry.measure_angle` are read-only
queries for world-coordinate points. `geometry.infer` accepts `includeGuides`
(default true) and an optional direction reference with `body` plus `guide`
in place of `edge`; results identify both sources of mixed intersections.
The current file schema is version 17. It stores a document-owned model style,
independent front/back texture projections, hosted component attachments,
uncut geometry and stable opening identities, explicit component glue-face
references and cutting behavior, persistent edge appearance flags,
display units, managed assets, material swatches and front/back
assignments, tag folders and assignments, canonical component definitions and
stable instance-member bindings. Versions 1–16 migrate to a deterministic default
model style, and versions 1–15 acquire no explicit texture projections. The
[style contract](decisions/0068-model-styles.md) defines the stored record;
View → Model styles exposes display modes, profiles and visibility controls,
with a Colors and details dialog for colors, ground height, profile width and
X-ray opacity. These are saved with the model and remain independent of the
application theme. `document.style` applies a complete style record, and
`document.describe` reports it; see the [example](../examples/model-style.json) and
[native contract](decisions/0069-native-model-styles.md). Versions 1–14 acquire no invented host attachments;
versions 1–13 acquire no invented glue behavior.
Versions 1–10 acquire no invented assets; versions 1–9 preserve legacy colors without
inventing swatches; versions 1–8 migrate with all entities Untagged, and versions
1–7 acquire no invented components. Earlier group and guide migrations remain supported.

`tag.create`, `tag.edit`, `tag.delete` and `tag.assign` manage tags separately
from scene ownership. Tag `"0"` means Untagged. Folder visibility affects its
descendant tags; hiding a tag preserves geometry and transforms. `tags.describe`
reports local and effective visibility. Component placement tags are local;
member assignments use shared component scope. `scene.rename` names an entity.
The Model panel offers Outliner, Tags, Info and Materials tabs. Search filters the entity
hierarchy while retaining matching ancestors. Enter/double-click opens a context;
Escape closes it. F2 renames, Space toggles visibility, Ctrl+Shift+L toggles an
entity lock, Ctrl+Shift+M opens Move to, and Ctrl+Alt+T assigns a tag. Buttons
provide the same operations. Drag onto a group/folder to reparent, or onto empty
space to move to the root; world placement is preserved. Tags offers folder and
tag creation, visibility checkboxes, rename, move, assignment and unused deletion.
Hidden/locked rows remain available for inspection and reveal/unlock. Shared
member edits still require opening their component context. See the
[native organization evidence](verification/R034b-native-organization.md).

`material.create`, `material.edit` and `material.delete` manage named in-model
RGB/opacity swatches. `material.assign` targets a face or a record's own faces,
with `front`, `back` or `both` sides; material `"0"` restores the legacy color.
Splits, extrusion, copies, grouping and mirrored consolidation retain both sides.
Shared component member assignments use explicit component scope; swatch table
edits remain document-wide. `materials.describe` lists swatches and
`material.sample` reports both sides without editing. See the
[material contract](decisions/0010-material-records.md) and
[recipe](../examples/materials.json). The viewport renders independent front/back
colors and opacity, including mirrored placements. Fully transparent sides pass
face picking through; topology edges remain visible. Editing a swatch refreshes
only dependent appearance buffers. Intersecting transparent surfaces retain the
centroid-sorting limitation. The Materials tab edits named swatches and offers local presets through New.
Choose Front, Back or Both sides; Apply paints selected faces. B activates Paint;
Alt-click samples the visible side. Open a group/component before painting its
contents. Swatch edits affect every use; assignments in an opened component
remain shared. See the [rendering contract](decisions/0012-material-rendering.md).

`asset.import` stores canonical base64 bytes; `asset.missing` retains an explicit
missing-resource record. `asset.replace` resolves/replaces bytes under the same
identity, or accepts null data to mark a resource missing. `asset.delete` rejects
resources still referenced by a swatch. Material create/edit accepts `asset`
(`"0"` clears it). `assets.describe` returns a checksummed manifest without raw
payloads; material queries expose missing/present status. Native containers own
their bytes and survive relocation without the source files. Asset paths are
fixed logical keys, never filesystem extraction paths. Limits are 16 MiB per
asset, 64 MiB per document and 1,024 records. See the
[asset contract](decisions/0011-managed-assets.md). Schema 16 retains independent
front/back affine UV projections through modeling edits, Undo, shared components
and relocation ([mapping contract](decisions/0062-face-texture-records.md)).
The image backend decodes bounded static PNG/JPEG assets into consistent sRGB
and straight-alpha pixels ([image contract](decisions/0063-texture-image-decoding.md)).
GLB/Blender export and the native viewport display those images with independent
side mappings. `material.map_texture` authors planar, three-pin or affine
projections in explicit local/world coordinates; null resets the chosen side(s).
Face inspection returns stored and effective mappings. See the
[command contract](decisions/0066-texture-authoring-commands.md) and
[packaged example](../examples/texture-mapping.json). Select editable faces and use
**Texture mapping…** in Materials to set repeat dimensions, origin, rotation and
UV offset. Choose a source face and world coordinates to project one mapping
across selected faces. **Reset mapping** restores the chosen sides to their default
projection. See the [native editor contract](decisions/0067-native-texture-editor.md).
Materials offers Attach file, Replace file
(including missing-resource resolution), Detach file and undoable Clean files
for unused resources. New/edit dialogs can also bind an existing stored file.

## Measurements and entity properties

`entity.inspect` reports world, parent and intrinsic bounds, lengths and areas.
Volume is present only after bounded material-solid validation, including enclosed
cavities. Open, invalid, multiple-record or disconnected material geometry returns
null volume with a reason.
`entity.position` and `entity.dimensions` edit real placement/geometry in world or
parent coordinates. Intrinsic measurements remain separate from placement scale.
`entity.properties` stores typed semantic values for recipes. See the
[measurement contract](decisions/0009-entity-measurements.md). The Info tab
shows the selected entity in an explicit coordinate frame. Edit entity (F2)
accepts metric/imperial or locale-aware origin/dimension values and edits name
and tag in the same undo step. Invalid inputs stay in the dialog for correction;
Cancel changes nothing. Resizing uses the bounds minimum; an explicitly entered
origin is applied afterward. Closed components edit their placement, while an
opened component's members use shared scope. Inspect problem geometry selects
available offending edges/faces without modifying the model. See the
[native Entity info evidence](verification/R035b-native-entity-info.md).

## Groups and components

`component.create` converts a geometry/group root into a reusable definition;
`component.selection` converts typed selected faces, edges, guides or contexts;
`component.instance` places it with a parent-local affine matrix. `component.edit`
runs a nested command batch using canonical member IDs from `component.inspect`
and propagates the change to every instance in one undo step. Its `world` space
means definition coordinates. New model-root records created inside this scope
become children of the definition root. Editing resolved member geometry outside
this explicit scope rejects; a locked affected instance rejects the whole edit.
`component.make_unique` isolates a placement; for nested placements it also clones
the ancestor ownership path. `component.replace` keeps placement while replacing
members with fresh scene IDs. `component.axes` changes a definition's local frame
while preserving world geometry in all placements. Whole-context copies/arrays
continue sharing definitions; explode removes the selected binding and retains
geometry. See the [command contract](verification/R033b-component-operations.md).
For native adapters, `component.edit` also accepts an `instance` matching the
specified definition. Inner commands then use that placement's scene IDs and
world coordinate frame. Geometry stays canonical; the temporary editing frame
is removed before publication. The operation reports created members for the
initiating placement, while topology changes still cover every affected instance.
`scene.state` with body `"0"` and false flags reveals/unlocks the whole document,
including canonical component members, in one undo step; global hide/lock rejects.

`group.create` groups sibling context IDs while preserving their geometry, colors
and world placement. `group.explode` removes one group boundary and merges eligible
promoted raw geometry; `merge: false` requests boundary removal alone;
`scene.reparent` moves a record to a group (or parent `"0"`) while preserving its
world transform. `scene.state` stores boolean `hidden` and `locked` flags, with
inherited visibility and authoritative protection of locked descendants. See
[the group recipe](../examples/groups.json). Select faces, edges, guides or whole groups and use `Ctrl+G` to make a group.
Double-click or Enter opens it; Esc closes one level. The viewport breadcrumb
links to parent contexts. `Ctrl+Shift+G` explodes selected groups. The Edit menu
also exposes persistent group hide/lock and document-wide reveal/unlock.
Drawing and deletion stay in the active context. The Edit menu can merge raw
geometry in that context through `geometry.merge_context`, with coincident seam
welding and per-face colors preserved. Nested groups, locked records and hidden
geometry stay isolated. This operation does not boolean intersecting faces. See
[consolidation semantics and evidence](verification/R032c-context-consolidation.md).

Hosted components use an explicit canonical glue face and an ordinary geometry
host. `component.glue` sets or clears the definition's member/face, local anchor,
tangent and cutting flag. `component.attach` places an instance on a host-local
anchor; optional tangent, signed scale, rotation in radians and normal inset
control placement. `component.bind` preserves its current pose and requires the
explicit host-local inset. `component.detach` restores its opening;
`component.bake_host` keeps the cut geometry and releases all attachments on that
host. Moves and shared-definition edits automatically regenerate attached openings
with surviving reveal identities and paint preserved. Copying or arraying an attached
whole instance retains its host and creates independent openings. Copy the host with
all its attachments (or their enclosing group) for an independent assembly; partial
attachment subsets are rejected. A host-only copy keeps baked cut geometry. Native
Ctrl-copy, `xN`, `/N` and exact spacing revisions share one Undo step. See the
[executable example](../examples/hosted-component.json) and
[hosted-component contract](decisions/0054-hosted-components.md).

Use `entity.describe` to discover a materialized face's canonical member binding,
and `component.instances` to inspect the definition's glue and paged attachments.
The assistant advertises attach/bind/detach as routine operations, glue edits with
shared-definition permission, and baking with destructive-edit permission.

For native placement, enter a component, select its alignment face and choose
**Edit → Set glue face**. Set its local anchor/direction and explicitly enable
opening cutting when wanted. Leave component editing, select the whole component
and Ctrl-click one host face, then press **Shift+H**. Move on that face to preview;
click or Enter applies, and Escape cancels. Measurements accepts three host-local
anchor coordinates or one signed inset length; repeated numeric input revises the
same Undo item. **Attachment placement options** sets rotation in degrees, signed
scale and inset; restart placement after closing it. **Bind component at current
pose** uses the explicit inset while retaining position. Edit also offers detach,
clear shared glue, and bake host openings.

To upgrade a validated room recipe, select the whole room and choose
**Edit → Adopt recipe window attachments**. This gives both windows general hosted
behavior in one Undo step, retaining their poses, IDs and paint. Existing files
keep their original relationships until explicitly upgraded. The shared command
is `assembly.room.adopt_hosted` with the room's `body` ID; the
[executable example](../examples/hosted-room-recipe-v1.json) creates and adopts a room,
then widens one window. Definitions used outside the room must first be made unique.
The authored instance-only resize remains available after adoption, while ordinary
Move and Delete update openings through the general host system.

## Topology, solid tools and face orientation

The topology query exposes stable context-scoped edges, oriented loops and radial
adjacency, plus analytic curve parameters and ordered derived-edge references.
Curve command angles use radians; segment counts are bounded to 256. Curve
metadata survives edge splits and retires when an edit breaks its outline. The wire recipe demonstrates a loose edge and a propagated edge split;
these operations currently have command paths while direct edge tools are in progress.
The planar-grid recipe forms four editable faces from finite segments. Planar insertion
handles intersections, overlaps and holes within the documented arrangement limits.
Intersect (**I**) inserts crossing or coplanar intersection edges into selected
faces. Use Select and Ctrl-click to choose targets, then I to preview; Enter or
click applies, Escape cancels, and Alt-drag orbits. Draw → Intersection references
chooses Selected faces, Active context, or Model. Context and Model retain
unselected reference bodies; only target bodies change, with target descendants
selected and one Undo item. Context stops at group boundaries; Model reads
persistently visible scene geometry across groups, including from an explicit
component edit. Existing seams produce an actionable no-change message. The same
operation is available as `geometry.intersect`; see the
[intersection contract](decisions/0045-face-intersections.md).

Solid tools (**Shift+B**) previews the two selected solids; selecting a face
from each is enough. Draw → Solid operation options chooses Union, Subtract,
Intersection, Trim, Split or Outer Shell. The viewport identifies target and tool by name and
ID; Swap target and tool reverses subtraction order. Keep originals is enabled
initially. Turning it off consumes both in the same Undo item. Trim instead
shows **Keep target (tool always retained)** and only replaces the target.
Split creates target-only, tool-only and overlap regions; Outer Shell fills
enclosed cavities while preserving through-holes. All generated regions are
selected together. Enter or click applies, Escape cancels, and Alt-drag orbits
while preserving the preview. Empty results explain whether the originals
will be retained or removed. Shared component edits update all instances; use
Make Unique first for an independent edit.

`geometry.boolean` combines two editable raw solids in one context using `union`,
`subtract` (target minus tool), or `intersection`. The required `keepOperands`
choice retains the exact sources or consumes them in the same Undo item. Outputs
inherit source face colors and correctly oriented front/back materials; receipts
identify the generated bodies and each source face. Enter group containers before
choosing their raw solids. Enclosed cavity boundaries stay with their surrounding
material solid; islands inside cavities become separate output bodies. See the
[Boolean contract](decisions/0046-solid-booleans.md) and
[executable example](../examples/solid-boolean.json). The
[enclosed-cavity example](../examples/enclosed-cavity.json) produces a 7 m³ hollow
solid from an 8 m³ cube and a 1 m³ internal cutter.

`geometry.trim` subtracts the tool while always retaining it; `keepTarget` selects
whether the target also survives. `geometry.split` returns separate target-only,
tool-only and overlap regions. `geometry.outer_shell` fills enclosed cavities of
the union while preserving exterior through-holes. Split and Outer Shell require
`keepOperands`. All three require `body`, `tool` and `context`, publish one Undo
item and return region/provenance records in `solidOperations`. See the installed
[Trim](../examples/solid-trim.json), [Split](../examples/solid-split.json) and
[Outer Shell](../examples/solid-outer-shell.json) examples and the
[publication contract](decisions/0048-split-outer-shell.md).

Face orientation (**Shift+O**) previews selected faces with arrows showing their
new front direction. Draw → Face orientation options chooses **Reverse selected
faces** or **Orient connected faces to selected reference**. Orient requires one
reference face and keeps its direction. Enter or click applies, Escape cancels,
and Alt-drag orbits. Physical front/back appearance and selection are retained;
shared component edits affect all instances. Use Make Unique for an isolated edit.

`geometry.reverse_faces` reverses explicitly selected faces while preserving the
appearance of their physical sides, including front/back materials and opacity.
`geometry.orient_faces` preserves a reference face and makes its edge-connected
surface consistent. Both require an explicit `context`; non-manifold connections
and contradictory cycles reject with diagnostics. Preview, component editing and
Undo use the shared command path. See the [orientation example](../examples/face-orientation.json)
and [contract](decisions/0049-face-orientation.md).


`geometry.edge_appearance` sets independent `hidden`, `soft` and `smooth` flags
on explicit `entities` (`body`/`edge` pairs) in an explicit `context`. Supply at
least one boolean flag; omitted flags retain their current value. Flags persist
and participate in shared component edits, preview and Undo. Edge detail and
paged topology inspection expose them. Smooth flags now drive shared corner
normals in the viewport, GLB export and Blender renders, including mirrored
components. **Edit → Edge appearance** changes flags on selected edges.
Use **View → Show hidden geometry** to display hidden/softened edges as dashed
strokes and select them for Reveal or Harden. These actions keep other flags
intact and support Undo. Locks and group/component editing boundaries still apply. See the [edge appearance example](../examples/edge-appearance.json)
and [contract](decisions/0051-edge-appearance.md).

**Edit → Geometry diagnostics** opens findings for selected geometry or the active
editing context. Select or frame listed entities, refresh after edits, and preview
eligible orientation repairs. Connected orientation requires an explicit reference
face. Enter applies the preview; Escape cancels; Undo restores the edit. Shared
components follow their usual editing scope. Truncated samples cannot reverse a
whole shell, and diagnostics never delete unrelated geometry automatically.

`geometry.diagnose` inspects one explicit body record and returns bounded findings
for open boundaries, non-manifold geometry, inconsistent or inverted orientation,
loose geometry and near-degenerate faces. Counts distinguish complete scans from
lower bounds; omitted reference samples and incomplete analysis are explicit.
Diagnosis reads hidden geometry too, uses local coordinates, and excludes child
records. It never edits the model. The same query works through CLI inspection,
snapshots, MCP and the assistant. See the [diagnostic contract](decisions/0053-geometry-diagnostics.md).

## Follow Me, Offset and Push/pull

Follow Me (**Shift+F**) sweeps a selected profile face along selected connected
path edges. Use Select and Ctrl-click to add the face and path, then Shift+F to
preview; Enter or click applies, and Escape cancels. Alt-drag can orbit during
preview. The source profile, path, and selection are retained; the result is a
separate editable solid with one Undo item. Open and closed paths use bounded
miter joins and explicit frame transport. Branches, crossings, consumed short
segments and twisted closures reject with an explanation. Closed paths with
holed profiles are currently unsupported. `geometry.sweep` exposes the same
operation with local/world coordinates and generated face mappings; see the
[sweep contract](decisions/0044-profile-sweep.md).

Offset (**F**) draws parallel boundaries for a selected planar face, including
concave outlines and holes. Click a face and move across its nearest edge to
preview, then click or finish a drag; Escape cancels. Measurements accepts an
exact signed distance: positive outward, negative inward. Select a face first
for keyboard-only entry. Re-enter the distance to revise the last eligible offset
as one Undo item. The tool uses world distance even in scaled components.

The same `geometry.offset` command accepts `body`, `face`, `distance` and optional
`space` (`local` by default or `world`). All surviving islands contribute
boundaries; complete collapse rejects without changing the source. Original
faces and holes are retained: insets partition coverage, outsets can add exterior
faces, and contracted hole outlines remain wires inside the original void. The
tool does not automatically heal those holes. See
[the contract](decisions/0043-planar-offset.md) and
[CLI example](../examples/planar-offset.json).

`geometry.push_pull` supports isolated profiles, complete prism caps, recessed face
regions and push-to-opposite-face openings. Unsupported intersections reject before
committing. Use `--preview --script recipe.json` to inspect prospective geometry and
lineage without changing the input document; preview cannot save an output file.

## Scripts, units and history

A script is a local JSON array, validated and committed as one batch. The in-process
API checks document identity and revision; failed batches change nothing. This is
an experimental local driver, not yet the durable AI/MCP protocol. The example's
IDs are specific to its empty-document fixture. Query live IDs before editing an
existing document; do not reuse them across documents.

The `document.units` command sets per-document display/entry preferences to `m`,
`mm` or `ft-in`. Coordinate arguments remain meters. Changing units is undoable
and survives save/reopen and recovery; it never resizes geometry. The
[units contract](decisions/0018-document-units.md) describes schema 12 and
migration of older models. First run asks for default units; **File → Document
units** changes the current model and can set the default for new documents.
Bare lengths use that choice (feet for feet/inches); explicit unit suffixes still
override it. Measurements, tape readouts and Entity info show the document units.

The headless `history.describe` query exposes bounded labeled undo/redo pages.
A batch may attach a human label and task/request metadata; this remains local
session history and is not stored in model files. `--history-position N` navigates
the retained cursor after a CLI recipe. See the
[history contract](decisions/0017-labeled-history.md). Open **View → History**
to browse labeled steps, saved markers and attached task requests. Click a step,
or select it and press Enter, to move through the same stack as Undo/Redo. The
panel pages large histories and marks the retained baseline when old steps have
been pruned. History navigation returns keyboard focus to the model.

## Worked example: the M4 room study

The [M4 room study](../examples/m4-room-study.sketchyup) is an editable native model
with two window assemblies, nested frame groups, materials and millimeter units.
The [integrated workflow record](verification/M4.md) documents its construction,
shared/unique edits, History navigation, save/reopen and simulated crash recovery.

## Inspect and migrate native documents

The first public format is document schema 24 in a version-2 `.sketchyup` container.
The CLI validates older files without rewriting them and migrates only to a new
path:

```sh
sketchyup-cli --format-capabilities
sketchyup-cli --inspect-native model.sketchyup
sketchyup-cli --validate-native model.sketchyup
sketchyup-cli --migrate-native old.sketchyup --output migrated.sketchyup
```

Migration verifies the complete model and embedded assets before publishing the
copy. Existing destinations and in-place migration are rejected. See the
[public storage contract](decisions/0108-public-native-format.md).

## Exchange formats

### GLB and glTF

Use **File → Import GLB/glTF** to create an unsaved native model. Mesh instances,
hierarchy, placement, supported base colors/textures and cameras are converted;
the report explains omitted or approximated features. Save chooses a native file.

The CLI can inspect the conversion or publish a new native copy:

```sh
sketchyup-cli --import-gltf model.gltf
sketchyup-cli --import-gltf model.glb --output converted.sketchyup
```

The output must be a new path. Relative buffers/images must stay inside the source
folder. Skinning, morph targets, required unsupported extensions and unsupported
material modes reject explicitly. See the [import contract](decisions/0111-native-gltf-import-workflow.md)
for limits and exchange guarantees.

### OBJ and MTL

OBJ/MTL interchange supports editable polygons, wires, groups, diffuse colors, opacity
and contained PNG/JPEG textures. File → Import OBJ/MTL and Export OBJ package ask
for units and up axis. Export includes hidden model geometry without section clipping;
reports enumerate unsupported metadata and missing assets. Headless equivalents:

```sh
sketchyup-cli --import-obj source.obj --obj-unit mm --obj-up z --output converted.sketchyup
sketchyup-cli --export-obj new-package --input converted.sketchyup --obj-unit mm --obj-up z
```

Import output and export folders must be new. Keep exported OBJ, MTL and image files
together. See the [native OBJ workflow contract](decisions/0115-native-obj-interchange-workflow.md).

### STL

STL interchange uses explicit units and axes. File → Import STL offers per-copy
welding and opt-in degenerate-facet removal; File → Export STL writes a new binary
or ASCII file. Materials and hierarchy are not carried. For headless use:

```sh
sketchyup-cli --import-stl source.stl --stl-unit mm --stl-up z --stl-weld exact --output new.sketchyup
sketchyup-cli --export-stl new.stl --input new.sketchyup --stl-unit mm --stl-up z --stl-encoding binary
```

See [STL workflow and limits](decisions/0119-native-stl-interchange-workflow.md).

### 2D DXF

The documented 2D DXF subset imports lines, supported polylines, arcs, circles and
layers as editable edges. File → Import 2D DXF lets you use declared units or an
explicit override; File → Export 2D DXF writes all world-XY edges to a new drawing.
Unsupported entities and metadata losses are reported.

```sh
sketchyup-cli --import-dxf source.dxf --dxf-unit header --output new.sketchyup
sketchyup-cli --export-dxf new.dxf --input new.sketchyup --dxf-unit mm
sketchyup-cli --export-dxf site.dxf --input terrain.sketchyup --dxf-unit m --dxf-site-coordinates
```

`--dxf-site-coordinates` (the dialog's Write site coordinates) adds the model's site origin back
to X and Y; it needs a site origin.

See [DXF workflow and limits](decisions/0123-native-dxf-interchange-workflow.md).

### IFC import

IFC import (File → Import IFC… or the command line) reads an IFC2X3, IFC4 or
IFC4X3_ADD2 STEP file through the isolated helper `sketchyup-ifc-worker` of the optional `sketchyup-ifc` package
and builds a new native model: the spatial structure as groups, elements as editable faces on one tag per class
(spaces on a tag that starts hidden), properties and quantities as `Pset.Property` entity properties, colours and
materials, and a fidelity report that accounts for every instance of the file. Units come from the file; a file
without a length unit needs `--ifc-length-unit`. A file whose map conversion (`IfcMapConversion` with an
`IfcProjectedCRS` in metres) has no rotation sets the document's site origin from its eastings, northings and
height; such a document is saved in schema 29 and opens only in SketchyUp 1.3.0 or later. A map conversion that
rotates the project axes is reported and the axes are kept; `--ifc-georef grid` rotates the model to the map
grid instead and sets the site origin.

```sh
sketchyup-cli --import-ifc building.ifc
sketchyup-cli --import-ifc building.ifc --output converted.sketchyup --ifc-deflection 1 --ifc-spaces hidden
sketchyup-cli --import-ifc building.ifc --output converted.sketchyup --ifc-georef grid
```

Without `--output` the command validates the import and prints the report. The output must be a new path. If
the helper is missing, the command says so and nothing else is affected. See the
[IFC exchange subset](decisions/0171-ifc-exchange-subset.md) and its R097.b implementation notes.

### IFC export

IFC export (File → Export IFC… or the command line) writes a native model to a new IFC4 file through the same helper. Every body
becomes one `IfcTriangulatedFaceSet` of its own tessellation (no parametric solids, no Reference View or buildingSMART
certification claim; the header says "SketchyUp export, tessellated geometry" and declares no view). Groups become
`IfcElementAssembly`, a model that came from IFC keeps its site, building and storeys and otherwise gets one site and one
building (no storey is invented), a body's class comes from its `ifc.Class` property when that is an IFC4 building element
and is an `IfcBuildingElementProxy` otherwise, `Pset.Property` entity properties become property sets, materials and
per-face colours become surface styles, and hidden bodies are written on a layer that is switched off. Identifiers are
kept from an import when valid and unique and are otherwise derived from the model's identity, so exporting twice gives
the same ids. The site origin is written as an `IfcProjectedCRS` and an `IfcMapConversion` only when its label is an
authority code such as `EPSG:32760`; with any other label, or none, neither is written and the report says so. The report
counts everything that is not written (terrain, guides, labels, scenes, sections, sheets, reference images, component
parameters, textures, loose edges) and balances written, written-as-copies and not-written against the model's items.

```sh
sketchyup-cli --input house.sketchyup --export-ifc house.ifc
sketchyup-cli --input house.sketchyup --export-ifc house.ifc --ifc-timestamp 2026-01-02T03:04:05
```

`--ifc-timestamp` (UTC seconds or `YYYY-MM-DDTHH:MM:SS`; otherwise `SOURCE_DATE_EPOCH`, otherwise the clock) is stamped into
the file header and the owner history, so a fixed value makes two exports byte for byte equal. The output must be a new
path; an existing file or symbolic link is never replaced. See the R097.d implementation notes.

### Measured PDF and SVG views

Export a measured orthographic drawing with explicit page, scale and camera settings:

```sh
build/dev/sketchyup-cli --export-view NewDrawing.pdf --input Model.sketchyup --view-settings examples/measured-view.json
```

This technical-line mode reports omitted appearance, preserves the native source, and requires a new output file. Set `format` to `svg` for millimetre-based SVG. Print at actual size to retain the requested scale. See [the measured export contract](decisions/0127-measured-export-cli.md).

File → **Export measured PDF/SVG** offers the same physical page and scale controls in the desktop. Choose technical lines for vector geometry or current appearance for an explicitly identified raster drawing with embedded images and shading. The editing camera and model remain unchanged.
