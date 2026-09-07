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
python3 - "$OUT/logs/moon.log" <<'PY'
import re, sys
text = open(sys.argv[1], encoding='utf-8', errors='replace').read()
diameters = [float(v) for v in re.findall(r'apparent_diameter_px=([0-9]+(?:\.[0-9]+)?)', text)]
errors = [float(v) for v in re.findall(r'angular_error_deg=([0-9]+(?:\.[0-9]+)?)', text)]
if not diameters or max(diameters) < 5.0:
    raise SystemExit(f'physical Moon apparent diameter gate failed: {diameters[-5:]}')
if errors and min(errors) > 5.0:
    raise SystemExit(f'Moon evidence camera did not hold the real Moon in view: {errors[-5:]}')
print(f'R24 moon visual gate PASS diameter_px={max(diameters):.3f}')
PY

# Actual travel: starts just outside Aster bubble and drives ordinary creative-flight input toward
# the physically located Sun. The 2R stellar inspection shell must prevent one-frame tunnelling.
start_app "$OUT/logs/sun-transit.log" VF_CAPTURE_SUN_TRANSIT=1 VF_CELESTIAL_TIME_SCALE=1 VF_RUNTIME_DIAGNOSTICS=1
for _ in $(seq 1 120); do
  grep -q 'R24 SUN_TRANSIT_ARRIVED' "$OUT/logs/sun-transit.log" && break
  sleep .5
done
grep -q 'R24 SUN_TRANSIT_ARRIVED' "$OUT/logs/sun-transit.log"
capture "$OUT/sun/near-sun-after-real-transit.png"
# Keep the runtime on the shell for a few more frames before stopping. This prevents a one-frame
# success from hiding repeated-input penetration on the next update.
sleep 1.0
stop_app

# Require genuinely interstellar travel, a close physical Sun, and persistent non-penetration.
python3 - "$OUT/logs/sun-transit.log" <<'PY'
import re, sys
text = open(sys.argv[1], encoding='utf-8', errors='replace').read()
speeds = [float(v) for v in re.findall(r'speed_c=([0-9]+(?:\.[0-9]+)?)', text)]
angles = [float(v) for v in re.findall(r'angular_diameter_deg=([0-9]+(?:\.[0-9]+)?)', text)]
clearances = [float(v) for v in re.findall(r'clearance_solar_radii=([0-9]+(?:\.[0-9]+)?)', text)]
arrivals = text.count('R24 SUN_TRANSIT_ARRIVED')
if not speeds or max(speeds) <= 1.0:
    raise SystemExit(f'interstellar speed gate failed: max={max(speeds) if speeds else None}')
if not angles or max(angles) <= 40.0:
    raise SystemExit(f'close Sun angular-size gate failed: max={max(angles) if angles else None}')
if not clearances:
    raise SystemExit('no solar clearance diagnostics found')
# We allow distant pre-arrival clearances; only an undershoot is invalid. V4 should settle at 1R
# photosphere clearance (2R centre distance) and stay there despite continued W input.
if min(clearances) < 0.95:
    raise SystemExit(f'stellar shell penetration detected: min_clearance_R={min(clearances):.6f}')
if arrivals < 2:
    raise SystemExit(f'not enough persistent shell frames after arrival: arrivals={arrivals}')
print('R24 Sun transit visual/physics gate PASS '
      f'max_speed_c={max(speeds):.3f} max_diameter_deg={max(angles):.3f} '
      f'min_clearance_R={min(clearances):.3f} arrivals={arrivals}')
PY

montage "$OUT/moon/ground-moon.png" "$OUT/sun/near-sun-after-real-transit.png" -tile 2x1 -geometry 800x450+8+8 "$OUT/r24-moon-sun-overview.png"
{
 echo '=== MOON ==='; grep -E 'moon evidence|moon ground observer|Fatal error' "$OUT/logs/moon.log" || true
 echo '=== SUN TRANSIT ==='; grep -E 'sun transit|SUN_TRANSIT|Fatal error' "$OUT/logs/sun-transit.log" | tail -100 || true
} > "$OUT/runtime-summary.txt"
echo "R24 interstellar Sun capture complete"
