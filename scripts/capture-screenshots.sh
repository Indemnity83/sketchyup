#!/usr/bin/env bash
# Regenerate the README screenshots in docs/images/ from the showcase model.
#
# The script builds docs/images/showcase.json and docs/images/showcase-sheet.json
# with sketchyup-cli, runs SketchyUp under its own Xvfb with an isolated HOME,
# and writes the PNGs (1440x900, stripped, max compression) to OUTPUT_DIR.
#
# Run it inside the screenshot image, which provides Xvfb, xdotool, ImageMagick
# and the SketchyUp 1.7.0 package, with this repository mounted read-only:
#
#   docker run --rm --network none --memory 3g --cpus 2 --user "$(id -u):$(id -g)" \
#     -v "$PWD":/src:ro -v "$PWD/docs/images":/out sketchyup-shots:1.7.0 \
#     /src/scripts/capture-screenshots.sh /out
#
# Usage: scripts/capture-screenshots.sh OUTPUT_DIR
# CI does not run this script.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 OUTPUT_DIR" >&2
  exit 2
fi

for tool in Xvfb xdotool import sketchyup sketchyup-cli; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "capture-screenshots: required tool not on PATH: $tool" >&2
    exit 1
  fi
done
if command -v magick >/dev/null 2>&1; then
  IM=magick
elif command -v convert >/dev/null 2>&1; then
  IM=convert
else
  echo "capture-screenshots: required tool not on PATH: ImageMagick (magick or convert)" >&2
  exit 1
fi

root=$(cd "$(dirname "$0")/.." && pwd)
images="$root/docs/images"
for input in "$images/showcase.json" "$images/showcase-sheet.json"; do
  if [[ ! -f $input ]]; then
    echo "capture-screenshots: missing input: $input" >&2
    exit 1
  fi
done

mkdir -p "$1"
out=$(cd "$1" && pwd)

work=$(mktemp -d "${TMPDIR:-/tmp}/sketchyup-shots.XXXXXX")
xpid=""
cleanup() {
  if [[ -n $xpid ]]; then
    kill "$xpid" 2>/dev/null || true
  fi
  rm -rf "$work"
}
trap cleanup EXIT

# Isolated profile: nothing is read from or written to the real home directory.
export HOME="$work/home"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_RUNTIME_DIR="$work/run"
export QT_QPA_PLATFORM=xcb QT_SCALE_FACTOR=1 LIBGL_ALWAYS_SOFTWARE=1
unset WAYLAND_DISPLAY DBUS_SESSION_BUS_ADDRESS
mkdir -p "$XDG_CONFIG_HOME/SketchyUp" "$XDG_DATA_HOME" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" "$work/shots"
chmod 700 "$XDG_RUNTIME_DIR"

# Build the model and the sheet page. Drawing sheet operations need their own batch.
mkdir -p "$work/build" "$work/model"
if ! sketchyup-cli --script "$images/showcase.json" --output "$work/build/showcase.sketchyup" \
    > "$work/build-model.json" 2> "$work/build-model.err"; then
  echo "capture-screenshots: model build failed:" >&2
  cat "$work/build-model.json" "$work/build-model.err" >&2
  exit 1
fi
if ! sketchyup-cli --input "$work/build/showcase.sketchyup" --script "$images/showcase-sheet.json" \
    --output "$work/model/showcase.sketchyup" > "$work/build-sheet.json" 2> "$work/build-sheet.err"; then
  echo "capture-screenshots: sheet build failed:" >&2
  cat "$work/build-sheet.json" "$work/build-sheet.err" >&2
  exit 1
fi
model="$work/model/showcase.sketchyup"

# Start a private X server on a display number that is not in use. The real
# desktop display is never opened.
display=""
for n in $(seq 99 140); do
  if [[ ! -e /tmp/.X$n-lock && ! -e /tmp/.X11-unix/X$n ]]; then
    display=$n
    break
  fi
done
if [[ -z $display ]]; then
  echo "capture-screenshots: no free X display number between :99 and :140" >&2
  exit 1
