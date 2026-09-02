import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js';

const canvas = document.querySelector('#game');
const playButton = document.querySelector('#play-button');
const startPanel = document.querySelector('#start-panel');
const hotbar = document.querySelector('#hotbar');
const statusEl = document.querySelector('#status');
const toastEl = document.querySelector('#toast');

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setSize(window.innerWidth, window.innerHeight, false);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87bfe2);
scene.fog = new THREE.Fog(0x87bfe2, 18, 52);

const camera = new THREE.PerspectiveCamera(72, window.innerWidth / window.innerHeight, 0.05, 100);
camera.rotation.order = 'YXZ';
scene.add(camera);

scene.add(new THREE.HemisphereLight(0xcbe9ff, 0x6c7257, 1.7));
const sun = new THREE.DirectionalLight(0xfff0cf, 2.2);
sun.position.set(24, 36, 12);
scene.add(sun);

const BLOCKS = {
  grass:  { label: '草地', color: 0x67a84f },
  dirt:   { label: '泥土', color: 0x896044 },
  stone:  { label: '岩石', color: 0x7d8388 },
  wood:   { label: '木材', color: 0x8d643f },
  plank:  { label: '木板', color: 0xb98c58 },
  leaves: { label: '树叶', color: 0x4e8a49 }
};

const hotbarTypes = ['grass', 'dirt', 'stone', 'wood', 'plank'];
let selectedIndex = 0;

const world = new Map();
const worldMeshes = [];
const interactiveMeshes = [];
const boxGeometry = new THREE.BoxGeometry(1, 1, 1);
const materials = Object.fromEntries(Object.entries(BLOCKS).map(([id, def]) => [
  id,
  new THREE.MeshLambertMaterial({ color: def.color })
]));

const keyOf = (x, y, z) => `${x},${y},${z}`;
const getBlock = (x, y, z) => world.get(keyOf(x, y, z));
const setBlock = (x, y, z, type) => {
  const key = keyOf(x, y, z);
  if (type) world.set(key, type);
  else world.delete(key);
};

function hash2(x, z) {
  const n = Math.sin(x * 127.1 + z * 311.7) * 43758.5453123;
  return n - Math.floor(n);
}

function terrainHeight(x, z) {
  const broad = Math.sin(x * 0.19) * 1.7 + Math.cos(z * 0.16) * 1.45;
  const ridge = Math.sin((x + z) * 0.085) * 1.2 + Math.cos((x - z) * 0.11) * 0.8;
  return Math.floor(3 + broad + ridge);
}

function generateWorld() {
  world.clear();
  const radius = 20;
  for (let x = -radius; x <= radius; x++) {
    for (let z = -radius; z <= radius; z++) {
      const top = terrainHeight(x, z);
      for (let y = -3; y <= top; y++) {
        let type = 'stone';
        if (y === top) type = 'grass';
        else if (y >= top - 2) type = 'dirt';
        setBlock(x, y, z, type);
      }

      const awayFromSpawn = Math.abs(x) > 4 || Math.abs(z) > 4;
      if (awayFromSpawn && hash2(x, z) > 0.975 && top > 1) addTree(x, top + 1, z);
    }
  }
}

function addTree(x, y, z) {
  const trunkHeight = 3 + Math.floor(hash2(x + 9, z - 4) * 2);
  for (let i = 0; i < trunkHeight; i++) setBlock(x, y + i, z, 'wood');
  const crownY = y + trunkHeight - 1;
  for (let dx = -2; dx <= 2; dx++) {
    for (let dz = -2; dz <= 2; dz++) {
      for (let dy = 0; dy <= 2; dy++) {
        const d = Math.abs(dx) + Math.abs(dz) + dy * 0.35;
        if (d <= 3.3 && !(dx === 0 && dz === 0 && dy === 0)) {
          if (!getBlock(x + dx, crownY + dy, z + dz)) setBlock(x + dx, crownY + dy, z + dz, 'leaves');
        }
      }
    }
  }
}

const neighborDirs = [
  [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]
];

function isExposed(x, y, z) {
  return neighborDirs.some(([dx, dy, dz]) => !getBlock(x + dx, y + dy, z + dz));
}

