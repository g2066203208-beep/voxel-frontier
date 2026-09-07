#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r24-epic-landscape-evidence}"
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
  for _ in $(seq 1 420); do
    local w
    w="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n1 || true)"
    [[ -n "$w" ]] && { echo "$w"; return 0; }
    sleep 0.30
  done
  return 1
}

start_app() {
  local log="$1"; shift
  env "$@" timeout 260s "$APP" >"$log" 2>&1 &
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
  for i in $(seq 1 90); do
    sleep .30
    local tmp="$OUT/frame.png"
    import -display :99 -window root "$tmp"
    local colors
    colors="$(convert "$tmp" -format '%k' info:)"
    if [[ "$colors" -gt 512 ]]; then
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
  echo "starting EPIC terrain target=${target} altitude_m=${altitude} min_contrast_m=${min_contrast}"
  start_app "$log" \
    VF_TERRAIN_TARGET="$target" VF_CAPTURE_AERIAL=1 VF_CAPTURE_ALTITUDE_METERS="$altitude" \
    VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1

  local ready=0
  for _ in $(seq 1 520); do
    if grep -q "R24 terrain evidence view: contrast_m=" "$log"; then
      ready=1
      break
    fi
    if grep -q 'Fatal error' "$log"; then break; fi
    sleep .25
  done
  if [[ "$ready" -ne 1 ]]; then
    echo "epic terrain target did not become ready: ${target}" >&2
    tail -160 "$log" || true
    stop_app
    return 21
  fi

  python3 - "$log" "$min_contrast" "$target" <<'PY'
import re, sys
text=open(sys.argv[1], encoding='utf-8', errors='replace').read()
rows=re.findall(r'R24 terrain evidence view: contrast_m=([0-9.]+)', text)
if not rows: raise SystemExit('missing terrain contrast diagnostics')
contrast=float(rows[-1]); minimum=float(sys.argv[2]); name=sys.argv[3]
print(f'{name} epic geometry gate: {contrast:.1f} m >= {minimum:.1f} m')
if contrast < minimum:
    raise SystemExit(f'{name} landscape is not epic enough: {contrast:.1f} m')
PY

  # Wait for the async adaptive mesh to settle after the first valid production frame.
  sleep 4.0
  capture_valid "$output" || {
    echo "epic terrain framebuffer stayed invalid: ${target}" >&2
    tail -160 "$log" || true
    stop_app
    return 22
  }
  stop_app
}

# Gameplay-first spectacle gates: these are intentionally far beyond ordinary terrestrial relief.
capture_target mountain 8500 "$OUT/terrain/mega-mountain-range.png" 4500
capture_target rift 6000 "$OUT/terrain/mega-rift-valley.png" 1800
capture_target canyon 4800 "$OUT/terrain/mega-canyon.png" 2200
capture_target abyss 3600 "$OUT/terrain/mega-abyss-cave-throat.png" 4500

montage \
  "$OUT/terrain/mega-mountain-range.png" \
  "$OUT/terrain/mega-rift-valley.png" \
  "$OUT/terrain/mega-canyon.png" \
  "$OUT/terrain/mega-abyss-cave-throat.png" \
  -tile 2x2 -geometry 800x450+6+6 "$OUT/r24-epic-landscape-overview.png"

{
  for target in mountain rift canyon abyss; do
    echo "=== ${target^^} ==="
    grep -E 'terrain target|terrain evidence view|QLOD|Fatal error' "$OUT/logs/${target}.log" | tail -40 || true
  done
} > "$OUT/runtime-summary.txt"

echo "R24 epic landscape Vulkan capture complete"
