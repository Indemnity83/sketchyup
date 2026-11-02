#!/usr/bin/env bash
# Export here; run the unchanged CPU/HIP Blender adapter on the rendering machine.
set -euo pipefail
ulimit -c 0
root=$(cd "$(dirname "$0")/.." && pwd)
exec timeout --foreground 1900 python3 "$root/docs/images/showcase/render_showcase.py" "$@"
