import { InputManager } from '../core/InputManager';
import { NativeEngine } from '../engine/NativeEngine';
import { WebGpuVoxelRenderer } from '../render-next/WebGpuVoxelRenderer';
import { ChunkManager } from './ChunkManager';
import { multiplyMat4, perspectiveWebGpu, viewFromYawPitch } from './Mat4';

export class NextEnginePreview {
  private readonly canvas: HTMLCanvasElement;
  private readonly input: InputManager;
  private readonly renderer: WebGpuVoxelRenderer;
  private readonly chunks: ChunkManager;
  private readonly status: HTMLElement;
  private readonly startPanel: HTMLElement;
  private readonly position = [0, 18, 0];

  private verticalVelocity = 0;
  private grounded = false;
  private lastTime = performance.now();
  private fpsFrames = 0;
  private fpsTimestamp = performance.now();
  private fps = 0;

  private constructor(
    canvas: HTMLCanvasElement,
    playButton: HTMLButtonElement,
    renderer: WebGpuVoxelRenderer,
    engine: NativeEngine
  ) {
    this.canvas = canvas;
    this.renderer = renderer;
    this.chunks = new ChunkManager(engine, renderer);
    this.status = this.requireElement('#status');
    this.startPanel = this.requireElement('#start-panel');

    this.input = new InputManager(canvas, {
      onActiveChange: (active) => this.startPanel.classList.toggle('hidden', active),
      onSecondaryAction: () => undefined,
      onSlotSelect: () => undefined,
      onSlotStep: () => undefined
    });
    playButton.addEventListener('click', () => this.input.requestPointerLock());

    this.preparePreviewUi();
  }

  static async create(canvas: HTMLCanvasElement, playButton: HTMLButtonElement): Promise<NextEnginePreview | null> {
    const renderer = await WebGpuVoxelRenderer.create(canvas);
    if (!renderer) return null;
    const engine = await NativeEngine.load();
    return new NextEnginePreview(canvas, playButton, renderer, engine);
  }

  start(): void {
    this.chunks.updateStreaming(this.position[0], this.position[2], 4, 9);
    const ground = this.groundEyeHeight(this.position[0], this.position[2]);
    if (ground !== null) this.position[1] = ground;
    requestAnimationFrame(this.animate);
  }

  private animate = (now: number): void => {
    const dt = Math.min(0.033, Math.max(0, (now - this.lastTime) / 1000));
    this.lastTime = now;

    this.updatePlayer(dt);
    this.chunks.updateStreaming(this.position[0], this.position[2], 4, 2);

    const projection = perspectiveWebGpu(
      72 * Math.PI / 180,
      Math.max(1, this.canvas.clientWidth) / Math.max(1, this.canvas.clientHeight),
      0.05,
      512
    );
    const view = viewFromYawPitch(
      [this.position[0], this.position[1], this.position[2]],
      this.input.yaw,
      this.input.pitch
    );
    this.renderer.render(multiplyMat4(projection, view), this.chunks.gpuMeshes);
    this.updateFps(now);
    requestAnimationFrame(this.animate);
  };

  private updatePlayer(dt: number): void {
    if (!this.input.active) return;

    const axes = this.input.movementAxes();
    const speed = axes.sprint ? 10.5 : 5.8;
    const sinYaw = Math.sin(this.input.yaw);
    const cosYaw = Math.cos(this.input.yaw);
    const forwardX = sinYaw;
    const forwardZ = -cosYaw;
    const rightX = cosYaw;
    const rightZ = sinYaw;

    this.position[0] += (forwardX * axes.forward + rightX * axes.right) * speed * dt;
    this.position[2] += (forwardZ * axes.forward + rightZ * axes.right) * speed * dt;

    const groundEye = this.groundEyeHeight(this.position[0], this.position[2]);
    if (this.input.consumeJump() && this.grounded) {
      this.verticalVelocity = 6.5;
      this.grounded = false;
    }

    this.verticalVelocity -= 18 * dt;
    this.position[1] += this.verticalVelocity * dt;

    if (groundEye !== null && this.position[1] <= groundEye) {
      this.position[1] = groundEye;
      this.verticalVelocity = 0;
      this.grounded = true;
    }
  }

  private groundEyeHeight(worldX: number, worldZ: number): number | null {
    const x = Math.floor(worldX);
    const z = Math.floor(worldZ);
    for (let y = this.chunks.dimensions.height - 1; y >= 0; y -= 1) {
      const block = this.chunks.getBlock(x, y, z);
      if (block === undefined) return null;
      if (block !== 0) return y + 2.62;
    }
    return 2.62;
  }

  private updateFps(now: number): void {
    this.fpsFrames += 1;
    const elapsed = now - this.fpsTimestamp;
    if (elapsed < 500) return;
    this.fps = Math.round(this.fpsFrames * 1000 / elapsed);
    this.fpsFrames = 0;
    this.fpsTimestamp = now;
    this.status.textContent = [
      'NEXT C++/WASM + WebGPU',
      `${this.fps} FPS`,
      `${this.chunks.loadedCount} chunks`,
      `X ${this.position[0].toFixed(1)}`,
      `Y ${this.position[1].toFixed(1)}`,
      `Z ${this.position[2].toFixed(1)}`
    ].join(' · ');
  }

  private preparePreviewUi(): void {
    const eyebrow = document.querySelector<HTMLElement>('#start-panel .eyebrow');
    const description = document.querySelector<HTMLElement>('#start-panel .panel-card > p:not(.eyebrow)');
    if (eyebrow) eyebrow.textContent = 'Next Engine Preview · C++23 / WebAssembly SIMD / WebGPU';
    if (description) {
      description.textContent = '新引擎性能预览：C++ 连续体素 Chunk、Greedy Meshing、WebAssembly SIMD 与原生 WebGPU 渲染。';
    }
    const vitals = document.querySelector<HTMLElement>('#vitals');
    const hotbar = document.querySelector<HTMLElement>('#hotbar');
    const dayClock = document.querySelector<HTMLElement>('#day-clock');
    if (vitals) vitals.hidden = true;
    if (hotbar) hotbar.hidden = true;
    if (dayClock) dayClock.textContent = 'NEXT ENGINE';
  }

  private requireElement<T extends HTMLElement = HTMLElement>(selector: string): T {
    const element = document.querySelector<T>(selector);
    if (!element) throw new Error(`Missing required element: ${selector}`);
    return element;
  }
}
