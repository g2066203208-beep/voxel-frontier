#!/usr/bin/env bash
set -euo pipefail
APP="${1:-}"
OUT="${2:-r24-interstellar-sun-evidence}"
[[ -n "$APP" && -x "$APP" ]] || exit 2
mkdir -p "$OUT/moon" "$OUT/sun" "$OUT/logs" "$OUT/failed-captures"
export SDL_VIDEODRIVER=x11 DISPLAY=:99
Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >"$OUT/logs/xvfb.log" 2>&1 &
XVFB_PID=$!
RUN_PID=""
trap '[[ -n "${RUN_PID:-}" ]] && kill "$RUN_PID" 2>/dev/null || true; kill "$XVFB_PID" 2>/dev/null || true' EXIT
sleep 2

wait_window() {
  for _ in $(seq 1 120); do
    local w
    w="$(xdotool search --name 'Voxel Frontier' 2>/dev/null | head -n1 || true)"
    [[ -n "$w" ]] && { echo "$w"; return 0; }
    sleep 0.5
  done
  return 1
}
start_app() {
  local log="$1"; shift
  env "$@" timeout 90s "$APP" >"$log" 2>&1 & RUN_PID=$!
  ACTIVE_WINDOW="$(wait_window)"
  xdotool windowfocus "$ACTIVE_WINDOW" 2>/dev/null || true
}
stop_app() { [[ -n "$RUN_PID" ]] && kill "$RUN_PID" 2>/dev/null || true; wait "$RUN_PID" 2>/dev/null || true; RUN_PID=""; sleep .3; }
capture() {
  local path="$1"
  for i in $(seq 1 30); do
    sleep .35
    local tmp="$OUT/cap.png"
    import -display :99 -window root "$tmp"
    local colors
    colors="$(convert "$tmp" -format '%k' info:)"
    if [[ "$colors" -gt 128 ]]; then mv "$tmp" "$path"; return 0; fi
    mv "$tmp" "$OUT/failed-captures/$(basename "${path%.png}")-$i.png"
  done
  return 1
}

# Ground observer: real physical Moon at 384,400 km, no proxy resize. Capture the framebuffer first
# so a slow llvmpipe diagnostic cannot erase visual evidence, then keep the runtime alive long enough
# to emit the physical apparent-size gate. On a real GPU the diagnostic normally arrives quickly.
start_app "$OUT/logs/moon.log" VF_CELESTIAL_TARGET=moon VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1
capture "$OUT/moon/ground-moon.png"
for _ in $(seq 1 120); do
  grep -q 'R24 moon evidence:' "$OUT/logs/moon.log" && break
  sleep .25
done
grep -q 'R24 moon evidence:' "$OUT/logs/moon.log"
stop_app
awk '/R24 moon evidence:/ {for(i=1;i<=NF;i++) if($i~/^apparent_diameter_px=/){split($i,a,"="); if(a[2]+0>=5.0) ok=1}} END{exit !ok}' "$OUT/logs/moon.log"

# Actual travel: starts just outside Aster bubble and drives ordinary creative-flight input toward
# the physically located Sun. Wait until production runtime reports arrival within 0.9 solar radii
# above the photosphere, then capture the live procedural Sun shader.
start_app "$OUT/logs/sun-transit.log" VF_CAPTURE_SUN_TRANSIT=1 VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1
for _ in $(seq 1 120); do
  grep -q 'R24 SUN_TRANSIT_ARRIVED' "$OUT/logs/sun-transit.log" && break
  sleep .5
done
grep -q 'R24 SUN_TRANSIT_ARRIVED' "$OUT/logs/sun-transit.log"
capture "$OUT/sun/near-sun-after-real-transit.png"
stop_app

# Require genuinely interstellar speed during the same real transit and a large close-Sun disc.
awk '/R24 sun transit:/ {for(i=1;i<=NF;i++){if($i~/^speed_c=/){split($i,a,"="); if(a[2]+0>1.0) fast=1} if($i~/^angular_diameter_deg=/){split($i,b,"="); if(b[2]+0>40.0) close=1}}} END{exit !(fast&&close)}' "$OUT/logs/sun-transit.log"

montage "$OUT/moon/ground-moon.png" "$OUT/sun/near-sun-after-real-transit.png" -tile 2x1 -geometry 800x450+8+8 "$OUT/r24-moon-sun-overview.png"
{
 echo '=== MOON ==='; grep -E 'moon evidence|Fatal error' "$OUT/logs/moon.log" || true
 echo '=== SUN TRANSIT ==='; grep -E 'sun transit|SUN_TRANSIT|Fatal error' "$OUT/logs/sun-transit.log" | tail -80 || true
} > "$OUT/runtime-summary.txt"
echo "R24 interstellar Sun capture complete"
