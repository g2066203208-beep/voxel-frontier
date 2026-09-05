// Voxel Frontier canonical ultra-low-poly stone material reference.
// Zero image textures. Intended as an art-direction reference, not yet wired into the runtime.

struct VfStoneMaterialSample {
    float3 albedo;
    float roughness;
    float specularStrength;
};

float vfSmooth01(float a, float b, float x) {
    float t = saturate((x - a) / max(1.0e-5, b - a));
    return t * t * (3.0 - 2.0 * t);
}

VfStoneMaterialSample vfCanonicalStoneMaterial(float3 localPosition, float3 faceNormal) {
    const float3 n = normalize(faceNormal);

    // Broad mineral variation: large wavelength and restrained amplitude.
    const float macro = 0.5 + 0.5 * sin(
        localPosition.x * 2.3 + localPosition.y * 1.6 + localPosition.z * 2.7);
    const float macro2 = 0.5 + 0.5 * sin(
        localPosition.x * 4.2 - localPosition.y * 3.1 + localPosition.z * 1.4 + 1.4);

    // Oblique strata / veins. Do not use perfect horizontal cake layers.
    const float strata = 0.5 + 0.5 * sin(
        (localPosition.z + 0.28 * localPosition.x - 0.10 * localPosition.y) * 7.5
        + macro * 1.2);
    const float vein = 1.0 - vfSmooth01(0.07, 0.22, abs(strata - 0.5));

    const float3 slate = float3(0.41, 0.385, 0.34);
    const float3 warmStone = float3(0.56, 0.47, 0.35);
    const float3 darkMineral = float3(0.29, 0.30, 0.28);
    float3 albedo = lerp(slate, warmStone, macro * 0.30);
    albedo = lerp(albedo, darkMineral, vein * 0.13);

    // Upward faces weather/bleach slightly more than protected faces.
    const float up = saturate(n.z);
    const float weather = vfSmooth01(0.32, 0.82, up)
        * vfSmooth01(0.48, 0.84, macro2);
    albedo = lerp(albedo, float3(0.61, 0.55, 0.43), weather * 0.13);

    // Restrained lichen only on eligible upward-facing regions.
    const float lichen = vfSmooth01(0.82, 0.94, macro2)
        * vfSmooth01(0.58, 0.90, up);
    albedo = lerp(albedo, float3(0.39, 0.41, 0.25), lichen * 0.10);

    // Fine grain is material detail only; it must never deform the silhouette.
    const float grain = 0.5 + 0.5 * sin(
        localPosition.x * 17.2 + localPosition.y * 13.7 - localPosition.z * 19.3);
    albedo *= 0.95 + 0.08 * grain;

    VfStoneMaterialSample result;
    result.albedo = saturate(albedo);
    result.roughness = 0.88;
    result.specularStrength = 0.08;
    return result;
}
