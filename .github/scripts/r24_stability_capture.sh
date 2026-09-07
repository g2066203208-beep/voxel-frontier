#!/usr/bin/env bash
set -euo pipefail

# R24 contact-shadow gate: this run must visibly include caster base + receiver + shadow origin.
# This rerun follows cleanup of duplicated capture state in Main.cpp; a green workflow is not enough
# unless the low-angle Vulkan frames visibly show the shadow beginning at the caster-ground contact.
APP="${1:-}"
OUT="${2:-r24-stability-evidence}"
if [[ -z "$APP" || ! -x "$APP" ]]; then
  echo "usage: r24_stability_capture.sh <voxel_frontier executable> [output-dir]" >&2
  exit 2
fi

mkdir -p "$OUT/ground" "$OUT/shadows" "$OUT/space" "$OUT/high-speed" "$OUT/logs" "$OUT/failed-captures"
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

# Wait for a real presented frame instead of accepting the first X11 black startup image.
# Every rejected black/low-information attempt is still preserved under failed-captures/.
capture_frame() {
  local path="$1"
  local minimum_colors="${2:-128}"
  local attempts="${3:-30}"
  local base stem temp colors last_failed=""
  base="$(basename "$path")"
  stem="${base%.png}"

  for attempt in $(seq 1 "$attempts"); do
    sleep 0.45
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

  if [[ -n "$last_failed" && -f "$last_failed" ]]; then
    cp -f "$last_failed" "$path"
    identify "$path" | tee -a "$OUT/capture-info.txt" || true
  fi
  echo "ERROR no information-rich framebuffer produced for $path" \
    | tee -a "$OUT/capture-warnings.txt" >&2
  CAPTURE_GATE_FAILED=1
  return 0
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
start_app "$OUT/logs/ground-spin.log" VF_CELESTIAL_TIME_SCALE=7200 VF_RUNTIME_DIAGNOSTICS=1
capture_sequence "$OUT/ground/ground-spin" 6
stop_app
montage "$OUT"/ground/ground-spin-{0,1,2,3,4,5}.png -tile 3x2 -geometry 800x450+6+6 \
  "$OUT/ground/ground-spin-montage.png"

# 2) Contact-shadow proof. The deterministic orange probe's lower face is exactly on
# PlanetSurfaceAuthority and it is rendered by the production shadow-map pass. Sweep accelerated
# daylight across a full set of sun azimuths instead of relying on one unlucky view-aligned shadow.
start_app "$OUT/logs/shadow-contact.log" \
  VF_CELESTIAL_TIME_SCALE=7200 VF_CAPTURE_SHADOW_CONTACT=1 VF_RUNTIME_DIAGNOSTICS=1
capture_sequence "$OUT/shadows/contact-cycle" 8
stop_app
montage "$OUT"/shadows/contact-cycle-{0,1,2,3,4,5,6,7}.png \
  -tile 4x2 -geometry 800x450+6+6 "$OUT/shadows/contact-cycle-montage.png"

# 3) External inertial observer: planet self-rotation must remain visible, not be disabled to fix
# the surface observer. The accelerated sequence makes rotational continuity easy to inspect.
start_app "$OUT/logs/earth-spin.log" \
  VF_CELESTIAL_VIEW=earth-globe VF_CELESTIAL_TIME_SCALE=7200 VF_RUNTIME_DIAGNOSTICS=1
capture_sequence "$OUT/space/earth-spin" 6
stop_app
montage "$OUT"/space/earth-spin-{0,1,2,3,4,5}.png -tile 3x2 -geometry 800x450+6+6 \
  "$OUT/space/earth-spin-montage.png"

# 4) High-speed transit uses the real production PlanetCamera/streaming path. The capture-only
# environment variable sets the initial editor/session state (flight enabled, 500 km/s target),
# then real SDL keyboard input drives forward flight. Logs must prove the renderer switched to the
# cheap smooth globe rather than attempting continuous expensive near-field rebuilds.
start_app "$OUT/logs/high-speed.log" \
  VF_CELESTIAL_TIME_SCALE=1 VF_CAPTURE_HIGH_SPEED=1 VF_RUNTIME_DIAGNOSTICS=1
capture_frame "$OUT/high-speed/before.png"
xdotool keydown --window "$ACTIVE_WINDOW" Shift_L
xdotool keydown --window "$ACTIVE_WINDOW" w
sleep 1.35
capture_frame "$OUT/high-speed/transit.png"
sleep 0.65
capture_frame "$OUT/high-speed/transit-late.png"
xdotool keyup --window "$ACTIVE_WINDOW" w
xdotool keyup --window "$ACTIVE_WINDOW" Shift_L
sleep 0.75
capture_frame "$OUT/high-speed/after.png"
stop_app

if ! grep -q 'R24 Earth renderer mode: smooth-globe speed_mps=' "$OUT/logs/high-speed.log"; then
  echo "ERROR high-speed capture never proved smooth-globe fallback" \
    | tee -a "$OUT/capture-warnings.txt" >&2
  CAPTURE_GATE_FAILED=1
fi
if ! grep -q 'R24 DIAG .*FLIGHT' "$OUT/logs/high-speed.log"; then
  echo "ERROR high-speed capture never proved production flight mode" \
    | tee -a "$OUT/capture-warnings.txt" >&2
  CAPTURE_GATE_FAILED=1
fi

# Preserve first/last image diffs even when ugly; they are diagnostics, never filtered evidence.
set +e
compare -metric AE "$OUT/ground/ground-spin-0.png" "$OUT/ground/ground-spin-5.png" \
  "$OUT/ground/ground-spin-diff.png" 2>"$OUT/ground/ground-spin-ae.txt"
compare -metric AE "$OUT/space/earth-spin-0.png" "$OUT/space/earth-spin-5.png" \
  "$OUT/space/earth-spin-diff.png" 2>"$OUT/space/earth-spin-ae.txt"
set -e

{
  echo "=== ground spin log ==="
  grep -E 'R24 DIAG|Earth renderer mode|terrain stale build|Fatal error|Earth-Moon physical scale' "$OUT/logs/ground-spin.log" || true
  echo "=== shadow contact log ==="
  grep -E 'shadow-contact|shadow-contact probe|R24 DIAG|Fatal error' "$OUT/logs/shadow-contact.log" || true
  echo "=== high speed log ==="
  grep -E 'capture high-speed|R24 DIAG|Earth renderer mode|terrain stale build|Fatal error|Earth-Moon physical scale' "$OUT/logs/high-speed.log" || true
  echo "=== earth spin log ==="
  grep -E 'R24\.2 view|R24 DIAG|Earth renderer mode|Fatal error|Earth-Moon physical scale' "$OUT/logs/earth-spin.log" || true
} > "$OUT/runtime-summary.txt"

montage "$OUT/ground/ground-spin-montage.png" "$OUT/shadows/contact-cycle-montage.png" \
        "$OUT/space/earth-spin-montage.png" "$OUT/high-speed/transit.png" \
        -tile 2x2 -geometry 800x450+6+6 "$OUT/r24-stability-overview.png"

cat > "$OUT/README.txt" <<'EOF'
R24 runtime stability evidence — real Vulkan framebuffer only

- ground/ground-spin-*.png: accelerated planet rotation while the player remains on the surface.
- shadows/contact-cycle-*.png: the production-rendered orange probe has its lower face exactly on
  PlanetSurfaceAuthority; accelerated daylight sweeps the real shadow over multiple azimuths so the
  contact origin can be inspected without hiding the shadow behind the caster.
- space/earth-spin-*.png: inertial external observer; physical planet self-rotation remains visible.
- high-speed/*.png: production PlanetCamera flight plus real SDL forward input at a configured
  500 km/s target; runtime-summary must prove smooth-globe fallback.
- failed-captures/: every startup black/low-information framebuffer attempt is intentionally kept.
- runtime-summary.txt: streaming/mode/FPS/fatal diagnostics captured from the tested executable.

Bad, blank, ugly, detached-shadow or low-information frames are deliberately retained.
EOF

echo "R24 stability capture complete: $OUT"
if [[ "$CAPTURE_GATE_FAILED" -ne 0 ]]; then
  echo "R24 stability capture gate FAILED; evidence has been preserved" >&2
  exit 1
fi
