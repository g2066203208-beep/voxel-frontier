import type { ItemId } from '../types';

export class Inventory {
  private readonly counts = new Map<ItemId, number>();

  constructor() {
    this.add('plank', 6);
    this.add('berry', 3);
  }

  count(item: ItemId): number {
    return this.counts.get(item) ?? 0;
  }

  add(item: ItemId, amount = 1): void {
    if (amount <= 0) return;
    this.counts.set(item, this.count(item) + amount);
  }

  remove(item: ItemId, amount = 1): boolean {
    if (amount <= 0) return true;
    const current = this.count(item);
    if (current < amount) return false;
    const next = current - amount;
    if (next === 0) this.counts.delete(item);
    else this.counts.set(item, next);
    return true;
  }

  reset(): void {
    this.counts.clear();
    this.add('plank', 6);
    this.add('berry', 3);
  }
}
