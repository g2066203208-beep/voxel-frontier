#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r24-celestial-motion-evidence}"
if [[ -z "$APP" || ! -x "$APP" ]]; then
  echo "usage: r24_celestial_motion_capture.sh <voxel_frontier executable> [output-dir]" >&2
  exit 2
fi

mkdir -p "$OUT/space-spin" "$OUT/escape" "$OUT/logs" "$OUT/failed-captures"
: > "$OUT/capture-info.txt"
: > "$OUT/capture-warnings.txt"
CAPTURE_GATE_FAILED=0

export SDL_VIDEODRIVER=x11
export DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >"$OUT/logs/xvfb.log" 2>&1 &
XVFB_PID=$!
RUN_PID=""
ACTIVE_WINDOW=""
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
}

stop_app() {
  if [[ -n "${RUN_PID:-}" ]]; then
    kill "$RUN_PID" 2>/dev/null || true
    wait "$RUN_PID" 2>/dev/null || true
    RUN_PID=""
  fi
  sleep 0.35
}

capture_frame() {
  local path="$1"
  local minimum_colors="${2:-128}"
  local attempts="${3:-30}"
  local base stem temp colors last_failed=""
  base="$(basename "$path")"
  stem="${base%.png}"
  for attempt in $(seq 1 "$attempts"); do
    sleep 0.35
    temp="$OUT/${stem}-capture-tmp.png"
    import -display :99 -window root "$temp"
    colors="$(convert "$temp" -format '%k' info:)"
    echo "$base attempt=$attempt colors=$colors" | tee -a "$OUT/capture-info.txt"
    if [[ "$colors" -gt "$minimum_colors" ]]; then
      mv -f "$temp" "$path"
      identify "$path" | tee -a "$OUT/capture-info.txt" || true
      return 0
    fi
    last_failed="$OUT/failed-captures/${stem}-attempt-${attempt}.png"
    mv -f "$temp" "$last_failed"
    echo "WARN low-information framebuffer retained: $last_failed colors=$colors" \
      | tee -a "$OUT/capture-warnings.txt" >&2
  done
  if [[ -n "$last_failed" && -f "$last_failed" ]]; then cp -f "$last_failed" "$path"; fi
  CAPTURE_GATE_FAILED=1
}

capture_sequence() {
  local prefix="$1"
  local count="$2"
  for i in $(seq 0 $((count - 1))); do
    capture_frame "${prefix}-${i}.png"
    sleep 0.32
  done
}

# A) Inertial observer. 7200x is intentionally aggressive so six hours of physical spin pass in
# about three real seconds. The new bounded step policy still integrates dvec3 position and dquat
# orientation every display frame instead of holding and jumping.
start_app "$OUT/logs/space-spin.log" \
  VF_CELESTIAL_VIEW=earth-globe VF_CELESTIAL_TIME_SCALE=7200 VF_RUNTIME_DIAGNOSTICS=1
capture_sequence "$OUT/space-spin/earth" 8
stop_app
montage "$OUT"/space-spin/earth-{0,1,2,3,4,5,6,7}.png \
  -tile 4x2 -geometry 800x450+6+6 "$OUT/space-spin/earth-spin-montage.png"

# B) Real frame handoff. The executable starts only 5 km inside Aster's production physics bubble
# with an outward local velocity. Holding Space for a fraction of a second crosses the actual frame
# boundary. We then release all input. The planet should remain on the original look-back line:
# orbital velocity was inherited, not erased by creative flight.
start_app "$OUT/logs/escape.log" \
  VF_CELESTIAL_TIME_SCALE=1 VF_CAPTURE_ESCAPE_INHERITANCE=1 VF_RUNTIME_DIAGNOSTICS=1
capture_frame "$OUT/escape/before.png"
xdotool keydown --window "$ACTIVE_WINDOW" space
sleep 0.35
xdotool keyup --window "$ACTIVE_WINDOW" space
capture_sequence "$OUT/escape/after" 8
stop_app
montage "$OUT/escape/before.png" "$OUT"/escape/after-{0,1,2,3,4,5,6,7}.png \
  -tile 3x3 -geometry 800x450+6+6 "$OUT/escape/escape-inheritance-montage.png"

if ! grep -q 'R24 escape inheritance: frame=inertial' "$OUT/logs/escape.log"; then
  echo "ERROR escape capture never crossed into inertial space" | tee -a "$OUT/capture-warnings.txt" >&2
  CAPTURE_GATE_FAILED=1
fi

# Numerically require the inherited component along Aster's orbital velocity to stay substantial.
# This catches the old absolute-velocity damping even if a tracking-friendly screenshot looks nice.
awk '
  /R24 escape inheritance: frame=inertial/ {
    for (i=1; i<=NF; ++i) {
      if ($i ~ /^inherited_orbit_mps=/) {
        split($i,a,"="); v=a[2]+0; seen=1; if (v > 20000 || v < -20000) good=1;
      }
      if ($i ~ /^effective_time_scale=/) {
        split($i,b,"="); s=b[2]+0; if (s > 0.99 && s < 1.01) scalegood=1;
      }
    }
  }
  END { exit !(seen && good && scalegood) }
' "$OUT/logs/escape.log" || {
  echo "ERROR inertial escape did not preserve orbital carrier velocity at physical 1x time" \
    | tee -a "$OUT/capture-warnings.txt" >&2
  CAPTURE_GATE_FAILED=1
}

set +e
compare -metric AE "$OUT/space-spin/earth-0.png" "$OUT/space-spin/earth-7.png" \
  "$OUT/space-spin/earth-spin-diff.png" 2>"$OUT/space-spin/earth-spin-ae.txt"
compare -metric AE "$OUT/escape/before.png" "$OUT/escape/after-7.png" \
  "$OUT/escape/escape-diff.png" 2>"$OUT/escape/escape-ae.txt"
set -e

{
  echo '=== accelerated vector/quaternion spin ==='
  grep -E 'R24 DIAG|R24\.2 view|Fatal error' "$OUT/logs/space-spin.log" || true
  echo '=== escape inheritance ==='
  grep -E 'escape inheritance|Fatal error|R24 DIAG' "$OUT/logs/escape.log" || true
} > "$OUT/runtime-summary.txt"

montage "$OUT/space-spin/earth-spin-montage.png" "$OUT/escape/escape-inheritance-montage.png" \
  -tile 1x2 -geometry 1200x675+8+8 "$OUT/r24-celestial-motion-overview.png"

cat > "$OUT/README.txt" <<'EOF'
R24 celestial motion closure — real Vulkan framebuffer evidence

space-spin/: fixed inertial observer, real Aster mesh, 7200x simulated time. The body uses the same
production dvec3 N-body state and dquat spin; the sequence is intended to expose frozen/jumping frames.

escape/: production PlanetCamera starts 5 km inside the real Aster precision-bubble edge and crosses
it through ordinary flight input. After input release the camera is not target-teleported or moved by
a capture script. Its world velocity must retain the parent's orbital carrier rather than being damped
toward zero. runtime-summary.txt records frame ownership, inherited orbital component and effective
free-space time scale.

failed-captures/: all startup black/low-information frames are intentionally preserved.
EOF

if [[ "$CAPTURE_GATE_FAILED" -ne 0 ]]; then
  echo 'R24 celestial motion capture gate FAILED; screenshots are still preserved' >&2
  exit 1
fi

echo "R24 celestial motion capture complete: $OUT"
