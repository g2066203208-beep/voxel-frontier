import * as THREE from 'three';

export interface InputCallbacks {
  onActiveChange(active: boolean): void;
  onPrimaryAction(): void;
  onSecondaryAction(): void;
  onSlotSelect(index: number): void;
  onSlotStep(step: number): void;
}

export class InputManager {
  private readonly keys = new Set<string>();
  private jumpRequested = false;
  private readonly canvas: HTMLCanvasElement;
  private readonly callbacks: InputCallbacks;

  yaw = 0;
  pitch = -0.12;

  constructor(canvas: HTMLCanvasElement, callbacks: InputCallbacks) {
    this.canvas = canvas;
    this.callbacks = callbacks;
    this.bindEvents();
  }

  get active(): boolean {
    return document.pointerLockElement === this.canvas;
  }

  requestPointerLock(): void {
    void this.canvas.requestPointerLock();
  }

  movementAxes(): { forward: number; right: number; sprint: boolean } {
    const forwardInput = (this.keys.has('KeyW') ? 1 : 0) - (this.keys.has('KeyS') ? 1 : 0);
    const rightInput = (this.keys.has('KeyD') ? 1 : 0) - (this.keys.has('KeyA') ? 1 : 0);
    const length = Math.hypot(forwardInput, rightInput) || 1;
    return {
      forward: forwardInput / length,
      right: rightInput / length,
      sprint: this.keys.has('ShiftLeft') || this.keys.has('ShiftRight')
    };
  }

  consumeJump(): boolean {
    const requested = this.jumpRequested;
    this.jumpRequested = false;
    return requested;
  }

  private bindEvents(): void {
    this.canvas.addEventListener('click', () => {
      if (!this.active) this.requestPointerLock();
    });

    document.addEventListener('pointerlockchange', () => {
      if (!this.active) this.keys.clear();
      this.callbacks.onActiveChange(this.active);
    });

    document.addEventListener('mousemove', (event) => {
      if (!this.active) return;
      this.yaw -= event.movementX * 0.0022;
      this.pitch -= event.movementY * 0.0022;
      this.pitch = THREE.MathUtils.clamp(
        this.pitch,
        -Math.PI / 2 + 0.02,
        Math.PI / 2 - 0.02
      );
    });

    document.addEventListener('keydown', (event) => {
      if (!this.active) return;
      this.keys.add(event.code);
      if (event.code === 'Space') this.jumpRequested = true;
      if (/^Digit[1-5]$/.test(event.code)) {
        this.callbacks.onSlotSelect(Number(event.code.slice(-1)) - 1);
      }
    });

    document.addEventListener('keyup', (event) => this.keys.delete(event.code));

    this.canvas.addEventListener('contextmenu', (event) => event.preventDefault());
    this.canvas.addEventListener('mousedown', (event) => {
      if (!this.active) return;
      if (event.button === 0) this.callbacks.onPrimaryAction();
      if (event.button === 2) this.callbacks.onSecondaryAction();
    });

    this.canvas.addEventListener(
      'wheel',
      (event) => {
        if (!this.active) return;
        this.callbacks.onSlotStep(event.deltaY > 0 ? 1 : -1);
      },
      { passive: true }
    );
  }
}