fi
export DISPLAY=":$display"
Xvfb "$DISPLAY" -screen 0 1440x900x24 -nolisten tcp > "$work/xvfb.log" 2>&1 &
xpid=$!
ready=""
for _ in $(seq 1 50); do
  if xdotool getdisplaygeometry >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.2
done
if [[ -z $ready ]]; then
  echo "capture-screenshots: Xvfb did not start on $DISPLAY; see $work/xvfb.log" >&2
  exit 1
fi

# One fresh SketchyUp process per shot, sized to 1440x900 and driven with xdotool.
# Steps: key:KEYS  type:TEXT  click:X,Y  move:X,Y  sleep:SECONDS  (separated by ;)
# The viewport tab row is at y=826, the Model/Sheets header and the right panel
# tabs move with the selection: the Info tab is at y=197 once an entity is selected.
shot() {
  local name=$1 theme=$2 steps=$3
  printf '[General]\ntheme=%s\ndefaultUnits=m\n' "$theme" > "$XDG_CONFIG_HOME/SketchyUp/SketchyUp.conf"
  sketchyup "$model" > "$work/app-$name.log" 2>&1 &
  local apid=$!
  local wid
  wid=$(timeout 30 xdotool search --sync --onlyvisible --pid "$apid" 2>/dev/null | head -1) || true
  if [[ -z $wid ]]; then
    kill "$apid" 2>/dev/null || true
    echo "capture-screenshots: no window for $name; see $work/app-$name.log" >&2
    exit 1
  fi
  xdotool windowmove "$wid" 0 0 windowsize "$wid" 1440 900
  sleep 3
  xdotool windowfocus --sync "$wid" || true
  local parts p x y
  IFS=';' read -ra parts <<< "$steps"
  for p in "${parts[@]}"; do
    case $p in
      key:*) xdotool key --clearmodifiers "${p#key:}" ;;
      type:*) xdotool type --delay 30 "${p#type:}" ;;
      click:*) IFS=, read -r x y <<< "${p#click:}"; xdotool mousemove "$x" "$y" click 1 ;;
      move:*) IFS=, read -r x y <<< "${p#move:}"; xdotool mousemove "$x" "$y" ;;
      sleep:*) sleep "${p#sleep:}" ;;
      "") ;;
      *) echo "capture-screenshots: bad step in $name: $p" >&2; exit 1 ;;
    esac
    sleep 1
  done
  sleep 2
  import -window root "$work/shots/$name.png"
  kill "$apid" 2>/dev/null || true
  wait "$apid" 2>/dev/null || true
  echo "shot $name"
}

shots=(
  "hero-light|1|click:124,826;sleep:2"
  "hero-dark|2|click:124,826;sleep:2"
  "components|1|click:124,826;sleep:2;click:840,505;sleep:2;click:1354,197;sleep:2"
  "sheets|1|key:ctrl+alt+s;sleep:2;click:1120,300;sleep:1;key:shift+z;sleep:2"
  "terrain|1|click:240,826;sleep:2;key:ctrl+k;sleep:1;type:site terr;sleep:1;key:Return;sleep:2;click:1354,197;sleep:2"
  "commands|1|click:124,826;sleep:2;key:ctrl+k;sleep:1;type:sec;sleep:1"
)
for entry in "${shots[@]}"; do
  IFS='|' read -r name theme steps <<< "$entry"
  shot "$name" "$theme" "$steps"
done

# Strip metadata and compress. The textured views need 256 colours to stay under
# 500 KB; no dithering, which would add grain to the flat areas of the UI.
status=0
for entry in "${shots[@]}"; do
  name=${entry%%|*}
  "$IM" "$work/shots/$name.png" -strip -colors 256 -dither None \
    -define png:compression-level=9 "PNG8:$out/$name.png"
  bytes=$(stat -c %s "$out/$name.png")
  echo "$name.png $((bytes / 1024)) KB"
  if (( bytes > 500 * 1024 )); then
    echo "capture-screenshots: $name.png is over 500 KB" >&2
    status=1
  fi
done
exit "$status"
