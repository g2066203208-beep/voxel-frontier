import type * as THREE from 'three';

export type BlockId = 'grass' | 'dirt' | 'stone' | 'wood' | 'plank' | 'leaves';

export interface BlockDefinition {
  readonly label: string;
  readonly color: number;
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
