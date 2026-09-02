import type { BlockDefinition, BlockId, ItemDefinition, ItemId } from '../types';

export const BLOCKS: Record<BlockId, BlockDefinition> = {
  grass: { label: '草地', color: 0x67a84f, hardness: 0.55, drop: 'grass' },
  dirt: { label: '泥土', color: 0x896044, hardness: 0.7, drop: 'dirt' },
  stone: { label: '岩石', color: 0x7d8388, hardness: 2.25, drop: 'stone' },
  wood: { label: '原木', color: 0x8d643f, hardness: 1.35, drop: 'wood' },
  plank: { label: '木板', color: 0xb98c58, hardness: 0.95, drop: 'plank' },
  leaves: { label: '树叶', color: 0x4e8a49, hardness: 0.3, drop: 'leaves' }
};

export const ITEMS: Record<ItemId, ItemDefinition> = {
  grass: { label: BLOCKS.grass.label, color: BLOCKS.grass.color, placeable: true },
  dirt: { label: BLOCKS.dirt.label, color: BLOCKS.dirt.color, placeable: true },
  stone: { label: BLOCKS.stone.label, color: BLOCKS.stone.color, placeable: true },
  wood: { label: BLOCKS.wood.label, color: BLOCKS.wood.color, placeable: true },
  plank: { label: BLOCKS.plank.label, color: BLOCKS.plank.color, placeable: true },
  leaves: { label: BLOCKS.leaves.label, color: BLOCKS.leaves.color, placeable: true },
  berry: { label: '野莓', color: 0xc93f5d, placeable: false }
};

export const HOTBAR_ITEMS: readonly ItemId[] = [
  'grass',
  'dirt',
  'stone',
  'wood',
  'plank',
  'leaves',
  'berry'
];

export function isBlockItem(item: ItemId): item is BlockId {
  return item !== 'berry';
}
