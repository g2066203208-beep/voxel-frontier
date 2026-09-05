struct VertexInput
{
    float3 position : POSITION;
    float3 normal : NORMAL;
    float3 color : COLOR0;
};

struct VertexOutput
{
    float4 position : SV_Position;
    float3 normal : TEXCOORD0;
    float3 surfaceData : TEXCOORD1;
    float3 relativePosition : TEXCOORD2;
    float3 localPosition : TEXCOORD3;
};

struct PushConstants
{
    float4x4 viewProj;
    float4 cameraPosition;
    float4 sunDirection;
    float4 sunColorIntensity;
    float4 objectRotation;
};

[[vk::push_constant]] ConstantBuffer<PushConstants> gPush;
[[vk::binding(0, 0)]] Texture2D<float> gShadowMap;
[[vk::binding(1, 0)]] SamplerState gShadowSampler;

static const float PI = 3.14159265358979323846;
static const float kShadowHalfExtent = 48.0;
static const float kShadowDepthRange = 180.0;
static const float kShadowResolution = 1024.0;
static const float2 kShadowTexel = float2(1.0 / kShadowResolution, 1.0 / kShadowResolution);
static const float kShadowWorldTexel = (2.0 * kShadowHalfExtent) / kShadowResolution;
// Environment energy is independent from visible sky RGB, but deliberately stays below the
// previous washed-out pass: indirect light preserves color in shadow without erasing form.
static const float kEnvironmentIrradiance = 2.65;
static const float kExposureScale = 1.4640857; // 2^0.55

float3 rotateByQuaternion(float3 v, float4 q)
{
    float3 t = 2.0 * cross(q.xyz, v);
    return v + q.w * t + cross(q.xyz, t);
}

float hash31(float3 p)
{
    p = frac(p * 0.1031);
    p += dot(p, p.yzx + 33.33);
    return frac((p.x + p.y) * p.z);
}

float valueNoise3(float3 p)
{
    float3 i = floor(p);
    float3 f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    float n000 = hash31(i + float3(0, 0, 0));
    float n100 = hash31(i + float3(1, 0, 0));
    float n010 = hash31(i + float3(0, 1, 0));
    float n110 = hash31(i + float3(1, 1, 0));
    float n001 = hash31(i + float3(0, 0, 1));
    float n101 = hash31(i + float3(1, 0, 1));
    float n011 = hash31(i + float3(0, 1, 1));
    float n111 = hash31(i + float3(1, 1, 1));
    float x00 = lerp(n000, n100, f.x);
    float x10 = lerp(n010, n110, f.x);
    float x01 = lerp(n001, n101, f.x);
    float x11 = lerp(n011, n111, f.x);
    return lerp(lerp(x00, x10, f.y), lerp(x01, x11, f.y), f.z);
}

float distributionGGX(float noH, float roughness)
{
    float a = roughness * roughness;
    float a2 = a * a;
    float denominator = noH * noH * (a2 - 1.0) + 1.0;
    return a2 / max(PI * denominator * denominator, 1.0e-5);
}

float geometrySchlickGGX(float noX, float roughness)
{
    float r = roughness + 1.0;
    float k = (r * r) * 0.125;
    return noX / max(noX * (1.0 - k) + k, 1.0e-5);
}

float3 fresnelSchlick(float voH, float3 f0)
{
    float grazing = pow(saturate(1.0 - voH), 5.0);
    return f0 + (1.0 - f0) * grazing;
}

// Jimenez et al. GTAO multi-bounce: AO remains environment visibility instead of black paint.
float3 multiBounceAO(float3 albedo, float ao)
{
    float3 a = 2.0404 * albedo - 0.3324;
    float3 b = -4.7951 * albedo + 0.6417;
    float3 c = 2.7552 * albedo + 0.6903;
    return max(float3(ao, ao, ao), ((ao * a + b) * ao + c) * ao);
}

