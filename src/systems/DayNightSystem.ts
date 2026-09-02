import * as THREE from 'three';

export interface WorldTime {
  readonly day: number;
  readonly hour: number;
  readonly minute: number;
}

export class DayNightSystem {
  private readonly scene: THREE.Scene;
  private readonly hemisphere: THREE.HemisphereLight;
  private readonly sun: THREE.DirectionalLight;
  private readonly dayColor = new THREE.Color(0x87bfe2);
  private readonly nightColor = new THREE.Color(0x07111e);
  private readonly skyColor = new THREE.Color();
  private elapsed = 0;

  private static readonly DAY_SECONDS = 300;
  private static readonly START_HOUR = 8;

  constructor(
    scene: THREE.Scene,
    hemisphere: THREE.HemisphereLight,
    sun: THREE.DirectionalLight
  ) {
    this.scene = scene;
    this.hemisphere = hemisphere;
    this.sun = sun;
  }

  update(dt: number): WorldTime {
    this.elapsed += dt;
    const totalHours = DayNightSystem.START_HOUR + (this.elapsed / DayNightSystem.DAY_SECONDS) * 24;
    const day = Math.floor(totalHours / 24) + 1;
    const hourFloat = totalHours % 24;
    const hour = Math.floor(hourFloat);
    const minute = Math.floor((hourFloat - hour) * 60);

    const solarAngle = ((hourFloat - 6) / 24) * Math.PI * 2;
    const sunHeight = Math.sin(solarAngle);
    const daylight = THREE.MathUtils.clamp((sunHeight + 0.16) / 1.05, 0.04, 1);

    this.skyColor.copy(this.nightColor).lerp(this.dayColor, daylight);
    this.scene.background = this.skyColor;
    if (this.scene.fog instanceof THREE.Fog) this.scene.fog.color.copy(this.skyColor);

    this.hemisphere.intensity = 0.18 + daylight * 1.52;
    this.sun.intensity = 0.08 + daylight * 2.15;
    this.sun.position.set(Math.cos(solarAngle) * 34, sunHeight * 46, 14);

    return { day, hour, minute };
  }
}
