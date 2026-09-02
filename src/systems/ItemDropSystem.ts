import * as THREE from 'three';
import type { BlockPosition, ItemId } from '../types';
import { ITEMS } from '../world/BlockRegistry';
import { Inventory } from './Inventory';

interface WorldDrop {
  readonly item: ItemId;
  readonly mesh: THREE.Mesh;
  readonly baseY: number;
  age: number;
}

export class ItemDropSystem {
  private readonly scene: THREE.Scene;
  private readonly cube = new THREE.BoxGeometry(0.28, 0.28, 0.28);
  private readonly berry = new THREE.SphereGeometry(0.16, 10, 8);
  private readonly materials = new Map<ItemId, THREE.MeshLambertMaterial>();
  private readonly drops: WorldDrop[] = [];

  constructor(scene: THREE.Scene) {
    this.scene = scene;
  }

  spawn(item: ItemId, position: BlockPosition): void {
    const geometry = item === 'berry' ? this.berry : this.cube;
    const material = this.getMaterial(item);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(position.x + 0.5, position.y + 0.38, position.z + 0.5);
    mesh.rotation.set(0.2, Math.random() * Math.PI, 0.15);
    this.scene.add(mesh);
    this.drops.push({ item, mesh, baseY: mesh.position.y, age: 0 });
  }

  update(dt: number, playerPosition: THREE.Vector3, inventory: Inventory): ItemId[] {
    const collected: ItemId[] = [];
    for (let index = this.drops.length - 1; index >= 0; index -= 1) {
      const drop = this.drops[index];
      drop.age += dt;
      drop.mesh.rotation.y += dt * 1.8;
      drop.mesh.position.y = drop.baseY + Math.sin(drop.age * 3.2) * 0.08;

      const dx = drop.mesh.position.x - playerPosition.x;
      const dy = drop.mesh.position.y - (playerPosition.y + 0.8);
      const dz = drop.mesh.position.z - playerPosition.z;
      const distanceSq = dx * dx + dy * dy + dz * dz;

      if (drop.age > 0.2 && distanceSq <= 1.15 * 1.15) {
        inventory.add(drop.item);
        collected.push(drop.item);
        this.scene.remove(drop.mesh);
        this.drops.splice(index, 1);
      }
    }
    return collected;
  }

  clear(): void {
    for (const drop of this.drops) this.scene.remove(drop.mesh);
    this.drops.length = 0;
  }

  private getMaterial(item: ItemId): THREE.MeshLambertMaterial {
    const existing = this.materials.get(item);
    if (existing) return existing;
    const material = new THREE.MeshLambertMaterial({ color: ITEMS[item].color });
    this.materials.set(item, material);
    return material;
  }
}