function rebuildWorldMeshes() {
  for (const mesh of worldMeshes) scene.remove(mesh);
  worldMeshes.length = 0;
  interactiveMeshes.length = 0;

  const grouped = new Map();
  for (const [key, type] of world.entries()) {
    const [x, y, z] = key.split(',').map(Number);
    if (!isExposed(x, y, z)) continue;
    if (!grouped.has(type)) grouped.set(type, []);
    grouped.get(type).push({ x, y, z });
  }

  const matrix = new THREE.Matrix4();
  for (const [type, positions] of grouped.entries()) {
    const mesh = new THREE.InstancedMesh(boxGeometry, materials[type], positions.length);
    mesh.userData.blocks = positions;
    mesh.userData.blockType = type;
    for (let i = 0; i < positions.length; i++) {
      const p = positions[i];
      matrix.makeTranslation(p.x + 0.5, p.y + 0.5, p.z + 0.5);
      mesh.setMatrixAt(i, matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
    scene.add(mesh);
    worldMeshes.push(mesh);
    interactiveMeshes.push(mesh);
  }
}

function renderHotbar() {
  hotbar.innerHTML = '';
  hotbarTypes.forEach((type, index) => {
    const slot = document.createElement('div');
    slot.className = `slot${index === selectedIndex ? ' selected' : ''}`;
    slot.innerHTML = `<span class="slot-number">${index + 1}</span><span class="swatch" style="background:#${BLOCKS[type].color.toString(16).padStart(6, '0')}"></span><span class="slot-name">${BLOCKS[type].label}</span>`;
    hotbar.appendChild(slot);
  });
}

function selectSlot(index) {
  selectedIndex = (index + hotbarTypes.length) % hotbarTypes.length;
  renderHotbar();
  showToast(`已选择：${BLOCKS[hotbarTypes[selectedIndex]].label}`);
}

let toastTimer = 0;
function showToast(text) {
  toastEl.textContent = text;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), 1100);
}

const player = {
  x: 0.5,
  y: 12,
  z: 0.5,
  radius: 0.31,
  height: 1.8,
  eye: 1.62,
  vy: 0,
  grounded: false
};

function topSolidY(x, z) {
  for (let y = 30; y >= -3; y--) if (getBlock(x, y, z)) return y;
  return -3;
}

function respawn() {
  player.x = 0.5;
  player.z = 0.5;
  player.y = topSolidY(0, 0) + 1.02;
  player.vy = 0;
}

function collidesAt(px, py, pz) {
  const eps = 0.001;
  const minX = Math.floor(px - player.radius);
  const maxX = Math.floor(px + player.radius - eps);
  const minY = Math.floor(py);
  const maxY = Math.floor(py + player.height - eps);
  const minZ = Math.floor(pz - player.radius);
  const maxZ = Math.floor(pz + player.radius - eps);
  for (let x = minX; x <= maxX; x++) {
    for (let y = minY; y <= maxY; y++) {
      for (let z = minZ; z <= maxZ; z++) {
        if (getBlock(x, y, z)) return true;
      }
    }
  }
  return false;
}

function blockHitsPlayer(x, y, z) {
  const pMinX = player.x - player.radius;
  const pMaxX = player.x + player.radius;
  const pMinY = player.y;
  const pMaxY = player.y + player.height;
  const pMinZ = player.z - player.radius;
  const pMaxZ = player.z + player.radius;
  return pMaxX > x && pMinX < x + 1 && pMaxY > y && pMinY < y + 1 && pMaxZ > z && pMinZ < z + 1;
}

let yaw = 0;
let pitch = -0.12;
const keys = new Set();
let jumpRequested = false;

function updateCamera() {
  camera.position.set(player.x, player.y + player.eye, player.z);
  camera.rotation.y = yaw;
  camera.rotation.x = pitch;
}

playButton.addEventListener('click', () => canvas.requestPointerLock());
canvas.addEventListener('click', () => {
  if (document.pointerLockElement !== canvas) canvas.requestPointerLock();
});

document.addEventListener('pointerlockchange', () => {
  const active = document.pointerLockElement === canvas;
  startPanel.classList.toggle('hidden', active);
  if (!active) keys.clear();
});

document.addEventListener('mousemove', (event) => {
  if (document.pointerLockElement !== canvas) return;
  yaw -= event.movementX * 0.0022;
  pitch -= event.movementY * 0.0022;
  pitch = THREE.MathUtils.clamp(pitch, -Math.PI / 2 + 0.02, Math.PI / 2 - 0.02);
});

