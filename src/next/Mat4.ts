export type Vec3 = readonly [number, number, number];

export function perspectiveWebGpu(fovY: number, aspect: number, near: number, far: number): Float32Array {
  const f = 1 / Math.tan(fovY / 2);
  const out = new Float32Array(16);
  out[0] = f / aspect;
  out[5] = f;
  out[10] = far / (near - far);
  out[11] = -1;
  out[14] = (near * far) / (near - far);
  return out;
}

export function viewFromYawPitch(position: Vec3, yaw: number, pitch: number): Float32Array {
  const cosPitch = Math.cos(pitch);
  const forwardX = Math.sin(yaw) * cosPitch;
  const forwardY = Math.sin(pitch);
  const forwardZ = -Math.cos(yaw) * cosPitch;

  let rightX = -forwardZ;
  let rightY = 0;
  let rightZ = forwardX;
  const rightLength = Math.hypot(rightX, rightZ) || 1;
  rightX /= rightLength;
  rightZ /= rightLength;

  const upX = rightY * forwardZ - rightZ * forwardY;
  const upY = rightZ * forwardX - rightX * forwardZ;
  const upZ = rightX * forwardY - rightY * forwardX;

  const backX = -forwardX;
  const backY = -forwardY;
  const backZ = -forwardZ;

  const out = new Float32Array(16);
  out[0] = rightX;
  out[1] = upX;
  out[2] = backX;
  out[3] = 0;
  out[4] = rightY;
  out[5] = upY;
  out[6] = backY;
  out[7] = 0;
  out[8] = rightZ;
  out[9] = upZ;
  out[10] = backZ;
  out[11] = 0;
  out[12] = -(rightX * position[0] + rightY * position[1] + rightZ * position[2]);
  out[13] = -(upX * position[0] + upY * position[1] + upZ * position[2]);
  out[14] = -(backX * position[0] + backY * position[1] + backZ * position[2]);
  out[15] = 1;
  return out;
}

export function multiplyMat4(a: Float32Array, b: Float32Array): Float32Array {
  const out = new Float32Array(16);
  for (let column = 0; column < 4; column += 1) {
    const bi0 = b[column * 4];
    const bi1 = b[column * 4 + 1];
    const bi2 = b[column * 4 + 2];
    const bi3 = b[column * 4 + 3];
    out[column * 4] = a[0] * bi0 + a[4] * bi1 + a[8] * bi2 + a[12] * bi3;
    out[column * 4 + 1] = a[1] * bi0 + a[5] * bi1 + a[9] * bi2 + a[13] * bi3;
    out[column * 4 + 2] = a[2] * bi0 + a[6] * bi1 + a[10] * bi2 + a[14] * bi3;
    out[column * 4 + 3] = a[3] * bi0 + a[7] * bi1 + a[11] * bi2 + a[15] * bi3;
  }
  return out;
}
