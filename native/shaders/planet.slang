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
    // Backward-compatible channel: literal RGB for proxies/debug, packed procedural surface data
    // for primary terrain, bark, foliage, rocks and ocean.
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
    // Quaternion packed as xyz = vector part, w = scalar part.
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

float noise3(float3 p)
{
    float3 i = floor(p);
    float3 f = frac(p);
    f = f * f * (3.0 - 2.0 * f);

    float n000 = hash31(i + float3(0.0, 0.0, 0.0));
    float n100 = hash31(i + float3(1.0, 0.0, 0.0));
    float n010 = hash31(i + float3(0.0, 1.0, 0.0));
    float n110 = hash31(i + float3(1.0, 1.0, 0.0));
    float n001 = hash31(i + float3(0.0, 0.0, 1.0));
    float n101 = hash31(i + float3(1.0, 0.0, 1.0));
    float n011 = hash31(i + float3(0.0, 1.0, 1.0));
    float n111 = hash31(i + float3(1.0, 1.0, 1.0));

    float x00 = lerp(n000, n100, f.x);
    float x10 = lerp(n010, n110, f.x);
    float x01 = lerp(n001, n101, f.x);
    float x11 = lerp(n011, n111, f.x);
    return lerp(lerp(x00, x10, f.y), lerp(x01, x11, f.y), f.z);
}

float fbm3(float3 p)
{
    float value = 0.0;
    float amplitude = 0.5;
    float normalization = 0.0;
    [unroll]
    for (int octave = 0; octave < 4; ++octave)
    {
        value += noise3(p) * amplitude;
        normalization += amplitude;
        p = p * 2.03 + float3(11.7, -7.3, 5.1);
        amplitude *= 0.5;
    }
    return value / normalization;
}