float3 agxInset(float3 v)
{
    return float3(
        0.842479062253094 * v.x + 0.0784335999999992 * v.y + 0.0792237451477643 * v.z,
        0.0423282422610123 * v.x + 0.878468636469772 * v.y + 0.0791661274605434 * v.z,
        0.0423756549057051 * v.x + 0.0784336 * v.y + 0.879142973793104 * v.z);
}

float3 agxOutset(float3 v)
{
    return float3(
        1.19687900512017 * v.x - 0.0980208811401368 * v.y - 0.0990297440797205 * v.z,
       -0.0528968517574562 * v.x + 1.15190312990417 * v.y - 0.0989611768448433 * v.z,
       -0.0529716355144438 * v.x - 0.0980434501171241 * v.y + 1.15107367264116 * v.z);
}

float3 agxContrastApprox(float3 x)
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

float3 agxStylizedLook(float3 v)
{
    float luma = dot(v, float3(0.2126, 0.7152, 0.0722));
    return float3(luma, luma, luma) + 1.06 * (v - float3(luma, luma, luma));
}

float3 toneMapAgX(float3 color)
{
    const float minEv = -12.47393;
    const float maxEv = 4.026069;
    float3 v = agxInset(max(color, 0.0));
    v = clamp(log2(max(v, 1.0e-10)), minEv, maxEv);
    v = (v - minEv) / (maxEv - minEv);
    v = agxContrastApprox(v);
    v = agxStylizedLook(v);
    v = agxOutset(v);
    v = pow(max(v, 0.0), 2.2);
    return saturate(v);
}

float3 atmosphereSky(float solarElevation, float density)
{
    float daylight = smoothstep(-0.12, 0.18, solarElevation);
    float twilight = saturate(1.0 - abs(solarElevation + 0.045) / 0.24);
    float3 zenith = lerp(float3(0.008, 0.014, 0.032), float3(0.12, 0.31, 0.62), daylight);
    float3 warm = float3(0.74, 0.30, 0.105);
    zenith = lerp(zenith, warm, twilight * (1.0 - daylight * 0.58) * 0.62);
    return lerp(float3(0.012, 0.018, 0.028), zenith, density);
}

void shadowBasis(float3 lightDirection, out float3 right, out float3 up)
{
    float3 helper = abs(lightDirection.y) < 0.94 ? float3(0.0, 1.0, 0.0) : float3(1.0, 0.0, 0.0);
    right = normalize(cross(helper, lightDirection));
    up = normalize(cross(lightDirection, right));
}

float2 stableShadowOffset(float3 right, float3 up)
{
    float2 cameraPlane = float2(dot(gPush.cameraPosition.xyz, right), dot(gPush.cameraPosition.xyz, up));
    float2 snapped = round(cameraPlane / kShadowWorldTexel) * kShadowWorldTexel;
    return cameraPlane - snapped;
}

float shadowTap(float2 uv, float receiverDepth, float bias, float2 offset)
{
    float storedDepth = gShadowMap.SampleLevel(gShadowSampler, uv + offset * kShadowTexel, 0.0);
    return receiverDepth - bias <= storedDepth ? 1.0 : 0.0;
}

