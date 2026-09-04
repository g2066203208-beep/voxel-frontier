struct VertexInput
{
    float3 position : POSITION;
    float3 normal : NORMAL;
    float3 color : COLOR0;
    // x=metallic, y=roughness, z=transmission, w=emissive strength.
    float4 material : TEXCOORD0;
};

struct VertexOutput
{
    float4 position : SV_Position;
    float3 normal : TEXCOORD0;
    float3 color : TEXCOORD1;
    float3 relativePosition : TEXCOORD2;
    float4 material : TEXCOORD3;
};

struct ShadowVertexOutput
{
    float4 position : SV_Position;
    float skipOccluder : TEXCOORD0;
};

struct PushConstants
{
    float4x4 viewProj;
    float4 cameraPosition;
    float4 sunDirection;
    float4 sunColorIntensity;
    float4 objectRotation;
};

struct ShadowUniforms
{
    // Transforms camera-relative surface-space positions into the directional light clip space.
    float4x4 lightViewProj;
};

[[vk::push_constant]] ConstantBuffer<PushConstants> gPush;
[[vk::binding(0, 0)]] Texture2D<float> gShadowMap;
[[vk::binding(1, 0)]] SamplerState gShadowSampler;
[[vk::binding(2, 0)]] ConstantBuffer<ShadowUniforms> gShadow;

static const float PI = 3.14159265358979323846;
static const float SHADOW_TEXEL = 1.0 / 1536.0;

