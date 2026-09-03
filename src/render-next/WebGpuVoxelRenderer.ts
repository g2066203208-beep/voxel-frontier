import type { NativeMesh } from '../engine/NativeEngine';

const CAMERA_UNIFORM_BYTES = 80;
const CHUNK_UNIFORM_BYTES = 16;

const SHADER = /* wgsl */ `
struct CameraUniform {
  viewProjection: mat4x4<f32>,
  lightDirection: vec4<f32>,
};

struct ChunkUniform {
  origin: vec4<f32>,
};

@group(0) @binding(0) var<uniform> camera: CameraUniform;
@group(1) @binding(0) var<uniform> chunk: ChunkUniform;

struct VertexInput {
  @location(0) position: vec3<f32>,
  @location(1) packed: u32,
};

struct VertexOutput {
  @builtin(position) clipPosition: vec4<f32>,
  @location(0) color: vec3<f32>,
  @location(1) normal: vec3<f32>,
};

fn blockColor(block: u32) -> vec3<f32> {
  switch block {
    case 1u: { return vec3<f32>(0.48, 0.50, 0.53); }
    case 2u: { return vec3<f32>(0.43, 0.29, 0.18); }
    case 3u: { return vec3<f32>(0.29, 0.61, 0.24); }
    case 4u: { return vec3<f32>(0.46, 0.31, 0.16); }
    case 5u: { return vec3<f32>(0.22, 0.52, 0.20); }
    default: { return vec3<f32>(0.85, 0.20, 0.85); }
  }
}

fn normalFromIndex(index: u32) -> vec3<f32> {
  switch index {
    case 0u: { return vec3<f32>(-1.0, 0.0, 0.0); }
    case 1u: { return vec3<f32>( 1.0, 0.0, 0.0); }
    case 2u: { return vec3<f32>(0.0, -1.0, 0.0); }
    case 3u: { return vec3<f32>(0.0,  1.0, 0.0); }
    case 4u: { return vec3<f32>(0.0, 0.0, -1.0); }
    default: { return vec3<f32>(0.0, 0.0, 1.0); }
  }
}

@vertex
fn vsMain(input: VertexInput) -> VertexOutput {
  let block = input.packed & 255u;
  let normalIndex = (input.packed >> 8u) & 7u;
  let worldPosition = input.position + chunk.origin.xyz;

  var output: VertexOutput;
  output.clipPosition = camera.viewProjection * vec4<f32>(worldPosition, 1.0);
  output.color = blockColor(block);
  output.normal = normalFromIndex(normalIndex);
  return output;
}

@fragment
fn fsMain(input: VertexOutput) -> @location(0) vec4<f32> {
  let n = normalize(input.normal);
  let l = normalize(-camera.lightDirection.xyz);
  let diffuse = max(dot(n, l), 0.0);
  let brightness = 0.38 + diffuse * 0.62;
  return vec4<f32>(input.color * brightness, 1.0);
}
`;

export interface GpuChunkMesh {
  readonly vertexBuffer: GPUBuffer;
  readonly indexBuffer: GPUBuffer;
  readonly indexCount: number;
  readonly uniformBuffer: GPUBuffer;
  readonly bindGroup: GPUBindGroup;
  readonly origin: readonly [number, number, number];
}

export class WebGpuVoxelRenderer {
  private readonly canvas: HTMLCanvasElement;
  private readonly device: GPUDevice;
  private readonly context: GPUCanvasContext;
  private readonly format: GPUTextureFormat;
  private readonly pipeline: GPURenderPipeline;
  private readonly cameraBuffer: GPUBuffer;
  private readonly cameraBindGroup: GPUBindGroup;
  private depthTexture: GPUTexture | null = null;
  private depthWidth = 0;
  private depthHeight = 0;

  private constructor(
    canvas: HTMLCanvasElement,
    device: GPUDevice,
    context: GPUCanvasContext,
    format: GPUTextureFormat
  ) {
    this.canvas = canvas;
    this.device = device;
    this.context = context;
    this.format = format;

    const shader = device.createShaderModule({ label: 'Voxel Frontier WGSL', code: SHADER });
    const cameraLayout = device.createBindGroupLayout({
      label: 'camera bind group layout',
      entries: [{
        binding: 0,
        visibility: GPUShaderStage.VERTEX | GPUShaderStage.FRAGMENT,
        buffer: { type: 'uniform' }
      }]
    });
    const chunkLayout = device.createBindGroupLayout({
      label: 'chunk bind group layout',
      entries: [{ binding: 0, visibility: GPUShaderStage.VERTEX, buffer: { type: 'uniform' } }]
    });

    const layout = device.createPipelineLayout({ bindGroupLayouts: [cameraLayout, chunkLayout] });
    this.pipeline = device.createRenderPipeline({
      label: 'voxel pipeline',
      layout,
      vertex: {
        module: shader,
        entryPoint: 'vsMain',
        buffers: [{
          arrayStride: 16,
          stepMode: 'vertex',
          attributes: [
            { shaderLocation: 0, offset: 0, format: 'float32x3' },
            { shaderLocation: 1, offset: 12, format: 'uint32' }
          ]
        }]
      },
      fragment: {
        module: shader,
        entryPoint: 'fsMain',
        targets: [{ format }]
      },
      primitive: {
        topology: 'triangle-list',
        frontFace: 'ccw',
        cullMode: 'back'
      },
      depthStencil: {
        format: 'depth24plus',
        depthWriteEnabled: true,
        depthCompare: 'less'
      }
    });

    this.cameraBuffer = device.createBuffer({
      label: 'camera uniform',
      size: CAMERA_UNIFORM_BYTES,
      usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST
    });
    this.cameraBindGroup = device.createBindGroup({
      layout: cameraLayout,
      entries: [{ binding: 0, resource: { buffer: this.cameraBuffer } }]
    });
  }

