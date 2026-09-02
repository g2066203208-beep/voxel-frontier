import type * as THREE from 'three';

export type BlockId = 'grass' | 'dirt' | 'stone' | 'wood' | 'plank' | 'leaves';
export type ItemId = BlockId | 'berry';

export interface BlockDefinition {
  readonly label: string;
  readonly color: number;
  readonly hardness: number;
  readonly drop: ItemId;
}

export interface ItemDefinition {
  readonly label: string;
  readonly color: number;
  readonly placeable: boolean;
}

export interface BlockPosition {
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

export interface TargetBlock {
  readonly position: BlockPosition;
  readonly normal: THREE.Vector3;
}

export interface PlayerVitals {
  readonly health: number;
  readonly hunger: number;
  readonly stamina: number;
}

export interface PlayerMotionState {
  readonly moving: boolean;
  readonly sprinting: boolean;
  readonly fallDistance: number;
  readonly voided: boolean;
}
