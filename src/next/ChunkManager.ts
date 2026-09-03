import { NativeEngine, type ChunkDimensions } from '../engine/NativeEngine';
import { WebGpuVoxelRenderer, type GpuChunkMesh } from '../render-next/WebGpuVoxelRenderer';

interface LoadedChunk {
  readonly chunkX: number;
  readonly chunkZ: number;
  readonly blocks: Uint8Array;
  mesh: GpuChunkMesh;
}

interface ChunkCandidate {
  readonly chunkX: number;
  readonly chunkZ: number;
  readonly distanceSquared: number;
}

export class ChunkManager {
  readonly dimensions: ChunkDimensions = { width: 16, height: 64, depth: 16 };

  private readonly engine: NativeEngine;
  private readonly renderer: WebGpuVoxelRenderer;
  private readonly chunks = new Map<string, LoadedChunk>();

  constructor(engine: NativeEngine, renderer: WebGpuVoxelRenderer) {
    this.engine = engine;
    this.renderer = renderer;
  }

  get loadedCount(): number {
    return this.chunks.size;
  }

  get gpuMeshes(): GpuChunkMesh[] {
    return Array.from(this.chunks.values(), (chunk) => chunk.mesh);
  }

  updateStreaming(worldX: number, worldZ: number, radius = 4, generationBudget = 3): number {
    const centerX = Math.floor(worldX / this.dimensions.width);
    const centerZ = Math.floor(worldZ / this.dimensions.depth);
    this.unloadFarChunks(centerX, centerZ, radius + 1);

    const missing: ChunkCandidate[] = [];
    for (let dz = -radius; dz <= radius; dz += 1) {
      for (let dx = -radius; dx <= radius; dx += 1) {
        const chunkX = centerX + dx;
        const chunkZ = centerZ + dz;
        if (this.chunks.has(this.key(chunkX, chunkZ))) continue;
        missing.push({ chunkX, chunkZ, distanceSquared: dx * dx + dz * dz });
      }
    }
    missing.sort((a, b) => a.distanceSquared - b.distanceSquared);

    const count = Math.min(generationBudget, missing.length);
    for (let index = 0; index < count; index += 1) {
      const candidate = missing[index];
      this.loadChunk(candidate.chunkX, candidate.chunkZ);
    }
    return count;
  }

  getBlock(worldX: number, worldY: number, worldZ: number): number | undefined {
    if (worldY < 0 || worldY >= this.dimensions.height) return undefined;
    const chunkX = Math.floor(worldX / this.dimensions.width);
    const chunkZ = Math.floor(worldZ / this.dimensions.depth);
    const chunk = this.chunks.get(this.key(chunkX, chunkZ));
    if (!chunk) return undefined;

    const localX = this.positiveMod(worldX, this.dimensions.width);
    const localZ = this.positiveMod(worldZ, this.dimensions.depth);
    return chunk.blocks[this.index(localX, worldY, localZ)];
  }

  setBlock(worldX: number, worldY: number, worldZ: number, block: number): boolean {
    if (worldY < 0 || worldY >= this.dimensions.height || block < 0 || block > 255) return false;
    const chunkX = Math.floor(worldX / this.dimensions.width);
    const chunkZ = Math.floor(worldZ / this.dimensions.depth);
    const chunk = this.chunks.get(this.key(chunkX, chunkZ));
    if (!chunk) return false;

    const localX = this.positiveMod(worldX, this.dimensions.width);
    const localZ = this.positiveMod(worldZ, this.dimensions.depth);
    chunk.blocks[this.index(localX, worldY, localZ)] = block;
    this.remeshChunk(chunk);
    return true;
  }

  dispose(): void {
    for (const chunk of this.chunks.values()) this.renderer.destroyChunk(chunk.mesh);
    this.chunks.clear();
  }

  private loadChunk(chunkX: number, chunkZ: number): void {
    const blocks = this.engine.generateChunk(chunkX, chunkZ, this.dimensions);
    const nativeMesh = this.engine.buildMesh(blocks, this.dimensions);
    const origin: readonly [number, number, number] = [
      chunkX * this.dimensions.width,
      0,
      chunkZ * this.dimensions.depth
    ];
    const mesh = this.renderer.uploadChunk(nativeMesh, origin);
    this.chunks.set(this.key(chunkX, chunkZ), { chunkX, chunkZ, blocks, mesh });
  }

  private remeshChunk(chunk: LoadedChunk): void {
    const nativeMesh = this.engine.buildMesh(chunk.blocks, this.dimensions);
    const origin: readonly [number, number, number] = [
      chunk.chunkX * this.dimensions.width,
      0,
      chunk.chunkZ * this.dimensions.depth
    ];
    const nextMesh = this.renderer.uploadChunk(nativeMesh, origin);
    this.renderer.destroyChunk(chunk.mesh);
    chunk.mesh = nextMesh;
  }

  private unloadFarChunks(centerX: number, centerZ: number, keepRadius: number): void {
    for (const [key, chunk] of this.chunks.entries()) {
      const dx = Math.abs(chunk.chunkX - centerX);
      const dz = Math.abs(chunk.chunkZ - centerZ);
      if (dx <= keepRadius && dz <= keepRadius) continue;
      this.renderer.destroyChunk(chunk.mesh);
      this.chunks.delete(key);
    }
  }

  private index(x: number, y: number, z: number): number {
    return (y * this.dimensions.depth + z) * this.dimensions.width + x;
  }

  private positiveMod(value: number, modulus: number): number {
    return ((value % modulus) + modulus) % modulus;
  }

  private key(chunkX: number, chunkZ: number): string {
    return `${chunkX},${chunkZ}`;
  }
}
