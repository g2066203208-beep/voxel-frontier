import * as THREE from 'three';
import type { BlockId, BlockPosition, TargetBlock } from '../types';
import { BLOCKS } from '../world/BlockRegistry';
import { VoxelWorld } from '../world/VoxelWorld';

const NEIGHBORS: ReadonlyArray<readonly [number, number, number]> = [
  [1, 0, 0],
  [-1, 0, 0],
  [0, 1, 0],
  [0, -1, 0],
  [0, 0, 1],
  [0, 0, -1]
];

interface InteractiveMeshData {
  blocks: BlockPosition[];
  blockType: BlockId;
}

export class WorldRenderer {
  private readonly scene: THREE.Scene;
  private readonly geometry = new THREE.BoxGeometry(1, 1, 1);
  private readonly materials: Record<BlockId, THREE.MeshLambertMaterial>;
  private readonly meshes: THREE.InstancedMesh[] = [];
  private readonly raycaster = new THREE.Raycaster();

  constructor(scene: THREE.Scene) {
    this.scene = scene;
    this.raycaster.far = 6;
    this.materials = Object.fromEntries(
      (Object.entries(BLOCKS) as Array<[BlockId, (typeof BLOCKS)[BlockId]]>).map(([id, def]) => [
        id,
        new THREE.MeshLambertMaterial({ color: def.color })
      ])
    ) as Record<BlockId, THREE.MeshLambertMaterial>;
  }

  rebuild(world: VoxelWorld): void {
    for (const mesh of this.meshes) this.scene.remove(mesh);
    this.meshes.length = 0;

    const grouped = new Map<BlockId, BlockPosition[]>();
    for (const [key, type] of world.entries()) {
      const [x, y, z] = key.split(',').map(Number);
      if (!this.isExposed(world, x, y, z)) continue;
      const list = grouped.get(type) ?? [];
      list.push({ x, y, z });
      grouped.set(type, list);
    }

    const matrix = new THREE.Matrix4();
    for (const [type, positions] of grouped.entries()) {
      const mesh = new THREE.InstancedMesh(this.geometry, this.materials[type], positions.length);
      const data: InteractiveMeshData = { blocks: positions, blockType: type };
      mesh.userData = data;

      positions.forEach((position, index) => {
        matrix.makeTranslation(position.x + 0.5, position.y + 0.5, position.z + 0.5);
        mesh.setMatrixAt(index, matrix);
      });

      mesh.instanceMatrix.needsUpdate = true;
      mesh.computeBoundingSphere();
      this.scene.add(mesh);
      this.meshes.push(mesh);
    }
  }

  target(camera: THREE.PerspectiveCamera): TargetBlock | null {
    this.raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
    const hit = this.raycaster.intersectObjects(this.meshes, false)[0];
    if (!hit || hit.instanceId === undefined || !hit.face) return null;

    const data = hit.object.userData as InteractiveMeshData;
    const position = data.blocks[hit.instanceId];
    if (!position) return null;

    return {
      position,
      normal: hit.face.normal.clone()
    };
  }

  private isExposed(world: VoxelWorld, x: number, y: number, z: number): boolean {
    return NEIGHBORS.some(([dx, dy, dz]) => !world.has(x + dx, y + dy, z + dz));
  }
}
