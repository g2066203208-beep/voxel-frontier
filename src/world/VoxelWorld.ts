import type { BlockId } from '../types';

export class VoxelWorld {
  private readonly blocks = new Map<string, BlockId>();

  static key(x: number, y: number, z: number): string {
    return `${x},${y},${z}`;
  }

  clear(): void {
    this.blocks.clear();
  }

  get(x: number, y: number, z: number): BlockId | undefined {
    return this.blocks.get(VoxelWorld.key(x, y, z));
  }

  set(x: number, y: number, z: number, type?: BlockId): void {
    const key = VoxelWorld.key(x, y, z);
    if (type) this.blocks.set(key, type);
    else this.blocks.delete(key);
  }

  has(x: number, y: number, z: number): boolean {
    return this.blocks.has(VoxelWorld.key(x, y, z));
  }

  entries(): IterableIterator<[string, BlockId]> {
    return this.blocks.entries();
  }

  get size(): number {
    return this.blocks.size;
  }

  topSolidY(x: number, z: number, fromY = 40): number {
    for (let y = fromY; y >= -3; y -= 1) {
      if (this.has(x, y, z)) return y;
    }
    return -3;
  }
}
