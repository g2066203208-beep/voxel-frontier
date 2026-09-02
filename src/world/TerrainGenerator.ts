import type { BlockId } from '../types';
import { VoxelWorld } from './VoxelWorld';

function hash2(x: number, z: number): number {
  const n = Math.sin(x * 127.1 + z * 311.7) * 43758.5453123;
  return n - Math.floor(n);
}

function terrainHeight(x: number, z: number): number {
  const broad = Math.sin(x * 0.19) * 1.7 + Math.cos(z * 0.16) * 1.45;
  const ridge = Math.sin((x + z) * 0.085) * 1.2 + Math.cos((x - z) * 0.11) * 0.8;
  return Math.floor(3 + broad + ridge);
}

function addTree(world: VoxelWorld, x: number, y: number, z: number): void {
  const trunkHeight = 3 + Math.floor(hash2(x + 9, z - 4) * 2);
  for (let i = 0; i < trunkHeight; i += 1) world.set(x, y + i, z, 'wood');

  const crownY = y + trunkHeight - 1;
  for (let dx = -2; dx <= 2; dx += 1) {
    for (let dz = -2; dz <= 2; dz += 1) {
      for (let dy = 0; dy <= 2; dy += 1) {
        const distance = Math.abs(dx) + Math.abs(dz) + dy * 0.35;
        if (distance <= 3.3 && !(dx === 0 && dz === 0 && dy === 0)) {
          if (!world.has(x + dx, crownY + dy, z + dz)) {
            world.set(x + dx, crownY + dy, z + dz, 'leaves');
          }
        }
      }
    }
  }
}

export function generateInitialWorld(world: VoxelWorld, radius = 20): void {
  world.clear();
  for (let x = -radius; x <= radius; x += 1) {
    for (let z = -radius; z <= radius; z += 1) {
      const top = terrainHeight(x, z);
      for (let y = -3; y <= top; y += 1) {
        let type: BlockId = 'stone';
        if (y === top) type = 'grass';
        else if (y >= top - 2) type = 'dirt';
        world.set(x, y, z, type);
      }

      const awayFromSpawn = Math.abs(x) > 4 || Math.abs(z) > 4;
      if (awayFromSpawn && hash2(x, z) > 0.975 && top > 1) {
        addTree(world, x, top + 1, z);
      }
    }
  }
}
