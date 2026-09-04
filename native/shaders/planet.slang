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
static const float PI = 3.14159265358979323846;

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
    float3 sky = lerp(float3(0.010, 0.018, 0.035), float3(0.23, 0.48, 0.72), daylight);
    sky = lerp(sky, float3(0.62, 0.31, 0.16), twilight * (1.0 - daylight * 0.55));
    return lerp(float3(0.015, 0.020, 0.028), sky, density);
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

        float3 dryGrass = float3(0.25, 0.32, 0.12);
        float3 meadow = float3(0.16, 0.43, 0.10);
        float3 lushGrass = float3(0.08, 0.36, 0.075);
        float3 soil = float3(0.31, 0.22, 0.105);
        float3 stone = float3(0.34, 0.33, 0.29);
        float3 coldStone = float3(0.42, 0.44, 0.43);
        float3 snow = float3(0.72, 0.76, 0.73);

        float3 grass = lerp(dryGrass, lushGrass, moisture);
        grass = lerp(grass, meadow, saturate((temperature - 0.35) * 1.5));
        grass *= 0.90 + macro * 0.17;
        float soilMask = saturate(smoothstep(0.17, 0.48, normalizedHeight) * (0.65 - moisture * 0.25));
        float rockMask = saturate(smoothstep(0.07, 0.36, slope)
            + smoothstep(0.38, 0.68, normalizedHeight) * 0.75
            + max(0.0, meso - 0.76) * 0.55);
        float snowMask = smoothstep(0.58, 0.84, normalizedHeight)
            * (1.0 - smoothstep(0.22, 0.62, temperature));

        baseColor = lerp(grass, soil * (0.90 + meso * 0.14), soilMask);
        baseColor = lerp(baseColor, lerp(stone, coldStone, 1.0 - temperature), rockMask);
        baseColor = lerp(baseColor, snow * (0.94 + mineral * 0.07), snowMask);
        baseColor *= 0.96 + (mineral - 0.5) * 0.06;
        roughness = lerp(0.95, 0.82, rockMask);
        f0 = float3(0.028, 0.030, 0.028);
        materialAO = lerp(0.78, 1.0, faceUp);
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
        baseColor = lerp(float3(0.060, 0.020, 0.006), float3(0.28, 0.105, 0.022), 0.45 + 0.48 * warp);
        baseColor = lerp(baseColor, float3(0.42, 0.205, 0.055), fibre * 0.11);
        baseColor *= (1.0 - fissure * 0.27) * (0.96 + micro * 0.06);
        roughness = saturate(0.78 + fissure * 0.10 + micro * 0.05);
        f0 = float3(0.024, 0.021, 0.017);
        materialAO = 0.82 - fissure * 0.12;
    }
    else if (foliageMaterial)
    {
        float variation = input.surfaceData.y;
        float canopyHeight = saturate(input.surfaceData.z);
        float macro = valueNoise3(input.localPosition * 0.18 + variation * 9.0);
        float faceBreakup = hash31(floor(n * 17.0 + variation * 29.0));
        float upFacing = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
        baseColor = lerp(float3(0.022, 0.135, 0.018), float3(0.085, 0.34, 0.036), 0.42 + 0.50 * macro);
        baseColor = lerp(baseColor, float3(0.36, 0.56, 0.10), upFacing * (0.12 + canopyHeight * 0.15));
        baseColor *= 0.96 + (faceBreakup - 0.5) * 0.07;
        roughness = 0.91;
        f0 = float3(0.021, 0.024, 0.017);
        materialAO = lerp(0.56, 0.94, canopyHeight) * lerp(0.84, 1.0, upFacing);
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
        baseColor = lerp(float3(0.28, 0.30, 0.30), float3(0.39, 0.31, 0.22), variation * 0.52 + macro * 0.34);
        baseColor = lerp(baseColor, float3(0.18, 0.16, 0.13), (1.0 - strata) * 0.13);
        baseColor *= 0.94 + grains * 0.09;
        baseColor = lerp(baseColor, float3(0.25, 0.34, 0.12), lichen * 0.16);
        roughness = 0.84 + grains * 0.11;
        f0 = float3(0.034, 0.032, 0.029);
        materialAO = lerp(0.72, 1.0, faceUp);
    }
    else if (oceanMaterial)
    {
        waterDepth = saturate(input.surfaceData.y);
        float shoreVariation = saturate(input.surfaceData.z);
        float macro = valueNoise3(input.localPosition * 0.040 + float3(1.7, -3.4, 6.2));
        float micro = hash31(floor(input.localPosition * 0.20 + float3(-5.3, 2.1, 8.7)));
        float foamNoise = hash31(floor(input.localPosition * 0.33 + shoreVariation * 17.0));
        baseColor = lerp(float3(0.040, 0.42, 0.46), float3(0.020, 0.22, 0.34), smoothstep(0.04, 0.34, waterDepth));
        baseColor = lerp(baseColor, float3(0.008, 0.050, 0.125), smoothstep(0.30, 0.92, waterDepth));
        baseColor *= 0.95 + (macro - 0.5) * 0.08;
        baseColor += float3(0.010, 0.024, 0.032) * micro;
        float shoreBand = 1.0 - smoothstep(0.018, 0.16 + shoreVariation * 0.035, waterDepth);
        float brokenFoam = smoothstep(0.56, 0.78, foamNoise + shoreVariation * 0.10);
        foamMask = shoreBand * brokenFoam;
        baseColor = lerp(baseColor, float3(0.72, 0.88, 0.86), foamMask * 0.82);
        f0 = float3(0.0204, 0.0204, 0.0204);
        roughness = lerp(0.18, 0.075, smoothstep(0.12, 0.85, waterDepth));
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

    // Derive the atmosphere from geometry instead of adding uniforms/descriptors.
    float cameraRadius = length(gPush.cameraPosition.xyz);
    float cameraAltitude = max(0.0, cameraRadius - localRadius);
    float atmosphereDensity = proceduralMaterial ? exp(-cameraAltitude / 72.0) : 0.0;
    float solarElevation = dot(surfaceUp, l);
    float daylight = smoothstep(-0.10, 0.16, solarElevation);
    float twilight = saturate(1.0 - abs(solarElevation + 0.04) / 0.22);
    float3 skyColor = atmosphereSky(solarElevation, atmosphereDensity);
    float3 horizonColor = lerp(float3(0.16, 0.24, 0.31), float3(0.78, 0.40, 0.20), twilight * 0.72);
    horizonColor = lerp(float3(0.03, 0.045, 0.065), horizonColor, atmosphereDensity);

    float3 stellarRadiance = max(gPush.sunColorIntensity.rgb, 0.0) * max(gPush.sunColorIntensity.a, 0.0);
    stellarRadiance *= lerp(float3(1.0, 0.56, 0.32), float3(1.0, 0.96, 0.88), daylight);
    float3 direct = (diffuse + specular) * noL * stellarRadiance;

    float hemiUp = saturate(dot(n, surfaceUp) * 0.5 + 0.5);
    float3 skyAmbient = skyColor * (0.16 + 0.34 * hemiUp);
    float3 groundBounceColor = float3(0.18, 0.15, 0.085);
    if (terrainMaterial || foliageMaterial) groundBounceColor = float3(0.12, 0.20, 0.065);
    if (oceanMaterial) groundBounceColor = float3(0.025, 0.08, 0.11);
    float3 indirect = max(baseColor, 0.0)
        * (skyAmbient + groundBounceColor * (0.05 + 0.16 * (1.0 - hemiUp)))
        * materialAO;

    if (foliageTransmission > 0.0)
    {
        float backLit = saturate(dot(-n, l));
        float edgeLit = pow(1.0 - noV, 2.0);
        direct += baseColor * float3(0.50, 0.78, 0.18)
            * backLit * (0.08 + 0.14 * edgeLit) * daylight;
    }

    float3 color = direct + indirect;
    if (oceanMaterial)
    {
        float grazing = pow(1.0 - noV, 4.0);
        float3 reflectedSky = lerp(horizonColor, skyColor, 0.38 + 0.62 * hemiUp);
        color += reflectedSky * (0.12 + 0.88 * grazing);
        color += baseColor * (0.11 + 0.10 * waterDepth);
        color += float3(0.42, 0.49, 0.44) * foamMask * (0.40 + 0.60 * noL);
    }

    // Cheap analytic mist: no volume texture, no ray march and no extra render pass.
    if (proceduralMaterial)
    {
        float viewDistance = length(input.relativePosition);
        float3 viewRay = normalize(input.relativePosition);
        float horizonView = 1.0 - saturate(abs(dot(viewRay, surfaceUp)));
        float fogDistance = 1.0 - exp(-viewDistance * 0.0034 * atmosphereDensity);
        float fogFactor = saturate(fogDistance * (0.62 + 0.38 * horizonView * horizonView));
        float3 fogColor = lerp(skyColor, horizonColor, 0.55 + 0.35 * horizonView);
        color = lerp(color, fogColor, fogFactor * 0.88);
    }

    color = toneMapFilmic(color);
    float luminance = dot(color, float3(0.2126, 0.7152, 0.0722));
    color = lerp(luminance.xxx, color, 1.06);
    color = pow(saturate(color), float3(0.96, 0.96, 0.96));
    return float4(color, 1.0);
}
