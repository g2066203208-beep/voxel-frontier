import type { BlockDefinition, BlockId } from '../types';

export const BLOCKS: Record<BlockId, BlockDefinition> = {
  grass: { label: '草地', color: 0x67a84f },
  dirt: { label: '泥土', color: 0x896044 },
  stone: { label: '岩石', color: 0x7d8388 },
  wood: { label: '木材', color: 0x8d643f },
  plank: { label: '木板', color: 0xb98c58 },
  leaves: { label: '树叶', color: 0x4e8a49 }
};

export const HOTBAR_BLOCKS: readonly BlockId[] = ['grass', 'dirt', 'stone', 'wood', 'plank'];
