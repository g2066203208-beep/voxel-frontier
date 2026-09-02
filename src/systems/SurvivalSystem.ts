import type { PlayerVitals } from '../types';

export interface SurvivalUpdateContext {
  readonly moving: boolean;
  readonly sprinting: boolean;
}

export class SurvivalSystem {
  private health = 100;
  private hunger = 100;
  private stamina = 100;

  get vitals(): PlayerVitals {
    return {
      health: this.health,
      hunger: this.hunger,
      stamina: this.stamina
    };
  }

  get canSprint(): boolean {
    return this.stamina > 4 && this.hunger > 2 && this.health > 0;
  }

  get dead(): boolean {
    return this.health <= 0;
  }

  update(dt: number, context: SurvivalUpdateContext): void {
    const activityDrain = context.sprinting ? 0.52 : context.moving ? 0.2 : 0.1;
    this.hunger = Math.max(0, this.hunger - activityDrain * dt);

    if (context.sprinting) {
      this.stamina = Math.max(0, this.stamina - 18 * dt);
    } else {
      const recovery = this.hunger > 10 ? 14 : 7;
      this.stamina = Math.min(100, this.stamina + recovery * dt);
    }

    if (this.hunger <= 0) {
      this.health = Math.max(0, this.health - 3.5 * dt);
    } else if (this.hunger >= 72 && this.health < 100) {
      const heal = Math.min(1.15 * dt, 100 - this.health);
      this.health += heal;
      this.hunger = Math.max(0, this.hunger - heal * 0.35);
    }
  }

  damage(amount: number): void {
    if (amount <= 0 || this.dead) return;
    this.health = Math.max(0, this.health - amount);
  }

  eat(nutrition: number): boolean {
    if (nutrition <= 0 || this.hunger >= 99.5 || this.dead) return false;
    this.hunger = Math.min(100, this.hunger + nutrition);
    this.stamina = Math.min(100, this.stamina + nutrition * 0.3);
    return true;
  }

  reset(): void {
    this.health = 100;
    this.hunger = 100;
    this.stamina = 100;
  }
}
