import './styles.css';
import { Game } from './core/Game';
import { NextEnginePreview } from './next/NextEnginePreview';

function requireElement<T extends HTMLElement>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Missing required element: ${selector}`);
  return element;
}

const canvas = requireElement<HTMLCanvasElement>('#game');
const playButton = requireElement<HTMLButtonElement>('#play-button');
const status = requireElement<HTMLElement>('#status');

async function boot(): Promise<void> {
  const nextRequested = new URLSearchParams(window.location.search).get('engine') === 'next';
  if (nextRequested) {
    try {
      const next = await NextEnginePreview.create(canvas, playButton);
      if (next) {
        next.start();
        return;
      }
      status.textContent = '当前浏览器/设备不支持 WebGPU，已回退兼容引擎';
    } catch (error) {
      console.error('Next engine failed to start; using compatibility engine.', error);
      status.textContent = '新引擎尚未就绪，已回退兼容引擎';
    }
  }

  const game = new Game(canvas, playButton);
  game.start();
}

void boot();
