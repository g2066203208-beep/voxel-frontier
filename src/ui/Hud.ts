import type { ItemId, PlayerVitals } from '../types';
import { Inventory } from '../systems/Inventory';
import { HOTBAR_ITEMS, ITEMS } from '../world/BlockRegistry';

export class Hud {
  private readonly startPanel: HTMLElement;
  private readonly hotbar: HTMLElement;
  private readonly status: HTMLElement;
  private readonly toast: HTMLElement;
  private readonly healthFill: HTMLElement;
  private readonly hungerFill: HTMLElement;
  private readonly staminaFill: HTMLElement;
  private readonly healthValue: HTMLElement;
  private readonly hungerValue: HTMLElement;
  private readonly staminaValue: HTMLElement;
  private readonly breakProgress: HTMLElement;
  private readonly breakFill: HTMLElement;
  private readonly breakLabel: HTMLElement;
  private readonly dayClock: HTMLElement;
  private readonly damageFlash: HTMLElement;
  private toastTimer: number | undefined;
  private damageTimer: number | undefined;

  constructor() {
    this.startPanel = this.requireElement('#start-panel');
    this.hotbar = this.requireElement('#hotbar');
    this.status = this.requireElement('#status');
    this.toast = this.requireElement('#toast');
    this.healthFill = this.requireElement('#health-fill');
    this.hungerFill = this.requireElement('#hunger-fill');
    this.staminaFill = this.requireElement('#stamina-fill');
    this.healthValue = this.requireElement('#health-value');
    this.hungerValue = this.requireElement('#hunger-value');
    this.staminaValue = this.requireElement('#stamina-value');
    this.breakProgress = this.requireElement('#break-progress');
    this.breakFill = this.requireElement('#break-fill');
    this.breakLabel = this.requireElement('#break-label');
    this.dayClock = this.requireElement('#day-clock');
    this.damageFlash = this.requireElement('#damage-flash');
  }

  setActive(active: boolean): void {
    this.startPanel.classList.toggle('hidden', active);
  }

  renderHotbar(selectedIndex: number, inventory: Inventory): void {
    this.hotbar.replaceChildren();
    HOTBAR_ITEMS.forEach((item, index) => {
      const slot = document.createElement('div');
      slot.className = `slot${index === selectedIndex ? ' selected' : ''}`;

      const number = document.createElement('span');
      number.className = 'slot-number';
      number.textContent = String(index + 1);

      const swatch = document.createElement('span');
      swatch.className = `swatch${item === 'berry' ? ' round' : ''}`;
      swatch.style.backgroundColor = `#${ITEMS[item].color.toString(16).padStart(6, '0')}`;

      const count = document.createElement('span');
      count.className = 'slot-count';
      count.textContent = String(inventory.count(item));

      const name = document.createElement('span');
      name.className = 'slot-name';
      name.textContent = ITEMS[item].label;

      slot.append(number, swatch, count, name);
      this.hotbar.append(slot);
    });
  }

  showSelection(item: ItemId): void {
    this.showToast(`已选择：${ITEMS[item].label}`);
  }

  showToast(text: string): void {
    this.toast.textContent = text;
    this.toast.classList.add('show');
    if (this.toastTimer !== undefined) window.clearTimeout(this.toastTimer);
    this.toastTimer = window.setTimeout(() => this.toast.classList.remove('show'), 1300);
  }

  flashDamage(): void {
    this.damageFlash.classList.add('show');
    if (this.damageTimer !== undefined) window.clearTimeout(this.damageTimer);
    this.damageTimer = window.setTimeout(() => this.damageFlash.classList.remove('show'), 180);
  }

  updateVitals(vitals: PlayerVitals): void {
    this.healthFill.style.width = `${vitals.health}%`;
    this.hungerFill.style.width = `${vitals.hunger}%`;
    this.staminaFill.style.width = `${vitals.stamina}%`;
    this.healthValue.textContent = String(Math.ceil(vitals.health));
    this.hungerValue.textContent = String(Math.ceil(vitals.hunger));
    this.staminaValue.textContent = String(Math.ceil(vitals.stamina));
  }

  updateBreakProgress(progress: number, label = ''): void {
    const clamped = Math.max(0, Math.min(1, progress));
    this.breakProgress.classList.toggle('visible', clamped > 0);
    this.breakFill.style.width = `${clamped * 100}%`;
    this.breakLabel.textContent = label;
  }

  updateWorldTime(day: number, hour: number, minute: number): void {
    this.dayClock.textContent = `第 ${day} 天 · ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
  }

  updateStatus(x: number, y: number, z: number, fps: number, blockCount: number): void {
    this.status.textContent = `X ${x.toFixed(1)} · Y ${y.toFixed(1)} · Z ${z.toFixed(1)} · ${fps} FPS · ${blockCount.toLocaleString()} blocks`;
  }

  private requireElement<T extends HTMLElement = HTMLElement>(selector: string): T {
    const element = document.querySelector<T>(selector);
    if (!element) throw new Error(`Missing required UI element: ${selector}`);
    return element;
  }
}