float3 rotateByQuaternion(float3 v, float4 q)
{
    float3 t = 2.0 * cross(q.xyz, v);
    return v + q.w * t + cross(q.xyz, t);
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

float screenDoorNoise(float2 pixel)
{
    float2 p = floor(pixel);
    return frac(sin(dot(p, float2(12.9898, 78.233))) * 43758.5453);
}

float shadowVisibility(float3 relativePosition, float3 normal, float3 lightDirection)
{
    float4 clip = mul(gShadow.lightViewProj, float4(relativePosition, 1.0));
    if (clip.w <= 1.0e-6) return 1.0;
    float3 ndc = clip.xyz / clip.w;
    float2 uv = ndc.xy * 0.5 + 0.5;
    if (uv.x <= 0.0 || uv.x >= 1.0 || uv.y <= 0.0 || uv.y >= 1.0 || ndc.z <= 0.0 || ndc.z >= 1.0)
        return 1.0;

    float noL = saturate(dot(normal, lightDirection));
    float bias = max(0.00010, 0.00065 * (1.0 - noL));
    float currentDepth = ndc.z - bias;
    float visibility = 0.0;
    const float2 offsets[4] = {
        float2(-0.5, -0.5), float2(0.5, -0.5),
        float2(-0.5, 0.5), float2(0.5, 0.5)
    };
    [unroll]
    for (int i = 0; i < 4; ++i)
    {
        float storedDepth = gShadowMap.SampleLevel(gShadowSampler, uv + offsets[i] * SHADOW_TEXEL, 0.0);
        visibility += currentDepth <= storedDepth ? 1.0 : 0.0;
    }
    return visibility * 0.25;
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
    output.normal = worldNormal;
    output.color = input.color;
    output.material = input.material;
    return output;
}

[shader("vertex")]
ShadowVertexOutput shadowVertexMain(VertexInput input)
{
    ShadowVertexOutput output;
    float3 worldPosition = rotateByQuaternion(input.position, gPush.objectRotation);
    float3 relativePosition = worldPosition - gPush.cameraPosition.xyz;
    output.position = mul(gPush.viewProj, float4(relativePosition, 1.0));
    // Atmosphere, transmissive glass and emissive HUD/celestial proxies do not block the opaque
    // directional shadow depth map. Glass gets its tinted transmission footprint separately.
    bool atmosphere = input.color.x < 0.0 || input.color.y < 0.0 || input.color.z < 0.0;
    output.skipOccluder = (atmosphere || input.material.z > 0.50 || input.material.w > 1.0) ? 1.0 : 0.0;
    return output;
}

[shader("fragment")]
void shadowFragmentMain(ShadowVertexOutput input)
{
    if (input.skipOccluder > 0.5) discard;
}

[shader("fragment")]
float4 fragmentMain(VertexOutput input) : SV_Target
{
    float3 n = normalize(input.normal);
    float3 l = normalize(gPush.sunDirection.xyz);
    float3 v = normalize(-input.relativePosition);

    if (input.color.x < 0.0 || input.color.y < 0.0 || input.color.z < 0.0)
    {
        float3 packed = max(-input.color, 0.0);
        float opticalStrength = max(max(packed.x, packed.y), packed.z);
        float3 tint = packed / max(opticalStrength, 1.0e-4);
        float grazing = pow(saturate(1.0 - abs(dot(n, v))), 0.55);
        float forwardScatter = pow(saturate(dot(l, -v) * 0.5 + 0.5), 6.0);
        float sunFacing = saturate(dot(n, l) * 0.5 + 0.5);
        float coverage = saturate(opticalStrength * (0.025 + 0.95 * grazing));
        if (screenDoorNoise(input.position.xy) > coverage) discard;
        float3 stellar = max(gPush.sunColorIntensity.rgb, 0.0)
            * max(gPush.sunColorIntensity.a, 0.0);
        float3 scatter = tint
            * (0.035 + 0.78 * grazing + 0.22 * forwardScatter)
            * (0.28 + 0.72 * sunFacing)
            * max(stellar, float3(0.06, 0.06, 0.06));
        return float4(scatter, 1.0);
    }

    float3 baseColor = saturate(input.color);
    float metallic = saturate(input.material.x);
    float roughness = clamp(input.material.y, 0.045, 1.0);
    float transmission = saturate(input.material.z);
    float emissive = max(input.material.w, 0.0);

    float3 h = normalize(l + v);
    float noL = saturate(dot(n, l));
    float noV = saturate(dot(n, v));
    float noH = saturate(dot(n, h));
    float voH = saturate(dot(v, h));

    float3 f0 = lerp(float3(0.04, 0.04, 0.04), baseColor, metallic);
    float d = distributionGGX(noH, roughness);
    float g = geometrySchlickGGX(noV, roughness) * geometrySchlickGGX(noL, roughness);
    float3 f = fresnelSchlick(voH, f0);
    float3 specular = (d * g * f) / max(4.0 * noV * max(noL, 1.0e-4), 1.0e-4);
    float3 kd = (1.0 - f) * (1.0 - metallic) * (1.0 - transmission);
    float3 diffuse = kd * baseColor / PI;

    float visibility = shadowVisibility(input.relativePosition, n, l);
    float3 stellarRadiance = max(gPush.sunColorIntensity.rgb, 0.0)
        * max(gPush.sunColorIntensity.a, 0.0);
    float3 direct = (diffuse + specular) * noL * stellarRadiance * visibility;

    // Sky hemisphere + warm ground bounce + image-based-reflection approximation. Opaque shadowing
    // only removes direct solar light; diffuse sky/ground environment remains, so shadows and
    // back-facing surfaces never collapse to featureless black.
    float skyWeight = saturate(n.y * 0.5 + 0.5);
    float3 skyRadiance = lerp(float3(0.022, 0.019, 0.016), float3(0.14, 0.22, 0.36), skyWeight);
    float3 groundBounce = float3(0.060, 0.047, 0.031) * saturate(-n.y * 0.5 + 0.5);
    float3 r = reflect(-v, n);
    float reflectionSky = saturate(r.y * 0.5 + 0.5);
    float3 reflectionColor = lerp(float3(0.036, 0.030, 0.025), float3(0.20, 0.31, 0.50), reflectionSky);
    float3 ambientDiffuse = baseColor * (skyRadiance + groundBounce) * (1.0 - metallic) * (1.0 - transmission);
    float3 ambientSpecular = reflectionColor * f * (1.0 - roughness * 0.82);

    if (transmission > 0.0)
    {
        float fresnelAmount = saturate(max(max(f.x, f.y), f.z));
        float3 transmitted = lerp(reflectionColor, skyRadiance, 0.62) * baseColor * transmission;
        float coverage = saturate(0.10 + 0.34 * fresnelAmount + 0.09 * (1.0 - transmission));
        if (screenDoorNoise(input.position.xy) > coverage) discard;
        return float4(direct + ambientSpecular * 2.5 + transmitted * (1.0 - fresnelAmount), 1.0);
    }

    float3 emission = baseColor * emissive;
    return float4(direct + ambientDiffuse + ambientSpecular + emission, 1.0);
}
