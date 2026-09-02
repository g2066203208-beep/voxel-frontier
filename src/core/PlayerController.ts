import * as THREE from 'three';
import type { BlockPosition, PlayerMotionState } from '../types';
import { VoxelWorld } from '../world/VoxelWorld';
import type { InputManager } from './InputManager';

export class PlayerController {
  readonly position = new THREE.Vector3(0.5, 12, 0.5);
  readonly radius = 0.31;
  readonly height = 1.8;
  readonly eyeHeight = 1.62;

  private verticalVelocity = 0;
  private grounded = false;
  private fallStartY: number | null = null;

  respawn(world: VoxelWorld): void {
    this.position.set(0.5, world.topSolidY(0, 0) + 1.02, 0.5);
    this.verticalVelocity = 0;
    this.grounded = false;
    this.fallStartY = null;
  }

  update(
    dt: number,
    input: InputManager,
    world: VoxelWorld,
    canSprint: boolean
  ): PlayerMotionState {
    const movement = input.movementAxes();
    const moving = Math.abs(movement.forward) > 0.001 || Math.abs(movement.right) > 0.001;
    const sprinting = moving && movement.sprint && canSprint;
    const forwardX = -Math.sin(input.yaw);
    const forwardZ = -Math.cos(input.yaw);
    const rightX = Math.cos(input.yaw);
    const rightZ = -Math.sin(input.yaw);
    const speed = sprinting ? 7.2 : 4.8;

    const dx = (forwardX * movement.forward + rightX * movement.right) * speed * dt;
    const dz = (forwardZ * movement.forward + rightZ * movement.right) * speed * dt;

    if (!this.collidesAt(this.position.x + dx, this.position.y, this.position.z, world)) {
      this.position.x += dx;
    }
    if (!this.collidesAt(this.position.x, this.position.y, this.position.z + dz, world)) {
      this.position.z += dz;
    }

    this.grounded = this.collidesAt(
      this.position.x,
      this.position.y - 0.055,
      this.position.z,
      world
    );

    if (input.consumeJump() && this.grounded) {
      this.verticalVelocity = 8.4;
      this.grounded = false;
      this.fallStartY = this.position.y;
    }

    if (!this.grounded) {
      this.fallStartY = Math.max(this.fallStartY ?? this.position.y, this.position.y);
    }

    let fallDistance = 0;
    this.verticalVelocity -= 24 * dt;
    const nextY = this.position.y + this.verticalVelocity * dt;
    if (!this.collidesAt(this.position.x, nextY, this.position.z, world)) {
      this.position.y = nextY;
    } else {
      if (nextY < this.position.y) {
        this.grounded = true;
        if (this.fallStartY !== null) {
          fallDistance = Math.max(0, this.fallStartY - this.position.y);
          this.fallStartY = null;
        }
      }
      this.verticalVelocity = 0;
    }

    const voided = this.position.y < -20;
    return { moving, sprinting, fallDistance, voided };
  }

  applyCamera(camera: THREE.PerspectiveCamera, input: InputManager): void {
    camera.position.set(this.position.x, this.position.y + this.eyeHeight, this.position.z);
    camera.rotation.y = input.yaw;
    camera.rotation.x = input.pitch;
  }

  intersectsBlock(block: BlockPosition): boolean {
    const minX = this.position.x - this.radius;
    const maxX = this.position.x + this.radius;
    const minY = this.position.y;
    const maxY = this.position.y + this.height;
    const minZ = this.position.z - this.radius;
    const maxZ = this.position.z + this.radius;

    return (
      maxX > block.x &&
      minX < block.x + 1 &&
      maxY > block.y &&
      minY < block.y + 1 &&
      maxZ > block.z &&
      minZ < block.z + 1
    );
  }

  private collidesAt(px: number, py: number, pz: number, world: VoxelWorld): boolean {
    const epsilon = 0.001;
    const minX = Math.floor(px - this.radius);
    const maxX = Math.floor(px + this.radius - epsilon);
    const minY = Math.floor(py);
    const maxY = Math.floor(py + this.height - epsilon);
    const minZ = Math.floor(pz - this.radius);
    const maxZ = Math.floor(pz + this.radius - epsilon);

    for (let x = minX; x <= maxX; x += 1) {
      for (let y = minY; y <= maxY; y += 1) {
        for (let z = minZ; z <= maxZ; z += 1) {
          if (world.has(x, y, z)) return true;
        }
      }
    }
    return false;
  }
}