  static async create(canvas: HTMLCanvasElement): Promise<WebGpuVoxelRenderer | null> {
    if (!navigator.gpu) return null;
    const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
    if (!adapter) return null;
    const device = await adapter.requestDevice();
    const context = canvas.getContext('webgpu');
    if (!context) return null;
    const format = navigator.gpu.getPreferredCanvasFormat();
    context.configure({ device, format, alphaMode: 'opaque' });
    return new WebGpuVoxelRenderer(canvas, device, context, format);
  }

  uploadChunk(mesh: NativeMesh, origin: readonly [number, number, number]): GpuChunkMesh {
    if (mesh.vertexStride !== 16) throw new Error(`Unsupported native vertex stride: ${mesh.vertexStride}`);

    const vertexBuffer = this.device.createBuffer({
      label: 'chunk vertex buffer',
      size: Math.max(4, mesh.vertexBytes.byteLength),
      usage: GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST
    });
    if (mesh.vertexBytes.byteLength > 0) this.device.queue.writeBuffer(vertexBuffer, 0, mesh.vertexBytes);

    const indexBuffer = this.device.createBuffer({
      label: 'chunk index buffer',
      size: Math.max(4, mesh.indices.byteLength),
      usage: GPUBufferUsage.INDEX | GPUBufferUsage.COPY_DST
    });
    if (mesh.indices.byteLength > 0) this.device.queue.writeBuffer(indexBuffer, 0, mesh.indices);

    const uniformBuffer = this.device.createBuffer({
      label: 'chunk origin uniform',
      size: CHUNK_UNIFORM_BYTES,
      usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST
    });
    this.device.queue.writeBuffer(uniformBuffer, 0, new Float32Array([origin[0], origin[1], origin[2], 0]));

    const bindGroup = this.device.createBindGroup({
      layout: this.pipeline.getBindGroupLayout(1),
      entries: [{ binding: 0, resource: { buffer: uniformBuffer } }]
    });

    return { vertexBuffer, indexBuffer, indexCount: mesh.indices.length, uniformBuffer, bindGroup, origin };
  }

  destroyChunk(mesh: GpuChunkMesh): void {
    mesh.vertexBuffer.destroy();
    mesh.indexBuffer.destroy();
    mesh.uniformBuffer.destroy();
  }

  render(viewProjection: Float32Array, chunks: readonly GpuChunkMesh[]): void {
    if (viewProjection.length !== 16) throw new Error('viewProjection must contain 16 floats');
    this.ensureDepthTexture();
    if (!this.depthTexture) return;

    const cameraData = new Float32Array(20);
    cameraData.set(viewProjection, 0);
    cameraData.set([0.45, -1.0, 0.35, 0.0], 16);
    this.device.queue.writeBuffer(this.cameraBuffer, 0, cameraData);

    const encoder = this.device.createCommandEncoder({ label: 'voxel frame encoder' });
    const pass = encoder.beginRenderPass({
      colorAttachments: [{
        view: this.context.getCurrentTexture().createView(),
        clearValue: { r: 0.48, g: 0.70, b: 0.86, a: 1 },
        loadOp: 'clear',
        storeOp: 'store'
      }],
      depthStencilAttachment: {
        view: this.depthTexture.createView(),
        depthClearValue: 1,
        depthLoadOp: 'clear',
        depthStoreOp: 'store'
      }
    });

    pass.setPipeline(this.pipeline);
    pass.setBindGroup(0, this.cameraBindGroup);
    for (const chunk of chunks) {
      if (chunk.indexCount === 0) continue;
      pass.setBindGroup(1, chunk.bindGroup);
      pass.setVertexBuffer(0, chunk.vertexBuffer);
      pass.setIndexBuffer(chunk.indexBuffer, 'uint32');
      pass.drawIndexed(chunk.indexCount);
    }
    pass.end();
    this.device.queue.submit([encoder.finish()]);
  }

  private ensureDepthTexture(): void {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.floor(this.canvas.clientWidth * dpr));
    const height = Math.max(1, Math.floor(this.canvas.clientHeight * dpr));
    if (this.canvas.width !== width || this.canvas.height !== height) {
      this.canvas.width = width;
      this.canvas.height = height;
    }
    if (width === this.depthWidth && height === this.depthHeight && this.depthTexture) return;

    this.depthTexture?.destroy();
    this.depthTexture = this.device.createTexture({
      label: 'depth texture',
      size: { width, height },
      format: 'depth24plus',
      usage: GPUTextureUsage.RENDER_ATTACHMENT
    });
    this.depthWidth = width;
    this.depthHeight = height;
  }
}
