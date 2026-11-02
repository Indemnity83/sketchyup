#!/usr/bin/env bash
# Regenerate the README screenshots in docs/images/ from the showcase model.
#
# The script builds docs/images/showcase.json and docs/images/showcase-sheet.json
# with sketchyup-cli, runs SketchyUp under its own Xvfb with an isolated HOME,
# and writes the PNGs (1440x900, stripped, max compression) to OUTPUT_DIR.
#
# Run it inside the screenshot image, which provides Xvfb, xdotool, ImageMagick
# and the SketchyUp 1.7.0 package. Build the image from scripts/screenshots.Dockerfile
# first, then run the script with this repository mounted read-only:
#
#   docker build -f scripts/screenshots.Dockerfile -t sketchyup-shots:1.7.0 packaging/arch
#   docker run --rm --network none --memory 3g --cpus 2 --user "$(id -u):$(id -g)" \
#     -v "$PWD":/src:ro -v "$PWD/docs/images":/out sketchyup-shots:1.7.0 \
#     /src/scripts/capture-screenshots.sh /out
#
# Usage: scripts/capture-screenshots.sh OUTPUT_DIR
# CI does not run this script.
set -euo pipefail
ulimit -c 0

if [[ $# -ne 1 ]]; then
  echo "usage: $0 OUTPUT_DIR" >&2
  exit 2
fi

for tool in Xvfb xdotool import sketchyup sketchyup-cli python3; do
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

# Emit bounded command batches and build them with the released CLI.
timeout 300 python3 "$images/showcase/build_showcase.py" "$work/build"
model="$work/build/showcase.sketchyup"
if [[ -n ${SHOWCASE_BUILD_OUT:-} ]]; then
  mkdir -p "$SHOWCASE_BUILD_OUT"
  cp "$model" "$work/build/stats.json" "$work/build/document.json" "$SHOWCASE_BUILD_OUT/"
fi

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
  # A fresh profile and model copy for each shot, so that no recovery data or edit
  # from an earlier shot reaches this one.
  local dir="$work/shot-$name"
  mkdir -p "$dir/home/.config/SketchyUp" "$dir/home/.local/share" "$dir/home/.cache" \
    "$dir/run" "$dir/model"
  chmod 700 "$dir/run"
  cp "$model" "$dir/model/showcase.sketchyup"
  printf '[General]\ntheme=%s\ndefaultUnits=m\n' "$theme" > "$dir/home/.config/SketchyUp/SketchyUp.conf"
  env HOME="$dir/home" XDG_CONFIG_HOME="$dir/home/.config" XDG_DATA_HOME="$dir/home/.local/share" \
    XDG_CACHE_HOME="$dir/home/.cache" XDG_RUNTIME_DIR="$dir/run" \
    sketchyup "$dir/model/showcase.sketchyup" > "$work/app-$name.log" 2>&1 &
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

# Hint workaround. The Select tool draws its hint line at a fixed height, and that line
# overlaps the saved-scene tabs (a product bug). Orbit and Pan draw a camera hint of their
# own, so the model shots use Paint (B), which draws no viewport hint. Each shot clicks
# empty sky above the terrain (which selects nothing) or the table, then presses b and
# moves the pointer onto the status bar. Paint opens the Materials tab, so a shot clicks
# the tab it needs.
#
# The dining table (a configurable assembly, 5 parameters) is placed beside the recipe
# table: choose it in the Components list, then type its position into the Measurements
# box. It is placed only in the components shot.
shots=(
  "hero-light|1|click:124,826;key:b;key:ctrl+k;type:Outliner;key:Return;move:640,884;sleep:4"
  "hero-dark|2|click:124,826;key:b;key:ctrl+k;type:Outliner;key:Return;move:640,884;sleep:4"
  "components|1|click:520,826;key:space;click:650,470;key:b;key:ctrl+k;type:Entity info;key:Return;move:640,884;sleep:4"
  "sheets|1|key:ctrl+alt+s;sleep:3;key:shift+z;move:640,884;sleep:4"
  "terrain|1|click:456,826;key:b;key:ctrl+k;type:Sun and shadows;key:Return;move:640,884;sleep:4"
  "commands|1|click:124,826;key:b;key:ctrl+k;type:export;move:640,884;sleep:4"
  "section|1|click:330,826;key:b;key:ctrl+k;type:Outliner;key:Return;move:640,884;sleep:4"
  "interior|1|click:265,826;key:b;key:ctrl+k;type:Outliner;key:Return;move:640,884;sleep:4"
)

for entry in "${shots[@]}"; do
  IFS='|' read -r name theme steps <<< "$entry"
  shot "$name" "$theme" "$steps"
done

# Strip metadata and compress. The textured views need 192 colours to stay under
# 500 KB; no dithering, which would add grain to the flat areas of the UI.
status=0
for entry in "${shots[@]}"; do
  name=${entry%%|*}
  "$IM" "$work/shots/$name.png" -strip -colors 192 -dither None \
    -define png:compression-level=9 "PNG8:$out/$name.png"
  bytes=$(stat -c %s "$out/$name.png")
  echo "$name.png $((bytes / 1024)) KB"
  if (( bytes > 500 * 1024 )); then
    echo "capture-screenshots: $name.png is over 500 KB" >&2
    status=1
  fi
done
exit "$status"
