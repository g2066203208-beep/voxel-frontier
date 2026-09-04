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
    float3 color : TEXCOORD1;
    float3 relativePosition : TEXCOORD2;
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

[[vk::push_constant]] ConstantBuffer<PushConstants> gPush;

static const float PI = 3.14159265358979323846;

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
    return output;
}

[shader("vertex")]
ShadowVertexOutput shadowVertexMain(VertexInput input)
{
    ShadowVertexOutput output;
    float3 worldPosition = rotateByQuaternion(input.position, gPush.objectRotation);
    float3 relativePosition = worldPosition - gPush.cameraPosition.xyz;
    output.position = mul(gPush.viewProj, float4(relativePosition, 1.0));
    float marker = min(min(input.color.x, input.color.y), input.color.z);
    bool atmosphere = input.color.x < 0.0 || input.color.y < 0.0 || input.color.z < 0.0;
    bool transmissive = marker > 3.5 && marker < 7.5;
    bool emissive = marker > 7.5;
    output.skipOccluder = (atmosphere || transmissive || emissive) ? 1.0 : 0.0;
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

    // Zero-descriptor material encoding used only by this hardware acceptance build:
    // [0,1] stone/terrain, +1 wood, +2 metal, +4 colored glass, +8 emissive/HUD/star.
    float3 encoded = input.color;
    float marker = min(min(encoded.x, encoded.y), encoded.z);
    float3 baseColor = saturate(encoded);
    float metallic = 0.0;
    float roughness = 0.92;
    float transmission = 0.0;
    float emissive = 0.0;

    if (marker > 7.5)
    {
        baseColor = saturate(encoded - 8.0);
        roughness = 0.35;
        emissive = 16.0;
    }
    else if (marker > 3.5)
    {
        baseColor = saturate(encoded - 4.0);
        roughness = 0.055;
        transmission = 0.90;
    }
    else if (marker > 1.5)
    {
        baseColor = saturate(encoded - 2.0);
        metallic = 1.0;
        roughness = 0.14;
    }
    else if (marker > 0.95)
    {
        baseColor = saturate(encoded - 1.0);
        roughness = 0.70;
    }

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

    float3 stellarRadiance = max(gPush.sunColorIntensity.rgb, 0.0)
        * max(gPush.sunColorIntensity.a, 0.0);
    float3 direct = (diffuse + specular) * noL * stellarRadiance;

    // Environment contribution is always present. Back-facing faces and cast-shadow surfaces
    // retain diffuse sky irradiance, warm terrain bounce and roughness-dependent specular IBL
    // instead of collapsing to pure black.
    float skyWeight = saturate(n.y * 0.5 + 0.5);
    float3 skyRadiance = lerp(float3(0.020, 0.017, 0.014), float3(0.13, 0.21, 0.36), skyWeight);
    float3 groundBounce = float3(0.070, 0.052, 0.032) * saturate(-n.y * 0.5 + 0.5);
    float3 r = reflect(-v, n);
    float reflectionSky = saturate(r.y * 0.5 + 0.5);
    float3 reflectionColor = lerp(float3(0.032, 0.026, 0.021), float3(0.22, 0.34, 0.54), reflectionSky);
    float3 ambientDiffuse = baseColor * (skyRadiance + groundBounce) * (1.0 - metallic) * (1.0 - transmission);
    float3 ambientSpecular = reflectionColor * f * (1.0 - roughness * 0.84);

    if (transmission > 0.0)
    {
        float fresnelAmount = saturate(max(max(f.x, f.y), f.z));
        // Thin-volume colored-glass preview: view-angle Fresnel reflection plus Beer-like tinting
        // of the environment seen through the pane. The ground transmission footprint is emitted
        // separately from the exact projected box silhouette in Main.cpp.
        float viewThickness = 1.0 / max(abs(dot(n, v)), 0.18);
        float3 absorptionTint = pow(max(baseColor, float3(0.02, 0.02, 0.02)), viewThickness * 0.55);
        float3 transmitted = lerp(reflectionColor, skyRadiance, 0.62)
            * absorptionTint * transmission;
        float coverage = saturate(0.12 + 0.38 * fresnelAmount + 0.10 * (1.0 - transmission));
        if (screenDoorNoise(input.position.xy) > coverage) discard;
        return float4(direct * 0.28 + ambientSpecular * 2.6 + transmitted * (1.0 - fresnelAmount), 1.0);
    }

    float3 emission = baseColor * emissive;
    return float4(direct + ambientDiffuse + ambientSpecular + emission, 1.0);
}
