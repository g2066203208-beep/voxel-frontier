#!/usr/bin/env python3
"""Materialize R24's dedicated 120 Hz water path.

Water covers huge screen area but was routed through generic GGX, fragment wave synthesis and
fragment atmospheric exponentials. Move its static wave normal and aerial terms to vertices and
use a compact dielectric-water BRDF in the transparent fragment path. Glass keeps generic PBR.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHADER = ROOT / "native/shaders/planet.slang"

text = SHADER.read_text(encoding="utf-8")
if "R24_FAST_WATER_120_V1" not in text:
    # 1) Water normals: old waves are position-only (no time), so computing them per fragment was
    # pure redundant work. Interpolate the perturbed normal from vertices instead.
    old_vertex_head = r'''    float3 worldPosition = rotateByQuaternion(input.position, gPush.data3);
    float3 worldNormal = normalize(rotateByQuaternion(input.normal, gPush.data3));
    float3 relativePosition = worldPosition - gPush.data0.xyz;
    output.position = mul(gPush.matrix, float4(relativePosition, 1.0));
    output.relativePosition = relativePosition;
    output.normal = worldNormal;
'''
    new_vertex_head = r'''    float3 worldPosition = rotateByQuaternion(input.position, gPush.data3);
    float3 worldNormal = normalize(rotateByQuaternion(input.normal, gPush.data3));
    const bool waterMaterialVertex = input.material.x < -0.5;
    if (waterMaterialVertex)
    {
        // R24_FAST_WATER_120_V1: the legacy wave function has no time input. Evaluate it once per
        // vertex instead of once per covered pixel; interpolation preserves the broad low-poly wave.
        float2 p = input.position.xz * 0.00175;
        float2 waveSlope = float2(
            sin(p.x + p.y * 0.57) + 0.48 * sin(p.x * 2.31 - p.y * 1.73),
            cos(p.y * 1.07 - p.x * 0.61) + 0.44 * cos(p.y * 2.19 + p.x * 1.51));
        worldNormal = normalize(worldNormal + float3(waveSlope.x, 0.0, waveSlope.y) * 0.055);
    }
    float3 relativePosition = worldPosition - gPush.data0.xyz;
    output.position = mul(gPush.matrix, float4(relativePosition, 1.0));
    output.relativePosition = relativePosition;
    output.normal = worldNormal;
'''
    if text.count(old_vertex_head) != 1:
        raise SystemExit(f"fast water vertex head anchor count={text.count(old_vertex_head)}")
    text = text.replace(old_vertex_head, new_vertex_head, 1)

    # 2) Compute low-frequency aerial perspective per vertex for terrain AND water. This removes
    # length/normalize/pow/three exp from every water fragment.
    old_aerial = r'''    const bool terrainMaterial = input.material.w < -0.5 && input.material.w > -1.5;
    output.terrainMacro = terrainMaterial ? valueNoise2(input.position.xz * 0.0032) : 0.5;
    output.terrainAerialTransmittance = float3(1.0, 1.0, 1.0);
    output.terrainAerialInscatter = float3(0.0, 0.0, 0.0);
    if (terrainMaterial)
    {
        // Same optical model as the former fragment path, evaluated once per terrain vertex.
        // Planet LOD cells are much smaller than the 350 m haze onset and atmospheric scale,
        // so perspective-correct interpolation preserves the continuous appearance while removing
        // length/normalize/pow/exp work from every covered terrain pixel.
        float distanceMeters = length(relativePosition);
        if (distanceMeters > 350.0)
        {
            float3 viewDir = relativePosition / max(distanceMeters, 1.0e-4);
            float3 sunDir = normalize(gPush.data1.xyz);
            float cameraAltitude = max(gPush.data0.w, 0.0);
            float densityRatio = exp(-cameraAltitude / 8500.0);
            float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 220000.0);
            float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.15);
            float opticalLength = effectiveDistance * densityRatio
                * (0.55 + 0.45 * horizon) * 0.58;
            const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);
            const float betaM = 4.0e-6;
            float3 transmittance = exp(-(betaR + betaM) * opticalLength);
            float3 haze = stylizedSkyPalette(viewDir, sunDir);
            output.terrainAerialTransmittance = transmittance;
            output.terrainAerialInscatter = haze * (1.0 - transmittance);
        }
    }
'''
    new_aerial = r'''    const bool terrainMaterial = input.material.w < -0.5 && input.material.w > -1.5;
    const bool waterMaterialAerial = input.material.x < -0.5;
    output.terrainMacro = terrainMaterial ? valueNoise2(input.position.xz * 0.0032) : 0.5;
    output.terrainAerialTransmittance = float3(1.0, 1.0, 1.0);
    output.terrainAerialInscatter = float3(0.0, 0.0, 0.0);
    if (terrainMaterial || waterMaterialAerial)
    {
        // Shared vertex aerial term. Water uses its former 0.30 strength, terrain 0.58.
        float distanceMeters = length(relativePosition);
        if (distanceMeters > 350.0)
        {
            float3 viewDir = relativePosition / max(distanceMeters, 1.0e-4);
            float3 sunDir = normalize(gPush.data1.xyz);
            float cameraAltitude = max(gPush.data0.w, 0.0);
            float densityRatio = exp(-cameraAltitude / 8500.0);
            float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 220000.0);
            float horizonBase = saturate(1.0 - abs(viewDir.y));
            // x^1.15 is visually close to the old pow but this work is vertex-rate anyway.
            float horizon = pow(horizonBase, 1.15);
            float aerialStrength = waterMaterialAerial ? 0.30 : 0.58;
            float opticalLength = effectiveDistance * densityRatio
                * (0.55 + 0.45 * horizon) * aerialStrength;
            const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);
            const float betaM = 4.0e-6;
            float3 transmittance = exp(-(betaR + betaM) * opticalLength);
            float3 haze = stylizedSkyPalette(viewDir, sunDir);
            output.terrainAerialTransmittance = transmittance;
            output.terrainAerialInscatter = haze * (1.0 - transmittance);
        }
    }
'''
    if text.count(old_aerial) != 1:
        raise SystemExit(f"fast water aerial anchor count={text.count(old_aerial)}")
    text = text.replace(old_aerial, new_aerial, 1)

    # 3) Remove fragment wave perturbation from the generic path; only glass/other materials should
    # reach generic transparent PBR after the specialized water early return below.
    old_wave = r'''    if (waterMaterial)
    {
        float2 p = input.objectPosition.xz * 0.00175;
        float2 waveSlope = float2(
            sin(p.x * 1.00 + p.y * 0.57) + 0.48 * sin(p.x * 2.31 - p.y * 1.73),
            cos(p.y * 1.07 - p.x * 0.61) + 0.44 * cos(p.y * 2.19 + p.x * 1.51));
        n = normalize(n + float3(waveSlope.x, 0.0, waveSlope.y) * 0.055);
    }

'''
    if text.count(old_wave) != 1:
        raise SystemExit(f"fast water legacy fragment wave anchor count={text.count(old_wave)}")
    text = text.replace(old_wave, "", 1)

    start = text.find('[shader("fragment")]\nfloat4 transparentFragmentMain(VertexOutput input) : SV_Target\n{')
    end = text.find('\n[shader("vertex")]\nFullscreenOutput fullscreenVertexMain', start)
    if start < 0 or end < 0:
        raise SystemExit("fast water transparent shader anchors not found")
    fast_transparent = r'''[shader("fragment")]
float4 transparentFragmentMain(VertexOutput input) : SV_Target
{
    float transmission = saturate(input.material.z);
    if (transmission <= 0.02) discard;

    bool waterMaterial = input.material.x < -0.5;
    float exposure = max(gScene.skyAmbientExposure.a, 0.01);
    if (waterMaterial)
    {
        // R24_FAST_WATER_120_V1: dedicated high-coverage dielectric path. No generic GGX D/G,
        // fragment wave synthesis or fragment aerial exponentials.
        float3 n = normalize(input.normal);
        float3 v = normalize(-input.relativePosition);
        float3 l = normalize(gPush.data1.xyz);
        float noVRaw = dot(n, v);
        if (noVRaw <= 0.015) discard;
        float noV = saturate(abs(noVRaw));
        float oneMinus = 1.0 - noV;
        float oneMinus2 = oneMinus * oneMinus;
        float oneMinus5 = oneMinus2 * oneMinus2 * oneMinus;
        const float waterF0 = 0.02037;
        float fresnel = waterF0 + (1.0 - waterF0) * oneMinus5;
        float opticalOpacity = saturate(0.66 + fresnel * 0.32);
        float cameraAltitude = max(gPush.data0.w, 0.0);
        if (input.material.w < -19.0)
            opticalOpacity *= smoothstep(18000.0, 34000.0, cameraAltitude);
        else if (input.material.w < -9.0)
            opticalOpacity *= 1.0 - smoothstep(14000.0, 30000.0, cameraAltitude);
        if (opticalOpacity < 0.004) discard;

        float3 reflected = stylizedSkyPalette(reflect(-v, n), l);
        float3 baseColor = max(input.color, float3(0.002, 0.004, 0.006));
        float upWeight = saturate(n.y * 0.5 + 0.5);
        float3 shallowScatter = baseColor * (0.56 + 0.30 * upWeight);

        // Compact sharp sun glint: repeated squares instead of GGX divisions / pow.
        float3 h = normalize(l + v);
        float noH = saturate(dot(n, h));
        float noH2 = noH * noH;
        float noH4 = noH2 * noH2;
        float noH8 = noH4 * noH4;
        float noH16 = noH8 * noH8;
        float noH32 = noH16 * noH16;
        float noL = saturate(dot(n, l));
        float3 stellar = max(gPush.data2.rgb, 0.0) * max(gPush.data2.a, 0.0);
        float3 sunGlint = stellar * noH32 * noL * (0.035 + 0.26 * fresnel);

        float3 linearColor = shallowScatter * (1.0 - fresnel)
            + reflected * fresnel * 1.16 + sunGlint;
        linearColor *= exposure;
        linearColor = linearColor * input.terrainAerialTransmittance
            + input.terrainAerialInscatter;
        float3 color = acesFitted(stylizedWarmCoolGrade(linearColor));
        return float4(color, opticalOpacity);
    }

    // Glass and future low-coverage transparent props retain the generic PBR path.
    float3 n = normalize(input.normal);
    float3 v = normalize(-input.relativePosition);
    const float ior = 1.50;
    float f0Scalar = ((ior - 1.0) / (ior + 1.0));
    f0Scalar *= f0Scalar;
    float x = 1.0 - saturate(abs(dot(n, v)));
    float x2 = x * x;
    float fresnel = f0Scalar + (1.0 - f0Scalar) * x2 * x2 * x;
    float opticalOpacity = saturate((1.0 - transmission) * 0.48 + fresnel * 0.72 + 0.025);
    float3 linearColor = evaluatePbr(input, true) * exposure;
    linearColor = applyStylizedAerial(linearColor, input, 0.46);
    float3 color = acesFitted(stylizedWarmCoolGrade(linearColor));
    return float4(color, opticalOpacity);
}
'''
    text = text[:start] + fast_transparent + text[end:]
    SHADER.write_text(text, encoding="utf-8")
    print("R24 fast water 120 path materialized")
else:
    print("R24 fast water 120 path already materialized")

out = SHADER.read_text(encoding="utf-8")
for needle in ["R24_FAST_WATER_120_V1", "waterMaterialVertex", "waterMaterialAerial", "noH32"]:
    if needle not in out:
        raise SystemExit(f"fast water contract missing: {needle}")
print("R24 fast water source contracts passed")
