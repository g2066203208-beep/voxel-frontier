#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r24-r2-evidence}"
if [[ -z "$APP" || ! -x "$APP" ]]; then
  echo "usage: r24_capture_r2.sh <voxel_frontier executable> [output-dir]" >&2
  exit 2
fi

mkdir -p "$OUT/terrain" "$OUT/celestial" "$OUT/logs"
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
  for _ in $(seq 1 160); do
    window="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n 1 || true)"
    if [[ -n "$window" ]]; then echo "$window"; return 0; fi
    sleep 0.5
  done
  return 1
}

capture_frame() {
  local output="$1"
  local min_colors="${2:-64}"
  local attempts="${3:-45}"
  local colors=0
  for attempt in $(seq 1 "$attempts"); do
    sleep 0.75
    import -display :99 -window root "$output" || true
    colors="$(convert "$output" -format '%k' info: 2>/dev/null || echo 0)"
    echo "$(basename "$output") attempt=$attempt colors=$colors" | tee -a "$OUT/capture-info.txt"
    if [[ "$colors" -gt "$min_colors" ]]; then
      identify "$output" | tee -a "$OUT/capture-info.txt" || true
      return 0
    fi
  done
  echo "WARN retained low-information framebuffer $output colors=$colors" \
    | tee -a "$OUT/capture-warnings.txt" >&2
  return 0
}

stop_app() {
  [[ -n "${RUN_PID:-}" ]] && kill "$RUN_PID" 2>/dev/null || true
  [[ -n "${RUN_PID:-}" ]] && wait "$RUN_PID" 2>/dev/null || true
  RUN_PID=""
  sleep 0.5
}

capture_aerial() {
  local label="$1"
  local target="$2"
  local altitude="$3"
  local output="$OUT/terrain/${label}.png"
  local log="$OUT/logs/${label}.log"
  env VF_TERRAIN_TARGET="$target" VF_CAPTURE_AERIAL=1 \
      VF_CAPTURE_ALTITUDE_METERS="$altitude" VF_CELESTIAL_TIME_SCALE=1 \
      timeout 150s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  local window=""
  if window="$(wait_window)"; then
    xdotool windowfocus "$window" 2>/dev/null || true
    capture_frame "$output"
    xdotool getwindowname "$window" 2>/dev/null | tee -a "$OUT/capture-info.txt" || true
  else
    import -display :99 -window root "$output" || true
    echo "WARN window not found: $label; root framebuffer retained" | tee -a "$OUT/capture-warnings.txt" >&2
  fi
  grep -hE 'R24|terrain target|aerial camera|Spawn land elevation|Fatal error' "$log" \
      | tee -a "$OUT/terrain/runtime.txt" || true
  stop_app
}

# Repeat the three problem views plus a 30 km view that would immediately expose a square/high-detail
# island if the quadtree or local hydrology authority still leaked its topology.
capture_aerial canyon-6km canyon 6200
capture_aerial hydrology-7km hydrology 6800
capture_aerial mountain-9km mountain 9000
capture_aerial canyon-30km canyon 30000

montage "$OUT/terrain/canyon-6km.png" "$OUT/terrain/hydrology-7km.png" \
        "$OUT/terrain/mountain-9km.png" "$OUT/terrain/canyon-30km.png" \
        -tile 2x2 -geometry 800x450+8+8 "$OUT/terrain/r24-r2-terrain-montage.png" || true

# Actual integrated Moon, actual 1,737.4 km radius and current N-body distance. The camera only tracks
# its true direction; the body is neither enlarged nor moved. Four frames prove time evolution.
MOON_LOG="$OUT/logs/moon-tracked.log"
env VF_CELESTIAL_TARGET=moon VF_CELESTIAL_TIME_SCALE=3600 timeout 150s "$APP" >"$MOON_LOG" 2>&1 &
RUN_PID=$!
if MOON_WINDOW="$(wait_window)"; then
  xdotool windowfocus "$MOON_WINDOW" 2>/dev/null || true
  for frame in 0 1 2 3; do
    [[ "$frame" != 0 ]] && sleep 1.0
    capture_frame "$OUT/celestial/moon-${frame}.png" 64 8
  done
  xdotool getwindowname "$MOON_WINDOW" 2>/dev/null | tee -a "$OUT/capture-info.txt" || true
else
  import -display :99 -window root "$OUT/celestial/moon-0.png" || true
  echo "WARN Moon window not found; root framebuffer retained" | tee -a "$OUT/capture-warnings.txt" >&2
fi
stop_app

grep -hE 'R24 moon evidence|R24 celestial evidence target|Fatal error' "$MOON_LOG" \
    | tee "$OUT/celestial/moon-diagnostics.txt" || true

if [[ -f "$OUT/celestial/moon-3.png" ]]; then
  montage "$OUT"/celestial/moon-{0,1,2,3}.png -tile 2x2 -geometry 800x450+8+8 \
      "$OUT/celestial/moon-motion-montage.png" || true
  set +e
  compare -metric AE "$OUT/celestial/moon-0.png" "$OUT/celestial/moon-3.png" \
      "$OUT/celestial/moon-first-last-diff.png" 2>"$OUT/celestial/moon-first-last-ae.txt"
  set -e
fi

cat > "$OUT/README.txt" <<'EOF'
Voxel Frontier R24.1 mandatory framebuffer evidence.
All PNGs come from the real Vulkan runtime under Lavapipe/X11. Bad frames are retained.
Terrain includes 6-9 km problem views and a 30 km far-LOD view.
Moon sequence tracks the true integrated lunar direction without changing its physical radius or distance.
EOF
