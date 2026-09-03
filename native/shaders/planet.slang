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
};

[[vk::push_constant]] ConstantBuffer<PushConstants> gPush;

static const float PI = 3.14159265358979323846;

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
    float3 relativePosition = input.position - gPush.cameraPosition.xyz;
    output.position = mul(gPush.viewProj, float4(relativePosition, 1.0));
    output.relativePosition = relativePosition;
    output.normal = input.normal;
    output.color = input.color;
    return output;
}

[shader("fragment")]
float4 fragmentMain(VertexOutput input) : SV_Target
{
    float3 n = normalize(input.normal);
    float3 l = normalize(-gPush.sunDirection.xyz);
    float3 v = normalize(-input.relativePosition);
    float3 h = normalize(l + v);

    float noL = saturate(dot(n, l));
    float noV = saturate(dot(n, v));
    float noH = saturate(dot(n, h));
    float voH = saturate(dot(v, h));

    // One cheap physically based dielectric material until per-material GPU buffers land.
    // The CPU optical layer already carries wavelength-dependent IOR/absorption/thin-film data.
    float roughness = 0.62;
    float3 f0 = float3(0.04, 0.04, 0.04);
    float d = distributionGGX(noH, roughness);
    float g = geometrySchlickGGX(noV, roughness) * geometrySchlickGGX(noL, roughness);
    float3 f = fresnelSchlick(voH, f0);

    float3 specular = (d * g * f) / max(4.0 * noV * noL, 1.0e-4);
    float3 diffuse = (1.0 - f) * input.color / PI;

    // Tiny indirect floor avoids fully crushed unlit geometry while vacuum itself remains black.
    float3 direct = (diffuse + specular) * noL * 2.2;
    float3 indirect = input.color * 0.018;
    return float4(direct + indirect, 1.0);
}
