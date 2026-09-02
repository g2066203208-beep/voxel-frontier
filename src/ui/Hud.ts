import type { BlockId } from '../types';
import { BLOCKS, HOTBAR_BLOCKS } from '../world/BlockRegistry';

export class Hud {
  private readonly startPanel: HTMLElement;
  private readonly hotbar: HTMLElement;
  private readonly status: HTMLElement;
  private readonly toast: HTMLElement;
  private toastTimer: number | undefined;

  constructor() {
    this.startPanel = this.requireElement('#start-panel');
    this.hotbar = this.requireElement('#hotbar');
    this.status = this.requireElement('#status');
    this.toast = this.requireElement('#toast');
  }

  setActive(active: boolean): void {
    this.startPanel.classList.toggle('hidden', active);
  }

  renderHotbar(selectedIndex: number): void {
    this.hotbar.replaceChildren();
    HOTBAR_BLOCKS.forEach((type, index) => {
      const slot = document.createElement('div');
      slot.className = `slot${index === selectedIndex ? ' selected' : ''}`;

      const number = document.createElement('span');
      number.className = 'slot-number';
      number.textContent = String(index + 1);

      const swatch = document.createElement('span');
      swatch.className = 'swatch';
      swatch.style.backgroundColor = `#${BLOCKS[type].color.toString(16).padStart(6, '0')}`;

      const name = document.createElement('span');
      name.className = 'slot-name';
      name.textContent = BLOCKS[type].label;

      slot.append(number, swatch, name);
      this.hotbar.append(slot);
    });
  }

  showSelection(type: BlockId): void {
    this.showToast(`已选择：${BLOCKS[type].label}`);
  }

  showToast(text: string): void {
    this.toast.textContent = text;
    this.toast.classList.add('show');
    if (this.toastTimer !== undefined) window.clearTimeout(this.toastTimer);
    this.toastTimer = window.setTimeout(() => this.toast.classList.remove('show'), 1100);
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
