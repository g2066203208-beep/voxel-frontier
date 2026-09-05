// V15 keeps the complete V14 shader library (physical atmosphere, vertex ABI, shadow pass and HUD)
// as its base and overrides only the three art-facing fragment entry points.  This prevents the
// rendering pass from ever replacing the newer Earth-scale renderer with an older small-planet ABI.
#define opaqueFragmentMain v14OpaqueFragmentMain
#define transparentFragmentMain v14TransparentFragmentMain
#define skyFragmentMain v14SkyFragmentMain
#include "planet_v14_base.slang"
#undef opaqueFragmentMain
#undef transparentFragmentMain
#undef skyFragmentMain

float3 agxInsetV15(float3 v)
{
    return float3(
        0.842479062253094 * v.x + 0.0784335999999992 * v.y + 0.0792237451477643 * v.z,
        0.0423282422610123 * v.x + 0.878468636469772 * v.y + 0.0791661274605434 * v.z,
        0.0423756549057051 * v.x + 0.0784336 * v.y + 0.879142973793104 * v.z);
}

float3 agxOutsetV15(float3 v)
{
    return float3(
        1.19687900512017 * v.x - 0.0980208811401368 * v.y - 0.0990297440797205 * v.z,
       -0.0528968517574562 * v.x + 1.15190312990417 * v.y - 0.0989611768448433 * v.z,
       -0.0529716355144438 * v.x - 0.0980434501171241 * v.y + 1.15107367264116 * v.z);
}

float3 agxContrastV15(float3 x)
{
    float3 x2 = x * x;
    float3 x4 = x2 * x2;
    return 15.5 * x4 * x2
        - 40.14 * x4 * x
        + 31.96 * x4
        - 6.868 * x2 * x
        + 0.4298 * x2
        + 0.1191 * x
        - 0.00232;
}

float3 toneMapAgXV15(float3 color)
{
    const float minEv = -12.47393;
    const float maxEv = 4.026069;
    float3 v = agxInsetV15(max(color, 0.0));
    v = clamp(log2(max(v, 1.0e-10)), minEv, maxEv);
    v = (v - minEv) / (maxEv - minEv);
    v = agxContrastV15(v);
    float luma = luminance709(v);
    v = float3(luma, luma, luma) + 1.06 * (v - float3(luma, luma, luma));
    v = agxOutsetV15(v);
    // Filament/Blender-style display-linear output; the Vulkan sRGB attachment performs the final
    // electro-optical encoding.
    return saturate(pow(max(v, 0.0), 2.2));
}

float shadowVisibilityCircularV15(float4 lightClip, float noL)
{
    if (lightClip.w <= 0.0) return 1.0;
    float3 ndc = lightClip.xyz / lightClip.w;
    float2 uv = ndc.xy * 0.5 + 0.5;
    if (any(uv < 0.0) || any(uv > 1.0) || ndc.z < 0.0 || ndc.z > 1.0) return 1.0;

    float texel = max(gScene.groundAmbientShadowTexel.w, 1.0 / 4096.0);
    float bias = max(0.00018, 0.00088 * (1.0 - noL));
    const float2 taps[9] = {
        float2(0.0, 0.0),
        float2(0.0, -0.82), float2(0.58, -0.58), float2(0.82, 0.0), float2(0.58, 0.58),
        float2(0.0, 0.82), float2(-0.58, 0.58), float2(-0.82, 0.0), float2(-0.58, -0.58)
    };
    const float weights[9] = {4.0, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5};
    float visible = 0.0;
    [unroll]
    for (int i = 0; i < 9; ++i)
    {
        float stored = gShadowMap.SampleLevel(gShadowSampler, uv + taps[i] * texel, 0.0);
        visible += (ndc.z - bias <= stored ? 1.0 : 0.0) * weights[i];
    }
    return visible * (1.0 / 16.0);
}

float3 multiBounceAOV15(float3 albedo, float ao)
{
    float3 a = 2.0404 * albedo - 0.3324;
    float3 b = -4.7951 * albedo + 0.6417;
    float3 c = 2.7552 * albedo + 0.6903;
    return max(float3(ao, ao, ao), ((ao * a + b) * ao + c) * ao);
}

