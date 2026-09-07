#!/usr/bin/env bash
set -u

APP="${1:-}"
OUT="${2:-r24-gameplay-moon-terrain-evidence}"
[[ -n "$APP" && -x "$APP" ]] || { echo "missing executable: $APP" >&2; exit 2; }

mkdir -p "$OUT/moon" "$OUT/terrain" "$OUT/logs" "$OUT/failed-captures"
export SDL_VIDEODRIVER=x11
export DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >"$OUT/logs/xvfb.log" 2>&1 &
XVFB_PID=$!
RUN_PID=""
ACTIVE_WINDOW=""
FAIL=0
trap '[[ -n "${RUN_PID:-}" ]] && kill "$RUN_PID" 2>/dev/null || true; kill "$XVFB_PID" 2>/dev/null || true' EXIT
sleep 2

wait_window() {
  for _ in $(seq 1 180); do
    local w
    w="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n1 || true)"
    if [[ -n "$w" ]]; then echo "$w"; return 0; fi
    sleep .5
  done
  return 1
}

start_app() {
  local log="$1"; shift
  env "$@" stdbuf -oL -eL timeout 150s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  ACTIVE_WINDOW="$(wait_window)" || return 1
  xdotool windowfocus "$ACTIVE_WINDOW" 2>/dev/null || true
  return 0
}

stop_app() {
  if [[ -n "$RUN_PID" ]]; then
    kill "$RUN_PID" 2>/dev/null || true
    wait "$RUN_PID" 2>/dev/null || true
  fi
  RUN_PID=""
  ACTIVE_WINDOW=""
  sleep .4
}

capture_valid() {
  local path="$1"
  local stem
  stem="$(basename "${path%.png}")"
  for i in $(seq 1 50); do
    sleep .35
    local tmp="$OUT/frame.png"
    import -display :99 -window root "$tmp" 2>/dev/null || true
    if [[ -f "$tmp" ]]; then
      local colors
      colors="$(convert "$tmp" -format '%k' info: 2>/dev/null || echo 0)"
      if [[ "$colors" =~ ^[0-9]+$ ]] && [[ "$colors" -gt 256 ]]; then
        mv "$tmp" "$path"
        echo "captured $path colors=$colors"
        return 0
      fi
      mv "$tmp" "$OUT/failed-captures/${stem}-${i}.png"
    fi
  done
  echo "FAILED to capture valid frame: $path" >&2
  return 1
}

wait_log() {
  local log="$1"
  local pattern="$2"
  local loops="${3:-240}"
  for _ in $(seq 1 "$loops"); do
    grep -q "$pattern" "$log" 2>/dev/null && return 0
    if [[ -n "$RUN_PID" ]] && ! kill -0 "$RUN_PID" 2>/dev/null; then break; fi
    sleep .5
  done
  echo "FAILED waiting log pattern '$pattern' in $log" >&2
  tail -80 "$log" 2>/dev/null || true
  return 1
}

# 1) Surface gameplay Moon. Physical body remains unchanged; rendered disc should be ~4x.
if start_app "$OUT/logs/moon.log" \
    VF_CELESTIAL_TARGET=moon VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1; then
  wait_log "$OUT/logs/moon.log" 'R24 moon evidence:' 180 || FAIL=1
  capture_valid "$OUT/moon/gameplay-moon.png" || FAIL=1
else
  FAIL=1
fi
stop_app
python3 - "$OUT/logs/moon.log" <<'PY' || FAIL=1
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
  echo "=== capture terrain $target ==="
  if ! start_app "$log" \
      VF_TERRAIN_TARGET="$target" VF_CAPTURE_AERIAL=1 VF_CAPTURE_ALTITUDE_METERS="$altitude" \
      VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1; then
    FAIL=1
    stop_app
    return
  fi
  if ! wait_log "$log" "R24 terrain target: ${target}" 240; then FAIL=1; fi
  sleep 3
  if ! capture_valid "$output"; then FAIL=1; fi
  stop_app
}

# Independent real Vulkan views of three process-driven provinces.
capture_terrain mountain 9000 "$OUT/terrain/convergent-mountain.png"
capture_terrain rift 7000 "$OUT/terrain/divergent-rift.png"
capture_terrain hydrology 6000 "$OUT/terrain/river-basin.png"

# Build whatever overview is possible; individual frames remain available even on partial failure.
imgs=()
for f in \
  "$OUT/moon/gameplay-moon.png" \
  "$OUT/terrain/convergent-mountain.png" \
  "$OUT/terrain/divergent-rift.png" \
  "$OUT/terrain/river-basin.png"; do
  [[ -f "$f" ]] && imgs+=("$f")
done
if [[ ${#imgs[@]} -gt 0 ]]; then
  montage "${imgs[@]}" -tile 2x2 -geometry 800x450+8+8 "$OUT/r24-gameplay-moon-terrain-overview.png" || true
fi

{
  echo '=== MOON ==='; grep -E 'moon evidence|Fatal error' "$OUT/logs/moon.log" | tail -30 || true
  echo '=== MOUNTAIN ==='; grep -E 'terrain target|QLOD|Fatal error' "$OUT/logs/mountain.log" | tail -30 || true
  echo '=== RIFT ==='; grep -E 'terrain target|QLOD|Fatal error' "$OUT/logs/rift.log" | tail -30 || true
  echo '=== HYDROLOGY ==='; grep -E 'terrain target|QLOD|Fatal error' "$OUT/logs/hydrology.log" | tail -30 || true
} > "$OUT/runtime-summary.txt"

echo "R24 gameplay Moon + causal terrain capture finished FAIL=$FAIL"
exit "$FAIL"
