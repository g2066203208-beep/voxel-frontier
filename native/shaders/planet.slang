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

[shader("fragment")]
float4 fragmentMain(VertexOutput input) : SV_Target
{
    float3 n = normalize(input.normal);
    float3 l = normalize(gPush.sunDirection.xyz);
    float3 v = normalize(-input.relativePosition);

    // Negative color remains the atmosphere-shell marker.
    if (input.color.x < 0.0 || input.color.y < 0.0 || input.color.z < 0.0)
    {
        float3 packed = max(-input.color, 0.0);
        float opticalStrength = max(max(packed.x, packed.y), packed.z);
        float3 tint = packed / max(opticalStrength, 1.0e-4);
        float grazing = pow(saturate(1.0 - abs(dot(n, v))), 0.58);
        float forwardScatter = pow(saturate(dot(l, -v) * 0.5 + 0.5), 5.0);
        float sunFacing = saturate(dot(n, l) * 0.5 + 0.5);
        float coverage = saturate(opticalStrength * (0.05 + 0.92 * grazing));
        if (screenDoorNoise(input.position.xy) > coverage) discard;

        float3 stellar = max(gPush.sunColorIntensity.rgb, 0.0)
            * max(gPush.sunColorIntensity.a, 0.0);
        float3 scatter = tint
            * (0.07 + 0.72 * grazing + 0.20 * forwardScatter)
            * (0.35 + 0.65 * sunFacing)
            * max(stellar, float3(0.08, 0.08, 0.08));
        return float4(scatter, 1.0);
    }

    // Temporary zero-descriptor material encoding for the hardware preview:
    // normal RGB [0,1] = stone/terrain, +1 = wood, +2 = metal, +4 = colored glass,
    // +8 = emissive stellar surface. This is intentionally translated to the same metallic /
    // roughness / transmission concepts used by glTF and will later move to a material buffer.
    float3 encoded = input.color;
    float3 baseColor = encoded;
    float metallic = 0.0;
    float roughness = 0.92;
    float transmission = 0.0;
    float emissive = 0.0;

    float marker = min(min(encoded.x, encoded.y), encoded.z);
    if (marker > 7.5)
    {
        baseColor = saturate(encoded - 8.0);
        roughness = 0.45;
        emissive = 18.0;
    }
    else if (marker > 3.5)
    {
        baseColor = saturate(encoded - 4.0);
        roughness = 0.075;
        transmission = 0.88;
    }
    else if (marker > 1.5)
    {
        baseColor = saturate(encoded - 2.0);
        metallic = 1.0;
        roughness = 0.16;
    }
    else if (marker > 0.95)
    {
        baseColor = saturate(encoded - 1.0);
        roughness = 0.76;
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

    float3 specular = (d * g * f) / max(4.0 * noV * noL, 1.0e-4);
    float3 kd = (1.0 - f) * (1.0 - metallic) * (1.0 - transmission);
    float3 diffuse = kd * baseColor / PI;

    float3 stellarRadiance = max(gPush.sunColorIntensity.rgb, 0.0)
        * max(gPush.sunColorIntensity.a, 0.0);
    float3 direct = (diffuse + specular) * noL * stellarRadiance;

    // Very cheap environment term. Smooth metals/glass show a much stronger directional sheen;
    // rough stone/wood remain broad and matte. No cubemap or ray tracing is required for this pass.
    float horizon = pow(saturate(1.0 - abs(n.y)), 0.35);
    float3 environmentColor = lerp(float3(0.015, 0.025, 0.045), float3(0.10, 0.16, 0.24), horizon);
    float reflectionStrength = (1.0 - roughness) * (0.18 + 0.82 * max(max(f.x, f.y), f.z));
    float3 reflected = environmentColor * reflectionStrength;

    if (transmission > 0.0)
    {
        // Low-cost thin colored glass preview following the same Fresnel/transmission split as
        // KHR_materials_transmission. Screen-door coverage exposes the already-rendered scene
        // without a second color buffer; retained samples carry colored absorption + reflection.
        float fresnelAmount = max(max(f.x, f.y), f.z);
        float coverage = saturate(0.11 + 0.42 * fresnelAmount + 0.10 * (1.0 - transmission));
        if (screenDoorNoise(input.position.xy) > coverage) discard;
        float3 transmittedTint = baseColor * (0.055 + 0.09 * noL);
        return float4(direct + reflected * 2.2 + transmittedTint, 1.0);
    }

    float3 indirect = baseColor * (0.010 + 0.010 * (1.0 - roughness));
    float3 emission = baseColor * emissive;
    return float4(direct + reflected + indirect + emission, 1.0);
}
