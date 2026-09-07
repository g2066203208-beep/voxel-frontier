#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r24-gameplay-moon-terrain-evidence}"
[[ -n "$APP" && -x "$APP" ]] || { echo "missing executable: $APP" >&2; exit 2; }

mkdir -p "$OUT/moon" "$OUT/terrain" "$OUT/logs" "$OUT/failed-captures"
export SDL_VIDEODRIVER=x11
export DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >"$OUT/logs/xvfb.log" 2>&1 &
XVFB_PID=$!
RUN_PID=""
trap '[[ -n "${RUN_PID:-}" ]] && kill "$RUN_PID" 2>/dev/null || true; kill "$XVFB_PID" 2>/dev/null || true' EXIT
sleep 2

wait_window() {
  for _ in $(seq 1 140); do
    local w
    w="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n1 || true)"
    [[ -n "$w" ]] && { echo "$w"; return 0; }
    sleep 0.4
  done
  return 1
}

start_app() {
  local log="$1"; shift
  env "$@" timeout 90s "$APP" >"$log" 2>&1 &
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
  sleep .4
}

capture_valid() {
  local path="$1"
  local stem
  stem="$(basename "${path%.png}")"
  for i in $(seq 1 40); do
    sleep .35
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

# Gameplay Moon: physical orbit/gravity are unchanged, only the surface-view presentation is 4x.
start_app "$OUT/logs/moon.log" \
  VF_CELESTIAL_TARGET=moon VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1
for _ in $(seq 1 100); do
  grep -q 'R24 moon evidence:' "$OUT/logs/moon.log" && break
  sleep .3
done
grep -q 'R24 moon evidence:' "$OUT/logs/moon.log"
capture_valid "$OUT/moon/gameplay-moon.png"
stop_app
python3 - "$OUT/logs/moon.log" <<'PY'
import re, sys
text=open(sys.argv[1],encoding='utf-8',errors='replace').read()
rows=re.findall(r'R24 moon evidence:.*visual_scale=([0-9.]+).*visual_apparent_diameter_px=([0-9.]+)', text)
if not rows:
    raise SystemExit('missing gameplay Moon diagnostics')
scale, pixels=map(float, rows[-1])
print(f'gameplay Moon gate: scale={scale:.3f} visual_px={pixels:.3f}')
if scale < 3.5 or pixels < 18.0:
    raise SystemExit('gameplay Moon did not reach intended readable surface presentation')
PY

capture_terrain() {
  local target="$1"
  local altitude="$2"
  local output="$3"
  local log="$OUT/logs/${target}.log"
  start_app "$log" \
    VF_TERRAIN_TARGET="$target" VF_CAPTURE_AERIAL=1 VF_CAPTURE_ALTITUDE_METERS="$altitude" \
    VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1
  for _ in $(seq 1 120); do
    grep -q "R24 terrain target: ${target}" "$log" && break
    sleep .3
  done
  grep -q "R24 terrain target: ${target}" "$log"
  sleep 2.5
  capture_valid "$output"
  stop_app
}

# Three independent causal provinces, selected from the actual deterministic planet field.
capture_terrain mountain 9000 "$OUT/terrain/convergent-mountain.png"
capture_terrain rift 7000 "$OUT/terrain/divergent-rift.png"
capture_terrain hydrology 6000 "$OUT/terrain/river-basin.png"

montage \
  "$OUT/moon/gameplay-moon.png" \
  "$OUT/terrain/convergent-mountain.png" \
  "$OUT/terrain/divergent-rift.png" \
  "$OUT/terrain/river-basin.png" \
  -tile 2x2 -geometry 800x450+8+8 "$OUT/r24-gameplay-moon-terrain-overview.png"

{
  echo '=== MOON ==='
  grep -E 'moon evidence|Fatal error' "$OUT/logs/moon.log" | tail -20 || true
  echo '=== MOUNTAIN ==='
  grep -E 'terrain target|QLOD|Fatal error' "$OUT/logs/mountain.log" | tail -20 || true
  echo '=== RIFT ==='
  grep -E 'terrain target|QLOD|Fatal error' "$OUT/logs/rift.log" | tail -20 || true
  echo '=== HYDROLOGY ==='
  grep -E 'terrain target|QLOD|Fatal error' "$OUT/logs/hydrology.log" | tail -20 || true
} > "$OUT/runtime-summary.txt"

echo "R24 gameplay Moon + causal terrain capture complete"
