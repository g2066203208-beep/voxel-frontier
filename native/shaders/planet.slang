struct VertexInput
{
    float3 position : POSITION;
    float3 normal : NORMAL;
    float3 color : COLOR0;
    float4 material : TEXCOORD0;
};

struct VertexOutput
{
    float4 position : SV_Position;
    float3 normal : TEXCOORD0;
    float3 color : TEXCOORD1;
    float4 material : TEXCOORD2;
    float3 relativePosition : TEXCOORD3;
    float4 shadowPosition : TEXCOORD4;
};

struct ShadowVertexOutput
{
    float4 position : SV_Position;
    float transmission : TEXCOORD0;
    float emissive : TEXCOORD1;
};

struct FullscreenOutput
{
    float4 position : SV_Position;
    float2 uv : TEXCOORD0;
};

struct PushConstants
{
    float4x4 matrix;
    float4 data0;
    float4 data1;
    float4 data2;
    float4 data3;
};

struct SceneUniforms
{
    float4x4 lightViewProjection;
    float4 skyAmbientExposure;
    float4 groundAmbientShadowTexel;
};

[[vk::push_constant]] ConstantBuffer<PushConstants> gPush;
[[vk::binding(0, 0)]] ConstantBuffer<SceneUniforms> gScene;
[[vk::binding(1, 0)]] Texture2D<float> gShadowMap;
[[vk::binding(2, 0)]] SamplerState gShadowSampler;

static const float PI = 3.14159265358979323846;

float3 rotateByQuaternion(float3 v, float4 q)
{
    float3 t = 2.0 * cross(q.xyz, v);
    return v + q.w * t + cross(q.xyz, t);
}

float distributionGGX(float noH, float roughness)
{
    float a = max(roughness * roughness, 0.0025);
    float a2 = a * a;
    float d = noH * noH * (a2 - 1.0) + 1.0;
    return a2 / max(PI * d * d, 1.0e-6);
}

float geometrySchlickGGX(float noX, float roughness)
{
    float r = roughness + 1.0;
    float k = r * r * 0.125;
    return noX / max(noX * (1.0 - k) + k, 1.0e-5);
}

float3 fresnelSchlick(float cosTheta, float3 f0)
{
    float grazing = pow(1.0 - saturate(cosTheta), 5.0);
    return f0 + (1.0 - f0) * grazing;
}

float3 acesFitted(float3 x)
{
    float3 a = x * (2.51 * x + 0.03);
    float3 b = x * (2.43 * x + 0.59) + 0.14;
    return saturate(a / max(b, 1.0e-5));
}

float luminance709(float3 color)
{
    return dot(color, float3(0.2126, 0.7152, 0.0722));
}

// Procedural art direction only: no LUT, texture, HDRI or authored palette asset.
// The structure follows the lesson from SNOWFLOW's public aerial-perspective implementation:
// distance reduces contrast, hue converges toward the sky, and the sun-facing horizon warms.
float3 stylizedSkyPalette(float3 viewDir, float3 sunDir)
{
    viewDir = normalize(viewDir);
    sunDir = normalize(sunDir);
    float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.65);
    float zenith = saturate(viewDir.y * 0.88 + 0.12);
    float sunFacing = pow(saturate(dot(viewDir, sunDir)), 4.0);
    float lowSun = 1.0 - smoothstep(0.22, 0.68, sunDir.y);
    float daylight = smoothstep(-0.12, 0.16, sunDir.y);

    float3 nightZenith = float3(0.018, 0.027, 0.060);
    float3 nightHorizon = float3(0.075, 0.070, 0.115);
    float3 dayZenith = float3(0.18, 0.43, 0.72);
    float3 dayHorizon = float3(0.62, 0.69, 0.72);
    float3 zenithColor = lerp(nightZenith, dayZenith, daylight);
    float3 horizonColor = lerp(nightHorizon, dayHorizon, daylight);
    float3 color = lerp(horizonColor, zenithColor, zenith);

    float3 sunset = float3(1.00, 0.43, 0.20);
    float warm = horizon * sunFacing * lowSun * smoothstep(-0.18, 0.12, sunDir.y);
    return lerp(color, sunset, saturate(warm * 0.92));
}

float3 stylizedWarmCoolGrade(float3 color)
{
    color = max(color, 0.0);
    float y = luminance709(color);
    float3 saturated = lerp(float3(y, y, y), color, 1.14);
    float highlight = smoothstep(0.20, 0.82, y);
    float3 coolShadow = float3(0.91, 0.98, 1.10);
    float3 warmLight = float3(1.07, 1.015, 0.93);
    return max(saturated * lerp(coolShadow, warmLight, highlight), 0.0);
}

