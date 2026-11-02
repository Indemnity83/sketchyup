#!/usr/bin/env bash
# Brand panel adapted from the supplied layout; image is an actual Cycles output.
set -euo pipefail
ulimit -c 0
root=$(cd "$(dirname "$0")/.." && pwd)
render=${1:-$root/.local/showcase-render/image.png}
out=${2:-$root/docs/images/social-preview.jpg}
work=$(mktemp -d "$root/.local/social.XXXXXX")
trap 'rm -rf "$work"' EXIT
if command -v magick >/dev/null; then IM=magick; else IM=convert; fi
timeout 30 "$IM" -size 128x128 xc:none -fill '#314d3e' -draw 'roundrectangle 4,4 123,123 26,26' \
  -fill '#e6dfbc' -draw 'polygon 26,46 64,24 102,46 64,68' \
  -fill '#bfa978' -draw 'polygon 26,46 64,68 64,110 26,88' \
  -fill '#849979' -draw 'polygon 64,68 102,46 102,88 64,110' \
  -fill none -stroke '#314d3e' -strokewidth 4 -draw 'polyline 26,46 64,68 102,46' \
  -draw 'line 64,68 64,110' -resize 112x112 "$work/icon.png"
timeout 30 "$IM" "$render" -colorspace sRGB -depth 8 -resize '840x640^' \
  -gravity center -extent 840x640 "$work/render.png"
timeout 30 "$IM" -size 440x640 xc:'#1c2520' \
  "$work/icon.png" -geometry +48+150 -composite \
  -font DejaVu-Sans-Bold -pointsize 58 -fill '#f3efe0' -annotate +46+340 'SketchyUp' \
  -font DejaVu-Sans -pointsize 23 -fill '#c9d3c4' -annotate +48+390 'A native 3D modeler for Linux' \
  -pointsize 23 -annotate +48+424 'Local-first. No account.' \
  -pointsize 15 -fill '#8fa08a' -annotate +48+566 'Modeled in SketchyUp' \
  -annotate +48+590 'Rendered with Blender / Cycles CPU' "$work/panel.png"
timeout 30 "$IM" "$work/panel.png" "$work/render.png" +append -strip -quality 90 "$out"
timeout 10 identify "$out"