float3 evaluateOpaqueV15(VertexOutput input)
{
    float3 n = normalize(input.normal);
    float3 l = normalize(gPush.data1.xyz);
    float3 v = normalize(-input.relativePosition);
    float3 h = normalize(l + v);
    float metallic = saturate(input.material.x);
    float roughness = clamp(input.material.y, 0.045, 1.0);
    float3 baseColor = max(input.color, 0.0);
    bool water = input.material.x < -0.5;
    bool foliage = input.material.w < -0.5 && input.material.w > -1.5;
    bool bark = input.material.w <= -1.5 && input.material.w > -2.5;
    bool rock = input.material.w <= -2.5 && input.material.w > -3.5;

    float rawNoL = dot(n, l);
    float noL = saturate(rawNoL);
    float noV = max(saturate(dot(n, v)), 1.0e-4);
    float noH = saturate(dot(n, h));
    float voH = saturate(dot(v, h));
    float skyWeight = saturate(n.y * 0.5 + 0.5);
    float groundWeight = saturate(-n.y * 0.5 + 0.5);
    float3 skyIrradiance = max(gScene.skyAmbientExposure.rgb, 0.0) * (0.36 + 0.64 * skyWeight);
    float3 groundIrradiance = max(gScene.groundAmbientShadowTexel.rgb, 0.0) * (0.28 + 0.72 * groundWeight);
    float3 stellar = max(gPush.data2.rgb, 0.0) * max(gPush.data2.a, 0.0);

    if (water)
    {
        float3 reflectedDir = normalize(reflect(-v, n));
        float3 environment = stylizedSkyPalette(reflectedDir, l);
        float waterFresnel = 0.0204 + (1.0 - 0.0204) * pow(1.0 - noV, 5.0);
        float broadSun = pow(saturate(dot(reflectedDir, l)), 22.0);
        float tightSun = pow(saturate(dot(reflectedDir, l)), 110.0);
        float horizon = 1.0 - saturate(abs(n.y));
        float3 shallow = float3(0.025, 0.34, 0.42);
        float3 deep = float3(0.010, 0.075, 0.20);
        float3 body = lerp(deep, shallow, 0.24 + 0.42 * skyWeight);
        float3 color = lerp(body, environment, saturate(waterFresnel * 1.10));
        color += stellar * (broadSun * 0.055 + tightSun * 0.19);
        color += float3(0.020, 0.045, 0.050) * horizon;
        return color;
    }

    float3 f0 = lerp(float3(0.04, 0.04, 0.04), baseColor, metallic);
    if (foliage) f0 = float3(0.026, 0.030, 0.021);
    if (bark) f0 = float3(0.020, 0.018, 0.015);
    if (rock) f0 = float3(0.040, 0.038, 0.035);
    float3 f = fresnelSchlick(voH, f0);
    float d = distributionGGX(noH, roughness);
    float g = geometrySchlickGGX(noV, roughness) * geometrySchlickGGX(max(noL, 1.0e-4), roughness);
    float3 specular = d * g * f / max(4.0 * noV * max(noL, 1.0e-4), 1.0e-4);
    float3 diffuse = (1.0 - f) * (1.0 - metallic) * baseColor / PI;
    float shadow = shadowVisibilityCircularV15(input.shadowPosition, noL);

    // Foliage uses the transferred canopy normal as one coherent lighting volume.  Wrap diffuse
    // softens only the N.L terminator; shadow remains a real, independent visibility term.
    float lightingNoL = foliage ? saturate((rawNoL + 0.12) / 1.12) : noL;
    float3 direct = (diffuse + specular) * lightingNoL * stellar * shadow;

    float ao = 0.88;
    if (foliage) ao = 0.83 + 0.13 * skyWeight;
    else if (bark) ao = 0.87;
    else if (rock) ao = 0.80 + 0.18 * skyWeight;
    else ao = 0.84 + 0.14 * skyWeight;
    float3 visibility = multiBounceAOV15(saturate(baseColor), ao);
    float3 ambient = baseColor
        * (skyIrradiance * (foliage ? 1.20 : 1.0)
            + groundIrradiance * (foliage ? 1.45 : 1.0))
        * (1.0 - metallic)
        * visibility;

    float3 r = reflect(-v, n);
    float reflectionSky = saturate(r.y * 0.5 + 0.5);
    float3 reflectionColor = lerp(
        max(gScene.groundAmbientShadowTexel.rgb, float3(0.004, 0.004, 0.004)),
        max(gScene.skyAmbientExposure.rgb, float3(0.008, 0.012, 0.020)),
        reflectionSky);
    float envGloss = (1.0 - roughness) * (1.0 - roughness);
    float3 ambientSpecular = reflectionColor * fresnelSchlick(noV, f0) * envGloss * (0.18 + 0.28 * skyWeight);

    if (foliage)
    {
        // Godot/SpeedTree-style broad leaf transmission: light blocked by geometry still remains a
        // shadow; a separate back-light term models light passing through thin foliage.
        float backLit = saturate(dot(-n, l));
        float edgeLit = pow(1.0 - noV, 2.0);
        float transmissionVisibility = lerp(shadow, 1.0, 0.28);
        direct += baseColor * float3(0.58, 0.80, 0.16)
            * backLit * (0.060 + 0.105 * edgeLit) * stellar * transmissionVisibility;
    }

    return direct + ambient + ambientSpecular + baseColor * max(input.material.w, 0.0);
}