float3 applyStylizedAerial(float3 color, VertexOutput input, float strength)
{
    float distanceMeters = length(input.relativePosition);
    if (distanceMeters <= 350.0 || strength <= 0.0) return color;

    float3 viewDir = input.relativePosition / max(distanceMeters, 1.0e-4);
    float3 sunDir = normalize(gPush.data1.xyz);
    float cameraAltitude = max(gPush.data0.y, 0.0);

    // Near-surface haze is strong; it naturally disappears as the camera leaves the atmosphere.
    // Clamp the path because the physical atmosphere has finite thickness: a star millions of
    // kilometres away should not accumulate millions of kilometres of ground fog.
    float atmospherePresence = exp(-cameraAltitude / 90000.0);
    float effectiveDistance = min(max(distanceMeters - 350.0, 0.0), 180000.0);
    float horizon = pow(saturate(1.0 - abs(viewDir.y)), 1.35);
    float density = 2.25e-5 * (0.30 + 0.70 * horizon);
    float extinction = 1.0 - exp(-effectiveDistance * density);
    extinction = saturate(extinction * atmospherePresence * strength);

    float3 haze = stylizedSkyPalette(viewDir, sunDir);
    return lerp(color, haze, extinction);
}

float hash21(float2 p)
{
    float3 p3 = frac(float3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return frac((p3.x + p3.y) * p3.z);
}

float hash31(float3 p)
{
    p = frac(p * 0.1031);
    p += dot(p, p.yzx + 33.33);
    return frac((p.x + p.y) * p.z);
}

[shader("vertex")]
VertexOutput vertexMain(VertexInput input)
{
    VertexOutput output;
    float3 worldPosition = rotateByQuaternion(input.position, gPush.data3);
    float3 worldNormal = normalize(rotateByQuaternion(input.normal, gPush.data3));
    float3 relativePosition = worldPosition - gPush.data0.xyz;
    output.position = mul(gPush.matrix, float4(relativePosition, 1.0));
    output.relativePosition = relativePosition;
    output.normal = worldNormal;
    output.color = input.color;
    output.material = input.material;
    output.shadowPosition = mul(gScene.lightViewProjection, float4(relativePosition, 1.0));
    return output;
}

[shader("vertex")]
ShadowVertexOutput shadowVertexMain(VertexInput input)
{
    ShadowVertexOutput output;
    float3 worldPosition = rotateByQuaternion(input.position, gPush.data3);
    float3 relativePosition = worldPosition - gPush.data0.xyz;
    output.position = mul(gPush.matrix, float4(relativePosition, 1.0));
    output.transmission = input.material.z;
    output.emissive = input.material.w;
    return output;
}

[shader("fragment")]
void shadowFragmentMain(ShadowVertexOutput input)
{
    if (input.transmission > 0.02 || input.emissive > 0.5) discard;
}

float shadowVisibility(float4 lightClip, float noL)
{
    if (lightClip.w <= 0.0) return 1.0;
    float3 ndc = lightClip.xyz / lightClip.w;
    float2 uv = ndc.xy * 0.5 + 0.5;
    if (any(uv < 0.0) || any(uv > 1.0) || ndc.z < 0.0 || ndc.z > 1.0) return 1.0;

    float texel = max(gScene.groundAmbientShadowTexel.w, 1.0 / 4096.0);
    float bias = max(0.00025, 0.0012 * (1.0 - noL));
    float visible = 0.0;
    [unroll]
    for (int y = -1; y <= 1; ++y)
    {
        [unroll]
        for (int x = -1; x <= 1; ++x)
        {
            float stored = gShadowMap.SampleLevel(gShadowSampler, uv + float2(x, y) * texel, 0.0);
            visible += ndc.z - bias <= stored ? 1.0 : 0.0;
        }
    }
    return visible / 9.0;
}

float3 evaluatePbr(VertexOutput input, bool transparent)
{
    float3 n = normalize(input.normal);
    float3 l = normalize(gPush.data1.xyz);
    float3 v = normalize(-input.relativePosition);
    float3 h = normalize(l + v);

    float metallic = saturate(input.material.x);
    float roughness = clamp(input.material.y, 0.045, 1.0);
    float transmission = saturate(input.material.z);
    float emissive = max(input.material.w, 0.0);
    float3 baseColor = max(input.color, 0.0);

    float noL = saturate(dot(n, l));
    float noV = max(saturate(dot(n, v)), 1.0e-4);
    float noH = saturate(dot(n, h));
    float voH = saturate(dot(v, h));

    float3 f0 = lerp(float3(0.04, 0.04, 0.04), baseColor, metallic);
    float3 f = fresnelSchlick(voH, f0);
    float d = distributionGGX(noH, roughness);
    float g = geometrySchlickGGX(noV, roughness) * geometrySchlickGGX(noL, roughness);
    float3 specular = d * g * f / max(4.0 * noV * max(noL, 1.0e-4), 1.0e-4);
    float3 kd = (1.0 - f) * (1.0 - metallic) * (1.0 - transmission);
    float3 diffuse = kd * baseColor / PI;

    float shadow = shadowVisibility(input.shadowPosition, noL);
    float3 stellar = max(gPush.data2.rgb, 0.0) * max(gPush.data2.a, 0.0);
    float3 direct = (diffuse + specular) * noL * stellar * shadow;

    float skyWeight = saturate(n.y * 0.5 + 0.5);
    float3 skyIrradiance = max(gScene.skyAmbientExposure.rgb, 0.0) * (0.28 + 0.72 * skyWeight);
    float3 groundIrradiance = max(gScene.groundAmbientShadowTexel.rgb, 0.0)
        * saturate(-n.y * 0.5 + 0.5);
    float3 ambientDiffuse = baseColor * (skyIrradiance + groundIrradiance) * (1.0 - metallic) * (1.0 - transmission);

    float3 r = reflect(-v, n);
    float reflectionSky = saturate(r.y * 0.5 + 0.5);
    float3 reflectionColor = lerp(
        max(gScene.groundAmbientShadowTexel.rgb, float3(0.004, 0.004, 0.004)),
        max(gScene.skyAmbientExposure.rgb, float3(0.008, 0.012, 0.02)),
        reflectionSky);
    float3 ambientSpecular = reflectionColor * f * (1.0 - 0.72 * roughness);

    if (transparent)
    {
        float cosV = max(abs(dot(n, v)), 0.12);
        float path = 1.0 / cosV;
        float3 absorption = max(0.04, 1.0 - baseColor) * 0.72;
        float3 transmittance = exp(-absorption * path);
        float fresnelAmount = saturate(max(f.x, max(f.y, f.z)));
        float3 glassLighting = ambientSpecular * 2.2 + direct * 0.18;
        glassLighting += baseColor * 0.018;
        glassLighting += transmittance * (1.0 - fresnelAmount) * 0.08;
        return glassLighting;
    }

    return direct + ambientDiffuse + ambientSpecular + baseColor * emissive;
}

[shader("fragment")]
float4 opaqueFragmentMain(VertexOutput input) : SV_Target
{
    if (input.material.z > 0.02) discard;
    float exposure = max(gScene.skyAmbientExposure.a, 0.01);
    float3 linearColor = evaluatePbr(input, false) * exposure;
    linearColor = applyStylizedAerial(linearColor, input, 1.0);
    linearColor = stylizedWarmCoolGrade(linearColor);
    return float4(acesFitted(linearColor), 1.0);
}

[shader("fragment")]
float4 transparentFragmentMain(VertexOutput input) : SV_Target
{
    float transmission = saturate(input.material.z);
    if (transmission <= 0.02) discard;

    float3 n = normalize(input.normal);
    float3 v = normalize(-input.relativePosition);
    float ior = 1.50;
    float f0Scalar = ((ior - 1.0) / (ior + 1.0));
    f0Scalar *= f0Scalar;
    float fresnel = f0Scalar + (1.0 - f0Scalar) * pow(1.0 - saturate(abs(dot(n, v))), 5.0);
    float opticalOpacity = saturate((1.0 - transmission) * 0.48 + fresnel * 0.72 + 0.025);

    float exposure = max(gScene.skyAmbientExposure.a, 0.01);
    float3 linearColor = evaluatePbr(input, true) * exposure;
    linearColor = applyStylizedAerial(linearColor, input, 0.46);
    float3 color = acesFitted(stylizedWarmCoolGrade(linearColor));
    return float4(color, opticalOpacity);
}

[shader("vertex")]
FullscreenOutput fullscreenVertexMain(uint vertexId : SV_VertexID)
{
    FullscreenOutput output;
    float2 p = vertexId == 0 ? float2(-1.0, -1.0)
        : (vertexId == 1 ? float2(3.0, -1.0) : float2(-1.0, 3.0));
    output.position = float4(p, 0.0, 1.0);
    output.uv = p * float2(0.5, -0.5) + 0.5;
    return output;
}

bool raySphere(float3 origin, float3 direction, float radius, out float nearT, out float farT)
{
    float b = dot(origin, direction);
    float c = dot(origin, origin) - radius * radius;
    float h = b * b - c;
    if (h < 0.0)
    {
        nearT = 0.0;
        farT = 0.0;
        return false;
    }
    h = sqrt(h);
    nearT = -b - h;
    farT = -b + h;
    return farT >= 0.0;
}

float densityAtRadius(float radius, float groundRadius, float scaleHeight)
{
    return exp(-max(0.0, radius - groundRadius) / max(scaleHeight, 1.0));
}

float sunOpticalDepth(float3 point, float3 sunDir, float atmosphereRadius, float groundRadius, float scaleHeight)
{
    float t0, t1;
    if (!raySphere(point, sunDir, atmosphereRadius, t0, t1)) return 0.0;
    float ground0, ground1;
    if (raySphere(point, sunDir, groundRadius, ground0, ground1) && ground1 > 0.001 && ground0 > 0.0)
        return 1.0e8;

    float stepLength = max(t1, 0.0) / 4.0;
    float opticalDepth = 0.0;
    [unroll]
    for (int i = 0; i < 4; ++i)
    {
        float t = (i + 0.5) * stepLength;
        opticalDepth += densityAtRadius(length(point + sunDir * t), groundRadius, scaleHeight) * stepLength;
    }
    return opticalDepth;
}

float3 reconstructWorldRay(float2 uv)
{
    float2 ndc = float2(uv.x * 2.0 - 1.0, 1.0 - uv.y * 2.0);
    float4 p = mul(gPush.matrix, float4(ndc, 1.0, 1.0));
    return normalize(p.xyz / max(abs(p.w), 1.0e-7));
}

float3 proceduralStars(float3 ray)
{
    float3 cell = floor(ray * 1450.0);
    float h = hash31(cell);
    float star = smoothstep(0.9968, 0.9999, h);
    float galactic = pow(saturate(1.0 - abs(ray.y * 0.72 + ray.z * 0.24)), 5.0);
    star += smoothstep(0.9982, 0.99995, hash31(cell * 0.43 + 17.0)) * galactic * 0.75;
    float temperature = hash31(cell + 91.7);
    float3 tint = lerp(float3(1.0, 0.70, 0.48), float3(0.65, 0.80, 1.0), temperature);
    return tint * star * (0.55 + 2.8 * pow(h, 24.0));
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

    if (!hitsAtmosphere)
        return float4(acesFitted(background * exposure), 1.0);

    float startT = max(atmoNear, 0.0);
    float endT = max(atmoFar, startT);
    if (hitsGround) endT = min(endT, groundNear);
    if (endT <= startT)
        return float4(acesFitted(background * exposure), 1.0);

    const float3 betaR = float3(5.802e-6, 13.558e-6, 33.100e-6);
    float betaM = 21.0e-6 * mieScale;
    float mu = dot(ray, sunDir);
    float rayleighPhase = 3.0 * (1.0 + mu * mu) / (16.0 * PI);
    float g = 0.76;
    float miePhase = (1.0 - g * g)
        / max(4.0 * PI * pow(1.0 + g * g - 2.0 * g * mu, 1.5), 1.0e-5);

    float segment = (endT - startT) / 8.0;
    float opticalView = 0.0;
    float3 scattering = 0.0;
    float3 transmittance = 1.0;
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

    transmittance = exp(-(betaR + betaM) * opticalView);
    float3 color = scattering * 17.0;
    if (!hitsGround) color += background * transmittance;
    else color += float3(0.008, 0.009, 0.007) * transmittance;

    // Preserve the physically coherent scattering result, then art-direct only the dense lower
    // atmosphere. The weight naturally vanishes in high atmosphere/space, so orbital views keep
    // their real black-space contrast while ground scenes gain Firewatch-like readable layers.
    float localDensity = densityAtRadius(length(cameraPlanet), groundRadius, scaleHeight);
    float styleWeight = saturate(localDensity * 0.38);
    color = lerp(color, stylizedSkyPalette(ray, sunDir), styleWeight);

    return float4(acesFitted(stylizedWarmCoolGrade(color) * exposure), 1.0);
}

[shader("fragment")]
float4 hudFragmentMain(FullscreenOutput input) : SV_Target
{
    float2 sizePx = max(gPush.data0.xy, float2(1.0, 1.0));
    float2 p = input.position.xy - sizePx * 0.5;
    float2 ap = abs(p);

    float crossHorizontal = step(ap.y, 1.2) * step(4.0, ap.x) * step(ap.x, 11.0);
    float crossVertical = step(ap.x, 1.2) * step(4.0, ap.y) * step(ap.y, 11.0);
    float centerDot = 1.0 - step(1.15, length(p));
    float crosshair = saturate(crossHorizontal + crossVertical + centerDot);

    float speedNorm = saturate(gPush.data0.z);
    float2 barOrigin = float2(sizePx.x * 0.5 + 34.0, sizePx.y * 0.5 - 50.0);
    float2 bp = input.position.xy - barOrigin;
    float outline = step(abs(bp.x), 3.0) * step(abs(bp.y - 40.0), 42.0);
    float fill = step(abs(bp.x), 1.45) * step(0.0, bp.y) * step(bp.y, 80.0 * speedNorm);

    float alpha = saturate(crosshair * 0.96 + outline * 0.35 + fill * 0.85);
    float3 color = lerp(float3(0.94, 0.96, 1.0), float3(0.42, 0.78, 1.0), fill);
    return float4(color, alpha);
}
