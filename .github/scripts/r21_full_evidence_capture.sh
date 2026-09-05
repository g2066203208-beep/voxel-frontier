#!/usr/bin/env bash
set -euo pipefail

export SDL_VIDEODRIVER=x11
export DISPLAY=:99
mkdir -p recapture/terrain recapture/celestial

Xvfb :99 -screen 0 1600x900x24 -nolisten tcp >xvfb-full-evidence.log 2>&1 &
XVFB_PID=$!
trap 'kill $XVFB_PID 2>/dev/null || true' EXIT
sleep 2

APP="$(find build/visual -type f -name voxel_frontier -perm -111 | head -n 1)"
test -n "$APP"

capture_ready_frame() {
  local out="$1"
  local label="$2"
  local attempts="${3:-24}"
  for attempt in $(seq 1 "$attempts"); do
    sleep 3
    import -display :99 -window root "$out"
    local colors
    colors="$(convert "$out" -format '%k' info:)"
    echo "${label} attempt=${attempt} unique_colors=${colors}" | tee -a recapture/frame-readiness.txt
    if [ "$colors" -gt 64 ]; then
      return 0
    fi
  done
  return 1
}

capture_landform() {
  local mode="$1"
  local log="recapture/terrain/${mode}.log"
  stdbuf -oL -eL env VF_CAPTURE_LANDFORM="$mode" VF_CELESTIAL_TIME_SCALE=1 "$APP" >"$log" 2>&1 &
  local pid=$!
  local ready=0
  for _ in $(seq 1 75); do
    sleep 2
    if grep -q 'Capture target elevation' "$log"; then ready=1; break; fi
    kill -0 "$pid" 2>/dev/null || break
  done
  if [ "$ready" -ne 1 ]; then
    echo "${mode}: no target marker" | tee -a recapture/terrain/capture-info.txt
    cat "$log" || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    return 1
  fi

  if ! capture_ready_frame "recapture/terrain/${mode}.png" "terrain-${mode}" 24; then
    echo "${mode}: renderer never produced a nontrivial framebuffer" | tee -a recapture/terrain/capture-info.txt
    cat "$log" || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    return 1
  fi

  local colors
  colors="$(convert "recapture/terrain/${mode}.png" -format '%k' info:)"
  echo "${mode} unique_colors=${colors}" | tee -a recapture/terrain/capture-info.txt
  grep -E 'Capture target elevation|Spawn land elevation:' "$log" | tee -a recapture/terrain/terrain-physics.txt || true
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  sleep 1
}

for mode in mountain highland coast river hills canyon dunes wetland glacier volcano arid lowland; do
  capture_landform "$mode"
done

montage \
  recapture/terrain/mountain.png recapture/terrain/highland.png recapture/terrain/coast.png \
  recapture/terrain/river.png recapture/terrain/hills.png recapture/terrain/canyon.png \
  recapture/terrain/dunes.png recapture/terrain/wetland.png recapture/terrain/glacier.png \
  recapture/terrain/volcano.png recapture/terrain/arid.png recapture/terrain/lowland.png \
  -tile 3x4 -geometry 533x300+0+0 recapture/terrain/terrain-12-montage.png
identify recapture/terrain/*.png | tee -a recapture/terrain/capture-info.txt

capture_sequence() {
  local sky="$1"
  local log="recapture/celestial/${sky}.log"
  stdbuf -oL -eL env VF_CAPTURE_CELESTIAL="$sky" VF_CELESTIAL_TIME_SCALE=3600 "$APP" >"$log" 2>&1 &
  local pid=$!
  local ready=0
  for _ in $(seq 1 75); do
    sleep 2
    if grep -q "Celestial capture: ${sky}" "$log"; then ready=1; break; fi
    kill -0 "$pid" 2>/dev/null || break
  done
  if [ "$ready" -ne 1 ]; then
    echo "${sky}: no celestial target marker" | tee -a recapture/celestial/capture-info.txt
    cat "$log" || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    return 1
  fi

  if ! capture_ready_frame "recapture/celestial/${sky}-0.png" "celestial-${sky}-0" 24; then
    echo "${sky}: renderer never produced initial celestial framebuffer" | tee -a recapture/celestial/capture-info.txt
    cat "$log" || true
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    return 1
  fi

  # Continue the exact same process and camera. Every 1.5 real seconds at 3600x advances roughly
  # 1.5 simulated hours under a nominal 60 Hz loop while each individual step remains ~60 s.
  for i in 1 2 3 4 5; do
    sleep 1.5
    import -display :99 -window root "recapture/celestial/${sky}-${i}.png"
    local colors
    colors="$(convert "recapture/celestial/${sky}-${i}.png" -format '%k' info:)"
    echo "celestial-${sky}-${i} unique_colors=${colors}" | tee -a recapture/frame-readiness.txt
    test "$colors" -gt 64
  done
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true

  montage recapture/celestial/${sky}-0.png recapture/celestial/${sky}-1.png \
          recapture/celestial/${sky}-2.png recapture/celestial/${sky}-3.png \
          recapture/celestial/${sky}-4.png recapture/celestial/${sky}-5.png \
          -tile 3x2 -geometry 533x300+0+0 "recapture/celestial/${sky}-motion-montage.png"
  convert -delay 45 -loop 0 recapture/celestial/${sky}-0.png recapture/celestial/${sky}-1.png \
          recapture/celestial/${sky}-2.png recapture/celestial/${sky}-3.png \
          recapture/celestial/${sky}-4.png recapture/celestial/${sky}-5.png \
          "recapture/celestial/${sky}-motion.gif"
  compare -metric AE recapture/celestial/${sky}-0.png recapture/celestial/${sky}-5.png \
          "recapture/celestial/${sky}-first-last-diff.png" \
          2>"recapture/celestial/${sky}-first-last-ae.txt" || true
  grep -E 'Celestial capture:|Aster-Sun distance:|Aster-Luna distance:' "$log" \
    | tee -a recapture/celestial/physics-summary.txt || true
}

capture_sequence sun
capture_sequence moon
identify recapture/celestial/*.png | tee -a recapture/celestial/capture-info.txt
cat recapture/terrain/terrain-physics.txt || true
cat recapture/celestial/physics-summary.txt || true
cat recapture/celestial/*-first-last-ae.txt || true