[shader("fragment")]
float4 opaqueFragmentMain(VertexOutput input) : SV_Target
{
    if (input.material.z > 0.02) discard;
    float exposure = max(gScene.skyAmbientExposure.a, 0.01);
    float3 linearColor = evaluateOpaqueV15(input) * exposure;
    linearColor = applyStylizedAerial(linearColor, input, 1.0);
    linearColor = stylizedWarmCoolGrade(linearColor);
    return float4(toneMapAgXV15(linearColor), 1.0);
}

[shader("fragment")]
float4 transparentFragmentMain(VertexOutput input) : SV_Target
{
    float transmission = saturate(input.material.z);
    if (transmission <= 0.02) discard;
    float3 n = normalize(input.normal);
    float3 v = normalize(-input.relativePosition);
    float ior = 1.50;
    float f0 = (ior - 1.0) / (ior + 1.0);
    f0 *= f0;
    float fresnel = f0 + (1.0 - f0) * pow(1.0 - saturate(abs(dot(n, v))), 5.0);
    float opticalOpacity = saturate((1.0 - transmission) * 0.48 + fresnel * 0.72 + 0.025);
    float exposure = max(gScene.skyAmbientExposure.a, 0.01);
    float3 linearColor = evaluatePbr(input, true) * exposure;
    linearColor = applyStylizedAerial(linearColor, input, 0.46);
    return float4(toneMapAgXV15(stylizedWarmCoolGrade(linearColor)), opticalOpacity);
}

[shader("fragment")]
float4 skyFragmentMain(FullscreenOutput input) : SV_Target
{
    float3 ray = reconstructWorldRay(input.uv);
    float3 cameraPlanet = gPush.data0.xyz;
    float3 sunDir = normalize(gPush.data1.xyz);
    float groundRadius = max(gPush.data2.x, 1.0);
    float atmosphereRadius = groundRadius + max(gPush.data2.y, 1.0);
    float scaleHeight = max(gPush.data2.z, 100.0);
    float mieScale = max(gPush.data2.w, 0.0);
    float exposure = max(gPush.data3.x, 0.01);

    float atmoNear, atmoFar;
    bool hitsAtmosphere = raySphere(cameraPlanet, ray, atmosphereRadius, atmoNear, atmoFar);
    float groundNear, groundFar;
    bool hitsGround = raySphere(cameraPlanet, ray, groundRadius, groundNear, groundFar)
        && groundFar > 0.0 && groundNear > 0.0;

    float3 background = float3(0.00035, 0.00045, 0.00075) + proceduralStars(ray);
    float sunAngularRadius = 0.004675;
    float sunDisc = smoothstep(cos(sunAngularRadius * 1.15), cos(sunAngularRadius * 0.85), dot(ray, sunDir));
    if (!hitsGround) background += gPush.data3.yzw * sunDisc * 18.0;
    if (!hitsAtmosphere) return float4(toneMapAgXV15(background * exposure), 1.0);

    float startT = max(atmoNear, 0.0);
    float endT = max(atmoFar, startT);
    if (hitsGround) endT = min(endT, groundNear);
    if (endT <= startT) return float4(toneMapAgXV15(background * exposure), 1.0);

    const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);
    float betaM = 21.0e-6 * mieScale;
    float mu = dot(ray, sunDir);
    float rayleighPhase = 3.0 * (1.0 + mu * mu) / (16.0 * PI);
    float anisotropy = 0.76;
    float miePhase = (1.0 - anisotropy * anisotropy)
        / max(4.0 * PI * pow(1.0 + anisotropy * anisotropy - 2.0 * anisotropy * mu, 1.5), 1.0e-5);

    float segment = (endT - startT) / 8.0;
    float opticalView = 0.0;
    float3 scattering = 0.0;
    [unroll]
    for (int i = 0; i < 8; ++i)
    {
        float t = startT + (i + 0.5) * segment;
        float3 samplePoint = cameraPlanet + ray * t;
        float density = densityAtRadius(length(samplePoint), groundRadius, scaleHeight);
        float sunDepth = sunOpticalDepth(samplePoint, sunDir, atmosphereRadius, groundRadius, scaleHeight);
        if (sunDepth > 1.0e7) continue;
        opticalView += density * segment;
        float3 extinction = betaR * (opticalView + sunDepth) + betaM * (opticalView + sunDepth);
        float3 lightTransmittance = exp(-extinction);
        float3 source = (betaR * rayleighPhase + betaM * miePhase) * density;
        scattering += source * lightTransmittance * segment * gPush.data3.yzw;
    }

    float3 transmittance = exp(-(betaR + betaM) * opticalView);
    float3 color = scattering * 17.0;
    if (!hitsGround) color += background * transmittance;
    else color += float3(0.008, 0.009, 0.007) * transmittance;

    float localDensity = densityAtRadius(length(cameraPlanet), groundRadius, scaleHeight);
    float styleWeight = saturate(localDensity * 0.38);
    color = lerp(color, stylizedSkyPalette(ray, sunDir), styleWeight);
    color = stylizedWarmCoolGrade(color);
    return float4(toneMapAgXV15(color * exposure), 1.0);
}
