import './styles.css';
import { Game } from './core/Game';

function requireElement<T extends HTMLElement>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Missing required element: ${selector}`);
  return element;
}

const canvas = requireElement<HTMLCanvasElement>('#game');
const playButton = requireElement<HTMLButtonElement>('#play-button');

const game = new Game(canvas, playButton);
game.start();
