#!/usr/bin/env bash
set -euo pipefail

APP="${1:-}"
OUT="${2:-r24-evidence}"
if [[ -z "$APP" || ! -x "$APP" ]]; then
  echo "usage: r24_capture.sh <voxel_frontier executable> [output-dir]" >&2
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
  for _ in $(seq 1 140); do
    window="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n 1 || true)"
    if [[ -n "$window" ]]; then
      echo "$window"
      return 0
    fi
    sleep 0.5
  done
  return 1
}

capture_framebuffer() {
  local output="$1"
  local minimum_colors="${2:-64}"
  local attempts="${3:-40}"
  local colors=0
  for attempt in $(seq 1 "$attempts"); do
    sleep 0.75
    import -display :99 -window root "$output" || true
    if [[ ! -s "$output" ]]; then
      echo "WARN: framebuffer file missing on attempt $attempt: $output" | tee -a "$OUT/capture-warnings.txt" >&2
      continue
    fi
    colors="$(convert "$output" -format '%k' info: 2>/dev/null || echo 0)"
    echo "$(basename "$output") attempt=$attempt unique_colors=$colors" | tee -a "$OUT/capture-info.txt"
    if [[ "$colors" -gt "$minimum_colors" ]]; then
      identify "$output" | tee -a "$OUT/capture-info.txt" || true
      return 0
    fi
  done
  echo "WARN: low-information framebuffer retained: $output colors=$colors threshold=$minimum_colors" \
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

capture_mode() {
  local mode="$1"
  local altitude="$2"
  local output="$OUT/terrain/${mode}-aerial.png"
  local log="$OUT/logs/${mode}-aerial.log"
  echo "=== R24 terrain $mode aerial ===" | tee -a "$OUT/capture-info.txt"
  env VF_TERRAIN_TARGET="$mode" VF_CAPTURE_AERIAL=1 \
      VF_CAPTURE_ALTITUDE_METERS="$altitude" VF_CELESTIAL_TIME_SCALE=1 \
      timeout 120s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  local window
  if window="$(wait_window)"; then
    xdotool windowfocus "$window" 2>/dev/null || true
    capture_framebuffer "$output"
  else
    echo "WARN: window not found for $mode; retaining any root framebuffer" | tee -a "$OUT/capture-warnings.txt" >&2
    import -display :99 -window root "$output" || true
  fi
  grep -hE 'R24|terrain target|aerial camera|Spawn land elevation|QLOD|Fatal error' "$log" \
    | tee -a "$OUT/terrain/runtime.txt" || true
  stop_app
}

capture_ground() {
  local mode="$1"
  local output="$OUT/terrain/${mode}-ground.png"
  local log="$OUT/logs/${mode}-ground.log"
  env VF_TERRAIN_TARGET="$mode" VF_CELESTIAL_TIME_SCALE=1 timeout 120s "$APP" >"$log" 2>&1 &
  RUN_PID=$!
  local window
  if window="$(wait_window)"; then
    xdotool windowfocus "$window" 2>/dev/null || true
    capture_framebuffer "$output"
  else
    import -display :99 -window root "$output" || true
    echo "WARN: ground window not found; root framebuffer retained" | tee -a "$OUT/capture-warnings.txt" >&2
  fi
  stop_app
}

# These three frames directly target the defects seen in the prior evidence: exposed square LOD,
# unreadable mountain hierarchy, and weak drainage structure. Bad results are retained, not hidden.
capture_mode canyon 6200
capture_mode hydrology 6800
capture_mode mountain 9000
capture_ground hydrology

montage "$OUT/terrain/canyon-aerial.png" "$OUT/terrain/hydrology-aerial.png" \
        "$OUT/terrain/mountain-aerial.png" "$OUT/terrain/hydrology-ground.png" \
        -tile 2x2 -geometry 800x450+8+8 "$OUT/terrain/r24-terrain-montage.png" || true

# Physical Moon motion evidence: same Vulkan process, accelerated celestial clock, multiple frames.
MOON_LOG="$OUT/logs/moon-motion.log"
env VF_CELESTIAL_TARGET=moon VF_CELESTIAL_TIME_SCALE=3600 timeout 120s "$APP" >"$MOON_LOG" 2>&1 &
RUN_PID=$!
if MOON_WINDOW="$(wait_window)"; then
  xdotool windowfocus "$MOON_WINDOW" 2>/dev/null || true
  capture_framebuffer "$OUT/celestial/moon-0.png"
  for frame in 1 2 3; do
    sleep 0.9
    import -display :99 -window root "$OUT/celestial/moon-${frame}.png" || true
    colors="$(convert "$OUT/celestial/moon-${frame}.png" -format '%k' info: 2>/dev/null || echo 0)"
    echo "moon-${frame}.png unique_colors=$colors" | tee -a "$OUT/capture-info.txt"
    if [[ "$colors" -le 64 ]]; then
      echo "WARN: low-information Moon frame retained: moon-${frame}.png" | tee -a "$OUT/capture-warnings.txt" >&2
    fi
  done
else
  echo "WARN: Moon window not found; preserving root framebuffer" | tee -a "$OUT/capture-warnings.txt" >&2
  import -display :99 -window root "$OUT/celestial/moon-0.png" || true
fi
stop_app

if compgen -G "$OUT/celestial/moon-[0-3].png" >/dev/null; then
  montage "$OUT"/celestial/moon-{0,1,2,3}.png -tile 2x2 -geometry 800x450+8+8 \
      "$OUT/celestial/moon-motion-montage.png" || true
  set +e
  compare -metric AE "$OUT/celestial/moon-0.png" "$OUT/celestial/moon-3.png" \
      "$OUT/celestial/moon-first-last-diff.png" 2>"$OUT/celestial/moon-first-last-ae.txt"
  set -e
fi

grep -hE 'R24|celestial target|Spawn land elevation|Fatal error' "$MOON_LOG" \
  | tee -a "$OUT/celestial/runtime.txt" || true

cat > "$OUT/README.txt" <<'EOF'
Voxel Frontier R24 mandatory real framebuffer evidence

All PNG files are captured from the actual Vulkan runtime under X11/Lavapipe. No generated image is evidence.
The capture intentionally retains blank, broken, low-information, or visually poor frames and records warnings.
Terrain evidence targets canyon, hydrology, mountain and one ground view. Moon evidence is a four-frame motion sequence.
EOF

printf 'R24 real framebuffer capture complete: %s\n' "$OUT"
