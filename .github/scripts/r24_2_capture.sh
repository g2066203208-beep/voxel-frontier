#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r24-2-evidence}"
if [[ -z "$APP" || ! -x "$APP" ]]; then
  echo "usage: r24_2_capture.sh <voxel_frontier executable> [output-dir]" >&2
  exit 2
fi

mkdir -p "$OUT/globes" "$OUT/motion" "$OUT/terrain" "$OUT/logs"
: > "$OUT/capture-info.txt"
: > "$OUT/capture-warnings.txt"

export SDL_VIDEODRIVER=x11
export DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >"$OUT/logs/xvfb.log" 2>&1 &
XVFB_PID=$!
RUN_PID=""
trap '[[ -n "${RUN_PID:-}" ]] && kill "$RUN_PID" 2>/dev/null || true; kill "$XVFB_PID" 2>/dev/null || true' EXIT
sleep 2

wait_window() {
  local window=""
  for _ in $(seq 1 120); do
    window="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n 1 || true)"
    if [[ -n "$window" ]]; then
      echo "$window"
      return 0
    fi
    sleep 0.5
  done
  return 1
}

capture_frame() {
  local output="$1"
  local minimum_colors="${2:-64}"
  local attempts="${3:-25}"
  local colors=0
  for attempt in $(seq 1 "$attempts"); do
    sleep 0.65
    import -display :99 -window root "$output"
    colors="$(convert "$output" -format '%k' info:)"
    echo "$(basename "$output") attempt=$attempt colors=$colors" | tee -a "$OUT/capture-info.txt"
    if [[ "$colors" -gt "$minimum_colors" ]]; then
      identify "$output" | tee -a "$OUT/capture-info.txt"
      return 0
    fi
  done
  echo "WARN low-information framebuffer retained: $output colors=$colors" \
    | tee -a "$OUT/capture-warnings.txt" >&2
  identify "$output" | tee -a "$OUT/capture-info.txt" || true
  return 0
}

stop_app() {
  if [[ -n "${RUN_PID:-}" ]]; then
    kill "$RUN_PID" 2>/dev/null || true
    wait "$RUN_PID" 2>/dev/null || true
    RUN_PID=""
  fi
  sleep 0.5
}

start_app() {
  local log="$1"
  shift
  env "$@" timeout 120s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  local window
  window="$(wait_window)"
  xdotool windowfocus "$window" 2>/dev/null || true
}

single_view() {
  local name="$1"
  local view="$2"
  local timescale="${3:-1}"
  local log="$OUT/logs/${name}.log"
  start_app "$log" VF_CELESTIAL_VIEW="$view" VF_CELESTIAL_TIME_SCALE="$timescale"
  capture_frame "$OUT/globes/${name}.png"
  grep -E 'R24\.2 view|Earth-Moon physical scale|Earth renderer mode|Fatal error' "$log" \
    | tee -a "$OUT/globes/runtime-targets.txt" || true
  stop_app
}

single_view earth-globe earth-globe 1
single_view moon-globe moon-globe 1
single_view earth-from-moon earth-from-moon 1
single_view earth-moon-system earth-moon-system 1

# Preserve ground and aerial terrain proof as well: every runtime change must show it did not silently
# destroy the playable terrain while fixing celestial rendering.
start_app "$OUT/logs/terrain-ground.log" VF_TERRAIN_TARGET=mountain VF_CELESTIAL_TIME_SCALE=1
capture_frame "$OUT/terrain/mountain-ground.png"
stop_app
start_app "$OUT/logs/terrain-aerial.log" VF_TERRAIN_TARGET=mountain VF_CAPTURE_AERIAL=1 VF_CAPTURE_ALTITUDE_METERS=9000 VF_CELESTIAL_TIME_SCALE=1
capture_frame "$OUT/terrain/mountain-aerial-9km.png"
stop_app

capture_sequence() {
  local name="$1"
  local view="$2"
  local timescale="$3"
  local log="$OUT/logs/${name}.log"
  start_app "$log" VF_CELESTIAL_VIEW="$view" VF_CELESTIAL_TIME_SCALE="$timescale"
  capture_frame "$OUT/motion/${name}-0.png"
  for frame in 1 2 3 4 5; do
    sleep 0.75
    import -display :99 -window root "$OUT/motion/${name}-${frame}.png"
    local colors
    colors="$(convert "$OUT/motion/${name}-${frame}.png" -format '%k' info:)"
    echo "${name}-${frame}.png colors=$colors" | tee -a "$OUT/capture-info.txt"
    if [[ "$colors" -le 64 ]]; then
      echo "WARN low-information motion frame retained: ${name}-${frame}.png" \
        | tee -a "$OUT/capture-warnings.txt" >&2
    fi
  done
  montage "$OUT"/motion/${name}-{0,1,2,3,4,5}.png -tile 3x2 -geometry 800x450+6+6 \
    "$OUT/motion/${name}-montage.png"
  convert -delay 40 -loop 0 "$OUT"/motion/${name}-{0,1,2,3,4,5}.png \
    "$OUT/motion/${name}.gif"
  set +e
  compare -metric AE "$OUT/motion/${name}-0.png" "$OUT/motion/${name}-5.png" \
    "$OUT/motion/${name}-first-last-diff.png" 2>"$OUT/motion/${name}-first-last-ae.txt"
  set -e
  grep -E 'R24\.2 view|Earth-Moon physical scale|R24 moon evidence|Fatal error' "$log" \
    | tee -a "$OUT/motion/runtime-targets.txt" || true
  stop_app
}

# 7200x: Earth rotates by roughly 30 degrees per real second. 200000x: the Moon advances rapidly
# enough around its real 384,400 km orbit to be visible in a short CI sequence.
capture_sequence earth-spin earth-globe 7200
capture_sequence moon-revolution earth-moon-system 200000

montage "$OUT/globes/earth-globe.png" "$OUT/globes/moon-globe.png" \
        "$OUT/globes/earth-from-moon.png" "$OUT/globes/earth-moon-system.png" \
        -tile 2x2 -geometry 800x450+6+6 "$OUT/globes/r24-2-globes-montage.png"
montage "$OUT/terrain/mountain-ground.png" "$OUT/terrain/mountain-aerial-9km.png" \
        -tile 2x1 -geometry 800x450+6+6 "$OUT/terrain/r24-2-terrain-montage.png"

cat >"$OUT/README.txt" <<'EOF'
Voxel Frontier R24.2 real Vulkan framebuffer evidence

- earth-globe.png: physical 6371 km Earth radius, 3-D displaced terrain, smooth distant globe path.
- moon-globe.png: physical 1737.4 km Moon radius, near high-resolution globe path with 3-D relief.
- earth-from-moon.png: observer on the lunar near side looking back at the real-scale Earth.
- earth-moon-system.png: wide physical-scale Earth-Moon composition.
- earth-spin sequence: accelerated celestial clock proves Earth self-rotation in the real runtime.
- moon-revolution sequence: accelerated celestial clock proves Moon revolution in the real N-body runtime.
- terrain frames: mandatory regression proof that near-surface terrain remains present.

Bad, blank, ugly or low-information frames are intentionally retained and uploaded. No generated image is test evidence.
EOF

echo "R24.2 capture complete: $OUT"
