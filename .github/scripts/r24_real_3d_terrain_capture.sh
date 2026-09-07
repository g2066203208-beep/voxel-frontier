#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r24-real-3d-terrain-evidence}"
[[ -n "$APP" && -x "$APP" ]] || { echo "missing executable: $APP" >&2; exit 2; }

mkdir -p "$OUT/terrain" "$OUT/logs" "$OUT/failed-captures"
export SDL_VIDEODRIVER=x11
export DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >"$OUT/logs/xvfb.log" 2>&1 &
XVFB_PID=$!
RUN_PID=""
trap '[[ -n "${RUN_PID:-}" ]] && kill "$RUN_PID" 2>/dev/null || true; kill "$XVFB_PID" 2>/dev/null || true' EXIT
sleep 2

wait_window() {
  for _ in $(seq 1 300); do
    local w
    w="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n1 || true)"
    [[ -n "$w" ]] && { echo "$w"; return 0; }
    sleep 0.35
  done
  return 1
}

start_app() {
  local log="$1"; shift
  env "$@" timeout 220s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  ACTIVE_WINDOW="$(wait_window)"
  xdotool windowfocus "$ACTIVE_WINDOW" 2>/dev/null || true
}

stop_app() {
  if [[ -n "$RUN_PID" ]]; then
    kill "$RUN_PID" 2>/dev/null || true
    wait "$RUN_PID" 2>/dev/null || true
  fi
  RUN_PID=""
  sleep .5
}

capture_valid() {
  local path="$1"
  local stem
  stem="$(basename "${path%.png}")"
  for i in $(seq 1 70); do
    sleep .30
    local tmp="$OUT/frame.png"
    import -display :99 -window root "$tmp"
    local colors
    colors="$(convert "$tmp" -format '%k' info:)"
    if [[ "$colors" -gt 256 ]]; then
      mv "$tmp" "$path"
      echo "captured $path colors=$colors"
      return 0
    fi
    mv "$tmp" "$OUT/failed-captures/${stem}-${i}.png"
  done
  return 1
}

capture_target() {
  local target="$1"
  local altitude="$2"
  local output="$3"
  local min_contrast="$4"
  local log="$OUT/logs/${target}.log"
  echo "starting 3-D terrain capture target=${target} altitude_m=${altitude}"
  start_app "$log" \
    VF_TERRAIN_TARGET="$target" VF_CAPTURE_AERIAL=1 VF_CAPTURE_ALTITUDE_METERS="$altitude" \
    VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1

  local ready=0
  for _ in $(seq 1 420); do
    if grep -q "R24 terrain evidence view: contrast_m=" "$log"; then
      ready=1
      break
    fi
    if grep -q 'Fatal error' "$log"; then
      break
    fi
    sleep .25
  done
  if [[ "$ready" -ne 1 ]]; then
    echo "terrain target did not become ready: ${target}" >&2
    tail -120 "$log" || true
    stop_app
    return 21
  fi

  python3 - "$log" "$min_contrast" "$target" <<'PY'
import re, sys
text=open(sys.argv[1], encoding='utf-8', errors='replace').read()
rows=re.findall(r'R24 terrain evidence view: contrast_m=([0-9.]+)', text)
if not rows:
    raise SystemExit('missing terrain contrast diagnostics')
contrast=float(rows[-1])
minimum=float(sys.argv[2])
name=sys.argv[3]
print(f'{name} geometric contrast gate: {contrast:.2f} m >= {minimum:.2f} m')
if contrast < minimum:
    raise SystemExit(f'{name} is still visually flat: local geometric contrast {contrast:.2f} m')
PY

  sleep 3.0
  capture_valid "$output" || {
    echo "terrain framebuffer stayed invalid: ${target}" >&2
    tail -120 "$log" || true
    stop_app
    return 22
  }
  stop_app
}

# These are real production views. Passing requires geometry itself to have substantial relief.
capture_target mountain 2200 "$OUT/terrain/convergent-mountain-3d.png" 850
capture_target rift 1800 "$OUT/terrain/divergent-rift-3d.png" 260
capture_target hydrology 1600 "$OUT/terrain/river-basin-3d.png" 180

montage \
  "$OUT/terrain/convergent-mountain-3d.png" \
  "$OUT/terrain/divergent-rift-3d.png" \
  "$OUT/terrain/river-basin-3d.png" \
  -tile 3x1 -geometry 760x428+8+8 "$OUT/r24-real-3d-terrain-overview.png"

{
  echo '=== MOUNTAIN ==='
  grep -E 'terrain target|terrain evidence view|QLOD|Fatal error' "$OUT/logs/mountain.log" | tail -30 || true
  echo '=== RIFT ==='
  grep -E 'terrain target|terrain evidence view|QLOD|Fatal error' "$OUT/logs/rift.log" | tail -30 || true
  echo '=== HYDROLOGY ==='
  grep -E 'terrain target|terrain evidence view|QLOD|Fatal error' "$OUT/logs/hydrology.log" | tail -30 || true
} > "$OUT/runtime-summary.txt"

echo "R24 real 3-D terrain capture complete"