float shadowVisibility(float3 relativePosition, float noL, float3 lightDirection, float3 receiverNormal)
{
    float3 right;
    float3 up;
    shadowBasis(lightDirection, right, up);
    float2 snapOffset = stableShadowOffset(right, up);

    // High-density map allows a much smaller receiver offset and bias. This restores fine tree
    // self-shadow instead of erasing it with the old coarse-map acne compensation.
    float normalOffsetMeters = lerp(0.045, 0.008, noL);
    float3 shifted = relativePosition + normalize(receiverNormal) * normalOffsetMeters;
    float sx = dot(shifted, right) + snapOffset.x;
    float sy = dot(shifted, up) + snapOffset.y;
    float sz = dot(shifted, lightDirection);
    if (abs(sx) >= kShadowHalfExtent || abs(sy) >= kShadowHalfExtent || abs(sz) >= kShadowDepthRange * 0.5)
        return 1.0;

    float2 uv = float2(sx, sy) / (2.0 * kShadowHalfExtent) + 0.5;
    float receiverDepth = saturate(0.5 - sz / kShadowDepthRange);
    float bias = lerp(0.00028, 0.00085, 1.0 - noL);
    float centerDepth = gShadowMap.SampleLevel(gShadowSampler, uv, 0.0);
    float blockerGap = max(receiverDepth - bias - centerDepth, 0.0) * kShadowDepthRange;
    float radius = lerp(0.65, 1.35, saturate(blockerGap / 5.0)) * lerp(1.15, 1.0, noL);

    // Deterministic circular kernel. The old square/tent pattern made low-poly silhouettes read as
    // a grid; this only removes shadow-map aliasing and never acts like an artistic Gaussian blur.
    float visibility = 0.0;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 0.000,  0.000) * radius) * 4.0;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 0.000, -1.000) * radius) * 1.5;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 0.707, -0.707) * radius) * 1.5;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 1.000,  0.000) * radius) * 1.5;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 0.707,  0.707) * radius) * 1.5;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 0.000,  1.000) * radius) * 1.5;
    visibility += shadowTap(uv, receiverDepth, bias, float2(-0.707,  0.707) * radius) * 1.5;
    visibility += shadowTap(uv, receiverDepth, bias, float2(-1.000,  0.000) * radius) * 1.5;
    visibility += shadowTap(uv, receiverDepth, bias, float2(-0.707, -0.707) * radius) * 1.5;
    return visibility * (1.0 / 16.0);
}

[shader("vertex")]
VertexOutput vertexMain(VertexInput input)
{
    VertexOutput output;
    float3 worldPosition = rotateByQuaternion(input.position, gPush.objectRotation);
    float3 worldNormal = rotateByQuaternion(input.normal, gPush.objectRotation);
    float3 relativePosition = worldPosition - gPush.cameraPosition.xyz;
    output.position = mul(gPush.viewProj, float4(relativePosition, 1.0));
    output.relativePosition = relativePosition;
    output.localPosition = input.position;
    output.normal = worldNormal;
    output.surfaceData = input.color;
    return output;
}

