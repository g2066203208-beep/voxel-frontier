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
static const float2 kShadowTexel = float2(1.0 / 512.0, 1.0 / 512.0);

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

float cellNoise3(float3 p)
{
    return hash31(floor(p));
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

float shadowVisibility(float3 relativePosition, float noL, float3 lightDirection)
{
    float3 right;
    float3 up;
    shadowBasis(lightDirection, right, up);
    float sx = dot(relativePosition, right);
    float sy = dot(relativePosition, up);
    float sz = dot(relativePosition, lightDirection);
    if (abs(sx) >= kShadowHalfExtent || abs(sy) >= kShadowHalfExtent || abs(sz) >= kShadowDepthRange * 0.5)
        return 1.0;

    float2 uv = float2(sx, sy) / (2.0 * kShadowHalfExtent) + 0.5;
    float receiverDepth = saturate(0.5 - sz / kShadowDepthRange);
    float bias = lerp(0.00055, 0.00165, 1.0 - noL);
    float visibility = 0.0;
    visibility += receiverDepth - bias <= gShadowMap.SampleLevel(gShadowSampler, uv + kShadowTexel * float2(-0.5, -0.5), 0.0) ? 1.0 : 0.0;
    visibility += receiverDepth - bias <= gShadowMap.SampleLevel(gShadowSampler, uv + kShadowTexel * float2( 0.5, -0.5), 0.0) ? 1.0 : 0.0;
    visibility += receiverDepth - bias <= gShadowMap.SampleLevel(gShadowSampler, uv + kShadowTexel * float2(-0.5,  0.5), 0.0) ? 1.0 : 0.0;
    visibility += receiverDepth - bias <= gShadowMap.SampleLevel(gShadowSampler, uv + kShadowTexel * float2( 0.5,  0.5), 0.0) ? 1.0 : 0.0;
    visibility *= 0.25;
    // Do not crush the low-poly planes to black. Sky/bounce illumination remains unshadowed below.
    return lerp(0.24, 1.0, visibility);
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
        float macro = valueNoise3(input.localPosition * 0.023 + float3(3.2, -5.7, 1.9));
        float meso = cellNoise3(input.localPosition * 0.105 + float3(-7.1, 2.3, 4.8));
        float mineral = cellNoise3(input.localPosition * 0.28 + float3(4.0, 8.0, -6.0));
        float3 dryGrass = float3(0.20, 0.27, 0.095);
        float3 meadow = float3(0.12, 0.36, 0.075);
        float3 lushGrass = float3(0.055, 0.29, 0.055);
        float3 soil = float3(0.27, 0.18, 0.078);
        float3 stone = float3(0.30, 0.30, 0.28);
        float3 coldStone = float3(0.38, 0.40, 0.41);
        float3 snow = float3(0.74, 0.77, 0.75);
        float3 grass = lerp(dryGrass, lushGrass, moisture);
        grass = lerp(grass, meadow, saturate((temperature - 0.35) * 1.45));
        grass *= 0.88 + macro * 0.19;
        float soilMask = saturate(smoothstep(0.14, 0.44, normalizedHeight) * (0.70 - moisture * 0.30));
        float rockMask = saturate(smoothstep(0.06, 0.31, slope)
            + smoothstep(0.34, 0.64, normalizedHeight) * 0.82
            + max(0.0, meso - 0.74) * 0.62);
        float snowMask = smoothstep(0.58, 0.84, normalizedHeight)
            * (1.0 - smoothstep(0.22, 0.62, temperature));
        baseColor = lerp(grass, soil * (0.88 + meso * 0.16), soilMask);
        baseColor = lerp(baseColor, lerp(stone, coldStone, 1.0 - temperature), rockMask);
        baseColor = lerp(baseColor, snow * (0.94 + mineral * 0.07), snowMask);
        baseColor *= 0.94 + (mineral - 0.5) * 0.08;
        roughness = lerp(0.96, 0.78, rockMask);
        f0 = float3(0.027, 0.029, 0.028);
        materialAO = lerp(0.70, 1.0, faceUp);
    }
    else if (barkMaterial)
    {
        float u = input.surfaceData.y;
        float vCoord = input.surfaceData.z;
        float warp = cellNoise3(float3(u * 5.0, vCoord * 0.72, input.localPosition.z * 0.10));
        float fibre = 0.5 + 0.5 * sin((u + (warp - 0.5) * 0.035) * 6.2831853 * 7.0);
        float2 barkCell = float2(u * 7.0, vCoord * 0.95);
        float2 localCell = frac(barkCell) - 0.5;
        float cellSeed = hash21(floor(barkCell));
        float fissure = smoothstep(0.43, 0.49, abs(localCell.x + (cellSeed - 0.5) * 0.18));
        float micro = hash31(floor(float3(u * 25.0, vCoord * 4.0, 3.0)));
        baseColor = lerp(float3(0.040, 0.013, 0.004), float3(0.23, 0.075, 0.016), 0.42 + 0.50 * warp);
        baseColor = lerp(baseColor, float3(0.40, 0.17, 0.040), fibre * 0.12);
        baseColor *= (1.0 - fissure * 0.34) * (0.94 + micro * 0.08);
        roughness = saturate(0.82 + fissure * 0.09 + micro * 0.05);
        f0 = float3(0.022, 0.019, 0.015);
        materialAO = 0.76 - fissure * 0.14;
    }
    else if (foliageMaterial)
    {
        float variation = input.surfaceData.y;
        float canopyHeight = saturate(input.surfaceData.z);
        float macro = valueNoise3(input.localPosition * 0.18 + variation * 9.0);
        float faceBreakup = hash31(floor(n * 17.0 + variation * 29.0));
        float upFacing = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
        baseColor = lerp(float3(0.014, 0.095, 0.012), float3(0.060, 0.29, 0.028), 0.40 + 0.52 * macro);
        baseColor = lerp(baseColor, float3(0.38, 0.57, 0.085), upFacing * (0.10 + canopyHeight * 0.18));
        baseColor *= 0.94 + (faceBreakup - 0.5) * 0.10;
        roughness = 0.92;
        f0 = float3(0.019, 0.022, 0.016);
        materialAO = lerp(0.43, 0.90, canopyHeight) * lerp(0.78, 1.0, upFacing);
        foliageTransmission = 1.0;
    }
    else if (rockMaterial)
    {
        float variation = input.surfaceData.y;
        float strataCoord = input.surfaceData.z;
        float macro = valueNoise3(input.localPosition * (0.13 + variation * 0.04) + variation * 13.0);
        float grains = hash31(floor(input.localPosition * 0.72 + 5.0));
        float strata = 0.5 + 0.5 * sin(strataCoord * 5.0 + macro * 2.2);
        float faceUp = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
        float lichenNoise = hash31(floor(input.localPosition * 0.30 + float3(-8.0, 2.0, 4.0)));
        float lichen = smoothstep(0.88, 0.96, lichenNoise) * (0.35 + 0.65 * faceUp);
        baseColor = lerp(float3(0.24, 0.25, 0.255), float3(0.36, 0.28, 0.19), variation * 0.52 + macro * 0.36);
        baseColor = lerp(baseColor, float3(0.14, 0.125, 0.105), (1.0 - strata) * 0.16);
        baseColor *= 0.91 + grains * 0.13;
        baseColor = lerp(baseColor, float3(0.22, 0.30, 0.105), lichen * 0.18);
        roughness = 0.78 + grains * 0.15;
        f0 = float3(0.036, 0.033, 0.030);
        materialAO = lerp(0.62, 1.0, faceUp);
    }
    else if (oceanMaterial)
    {
        waterDepth = saturate(input.surfaceData.y);
        float shoreVariation = saturate(input.surfaceData.z);
        float macro = valueNoise3(input.localPosition * 0.040 + float3(1.7, -3.4, 6.2));
        float micro = hash31(floor(input.localPosition * 0.20 + float3(-5.3, 2.1, 8.7)));
        float foamNoise = hash31(floor(input.localPosition * 0.33 + shoreVariation * 17.0));
        baseColor = lerp(float3(0.025, 0.48, 0.52), float3(0.012, 0.20, 0.34), smoothstep(0.03, 0.30, waterDepth));
        baseColor = lerp(baseColor, float3(0.004, 0.034, 0.105), smoothstep(0.28, 0.90, waterDepth));
        baseColor *= 0.93 + (macro - 0.5) * 0.10;
        baseColor += float3(0.010, 0.026, 0.036) * micro;
        float shoreBand = 1.0 - smoothstep(0.015, 0.15 + shoreVariation * 0.035, waterDepth);
        float brokenFoam = smoothstep(0.53, 0.76, foamNoise + shoreVariation * 0.11);
        foamMask = shoreBand * brokenFoam;
        baseColor = lerp(baseColor, float3(0.79, 0.92, 0.88), foamMask * 0.90);
        f0 = float3(0.0204, 0.0204, 0.0204);
        roughness = lerp(0.14, 0.050, smoothstep(0.10, 0.82, waterDepth));
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
        float transmissionShadow = lerp(shadow, 1.0, 0.28);
        direct += baseColor * float3(0.64, 0.86, 0.16)
            * backLit * (0.09 + 0.16 * edgeLit) * daylight * transmissionShadow;
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

    color = toneMapFilmic(color);
    float luminance = dot(color, float3(0.2126, 0.7152, 0.0722));
    color = lerp(luminance.xxx, color, 1.11);
    color = pow(saturate(color), float3(0.94, 0.94, 0.94));
    return float4(color, 1.0);
}
