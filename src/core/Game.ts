import * as THREE from 'three';
import { WorldRenderer } from '../render/WorldRenderer';
import { DayNightSystem } from '../systems/DayNightSystem';
import { Inventory } from '../systems/Inventory';
import { ItemDropSystem } from '../systems/ItemDropSystem';
import { SurvivalSystem } from '../systems/SurvivalSystem';
import type { BlockPosition } from '../types';
import { Hud } from '../ui/Hud';
import { BLOCKS, HOTBAR_ITEMS, ITEMS, isBlockItem } from '../world/BlockRegistry';
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
  private readonly inventory = new Inventory();
  private readonly survival = new SurvivalSystem();
  private readonly drops: ItemDropSystem;
  private readonly dayNight: DayNightSystem;
  private readonly clock = new THREE.Clock();

  private selectedIndex = 0;
  private breakingKey: string | null = null;
  private breakingProgress = 0;
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

    const hemisphere = new THREE.HemisphereLight(0xcbe9ff, 0x6c7257, 1.7);
    const sun = new THREE.DirectionalLight(0xfff0cf, 2.2);
    sun.position.set(24, 36, 12);
    this.scene.add(hemisphere, sun);

    this.worldRenderer = new WorldRenderer(this.scene);
    this.drops = new ItemDropSystem(this.scene);
    this.dayNight = new DayNightSystem(this.scene, hemisphere, sun);
    this.input = new InputManager(canvas, {
      onActiveChange: (active) => {
        this.hud.setActive(active);
        if (!active) this.resetBreaking();
      },
      onSecondaryAction: () => this.useSelectedItem(),
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
    this.hud.renderHotbar(this.selectedIndex, this.inventory);
    this.hud.updateVitals(this.survival.vitals);
    this.resize();
    this.animate();
  }

  private selectSlot(index: number): void {
    const length = HOTBAR_ITEMS.length;
    this.selectedIndex = ((index % length) + length) % length;
    this.hud.renderHotbar(this.selectedIndex, this.inventory);
    this.hud.showSelection(HOTBAR_ITEMS[this.selectedIndex]);
    this.resetBreaking();
  }

  private useSelectedItem(): void {
    const item = HOTBAR_ITEMS[this.selectedIndex];
    if (item === 'berry') {
      this.eatBerry();
      return;
    }
    if (isBlockItem(item)) this.placeTargetBlock(item);
  }

  private eatBerry(): void {
    if (this.inventory.count('berry') <= 0) {
      this.hud.showToast('没有野莓了');
      return;
    }
    if (!this.survival.eat(22)) {
      this.hud.showToast('现在还不饿');
      return;
    }
    this.inventory.remove('berry');
    this.hud.renderHotbar(this.selectedIndex, this.inventory);
    this.hud.updateVitals(this.survival.vitals);
    this.hud.showToast('吃下野莓：饥饿恢复');
  }

  private placeTargetBlock(type: keyof typeof BLOCKS): void {
    if (this.inventory.count(type) <= 0) {
      this.hud.showToast(`没有${BLOCKS[type].label}，先去采集`);
      return;
    }

    const target = this.worldRenderer.target(this.camera);
    if (!target) return;
    const position = this.placementPosition(target.position, target.normal);

    if (this.world.has(position.x, position.y, position.z)) return;
    if (this.player.intersectsBlock(position)) {
      this.hud.showToast('不能在玩家身体内放置方块');
      return;
    }

    if (!this.inventory.remove(type)) return;
    this.world.set(position.x, position.y, position.z, type);
    this.worldRenderer.rebuild(this.world);
    this.hud.renderHotbar(this.selectedIndex, this.inventory);
  }

  private updateBreaking(dt: number): void {
    if (!this.input.primaryHeld) {
      this.resetBreaking();
      return;
    }

    const target = this.worldRenderer.target(this.camera);
    if (!target) {
      this.resetBreaking();
      return;
    }

    const key = VoxelWorld.key(target.position.x, target.position.y, target.position.z);
    if (target.position.y <= -3) {
      if (this.breakingKey !== key) this.hud.showToast('基岩层不可破坏');
      this.breakingKey = key;
      this.breakingProgress = 0;
      this.hud.updateBreakProgress(0);
      return;
    }

    const type = this.world.get(target.position.x, target.position.y, target.position.z);
    if (!type) {
      this.resetBreaking();
      return;
    }

    if (this.breakingKey !== key) {
      this.breakingKey = key;
      this.breakingProgress = 0;
    }

    const definition = BLOCKS[type];
    this.breakingProgress += dt / definition.hardness;
    this.hud.updateBreakProgress(
      this.breakingProgress,
      `破坏 ${definition.label} · ${Math.min(100, Math.floor(this.breakingProgress * 100))}%`
    );

    if (this.breakingProgress < 1) return;

    this.world.set(target.position.x, target.position.y, target.position.z);
    this.worldRenderer.rebuild(this.world);
    this.drops.spawn(definition.drop, target.position);
    if (type === 'leaves' && Math.random() < 0.32) {
      this.drops.spawn('berry', target.position);
    }
    this.resetBreaking();
  }

  private updatePlacementPreview(): void {
    const item = HOTBAR_ITEMS[this.selectedIndex];
    if (!isBlockItem(item)) {
      this.worldRenderer.hidePlacementPreview();
      return;
    }

    const target = this.worldRenderer.target(this.camera);
    if (!target) {
      this.worldRenderer.hidePlacementPreview();
      return;
    }

    const position = this.placementPosition(target.position, target.normal);
    const valid =
      this.inventory.count(item) > 0 &&
      !this.world.has(position.x, position.y, position.z) &&
      !this.player.intersectsBlock(position);
    this.worldRenderer.setPlacementPreview(position, valid);
  }

  private placementPosition(position: BlockPosition, normal: THREE.Vector3): BlockPosition {
    return {
      x: position.x + Math.round(normal.x),
      y: position.y + Math.round(normal.y),
      z: position.z + Math.round(normal.z)
    };
  }

  private resetBreaking(): void {
    this.breakingKey = null;
    this.breakingProgress = 0;
    this.hud.updateBreakProgress(0);
  }

  private applyFallDamage(fallDistance: number): void {
    const safeDistance = 3.25;
    if (fallDistance <= safeDistance) return;
    const damage = Math.min(100, (fallDistance - safeDistance) * 8.5);
    this.survival.damage(damage);
    this.hud.flashDamage();
    this.hud.showToast(`坠落伤害 -${Math.ceil(damage)}`);
  }

  private handleDeath(reason: string): void {
    this.hud.showToast(`${reason}，已在起点重生`);
    this.hud.flashDamage();
    this.survival.reset();
    this.player.respawn(this.world);
    this.resetBreaking();
  }

  private animate = (now = performance.now()): void => {
    requestAnimationFrame(this.animate);
    const dt = Math.min(this.clock.getDelta(), 0.033);

    if (this.input.active) {
      const motion = this.player.update(dt, this.input, this.world, this.survival.canSprint);
      this.player.applyCamera(this.camera, this.input);

      if (motion.fallDistance > 0) this.applyFallDamage(motion.fallDistance);
      if (motion.voided) this.survival.damage(1000);

      this.survival.update(dt, motion);
      if (this.survival.dead) {
        this.handleDeath(motion.voided ? '坠入深渊' : '你倒下了');
      } else {
        this.updateBreaking(dt);
      }
    } else {
      this.player.applyCamera(this.camera, this.input);
    }

    const collected = this.drops.update(dt, this.player.position, this.inventory);
    if (collected.length > 0) {
      this.hud.renderHotbar(this.selectedIndex, this.inventory);
      const first = collected[0];
      const extra = collected.length > 1 ? ` 等 ${collected.length} 件` : '';
      this.hud.showToast(`拾取 ${ITEMS[first].label}${extra}`);
    }

    this.updatePlacementPreview();
    const worldTime = this.dayNight.update(dt);
    this.hud.updateWorldTime(worldTime.day, worldTime.hour, worldTime.minute);
    this.hud.updateVitals(this.survival.vitals);
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
