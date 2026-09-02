import * as THREE from 'three';
import { WorldRenderer } from '../render/WorldRenderer';
import type { BlockPosition } from '../types';
import { Hud } from '../ui/Hud';
import { HOTBAR_BLOCKS } from '../world/BlockRegistry';
import { generateInitialWorld } from '../world/TerrainGenerator';
import { VoxelWorld } from '../world/VoxelWorld';
import { InputManager } from './InputManager';
import { PlayerController } from './PlayerController';

export class Game {
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.PerspectiveCamera;
  private readonly world = new VoxelWorld();
  private readonly worldRenderer: WorldRenderer;
  private readonly player = new PlayerController();
  private readonly hud = new Hud();
  private readonly input: InputManager;
  private readonly clock = new THREE.Clock();

  private selectedIndex = 0;
  private frameCount = 0;
  private fps = 0;
  private fpsTimestamp = performance.now();

  constructor(canvas: HTMLCanvasElement, playButton: HTMLButtonElement) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x87bfe2);
    this.scene.fog = new THREE.Fog(0x87bfe2, 18, 52);

    this.camera = new THREE.PerspectiveCamera(72, 1, 0.05, 100);
    this.camera.rotation.order = 'YXZ';
    this.scene.add(this.camera);

    this.scene.add(new THREE.HemisphereLight(0xcbe9ff, 0x6c7257, 1.7));
    const sun = new THREE.DirectionalLight(0xfff0cf, 2.2);
    sun.position.set(24, 36, 12);
    this.scene.add(sun);

    this.worldRenderer = new WorldRenderer(this.scene);
    this.input = new InputManager(canvas, {
      onActiveChange: (active) => this.hud.setActive(active),
      onPrimaryAction: () => this.breakTargetBlock(),
      onSecondaryAction: () => this.placeTargetBlock(),
      onSlotSelect: (index) => this.selectSlot(index),
      onSlotStep: (step) => this.selectSlot(this.selectedIndex + step)
    });

    playButton.addEventListener('click', () => this.input.requestPointerLock());
    window.addEventListener('resize', () => this.resize());
  }

  start(): void {
    generateInitialWorld(this.world);
    this.worldRenderer.rebuild(this.world);
    this.player.respawn(this.world);
    this.hud.renderHotbar(this.selectedIndex);
    this.resize();
    this.animate();
  }

  private selectSlot(index: number): void {
    const length = HOTBAR_BLOCKS.length;
    this.selectedIndex = ((index % length) + length) % length;
    this.hud.renderHotbar(this.selectedIndex);
    this.hud.showSelection(HOTBAR_BLOCKS[this.selectedIndex]);
  }

  private breakTargetBlock(): void {
    const target = this.worldRenderer.target(this.camera);
    if (!target) return;
    if (target.position.y <= -3) {
      this.hud.showToast('基岩层不可破坏');
      return;
    }
    this.world.set(target.position.x, target.position.y, target.position.z);
    this.worldRenderer.rebuild(this.world);
  }

  private placeTargetBlock(): void {
    const target = this.worldRenderer.target(this.camera);
    if (!target) return;

    const position: BlockPosition = {
      x: target.position.x + Math.round(target.normal.x),
      y: target.position.y + Math.round(target.normal.y),
      z: target.position.z + Math.round(target.normal.z)
    };

    if (this.world.has(position.x, position.y, position.z)) return;
    if (this.player.intersectsBlock(position)) {
      this.hud.showToast('不能在玩家身体内放置方块');
      return;
    }

    this.world.set(
      position.x,
      position.y,
      position.z,
      HOTBAR_BLOCKS[this.selectedIndex]
    );
    this.worldRenderer.rebuild(this.world);
  }

  private animate = (now = performance.now()): void => {
    requestAnimationFrame(this.animate);
    const dt = Math.min(this.clock.getDelta(), 0.033);

    if (this.input.active) this.player.update(dt, this.input, this.world);
    this.player.applyCamera(this.camera, this.input);
    this.updateFps(now);
    this.renderer.render(this.scene, this.camera);
  };

  private updateFps(now: number): void {
    this.frameCount += 1;
    if (now - this.fpsTimestamp < 500) return;

    this.fps = Math.round((this.frameCount * 1000) / (now - this.fpsTimestamp));
    this.frameCount = 0;
    this.fpsTimestamp = now;
    this.hud.updateStatus(
      this.player.position.x,
      this.player.position.y,
      this.player.position.z,
      this.fps,
      this.world.size
    );
  }

  private resize(): void {
    const width = window.innerWidth;
    const height = window.innerHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }
}
