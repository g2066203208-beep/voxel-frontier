from pathlib import Path

H = Path('native/include/vf/render/VulkanRenderer.hpp')
CPP = Path('native/src/render/VulkanRenderer.cpp')
SHADER = Path('native/shaders/planet.slang')
h = H.read_text(encoding='utf-8')
cpp = CPP.read_text(encoding='utf-8')
shader = SHADER.read_text(encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# 1) GPU profiler: discard startup/warm-up samples and report cumulative steady means + maxima.
# -----------------------------------------------------------------------------
h = replace_once(
    h,
'''    std::uint64_t timestampMask_{~std::uint64_t{0}};\n    std::uint64_t gpuTimingSamples_{};\n    bool gpuTimestampsSupported_{};\n''',
'''    std::uint64_t timestampMask_{~std::uint64_t{0}};\n    std::uint64_t gpuTimingSamples_{};\n    static constexpr std::uint64_t kGpuTimingWarmupSamples = 6U;\n    std::uint64_t gpuTimingSteadySamples_{};\n    std::array<double, 4> gpuTimingAccumMilliseconds_{};\n    std::array<double, 4> gpuTimingMaxMilliseconds_{};\n    bool gpuTimestampsSupported_{};\n''',
    'steady GPU timing accumulators')

cpp = replace_once(
    cpp,
'''    const double shadowMs = milliseconds(0U, 1U);\n    const double opaqueMs = milliseconds(2U, 3U);\n    const double skyMs = milliseconds(4U, 5U);\n    const double transparentMs = milliseconds(6U, 7U);\n    ++gpuTimingSamples_;\n    // Log the first measurement immediately for CI/evidence and then once per ~60 samples so a\n    // normal gameplay log is useful without becoming a per-frame I/O bottleneck.\n    if (gpuTimingSamples_ == 1U || (gpuTimingSamples_ % 60U) == 0U) {\n        SDL_Log(\n            "R24 GPU pass_ms shadow=%.3f opaque=%.3f sky=%.3f transparent=%.3f total_profiled=%.3f",\n            shadowMs, opaqueMs, skyMs, transparentMs,\n            shadowMs + opaqueMs + skyMs + transparentMs);\n    }\n''',
'''    const double shadowMs = milliseconds(0U, 1U);\n    const double opaqueMs = milliseconds(2U, 3U);\n    const double skyMs = milliseconds(4U, 5U);\n    const double transparentMs = milliseconds(6U, 7U);\n    ++gpuTimingSamples_;\n\n    // The first frames include static-buffer adoption, pipeline/cache warm-up and software-driver\n    // initialization on CI. They are useful hitch evidence but are not representative steady-state\n    // pass cost. Keep them out of the optimization baseline instead of letting one startup frame\n    // (the old mountain sample exceeded 600 ms) dominate every subsequent decision.\n    if (gpuTimingSamples_ <= kGpuTimingWarmupSamples) return;\n\n    const std::array<double, 4> current{shadowMs, opaqueMs, skyMs, transparentMs};\n    for (std::size_t i = 0; i < current.size(); ++i) {\n        gpuTimingAccumMilliseconds_[i] += current[i];\n        gpuTimingMaxMilliseconds_[i] = std::max(gpuTimingMaxMilliseconds_[i], current[i]);\n    }\n    ++gpuTimingSteadySamples_;\n\n    // Four-scene Vulkan evidence waits four seconds after terrain settles. Logging every eight\n    // steady samples guarantees CI captures a real mean even on llvmpipe while normal gameplay I/O\n    // remains negligible. Means are cumulative after warm-up; maxima preserve intermittent spikes.\n    if ((gpuTimingSteadySamples_ % 8U) == 0U) {\n        const double inv = 1.0 / static_cast<double>(gpuTimingSteadySamples_);\n        const double shadowMean = gpuTimingAccumMilliseconds_[0] * inv;\n        const double opaqueMean = gpuTimingAccumMilliseconds_[1] * inv;\n        const double skyMean = gpuTimingAccumMilliseconds_[2] * inv;\n        const double transparentMean = gpuTimingAccumMilliseconds_[3] * inv;\n        SDL_Log(\n            "R24 GPU steady_pass_ms samples=%llu shadow_mean=%.3f opaque_mean=%.3f sky_mean=%.3f transparent_mean=%.3f total_mean=%.3f shadow_max=%.3f opaque_max=%.3f sky_max=%.3f transparent_max=%.3f",\n            static_cast<unsigned long long>(gpuTimingSteadySamples_),\n            shadowMean, opaqueMean, skyMean, transparentMean,\n            shadowMean + opaqueMean + skyMean + transparentMean,\n            gpuTimingMaxMilliseconds_[0], gpuTimingMaxMilliseconds_[1],\n            gpuTimingMaxMilliseconds_[2], gpuTimingMaxMilliseconds_[3]);\n    }\n''',
    'steady timestamp statistics')

# -----------------------------------------------------------------------------
# 2) Terrain-specific fast BRDF.
# Filament's open-source material model uses Lambert because it is extremely efficient and close
# enough to more complex diffuse models. R24 terrain is explicitly rough (0.64--0.98), dielectric
# and covers most visible pixels; reserve full GGX for materials where its specular lobe matters.
# -----------------------------------------------------------------------------
shader = replace_once(
    shader,
'''float3 evaluatePbr(VertexOutput input, bool transparent)\n{\n''',
'''float3 evaluateTerrainFast(VertexOutput input)\n{\n    float3 n = normalize(input.normal);\n    float3 l = normalize(gPush.data1.xyz);\n    float noL = saturate(dot(n, l));\n    float3 baseColor = max(input.color, 0.0);\n\n    // PlanetSurface/LodMeshBuilder already bakes biome/elevation variation into vertex.color. One\n    // broad sample prevents flat color blocks without rebuilding multi-octave material noise.\n    float macro = valueNoise2(input.objectPosition.xz * 0.0032);\n    float localSlope = saturate(1.0 - n.y);\n    baseColor *= 0.95 + macro * 0.10;\n    baseColor = lerp(\n        baseColor, baseColor * float3(1.035, 1.005, 0.945),\n        smoothstep(0.62, 0.86, macro) * 0.14);\n    baseColor = lerp(\n        baseColor, baseColor * float3(0.89, 0.92, 0.90),\n        smoothstep(0.32, 0.72, localSlope) * 0.24);\n\n    // Common dielectrics reflect about 4% at normal incidence. For this deliberately high-roughness\n    // terrain path reserve that energy and spend the remaining 96% on a Lambert lobe. This removes\n    // the per-pixel half-vector normalization, Schlick pow, GGX D term, two Smith G terms, reflect\n    // and ambient-specular work from the overwhelmingly largest opaque material.\n    float shadow = noL > 0.0001 ? shadowVisibility(input.shadowPosition, noL) : 1.0;\n    float3 stellar = max(gPush.data2.rgb, 0.0) * max(gPush.data2.a, 0.0);\n    float3 directDiffuse = baseColor * (0.96 / PI) * noL * stellar * shadow;\n\n    float skyWeight = saturate(n.y * 0.5 + 0.5);\n    float3 skyIrradiance = max(gScene.skyAmbientExposure.rgb, 0.0) * (0.28 + 0.72 * skyWeight);\n    float3 groundIrradiance = max(gScene.groundAmbientShadowTexel.rgb, 0.0)\n        * saturate(-n.y * 0.5 + 0.5);\n    float3 ambientDiffuse = baseColor * (skyIrradiance + groundIrradiance) * 0.96;\n    return directDiffuse + ambientDiffuse;\n}\n\nfloat3 evaluatePbr(VertexOutput input, bool transparent)\n{\n''',
    'terrain fast BRDF function')

shader = replace_once(
    shader,
'''    bool waterMaterial = input.material.x < -0.5;\n    float materialTag = input.material.w;\n    bool terrainMaterial = !waterMaterial && materialTag < -0.5 && materialTag > -1.5;\n    bool foliageMaterial = !waterMaterial && materialTag <= -1.5 && materialTag > -2.5;\n''',
'''    bool waterMaterial = input.material.x < -0.5;\n    float materialTag = input.material.w;\n    bool foliageMaterial = !waterMaterial && materialTag <= -1.5 && materialTag > -2.5;\n''',
    'remove terrain from full PBR material switch')

terrain_block = '''    if (terrainMaterial)\n    {\n        // PlanetSurface/LodMeshBuilder already bakes biome/elevation variation into vertex.color.\n        // The old fragment path then recomputed one 3-octave FBM plus a second value-noise field on\n        // every terrain pixel (16 hash evaluations before PBR). Keep one broad value-noise sample\n        // for gentle breakup and let slope + the authored vertex palette carry the rest.\n        float2 q = input.objectPosition.xz;\n        float macro = valueNoise2(q * 0.0032);\n        float localSlope = saturate(1.0 - n.y);\n        baseColor *= 0.95 + macro * 0.10;\n        baseColor = lerp(\n            baseColor, baseColor * float3(1.035, 1.005, 0.945),\n            smoothstep(0.62, 0.86, macro) * 0.14);\n        baseColor = lerp(\n            baseColor, baseColor * float3(0.89, 0.92, 0.90),\n            smoothstep(0.32, 0.72, localSlope) * 0.24);\n        roughness = clamp(roughness + (macro - 0.5) * 0.035, 0.64, 0.98);\n    }\n    else if (foliageMaterial)\n'''
shader = replace_once(
    shader,
    terrain_block,
'''    if (foliageMaterial)\n''',
    'remove duplicated terrain work from full PBR')

shader = replace_once(
    shader,
'''    float exposure = max(gScene.skyAmbientExposure.a, 0.01);\n    float3 linearColor = evaluatePbr(input, false) * exposure;\n    float materialTag = input.material.w;\n''',
'''    float exposure = max(gScene.skyAmbientExposure.a, 0.01);\n    float materialTag = input.material.w;\n    const bool terrainMaterial = materialTag < -0.5 && materialTag > -1.5;\n    float3 linearColor = (terrainMaterial\n        ? evaluateTerrainFast(input)\n        : evaluatePbr(input, false)) * exposure;\n''',
    'route opaque terrain around full GGX')

H.write_text(h, encoding='utf-8')
CPP.write_text(cpp, encoding='utf-8')
SHADER.write_text(shader, encoding='utf-8')
print('R24 TERRAIN FAST BRDF materialized')
print(' - terrain skips full GGX and uses 4%-reserved Lambert fast path')
print(' - ecology/rock/moon retain full PBR')
print(' - startup GPU timing samples excluded from steady means')
print(' - cumulative per-pass mean/max emitted every eight steady samples')
