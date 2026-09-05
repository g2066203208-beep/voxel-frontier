#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r23-evidence}"
if [[ -z "$APP" || ! -x "$APP" ]]; then
  echo "usage: r23_capture.sh <voxel_frontier executable> [output-dir]" >&2
  exit 2
fi

mkdir -p "$OUT/terrain" "$OUT/celestial" "$OUT/logs"
export SDL_VIDEODRIVER=x11
export DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >"$OUT/logs/xvfb.log" 2>&1 &
XVFB_PID=$!
RUN_PID=""
trap '[[ -n "${RUN_PID:-}" ]] && kill "$RUN_PID" 2>/dev/null || true; kill "$XVFB_PID" 2>/dev/null || true' EXIT
sleep 2

wait_window() {
  local window=""
  for _ in $(seq 1 90); do
    window="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n 1 || true)"
    if [[ -n "$window" ]]; then
      echo "$window"
      return 0
    fi
    sleep 0.5
  done
  return 1
}

capture_ready() {
  local output="$1"
  local colors=0
  for attempt in $(seq 1 36); do
    sleep 0.8
    import -display :99 -window root "$output"
    colors="$(convert "$output" -format '%k' info:)"
    echo "$(basename "$output") attempt=$attempt unique_colors=$colors" | tee -a "$OUT/capture-info.txt"
    if [[ "$colors" -gt 64 ]]; then
      identify "$output" | tee -a "$OUT/capture-info.txt"
      return 0
    fi
  done
  echo "Framebuffer never became visually non-trivial for $output" >&2
  return 1
}

stop_app() {
  if [[ -n "${RUN_PID:-}" ]]; then
    kill "$RUN_PID" 2>/dev/null || true
    wait "$RUN_PID" 2>/dev/null || true
    RUN_PID=""
  fi
  sleep 0.8
}

capture_terrain_mode() {
  local mode="$1"
  local log="$OUT/logs/terrain-$mode.log"
  echo "=== terrain $mode ===" | tee -a "$OUT/capture-info.txt"
  VF_TERRAIN_TARGET="$mode" VF_CELESTIAL_TIME_SCALE=1 \
    timeout 80s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  local window
  window="$(wait_window)"
  xdotool windowfocus "$window" 2>/dev/null || true
  capture_ready "$OUT/terrain/${mode}-ground.png"

  # Use the real input path to enter flight, rise several hundred metres, and pitch down. This is
  # deliberately not a second renderer: both images are the game's actual Vulkan framebuffer.
  xdotool key --window "$window" space 2>/dev/null || true
  sleep 0.14
  xdotool key --window "$window" space 2>/dev/null || true
  sleep 0.6
  xdotool keydown --window "$window" space 2>/dev/null || true
  sleep 2.5
  xdotool keyup --window "$window" space 2>/dev/null || true
  xdotool mousemove_relative -- 0 250 2>/dev/null || true
  sleep 1.2
  capture_ready "$OUT/terrain/${mode}-aerial.png"
  grep -E 'R23 terrain target|Spawn land elevation|Voxel Frontier Earthlike' "$log" \
    | tee -a "$OUT/terrain/targets.txt" || true
  stop_app
}

terrain_modes=(mountain highland canyon coast dunes wetland glacier hydrology)
for mode in "${terrain_modes[@]}"; do
  capture_terrain_mode "$mode"
done

montage "$OUT"/terrain/*-aerial.png -tile 4x2 -geometry 800x450+8+8 \
  "$OUT/terrain/terrain-aerial-montage.png"
montage "$OUT"/terrain/*-ground.png -tile 4x2 -geometry 800x450+8+8 \
  "$OUT/terrain/terrain-ground-montage.png"

capture_celestial_sequence() {
  local target="$1"
  local log="$OUT/logs/celestial-$target.log"
  echo "=== celestial $target ===" | tee -a "$OUT/capture-info.txt"
  VF_CELESTIAL_TARGET="$target" VF_CELESTIAL_TIME_SCALE=3600 \
    timeout 80s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  local window
  window="$(wait_window)"
  xdotool windowfocus "$window" 2>/dev/null || true
  capture_ready "$OUT/celestial/${target}-0.png"
  for frame in 1 2 3 4 5; do
    sleep 0.70
    import -display :99 -window root "$OUT/celestial/${target}-${frame}.png"
    local colors
    colors="$(convert "$OUT/celestial/${target}-${frame}.png" -format '%k' info:)"
    echo "${target}-${frame}.png unique_colors=$colors" | tee -a "$OUT/capture-info.txt"
    test "$colors" -gt 64
  done
  montage "$OUT"/celestial/${target}-{0,1,2,3,4,5}.png -tile 3x2 -geometry 800x450+8+8 \
    "$OUT/celestial/${target}-motion-montage.png"
  convert -delay 45 -loop 0 "$OUT"/celestial/${target}-{0,1,2,3,4,5}.png \
    "$OUT/celestial/${target}-motion.gif"
  set +e
  compare -metric AE "$OUT/celestial/${target}-0.png" "$OUT/celestial/${target}-5.png" \
    "$OUT/celestial/${target}-first-last-diff.png" \
    2>"$OUT/celestial/${target}-first-last-ae.txt"
  set -e
  grep -E 'R23 celestial target|Spawn land elevation' "$log" | tee -a "$OUT/celestial/targets.txt" || true
  stop_app
}

capture_celestial_sequence sun
capture_celestial_sequence moon

cat >"$OUT/README.txt" <<'EOF'
Voxel Frontier R23 real Vulkan evidence

Terrain: mountain, highland, canyon, coast, dunes, wetland, glacier and process-derived hydrology.
Each terrain class contains a ground frame and an aerial frame captured from the actual Vulkan runtime.

Celestial: six fixed-camera accelerated-time frames for Sun and Moon, plus montage, GIF and first/last pixel difference.
The Moon is a real N-body CelestialBody in the preview runtime; the sequence is not a skybox animation.

No generated image is used as test evidence.
EOF

printf 'R23 capture complete: %s\n' "$OUT"
