#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r24-stability-evidence}"
if [[ -z "$APP" || ! -x "$APP" ]]; then
  echo "usage: r24_stability_capture.sh <voxel_frontier executable> [output-dir]" >&2
  exit 2
fi

mkdir -p "$OUT/ground" "$OUT/shadows" "$OUT/space" "$OUT/high-speed" "$OUT/logs"
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

start_app() {
  local log="$1"
  shift
  env "$@" timeout 150s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  ACTIVE_WINDOW="$(wait_window)"
  xdotool windowfocus "$ACTIVE_WINDOW" 2>/dev/null || true
  sleep 1.2
}

stop_app() {
  if [[ -n "${RUN_PID:-}" ]]; then
    kill "$RUN_PID" 2>/dev/null || true
    wait "$RUN_PID" 2>/dev/null || true
    RUN_PID=""
  fi
  sleep 0.5
}

capture_frame() {
  local path="$1"
  sleep 0.45
  import -display :99 -window root "$path"
  local colors
  colors="$(convert "$path" -format '%k' info:)"
  echo "$(basename "$path") colors=$colors" | tee -a "$OUT/capture-info.txt"
  identify "$path" | tee -a "$OUT/capture-info.txt" || true
  if [[ "$colors" -le 64 ]]; then
    echo "WARN low-information framebuffer retained: $path" | tee -a "$OUT/capture-warnings.txt" >&2
  fi
}

capture_sequence() {
  local prefix="$1"
  local count="$2"
  for i in $(seq 0 $((count - 1))); do
    capture_frame "${prefix}-${i}.png"
    sleep 0.55
  done
}

# 1) Ground-frame stability under very accelerated real planet spin. Terrain/props must stay
# registered to the camera while sun/shadows are allowed to move across the fixed ground.
start_app "$OUT/logs/ground-spin.log" VF_CELESTIAL_TIME_SCALE=7200
capture_sequence "$OUT/ground/ground-spin" 6
stop_app
montage "$OUT"/ground/ground-spin-{0,1,2,3,4,5}.png -tile 3x2 -geometry 800x450+6+6 \
  "$OUT/ground/ground-spin-montage.png"

# 2) Close ground frame at ordinary time for contact-shadow and ecology placement inspection.
start_app "$OUT/logs/shadow-contact.log" VF_CELESTIAL_TIME_SCALE=1
capture_frame "$OUT/shadows/contact-ground.png"
stop_app

# 3) External inertial observer: planet self-rotation must remain visible, not be disabled to fix
# the surface observer. The accelerated sequence makes rotational continuity easy to inspect.
start_app "$OUT/logs/earth-spin.log" VF_CELESTIAL_VIEW=earth-globe VF_CELESTIAL_TIME_SCALE=7200
capture_sequence "$OUT/space/earth-spin" 6
stop_app
montage "$OUT"/space/earth-spin-{0,1,2,3,4,5}.png -tile 3x2 -geometry 800x450+6+6 \
  "$OUT/space/earth-spin-montage.png"

# 4) Real input-driven high-speed flight. Double-tap Space enables creative flight, mouse wheel
# raises target speed, then Shift+W drives forward. The runtime title records STREAM/LOD/FPS state.
start_app "$OUT/logs/high-speed.log" VF_CELESTIAL_TIME_SCALE=1
capture_frame "$OUT/high-speed/before.png"
xdotool key --window "$ACTIVE_WINDOW" space
sleep 0.12
xdotool key --window "$ACTIVE_WINDOW" space
sleep 0.35
for _ in $(seq 1 24); do xdotool click --window "$ACTIVE_WINDOW" 4; done
sleep 0.25
xdotool keydown --window "$ACTIVE_WINDOW" Shift_L
xdotool keydown --window "$ACTIVE_WINDOW" w
sleep 2.2
capture_frame "$OUT/high-speed/transit.png"
xdotool keyup --window "$ACTIVE_WINDOW" w
xdotool keyup --window "$ACTIVE_WINDOW" Shift_L
sleep 0.8
capture_frame "$OUT/high-speed/after.png"
stop_app

# Preserve first/last image diffs even when ugly; they are diagnostics, never filtered evidence.
set +e
compare -metric AE "$OUT/ground/ground-spin-0.png" "$OUT/ground/ground-spin-5.png" \
  "$OUT/ground/ground-spin-diff.png" 2>"$OUT/ground/ground-spin-ae.txt"
compare -metric AE "$OUT/space/earth-spin-0.png" "$OUT/space/earth-spin-5.png" \
  "$OUT/space/earth-spin-diff.png" 2>"$OUT/space/earth-spin-ae.txt"
set -e

{
  echo "=== ground spin log ==="
  grep -E 'Earth renderer mode|terrain stale build|FPS|Fatal error|Earth-Moon physical scale' "$OUT/logs/ground-spin.log" || true
  echo "=== high speed log ==="
  grep -E 'Earth renderer mode|terrain stale build|FPS|Fatal error|Earth-Moon physical scale' "$OUT/logs/high-speed.log" || true
  echo "=== earth spin log ==="
  grep -E 'R24\.2 view|Earth renderer mode|Fatal error|Earth-Moon physical scale' "$OUT/logs/earth-spin.log" || true
} > "$OUT/runtime-summary.txt"

montage "$OUT/ground/ground-spin-montage.png" "$OUT/shadows/contact-ground.png" \
        "$OUT/space/earth-spin-montage.png" "$OUT/high-speed/transit.png" \
        -tile 2x2 -geometry 800x450+6+6 "$OUT/r24-stability-overview.png"

cat > "$OUT/README.txt" <<'EOF'
R24 runtime stability evidence — real Vulkan framebuffer only

- ground/ground-spin-*.png: accelerated planet rotation while the player remains on the surface.
  Terrain and local props should remain fixed relative to the camera; lighting/shadows may change.
- shadows/contact-ground.png: ordinary-time contact-shadow/ecology placement inspection.
- space/earth-spin-*.png: inertial external observer; physical planet self-rotation remains visible.
- high-speed/*.png: actual SDL input drives high-speed creative flight and records the fallback path.
- runtime-summary.txt: streaming/mode/fatal diagnostics captured from the tested executable.

Bad, blank, ugly, detached-shadow or low-information frames are deliberately retained.
EOF

echo "R24 stability capture complete: $OUT"
