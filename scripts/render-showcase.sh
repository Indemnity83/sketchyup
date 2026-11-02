#!/usr/bin/env bash
# Run the unchanged SketchyUp GLB exporter and fixed Blender adapter on the study.
set -euo pipefail
ulimit -c 0
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
out=${1:-.local/showcase-render}
mkdir -p "$out"
out=$(realpath "$out")
timeout 10 free -g
# Work directories must be fresh: the exporter never overwrites a snapshot.
timeout 300 python3 docs/images/showcase/build_showcase.py "$out/model"
timeout 30 python3 docs/images/showcase/sky_environment.py "$out/sky.hdr"
timeout 30 python3 - "$out" <<'PYTHON'
import json, math, pathlib, sys
out=pathlib.Path(sys.argv[1])
settings={"apiVersion":1,"width":1440,"height":900,"samples":256,"seed":17,
 "environment":{"path":str(out/"sky.hdr"),"strength":.65,"rotationDegrees":0},
 "camera":{"projection":"perspective","position":[-10,-20,6],"target":[5,1,1.9],
 "up":[0,0,1],"verticalFov":math.radians(43),"nearClip":.01,"farClip":1000}}
(out/"settings.json").write_text(json.dumps(settings,indent=2)+"\n")
PYTHON
timeout 60 sketchyup-cli --input "$out/model/showcase.sketchyup" \
  --export-glb "$out/snapshot" --render-settings "$out/settings.json" > "$out/export.log"
timeout 30 python3 - "$out" <<'PYTHON'
import hashlib,json,pathlib,sys
out=pathlib.Path(sys.argv[1]); snapshot=out/"snapshot"
request={"apiVersion":1,"operation":"render","backend":"CPU","deviceId":"CPU",
 "sourceDirectory":str(snapshot),"manifestSha256":hashlib.sha256((snapshot/"manifest.json").read_bytes()).hexdigest()}
(out/"request.json").write_text(json.dumps(request,indent=2)+"\n")
PYTHON
start=$SECONDS
systemd-run --user --scope -q -p MemoryMax=8G -p MemorySwapMax=0 \
  timeout --foreground 1200 /usr/bin/blender --background --factory-startup --disable-autoexec --threads 4 \
  --python-exit-code 1 --python "$root/src/integrations/blender_worker.py" -- "$out/request.json" \
  > "$out/blender.log" 2>&1
printf 'Blender elapsed: %s seconds\n' "$((SECONDS-start))" | tee "$out/elapsed.txt"
timeout 30 python3 - "$out/result.json" <<'PYTHON'
import json,sys
r=json.load(open(sys.argv[1])); assert r["status"]=="succeeded",r
print(json.dumps({k:r[k] for k in ("status","blenderVersionString","device","preset")},indent=2))
PYTHON

# Publish the actual adapter output, palette-quantized only for the README budget.
if command -v magick >/dev/null; then IM=magick; else IM=convert; fi
image_out=${2:-docs/images/render.png}
timeout 60 "$IM" "$out/image.png" -strip -colors 256 -dither None \
  -define png:compression-level=9 "PNG8:$image_out"
bytes=$(stat -c %s "$image_out")
if (( bytes > 500000 )); then
  echo "render-showcase: $image_out is over 500 KB" >&2
  exit 1
fi
