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
static const float kShadowHalfExtent = 72.0;
static const float kShadowDepthRange = 180.0;
static const float kShadowResolution = 512.0;
static const float2 kShadowTexel = float2(1.0 / kShadowResolution, 1.0 / kShadowResolution);
static const float kShadowWorldTexel = (2.0 * kShadowHalfExtent) / kShadowResolution;

float3 rotateByQuaternion(float3 v, float4 q)
{
    float3 t = 2.0 * cross(q.xyz, v);
    return v + q.w * t + cross(q.xyz, t);
}

float hash21(float2 p)
{
    float3 p3 = frac(float3(p.x, p.y, p.x) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return frac((p3.x + p3.y) * p3.z);
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

float3 toneMapFilmic(float3 x)
{
    x = max(x, 0.0);
    return saturate((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14));
}

float3 atmosphereSky(float solarElevation, float density)
{
    float daylight = smoothstep(-0.12, 0.18, solarElevation);
    float twilight = saturate(1.0 - abs(solarElevation + 0.045) / 0.24);
    float3 sky = lerp(float3(0.008, 0.015, 0.032), float3(0.17, 0.38, 0.68), daylight);
    sky = lerp(sky, float3(0.70, 0.30, 0.12), twilight * (1.0 - daylight * 0.50));
    return lerp(float3(0.012, 0.018, 0.028), sky, density);
}

void shadowBasis(float3 lightDirection, out float3 right, out float3 up)
{
    float3 helper = abs(lightDirection.y) < 0.94
        ? float3(0.0, 1.0, 0.0)
        : float3(1.0, 0.0, 0.0);
    right = normalize(cross(helper, lightDirection));
    up = normalize(cross(lightDirection, right));
}

float2 stableShadowOffset(float3 right, float3 up)
{
    float2 cameraPlane = float2(
        dot(gPush.cameraPosition.xyz, right),
        dot(gPush.cameraPosition.xyz, up));
    float2 snapped = round(cameraPlane / kShadowWorldTexel) * kShadowWorldTexel;
    return cameraPlane - snapped;
}

float shadowTap(float2 uv, float receiverDepth, float bias, float2 offset)
{
    float storedDepth = gShadowMap.SampleLevel(gShadowSampler, uv + offset * kShadowTexel, 0.0);
    return receiverDepth - bias <= storedDepth ? 1.0 : 0.0;
}

float shadowVisibility(float3 relativePosition, float noL, float3 lightDirection)
{
    float3 right;
    float3 up;
    shadowBasis(lightDirection, right, up);
    float2 snapOffset = stableShadowOffset(right, up);
    float sx = dot(relativePosition, right) + snapOffset.x;
    float sy = dot(relativePosition, up) + snapOffset.y;
    float sz = dot(relativePosition, lightDirection);
    if (abs(sx) >= kShadowHalfExtent || abs(sy) >= kShadowHalfExtent || abs(sz) >= kShadowDepthRange * 0.5)
        return 1.0;

    float2 uv = float2(sx, sy) / (2.0 * kShadowHalfExtent) + 0.5;
    float receiverDepth = saturate(0.5 - sz / kShadowDepthRange);
    float bias = lerp(0.00070, 0.00190, 1.0 - noL);

    // Fixed tent PCF: stable under motion, no temporal/random grain. 4/2/1 weights yield sixteen
    // effective levels instead of the old coarse 0/25/50/75/100% staircase.
    const float radius = 1.15;
    float visibility = 0.0;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 0.0,  0.0)) * 4.0;
    visibility += shadowTap(uv, receiverDepth, bias, float2(-radius,  0.0)) * 2.0;
    visibility += shadowTap(uv, receiverDepth, bias, float2( radius,  0.0)) * 2.0;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 0.0, -radius)) * 2.0;
    visibility += shadowTap(uv, receiverDepth, bias, float2( 0.0,  radius)) * 2.0;
    visibility += shadowTap(uv, receiverDepth, bias, float2(-radius, -radius));
    visibility += shadowTap(uv, receiverDepth, bias, float2( radius, -radius));
    visibility += shadowTap(uv, receiverDepth, bias, float2(-radius,  radius));
    visibility += shadowTap(uv, receiverDepth, bias, float2( radius,  radius));
    visibility *= 1.0 / 16.0;
    return lerp(0.30, 1.0, visibility);
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
    float3 n = proceduralMaterial ? flatNormal : smoothNormal;
    float localRadius = max(length(input.localPosition), 1.0);
    float3 surfaceUp = normalize(rotateByQuaternion(input.localPosition, gPush.objectRotation));

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

        float3 dryGrass = float3(0.20, 0.27, 0.095);
        float3 meadow = float3(0.12, 0.36, 0.075);
        float3 lushGrass = float3(0.055, 0.29, 0.055);
        float3 soil = float3(0.27, 0.18, 0.078);
        float3 stone = float3(0.30, 0.30, 0.28);
        float3 coldStone = float3(0.38, 0.40, 0.41);
        float3 snow = float3(0.74, 0.77, 0.75);

        float3 grass = lerp(dryGrass, lushGrass, moisture);
        grass = lerp(grass, meadow, saturate((temperature - 0.35) * 1.45));
        grass *= 0.93 + (macro - 0.5) * 0.10;
        float soilMask = saturate(smoothstep(0.16, 0.46, normalizedHeight) * (0.68 - moisture * 0.28));
        float rockMask = saturate(
            smoothstep(0.09, 0.34, slope)
            + smoothstep(0.38, 0.68, normalizedHeight) * 0.78);
        float snowMask = smoothstep(0.60, 0.86, normalizedHeight)
            * (1.0 - smoothstep(0.24, 0.64, temperature));

        baseColor = lerp(grass, soil, soilMask);
        baseColor = lerp(baseColor, lerp(stone, coldStone, 1.0 - temperature), rockMask);
        baseColor = lerp(baseColor, snow, snowMask);
        roughness = lerp(0.96, 0.80, rockMask);
        f0 = float3(0.027, 0.029, 0.028);
        materialAO = lerp(0.74, 1.0, faceUp);
    }
    else if (barkMaterial)
    {
        float u = input.surfaceData.y;
        float vCoord = input.surfaceData.z;
        float warp = valueNoise3(float3(u * 3.5, vCoord * 0.52, input.localPosition.z * 0.075));
        float fibre = 0.5 + 0.5 * sin((u + (warp - 0.5) * 0.025) * 6.2831853 * 5.0);
        float fissure = smoothstep(0.86, 0.96, 0.5 + 0.5 * sin(u * 6.2831853 * 6.0 + warp * 2.0));
        baseColor = lerp(float3(0.045, 0.015, 0.005), float3(0.24, 0.080, 0.018), 0.46 + 0.44 * warp);
        baseColor = lerp(baseColor, float3(0.38, 0.16, 0.038), fibre * 0.10);
        baseColor *= 1.0 - fissure * 0.22;
        roughness = 0.88 + fissure * 0.06;
        f0 = float3(0.022, 0.019, 0.015);
        materialAO = 0.78 - fissure * 0.10;
    }
    else if (foliageMaterial)
    {
        float variation = input.surfaceData.y;
        float canopyHeight = saturate(input.surfaceData.z);
        float macro = valueNoise3(input.localPosition * 0.115 + variation * 7.0);
        float upFacing = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
        baseColor = lerp(float3(0.018, 0.105, 0.014), float3(0.066, 0.30, 0.030), 0.44 + 0.46 * macro);
        baseColor = lerp(baseColor, float3(0.34, 0.53, 0.080), upFacing * (0.08 + canopyHeight * 0.15));
        roughness = 0.92;
        f0 = float3(0.019, 0.022, 0.016);
        materialAO = lerp(0.47, 0.91, canopyHeight) * lerp(0.82, 1.0, upFacing);
        foliageTransmission = 1.0;
    }
    else if (rockMaterial)
    {
        float variation = input.surfaceData.y;
        float strataCoord = input.surfaceData.z;
        float macro = valueNoise3(input.localPosition * (0.095 + variation * 0.025) + variation * 11.0);
        float strata = 0.5 + 0.5 * sin(strataCoord * 4.0 + macro * 1.6);
        float faceUp = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
        float lichen = smoothstep(0.78, 0.94, valueNoise3(input.localPosition * 0.18 + float3(-8.0, 2.0, 4.0)))
            * (0.30 + 0.70 * faceUp);
        baseColor = lerp(float3(0.25, 0.26, 0.265), float3(0.35, 0.285, 0.205), variation * 0.50 + macro * 0.30);
        baseColor = lerp(baseColor, float3(0.16, 0.145, 0.125), (1.0 - strata) * 0.12);
        baseColor = lerp(baseColor, float3(0.22, 0.30, 0.11), lichen * 0.12);
        roughness = 0.84;
        f0 = float3(0.034, 0.032, 0.030);
        materialAO = lerp(0.66, 1.0, faceUp);
    }
    else if (oceanMaterial)
    {
        waterDepth = saturate(input.surfaceData.y);
        float shoreVariation = saturate(input.surfaceData.z);
        float macro = valueNoise3(input.localPosition * 0.032 + float3(1.7, -3.4, 6.2));
        baseColor = lerp(float3(0.025, 0.48, 0.52), float3(0.012, 0.20, 0.34), smoothstep(0.03, 0.30, waterDepth));
        baseColor = lerp(baseColor, float3(0.004, 0.034, 0.105), smoothstep(0.28, 0.90, waterDepth));
        baseColor *= 0.96 + (macro - 0.5) * 0.06;

        float shoreBand = 1.0 - smoothstep(0.018, 0.15 + shoreVariation * 0.030, waterDepth);
        float foamFlow = 0.5 + 0.5 * sin(
            input.localPosition.x * 0.34
            + input.localPosition.z * 0.27
            + macro * 2.6
            + shoreVariation * 6.2831853);
        foamMask = shoreBand * smoothstep(0.64, 0.82, foamFlow);
        baseColor = lerp(baseColor, float3(0.79, 0.92, 0.88), foamMask * 0.82);
        f0 = float3(0.0204, 0.0204, 0.0204);
        roughness = lerp(0.14, 0.052, smoothstep(0.10, 0.82, waterDepth));
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
    float3 horizonColor = lerp(float3(0.13, 0.22, 0.31), float3(0.86, 0.36, 0.14), twilight * 0.78);
    horizonColor = lerp(float3(0.025, 0.038, 0.060), horizonColor, atmosphereDensity);

    float3 stellarRadiance = max(gPush.sunColorIntensity.rgb, 0.0) * max(gPush.sunColorIntensity.a, 0.0);
    stellarRadiance *= lerp(float3(1.0, 0.50, 0.27), float3(1.0, 0.95, 0.86), daylight);
    float shadow = oceanMaterial ? 1.0 : shadowVisibility(input.relativePosition, noL, l);
    float3 direct = (diffuse + specular) * noL * stellarRadiance * 1.12 * shadow;

    float hemiUp = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
    float3 skyAmbient = skyColor * (0.10 + 0.26 * hemiUp);
    float3 groundBounceColor = float3(0.16, 0.125, 0.060);
    if (terrainMaterial || foliageMaterial) groundBounceColor = float3(0.09, 0.17, 0.050);
    if (oceanMaterial) groundBounceColor = float3(0.018, 0.065, 0.095);
    float3 indirect = max(baseColor, 0.0)
        * (skyAmbient + groundBounceColor * (0.035 + 0.105 * (1.0 - hemiUp)))
        * materialAO;

    if (foliageTransmission > 0.0)
    {
        float backLit = saturate(dot(-n, l));
        float edgeLit = pow(1.0 - noV, 2.0);
        float transmissionShadow = lerp(shadow, 1.0, 0.24);
        direct += baseColor * float3(0.64, 0.86, 0.16)
            * backLit * (0.09 + 0.15 * edgeLit) * daylight * transmissionShadow;
    }

    float3 color = direct + indirect;
    if (oceanMaterial)
    {
        float grazing = pow(1.0 - noV, 4.0);
        float3 reflectedSky = lerp(horizonColor, skyColor, 0.30 + 0.70 * hemiUp);
        color += reflectedSky * (0.18 + 1.02 * grazing);
        color += baseColor * (0.08 + 0.08 * waterDepth);
        color += float3(0.55, 0.62, 0.54) * foamMask * (0.45 + 0.55 * noL);
    }

    if (proceduralMaterial)
    {
        float viewDistance = length(input.relativePosition);
        float3 viewRay = normalize(input.relativePosition);
        float horizonView = 1.0 - saturate(abs(dot(viewRay, surfaceUp)));
        float fogDistance = 1.0 - exp(-viewDistance * 0.0032 * atmosphereDensity);
        float fogFactor = saturate(fogDistance * (0.54 + 0.62 * horizonView * horizonView));
        float3 fogColor = lerp(skyColor, horizonColor, 0.48 + 0.42 * horizonView);
        color = lerp(color, fogColor, fogFactor * 0.84);
    }

    return float4(toneMapFilmic(color), 1.0);
}