float voronoiEdge(float2 p)
{
    float2 cell = floor(p);
    float2 f = frac(p);
    float nearest = 10.0;
    float second = 10.0;
    [unroll]
    for (int y = -1; y <= 1; ++y)
    {
        [unroll]
        for (int x = -1; x <= 1; ++x)
        {
            float2 g = float2((float)x, (float)y);
            float h = hash21(cell + g);
            float2 offset = 0.5 + 0.38 * float2(cos(h * 6.2831853), sin(h * 6.2831853));
            float distanceToCell = length(g + offset - f);
            if (distanceToCell < nearest)
            {
                second = nearest;
                nearest = distanceToCell;
            }
            else if (distanceToCell < second)
            {
                second = distanceToCell;
            }
        }
    }
    return second - nearest;
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
    float localRadius2 = dot(input.localPosition, input.localPosition);
    float3 surfaceUp = localRadius2 > 1.0e-8
        ? normalize(rotateByQuaternion(input.localPosition, gPush.objectRotation))
        : float3(0.0, 1.0, 0.0);

    float3 baseColor = input.surfaceData;
    float roughness = 0.62;
    float3 f0 = float3(0.04, 0.04, 0.04);
    float foamMask = 0.0;
    float waterDepth = 0.0;

    if (terrainMaterial)
    {
        float normalizedHeight = input.surfaceData.y;
        float moisture = saturate(input.surfaceData.z);
        float temperature = saturate((marker - 1.25) / 0.35);
        float slope = 1.0 - saturate(dot(n, surfaceUp));

        float macro = fbm3(input.localPosition * 0.024 + float3(3.2, -5.7, 1.9));
        float meso = fbm3(input.localPosition * 0.090 + float3(-7.1, 2.3, 4.8));
        float mineral = fbm3(input.localPosition * 0.26 + float3(4.0, 8.0, -6.0));

        float3 dryGrass = float3(0.25, 0.32, 0.12);
        float3 meadow = float3(0.16, 0.43, 0.10);
        float3 lushGrass = float3(0.08, 0.36, 0.075);
        float3 soil = float3(0.31, 0.22, 0.105);
        float3 stone = float3(0.34, 0.33, 0.29);
        float3 coldStone = float3(0.42, 0.44, 0.43);
        float3 snow = float3(0.72, 0.76, 0.73);

        float3 grass = lerp(dryGrass, lushGrass, moisture);
        grass = lerp(grass, meadow, saturate((temperature - 0.35) * 1.5));
        grass *= 0.88 + macro * 0.20;

        float soilMask = saturate(smoothstep(0.17, 0.48, normalizedHeight) * (0.65 - moisture * 0.25));
        float rockMask = saturate(
            smoothstep(0.07, 0.36, slope)
            + smoothstep(0.38, 0.68, normalizedHeight) * 0.75
            + max(0.0, meso - 0.70) * 0.70);
        float snowMask = smoothstep(0.58, 0.84, normalizedHeight)
            * (1.0 - smoothstep(0.22, 0.62, temperature));

        baseColor = lerp(grass, soil * (0.88 + meso * 0.18), soilMask);
        baseColor = lerp(baseColor, lerp(stone, coldStone, 1.0 - temperature), saturate(rockMask));
        baseColor = lerp(baseColor, snow * (0.92 + mineral * 0.10), saturate(snowMask));
        baseColor *= 0.94 + (mineral - 0.5) * 0.08;
        roughness = lerp(0.94, 0.84, saturate(rockMask));
        f0 = float3(0.028, 0.030, 0.028);
    }
    else if (barkMaterial)
    {
        float u = input.surfaceData.y;
        float vCoord = input.surfaceData.z;
        float warp = fbm3(float3(u * 4.0, vCoord * 0.55, input.localPosition.z * 0.08));
        float fibre = 0.5 + 0.5 * sin((u + (warp - 0.5) * 0.045) * 6.2831853 * 7.0);
        float fissureDistance = voronoiEdge(float2(u * 5.2, vCoord * 0.82 + warp * 0.30));
        float fissure = 1.0 - smoothstep(0.025, 0.10, fissureDistance);
        float micro = fbm3(float3(u * 22.0, vCoord * 3.4, 7.3));

        float3 darkBark = float3(0.060, 0.020, 0.006);
        float3 bark = float3(0.28, 0.105, 0.022);
        float3 warmRidge = float3(0.42, 0.205, 0.055);
        baseColor = lerp(darkBark, bark, 0.44 + 0.56 * warp);
        baseColor = lerp(baseColor, warmRidge, fibre * 0.12);
        baseColor *= 1.0 - fissure * 0.34;
        baseColor *= 0.94 + micro * 0.09;
        roughness = saturate(0.72 + fissure * 0.13 + micro * 0.08);
        f0 = float3(0.025, 0.022, 0.018);
    }
    else if (foliageMaterial)
    {
        float variation = input.surfaceData.y;
        float canopyHeight = input.surfaceData.z;
        float macro = fbm3(input.localPosition * 0.22 + variation * 11.0);
        float micro = fbm3(input.localPosition * 0.75 + float3(3.0, -2.0, 9.0));
        float upFacing = saturate(dot(n, surfaceUp) * 0.5 + 0.5);

        float3 deepGreen = float3(0.025, 0.155, 0.020);
        float3 leafGreen = float3(0.095, 0.36, 0.040);
        float3 sunGreen = float3(0.32, 0.53, 0.085);
        baseColor = lerp(deepGreen, leafGreen, 0.40 + 0.60 * macro);
        baseColor = lerp(baseColor, sunGreen, upFacing * (0.12 + canopyHeight * 0.14));
        baseColor *= 0.94 + (micro - 0.5) * 0.08;
        roughness = 0.91;
        f0 = float3(0.022, 0.025, 0.018);
    }
    else if (rockMaterial)
    {
        float variation = input.surfaceData.y;
        float strataCoord = input.surfaceData.z;
        float macro = fbm3(input.localPosition * (0.15 + variation * 0.05) + variation * 17.0);
        float grains = fbm3(input.localPosition * 0.65 + float3(5.0, -7.0, 3.0));
        float strata = 0.5 + 0.5 * sin(strataCoord * 5.2 + macro * 2.6);
        float lichen = smoothstep(0.73, 0.88, fbm3(input.localPosition * 0.31 + float3(-8.0, 2.0, 4.0)))
            * saturate(dot(n, surfaceUp) * 0.65 + 0.35);

        float3 coolRock = float3(0.29, 0.30, 0.285);
        float3 warmRock = float3(0.37, 0.30, 0.22);
        float3 darkSeam = float3(0.19, 0.17, 0.14);
        baseColor = lerp(coolRock, warmRock, variation * 0.55 + macro * 0.35);
        baseColor = lerp(baseColor, darkSeam, (1.0 - strata) * 0.14);
        baseColor *= 0.92 + grains * 0.12;
        baseColor = lerp(baseColor, float3(0.25, 0.34, 0.12), lichen * 0.18);
        roughness = 0.88 + grains * 0.06;
        f0 = float3(0.032, 0.030, 0.028);
    }
    else if (oceanMaterial)
    {
        waterDepth = saturate(input.surfaceData.y);
        float shoreVariation = saturate(input.surfaceData.z);
        float macro = fbm3(input.localPosition * 0.045 + float3(1.7, -3.4, 6.2));
        float micro = fbm3(input.localPosition * 0.19 + float3(-5.3, 2.1, 8.7));
        float foamNoise = fbm3(input.localPosition * 0.31 + shoreVariation * 13.0);

        float3 shallows = float3(0.055, 0.47, 0.50);
        float3 shelf = float3(0.025, 0.255, 0.37);
        float3 deep = float3(0.010, 0.075, 0.155);
        baseColor = lerp(shallows, shelf, smoothstep(0.04, 0.34, waterDepth));
        baseColor = lerp(baseColor, deep, smoothstep(0.30, 0.92, waterDepth));
        baseColor *= 0.94 + (macro - 0.5) * 0.10;
        baseColor += float3(0.015, 0.035, 0.045) * micro;

        float shoreBand = 1.0 - smoothstep(0.018, 0.16 + shoreVariation * 0.035, waterDepth);
        float brokenFoam = smoothstep(0.47, 0.70, foamNoise + shoreVariation * 0.12);
        foamMask = shoreBand * brokenFoam;
        baseColor = lerp(baseColor, float3(0.72, 0.88, 0.86), foamMask * 0.82);

        // Water IOR ~1.333 => normal-incidence dielectric reflectance near 0.020.
        f0 = float3(0.0204, 0.0204, 0.0204);
        roughness = lerp(0.22, 0.13, smoothstep(0.12, 0.85, waterDepth));
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

    float3 stellarRadiance = max(gPush.sunColorIntensity.rgb, 0.0)
        * max(gPush.sunColorIntensity.a, 0.0);
    float3 direct = (diffuse + specular) * noL * stellarRadiance;

    float hemi = proceduralMaterial
        ? (0.030 + 0.018 * saturate(dot(n, surfaceUp) * 0.5 + 0.5))
        : 0.012;
    float3 indirect = max(baseColor, 0.0) * hemi;

    if (oceanMaterial)
    {
        // Stylized Fresnel reflection without a reflection texture: grazing facets lift toward a
        // cool sky tint while the real star still drives the GGX glint. This keeps the material
        // texture-free and makes the large low-poly planes readable at distance.
        float grazing = pow(1.0 - noV, 4.0);
        float3 skyReflection = float3(0.10, 0.23, 0.30) * (0.35 + 0.65 * grazing);
        float3 deepFill = baseColor * (0.15 + 0.09 * waterDepth);
        float3 foamLight = float3(0.26, 0.31, 0.28) * foamMask * (0.45 + 0.55 * noL);
        return float4(direct + indirect + skyReflection + deepFill + foamLight, 1.0);
    }

    return float4(direct + indirect, 1.0);
}
