export interface ChunkDimensions {
  width: number;
  height: number;
  depth: number;
}

export interface NativeMesh {
  vertexBytes: Uint8Array;
  indices: Uint32Array;
  vertexCount: number;
  vertexStride: number;
  quadCount: number;
}

export interface NativeRaycastHit {
  x: number;
  y: number;
  z: number;
  normalX: number;
  normalY: number;
  normalZ: number;
  distance: number;
  block: number;
}

interface WasmModule {
  HEAPU8: Uint8Array;
  HEAPU32: Uint32Array;
  _malloc(size: number): number;
  _free(ptr: number): void;
  _vf_engine_abi_version(): number;
  _vf_fill_chunk(ptr: number, length: number, chunkX: number, chunkZ: number, width: number, height: number, depth: number): number;
  _vf_build_greedy_mesh(ptr: number, length: number, width: number, height: number, depth: number): number;
  _vf_mesh_vertex_ptr(): number;
  _vf_mesh_vertex_count(): number;
  _vf_mesh_vertex_stride(): number;
  _vf_mesh_index_ptr(): number;
  _vf_mesh_index_count(): number;
  _vf_raycast(
    ptr: number,
    length: number,
    width: number,
    height: number,
    depth: number,
    originX: number,
    originY: number,
    originZ: number,
    directionX: number,
    directionY: number,
    directionZ: number,
    maxDistance: number
  ): number;
  _vf_hit_x(): number;
  _vf_hit_y(): number;
  _vf_hit_z(): number;
  _vf_hit_normal_x(): number;
  _vf_hit_normal_y(): number;
  _vf_hit_normal_z(): number;
  _vf_hit_distance(): number;
  _vf_hit_block(): number;
}

type WasmFactory = (options?: { locateFile?: (path: string) => string }) => Promise<WasmModule>;

const ENGINE_ABI = 1;

export class NativeEngine {
  private constructor(private readonly wasm: WasmModule) {}

  static async load(): Promise<NativeEngine> {
    const scriptUrl = new URL('engine/vf_engine.js', window.location.href).href;
    const namespace = (await import(/* @vite-ignore */ scriptUrl)) as { default: WasmFactory };
    const wasm = await namespace.default({
      locateFile: (path) => new URL(path, scriptUrl).href
    });
    const abi = wasm._vf_engine_abi_version();
    if (abi !== ENGINE_ABI) throw new Error(`Native engine ABI mismatch: web=${ENGINE_ABI}, wasm=${abi}`);
    return new NativeEngine(wasm);
  }

  generateChunk(chunkX: number, chunkZ: number, dimensions: ChunkDimensions): Uint8Array {
    const length = this.volume(dimensions);
    const ptr = this.wasm._malloc(length);
    if (!ptr) throw new Error('WASM allocation failed for chunk');
    try {
      const written = this.wasm._vf_fill_chunk(
        ptr,
        length,
        chunkX,
        chunkZ,
        dimensions.width,
        dimensions.height,
        dimensions.depth
      );
      if (written !== length) throw new Error(`Chunk generation failed: ${written}/${length}`);
      return this.wasm.HEAPU8.slice(ptr, ptr + length);
    } finally {
      this.wasm._free(ptr);
    }
  }

  buildMesh(blocks: Uint8Array, dimensions: ChunkDimensions): NativeMesh {
    const expected = this.volume(dimensions);
    if (blocks.length !== expected) throw new Error(`Chunk byte length mismatch: ${blocks.length}/${expected}`);

    return this.withChunkMemory(blocks, (ptr) => {
      const quadCount = this.wasm._vf_build_greedy_mesh(
        ptr,
        blocks.length,
        dimensions.width,
        dimensions.height,
        dimensions.depth
      );
      const vertexCount = this.wasm._vf_mesh_vertex_count();
      const vertexStride = this.wasm._vf_mesh_vertex_stride();
      const vertexPtr = this.wasm._vf_mesh_vertex_ptr();
      const indexCount = this.wasm._vf_mesh_index_count();
      const indexPtr = this.wasm._vf_mesh_index_ptr();

      const vertexBytes = this.wasm.HEAPU8.slice(vertexPtr, vertexPtr + vertexCount * vertexStride);
      const indexOffset = indexPtr >>> 2;
      const indices = this.wasm.HEAPU32.slice(indexOffset, indexOffset + indexCount);
      return { vertexBytes, indices, vertexCount, vertexStride, quadCount };
    });
  }

  raycast(
    blocks: Uint8Array,
    dimensions: ChunkDimensions,
    origin: readonly [number, number, number],
    direction: readonly [number, number, number],
    maxDistance: number
  ): NativeRaycastHit | null {
    return this.withChunkMemory(blocks, (ptr) => {
      const hit = this.wasm._vf_raycast(
        ptr,
        blocks.length,
        dimensions.width,
        dimensions.height,
        dimensions.depth,
        origin[0],
        origin[1],
        origin[2],
        direction[0],
        direction[1],
        direction[2],
        maxDistance
      );
      if (!hit) return null;
      return {
        x: this.wasm._vf_hit_x(),
        y: this.wasm._vf_hit_y(),
        z: this.wasm._vf_hit_z(),
        normalX: this.wasm._vf_hit_normal_x(),
        normalY: this.wasm._vf_hit_normal_y(),
        normalZ: this.wasm._vf_hit_normal_z(),
        distance: this.wasm._vf_hit_distance(),
        block: this.wasm._vf_hit_block()
      };
    });
  }

  private withChunkMemory<T>(blocks: Uint8Array, fn: (ptr: number) => T): T {
    const ptr = this.wasm._malloc(blocks.length);
    if (!ptr) throw new Error('WASM allocation failed for chunk input');
    try {
      this.wasm.HEAPU8.set(blocks, ptr);
      return fn(ptr);
    } finally {
      this.wasm._free(ptr);
    }
  }

  private volume(dimensions: ChunkDimensions): number {
    const volume = dimensions.width * dimensions.height * dimensions.depth;
    if (!Number.isSafeInteger(volume) || volume <= 0) throw new Error('Invalid chunk dimensions');
    return volume;
  }
}