[shader("fragment")]
float4 fragmentMain(VertexOutput input) : SV_Target
{
    float marker = input.surfaceData.x;
    bool terrainMaterial = marker > 1.0;
    bool barkMaterial = marker < -0.5 && marker > -1.5;
    bool foliageMaterial = marker <= -1.5 && marker > -2.5;
    bool rockMaterial = marker <= -2.5 && marker > -3.5;
    bool oceanMaterial = marker <= -3.5;
    bool proceduralMaterial = terrainMaterial || barkMaterial || foliageMaterial || rockMaterial || oceanMaterial;

    float3 smoothNormal = normalize(input.normal);
    float3 flatNormal = normalize(cross(ddx(input.relativePosition), ddy(input.relativePosition)));
    if (dot(flatNormal, smoothNormal) < 0.0) flatNormal = -flatNormal;

    float localRadius = max(length(input.localPosition), 1.0);
    float3 surfaceUp = normalize(rotateByQuaternion(input.localPosition, gPush.objectRotation));
    float3 n = proceduralMaterial ? flatNormal : smoothNormal;
    if (terrainMaterial) n = normalize(lerp(flatNormal, smoothNormal, 0.08));
    if (rockMaterial) n = normalize(lerp(flatNormal, smoothNormal, 0.12));
    // smoothNormal contains the CPU-generated whole-canopy proxy normal for foliage.
    if (foliageMaterial) n = normalize(lerp(flatNormal, smoothNormal, 0.74));
    if (barkMaterial) n = normalize(lerp(flatNormal, smoothNormal, 0.08));
    if (oceanMaterial)
    {
        float3 helper = abs(surfaceUp.y) < 0.92 ? float3(0.0, 1.0, 0.0) : float3(1.0, 0.0, 0.0);
        float3 tangent = normalize(cross(helper, surfaceUp));
        float3 bitangent = normalize(cross(surfaceUp, tangent));
        float x = dot(input.localPosition, tangent);
        float y = dot(input.localPosition, bitangent);
        float slopeX = cos(x * 0.22 + y * 0.07) * 0.070 + cos(x * 0.43 - y * 0.19 + 1.7) * 0.030 + cos(x * 0.12 + y * 0.37 - 0.8) * 0.020;
        float slopeY = cos(y * 0.20 - x * 0.08 + 0.9) * 0.060 + cos(y * 0.39 + x * 0.16 - 2.0) * 0.028 + cos(y * 0.14 - x * 0.31 + 0.4) * 0.018;
        n = normalize(surfaceUp - tangent * slopeX - bitangent * slopeY);
    }

    float3 baseColor = input.surfaceData;
    float roughness = 0.62;
    float3 f0 = float3(0.04, 0.04, 0.04);
    float materialAO = 1.0;
    float foliageTransmission = 0.0;
    float foamMask = 0.0;
    float waterDepth = 0.0;

    if (terrainMaterial)
    {
        float normalizedHeight = input.surfaceData.y;
        float moisture = saturate(input.surfaceData.z);
        float temperature = saturate((marker - 1.25) / 0.35);
        float faceUp = saturate(dot(n, surfaceUp));
        float slope = 1.0 - faceUp;
        float macro = valueNoise3(input.localPosition * 0.018 + float3(3.2, -5.7, 1.9));
        float3 dryGrass = float3(0.24, 0.33, 0.12);
        float3 meadow = float3(0.15, 0.42, 0.09);
        float3 lushGrass = float3(0.075, 0.34, 0.065);
        float3 soil = float3(0.30, 0.205, 0.085);
        float3 stone = float3(0.32, 0.32, 0.30);
        float3 coldStone = float3(0.40, 0.42, 0.43);
        float3 snow = float3(0.76, 0.79, 0.77);
        float3 grass = lerp(dryGrass, lushGrass, moisture);
        grass = lerp(grass, meadow, saturate((temperature - 0.35) * 1.45));
        grass *= 0.95 + (macro - 0.5) * 0.08;
        float soilMask = saturate(smoothstep(0.16, 0.46, normalizedHeight) * (0.68 - moisture * 0.28));
        float rockMask = saturate(smoothstep(0.09, 0.34, slope) + smoothstep(0.38, 0.68, normalizedHeight) * 0.78);
        float snowMask = smoothstep(0.60, 0.86, normalizedHeight) * (1.0 - smoothstep(0.24, 0.64, temperature));
        baseColor = lerp(grass, soil, soilMask);
        baseColor = lerp(baseColor, lerp(stone, coldStone, 1.0 - temperature), rockMask);
        baseColor = lerp(baseColor, snow, snowMask);
        roughness = lerp(0.95, 0.72, rockMask);
        f0 = lerp(float3(0.024, 0.026, 0.025), float3(0.040, 0.039, 0.037), rockMask);
        materialAO = lerp(0.82, 1.0, faceUp);
    }
    else if (barkMaterial)
    {
        float u = input.surfaceData.y;
        float vCoord = input.surfaceData.z;
        float warp = valueNoise3(float3(u * 3.5, vCoord * 0.52, input.localPosition.z * 0.075));
        float fibre = 0.5 + 0.5 * sin((u + (warp - 0.5) * 0.025) * 6.2831853 * 5.0);
        float fissure = smoothstep(0.86, 0.96, 0.5 + 0.5 * sin(u * 6.2831853 * 6.0 + warp * 2.0));
        baseColor = lerp(float3(0.065, 0.022, 0.007), float3(0.30, 0.105, 0.024), 0.48 + 0.42 * warp);
        baseColor = lerp(baseColor, float3(0.42, 0.18, 0.045), fibre * 0.11);
        baseColor *= 1.0 - fissure * 0.18;
        roughness = 0.93 + fissure * 0.04;
        f0 = float3(0.020, 0.018, 0.015);
        materialAO = 0.86 - fissure * 0.045;
    }
    else if (foliageMaterial)
    {
        float variation = input.surfaceData.y;
        float canopyHeight = saturate(input.surfaceData.z);
        float macro = valueNoise3(input.localPosition * 0.105 + variation * 6.0);
        float upFacing = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
        baseColor = lerp(float3(0.030, 0.145, 0.020), float3(0.095, 0.36, 0.045), 0.46 + 0.42 * macro);
        baseColor = lerp(baseColor, float3(0.38, 0.57, 0.10), upFacing * (0.09 + canopyHeight * 0.16));
        roughness = 0.82;
        f0 = float3(0.026, 0.030, 0.021);
        // Keep meaningful crown occlusion; multi-bounce AO below prevents it becoming black paint.
        materialAO = lerp(0.82, 0.97, canopyHeight) * lerp(0.95, 1.0, upFacing);
        foliageTransmission = 1.0;
    }
    else if (rockMaterial)
    {
        float variation = input.surfaceData.y;
        float strataCoord = input.surfaceData.z;
        float macro = valueNoise3(input.localPosition * (0.090 + variation * 0.022) + variation * 11.0);
        float strata = 0.5 + 0.5 * sin(strataCoord * 4.0 + macro * 1.5);
        float faceUp = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
        float lichen = smoothstep(0.80, 0.95, valueNoise3(input.localPosition * 0.16 + float3(-8.0, 2.0, 4.0))) * (0.30 + 0.70 * faceUp);
        baseColor = lerp(float3(0.27, 0.28, 0.285), float3(0.38, 0.31, 0.225), variation * 0.48 + macro * 0.28);
        baseColor = lerp(baseColor, float3(0.18, 0.16, 0.135), (1.0 - strata) * 0.10);
        baseColor = lerp(baseColor, float3(0.24, 0.32, 0.12), lichen * 0.10);
        roughness = lerp(0.70, 0.82, faceUp);
        f0 = float3(0.040, 0.038, 0.035);
        materialAO = lerp(0.78, 1.0, faceUp);
    }
    else if (oceanMaterial)
    {
        waterDepth = saturate(input.surfaceData.y);
        float shoreVariation = saturate(input.surfaceData.z);
        float macro = valueNoise3(input.localPosition * 0.032 + float3(1.7, -3.4, 6.2));
        baseColor = lerp(float3(0.030, 0.50, 0.54), float3(0.014, 0.23, 0.37), smoothstep(0.03, 0.30, waterDepth));
        baseColor = lerp(baseColor, float3(0.005, 0.045, 0.125), smoothstep(0.28, 0.90, waterDepth));
        baseColor *= 0.97 + (macro - 0.5) * 0.05;
        float shoreBand = 1.0 - smoothstep(0.018, 0.15 + shoreVariation * 0.030, waterDepth);
        float foamFlow = 0.5 + 0.5 * sin(input.localPosition.x * 0.34 + input.localPosition.z * 0.27 + macro * 2.6 + shoreVariation * 6.2831853);
        foamMask = shoreBand * smoothstep(0.64, 0.82, foamFlow);
        baseColor = lerp(baseColor, float3(0.82, 0.94, 0.90), foamMask * 0.82);
        f0 = float3(0.0204, 0.0204, 0.0204);
        roughness = lerp(0.105, 0.032, smoothstep(0.08, 0.80, waterDepth));
    }

    float3 l = normalize(gPush.sunDirection.xyz);
    float3 v = normalize(-input.relativePosition);
    float3 h = normalize(l + v);
    float noL = saturate(dot(n, l));
    float noV = saturate(dot(n, v));
    float noH = saturate(dot(n, h));
    float voH = saturate(dot(v, h));
    float d = distributionGGX(noH, roughness);
    float g = geometrySchlickGGX(noV, roughness) * geometrySchlickGGX(noL, roughness);
    float3 f = fresnelSchlick(voH, f0);
    float3 specular = (d * g * f) / max(4.0 * noV * noL, 1.0e-4);
    float3 diffuse = (1.0 - f) * max(baseColor, 0.0) / PI;

    float cameraRadius = length(gPush.cameraPosition.xyz);
    float cameraAltitude = max(0.0, cameraRadius - localRadius);
    float atmosphereDensity = proceduralMaterial ? exp(-cameraAltitude / 72.0) : 0.0;
    float solarElevation = dot(surfaceUp, l);
    float daylight = smoothstep(-0.10, 0.16, solarElevation);
    float twilight = saturate(1.0 - abs(solarElevation + 0.04) / 0.22);
    float3 skyColor = atmosphereSky(solarElevation, atmosphereDensity);
    float3 horizonColor = lerp(float3(0.11, 0.20, 0.31), float3(0.88, 0.34, 0.12), twilight * 0.78);
    horizonColor = lerp(float3(0.024, 0.037, 0.062), horizonColor, atmosphereDensity);

    float3 stellarRadiance = max(gPush.sunColorIntensity.rgb, 0.0) * max(gPush.sunColorIntensity.a, 0.0);
    float sunWarmth = 1.0 - smoothstep(0.045, 0.38, solarElevation);
    float3 neutralSun = float3(1.0, 0.95, 0.86);
    float3 lowSun = float3(1.0, 0.49, 0.23);
    float3 sunTint = lerp(neutralSun, lowSun, sunWarmth * 0.88);
    float tintLuma = dot(sunTint, float3(0.2126, 0.7152, 0.0722));
    float energyCompensation = lerp(1.0, 0.78 / max(tintLuma, 0.22), sunWarmth * 0.62);
    stellarRadiance *= sunTint * energyCompensation;

    float shadowNoL = saturate(dot(smoothNormal, l));
    float shadow = oceanMaterial ? 1.0 : shadowVisibility(input.relativePosition, shadowNoL, l, smoothNormal);
    // Wrap diffuse is a foliage BRDF choice, not a shadow override: self-shadow remains intact.
    float lightingNoL = foliageMaterial ? saturate((dot(n, l) + 0.12) / 1.12) : noL;
    float3 direct = (diffuse + specular) * lightingNoL * stellarRadiance * 1.12 * shadow;

    float hemiUp = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
    float3 ambientDirectionColor = lerp(horizonColor, skyColor, 0.18 + 0.82 * hemiUp);
    float3 skyAmbient = ambientDirectionColor * kEnvironmentIrradiance * (0.18 + 0.34 * hemiUp);
    float3 groundBounceColor = float3(0.16, 0.125, 0.060);
    if (terrainMaterial) groundBounceColor = float3(0.10, 0.205, 0.055);
    if (foliageMaterial) groundBounceColor = float3(0.12, 0.24, 0.060);
    if (oceanMaterial) groundBounceColor = float3(0.018, 0.065, 0.095);

    float3 diffuseVisibility = multiBounceAO(saturate(baseColor), materialAO);
    float groundWeight = 0.08 + 0.16 * (1.0 - hemiUp);
    if (foliageMaterial) groundWeight += 0.05;
    float3 firstBounce = max(baseColor, 0.0) * (skyAmbient + groundBounceColor * groundWeight);
    float3 localBounceTint = lerp(groundBounceColor, max(baseColor, 0.0), foliageMaterial ? 0.38 : 0.20);
    float localBounceWeight = foliageMaterial ? 0.08 : 0.035;
    float3 secondaryBounce = max(baseColor, 0.0) * localBounceTint * localBounceWeight;
    float3 indirect = (firstBounce + secondaryBounce) * diffuseVisibility;

    float3 reflectedDir = normalize(reflect(-v, n));
    float reflectedUp = saturate(dot(reflectedDir, surfaceUp) * 0.5 + 0.5);
    float3 reflectedEnvironment = lerp(horizonColor, skyColor, smoothstep(0.10, 0.90, reflectedUp)) * 1.25;
    float broadCloud = smoothstep(0.48, 0.72, valueNoise3(reflectedDir * 2.25 + float3(4.3, -2.1, 7.6)));
    reflectedEnvironment *= lerp(1.0, 0.76, broadCloud * daylight);

    float mirrorDot = saturate(dot(reflectedDir, l));
    float broadSunReflection = pow(mirrorDot, 18.0);
    float tightSunReflection = pow(mirrorDot, 96.0);
    float gloss = 1.0 - roughness;
    reflectedEnvironment += stellarRadiance * (broadSunReflection * 0.030 + tightSunReflection * 0.115) * (0.25 + 0.75 * gloss);

    float envGrazing = pow(1.0 - noV, 5.0);
    float3 envFresnel = f0 + (1.0 - f0) * envGrazing;
    float envWeight = gloss * gloss * (0.16 + 0.30 * hemiUp) * materialAO;
    float3 environmentSpecular = reflectedEnvironment * envFresnel * envWeight;

    if (foliageTransmission > 0.0)
    {
        float backLit = saturate(dot(-n, l));
        float edgeLit = pow(1.0 - noV, 2.0);
        // Transmission is the only foliage term allowed to recover some blocked sun.
        float transmissionVisibility = lerp(shadow, 1.0, 0.28);
        direct += baseColor * float3(0.58, 0.80, 0.16) * backLit
            * (0.065 + 0.105 * edgeLit) * daylight * transmissionVisibility;
    }

    float3 color = direct + indirect;
    if (!oceanMaterial)
    {
        color += environmentSpecular;
    }
    else
    {
        float waterFresnel = 0.0204 + (1.0 - 0.0204) * pow(1.0 - noV, 5.0);
        float depthTransmission = lerp(0.72, 0.28, waterDepth);
        color = lerp(baseColor * depthTransmission, reflectedEnvironment, saturate(waterFresnel * 1.12));
        color += environmentSpecular * 1.45;
        color += stellarRadiance * (broadSunReflection * 0.050 + tightSunReflection * 0.16);
        color += baseColor * (0.070 + 0.055 * waterDepth);
        color += float3(0.55, 0.62, 0.54) * foamMask * (0.48 + 0.52 * noL);
    }

    if (proceduralMaterial)
    {
        float viewDistance = length(input.relativePosition);
        float3 viewRay = normalize(input.relativePosition);
        float horizonView = 1.0 - saturate(abs(dot(viewRay, surfaceUp)));
        float extinction = 0.00245 * atmosphereDensity * (0.72 + 0.95 * horizonView * horizonView);
        const float fogStartMeters = 28.0;
        float fogTravel = max(0.0, viewDistance - fogStartMeters);
        float fogFactor = saturate(1.0 - exp(-fogTravel * extinction));

        float3 fogColor = lerp(skyColor, horizonColor, 0.40 + 0.48 * horizonView);
        float forwardScatter = pow(saturate(dot(viewRay, l)), 8.0);
        float3 warmAir = lerp(float3(0.72, 0.40, 0.18), float3(1.0, 0.70, 0.38), daylight);
        float scatterWeight = forwardScatter * fogFactor * (0.18 + 0.46 * sunWarmth) * horizonView;
        fogColor = lerp(fogColor, warmAir, saturate(scatterWeight));
        float fogLuma = dot(fogColor, float3(0.2126, 0.7152, 0.0722));
        fogColor = lerp(fogColor, float3(fogLuma, fogLuma, fogLuma), fogFactor * 0.06);
        color = lerp(color, fogColor, fogFactor * 0.90);
    }

    return float4(toneMapAgX(color * kExposureScale), 1.0);
}