document.addEventListener('keydown', (event) => {
  if (document.pointerLockElement !== canvas) return;
  keys.add(event.code);
  if (event.code === 'Space') jumpRequested = true;
  if (/^Digit[1-5]$/.test(event.code)) selectSlot(Number(event.code.slice(-1)) - 1);
});

document.addEventListener('keyup', (event) => keys.delete(event.code));
document.addEventListener('contextmenu', (event) => event.preventDefault());

document.addEventListener('wheel', (event) => {
  if (document.pointerLockElement !== canvas) return;
  selectSlot(selectedIndex + (event.deltaY > 0 ? 1 : -1));
}, { passive: true });

const raycaster = new THREE.Raycaster();
raycaster.far = 6;

function getTargetBlock() {
  raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
  const hits = raycaster.intersectObjects(interactiveMeshes, false);
  if (!hits.length) return null;
  const hit = hits[0];
  const pos = hit.object.userData.blocks[hit.instanceId];
  if (!pos || !hit.face) return null;
  return { hit, pos };
}

document.addEventListener('mousedown', (event) => {
  if (document.pointerLockElement !== canvas) return;
  const target = getTargetBlock();
  if (!target) return;
  const { hit, pos } = target;

  if (event.button === 0) {
    if (pos.y <= -3) return showToast('基岩层不可破坏');
    setBlock(pos.x, pos.y, pos.z, null);
    rebuildWorldMeshes();
  }

  if (event.button === 2) {
    const n = hit.face.normal;
    const x = pos.x + Math.round(n.x);
    const y = pos.y + Math.round(n.y);
    const z = pos.z + Math.round(n.z);
    if (getBlock(x, y, z)) return;
    if (blockHitsPlayer(x, y, z)) return showToast('不能在玩家身体内放置方块');
    setBlock(x, y, z, hotbarTypes[selectedIndex]);
    rebuildWorldMeshes();
  }
});

function updatePlayer(dt) {
  const forwardInput = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0);
  const rightInput = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0);
  const len = Math.hypot(forwardInput, rightInput) || 1;
  const f = forwardInput / len;
  const r = rightInput / len;

  const forwardX = -Math.sin(yaw);
  const forwardZ = -Math.cos(yaw);
  const rightX = Math.cos(yaw);
  const rightZ = -Math.sin(yaw);
  const speed = keys.has('ShiftLeft') || keys.has('ShiftRight') ? 7.2 : 4.8;
  const dx = (forwardX * f + rightX * r) * speed * dt;
  const dz = (forwardZ * f + rightZ * r) * speed * dt;

  if (!collidesAt(player.x + dx, player.y, player.z)) player.x += dx;
  if (!collidesAt(player.x, player.y, player.z + dz)) player.z += dz;

  player.grounded = collidesAt(player.x, player.y - 0.055, player.z);
  if (jumpRequested && player.grounded) {
    player.vy = 8.4;
    player.grounded = false;
  }
  jumpRequested = false;

  player.vy -= 24 * dt;
  const nextY = player.y + player.vy * dt;
  if (!collidesAt(player.x, nextY, player.z)) {
    player.y = nextY;
  } else {
    player.vy = 0;
    if (nextY < player.y) player.grounded = true;
  }

  if (player.y < -20) respawn();
}

let frames = 0;
let fps = 0;
let fpsTimer = performance.now();
function updateStatus(now) {
  frames++;
  if (now - fpsTimer >= 500) {
    fps = Math.round(frames * 1000 / (now - fpsTimer));
    frames = 0;
    fpsTimer = now;
    statusEl.textContent = `X ${player.x.toFixed(1)} · Y ${player.y.toFixed(1)} · Z ${player.z.toFixed(1)} · ${fps} FPS · ${world.size.toLocaleString()} blocks`;
  }
}

const clock = new THREE.Clock();
function animate(now = performance.now()) {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.033);
  if (document.pointerLockElement === canvas) updatePlayer(dt);
  updateCamera();
  updateStatus(now);
  renderer.render(scene, camera);
}

function onResize() {
  const width = window.innerWidth;
  const height = window.innerHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
}
window.addEventListener('resize', onResize);

generateWorld();
rebuildWorldMeshes();
renderHotbar();
respawn();
updateCamera();
statusEl.textContent = '世界已生成 · 点击进入';
animate();
