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
    // Stable per-pixel hash used only for atmosphere coverage. This gives a cheap screen-door
    // transparency without changing the Vulkan blend/depth pipeline used by opaque geometry.
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

    // Negative vertex color is an internal marker for a participating atmosphere shell.
    // The shell is not a fake skybox: it occupies an actual finite spherical volume. From space
    // this branch produces a grazing-angle Rayleigh/Mie-like rim; from inside the atmosphere the
    // CPU sky model supplies the full-screen background instead, so shells can be omitted there.
    if (input.color.x < 0.0 || input.color.y < 0.0 || input.color.z < 0.0)
    {
        float3 packed = max(-input.color, 0.0);
        float opticalStrength = max(max(packed.x, packed.y), packed.z);
        float3 tint = packed / max(opticalStrength, 1.0e-4);

        float grazing = pow(saturate(1.0 - abs(dot(n, v))), 0.58);
        float forwardScatter = pow(saturate(dot(l, -v) * 0.5 + 0.5), 5.0);
        float sunFacing = saturate(dot(n, l) * 0.5 + 0.5);
        float coverage = saturate(opticalStrength * (0.05 + 0.92 * grazing));

        // Screen-door transparency: discard most face-on shell fragments so opaque planet
        // surfaces remain visible, while grazing rays build a bright atmospheric limb.
        if (screenDoorNoise(input.position.xy) > coverage) discard;

        float3 stellar = max(gPush.sunColorIntensity.rgb, 0.0)
            * max(gPush.sunColorIntensity.a, 0.0);
        float3 scatter = tint
            * (0.07 + 0.72 * grazing + 0.20 * forwardScatter)
            * (0.35 + 0.65 * sunFacing)
            * max(stellar, float3(0.08, 0.08, 0.08));
        return float4(scatter, 1.0);
    }

    float3 h = normalize(l + v);

    float noL = saturate(dot(n, l));
    float noV = saturate(dot(n, v));
    float noH = saturate(dot(n, h));
    float voH = saturate(dot(v, h));

    // Cheap physically based dielectric surface. The CPU optical layer separately keeps
    // wavelength-dependent IOR/absorption/thin-film data for materials that need it.
    float roughness = 0.62;
    float3 f0 = float3(0.04, 0.04, 0.04);
    float d = distributionGGX(noH, roughness);
    float g = geometrySchlickGGX(noV, roughness) * geometrySchlickGGX(noL, roughness);
    float3 f = fresnelSchlick(voH, f0);

    float3 specular = (d * g * f) / max(4.0 * noV * noL, 1.0e-4);
    float3 diffuse = (1.0 - f) * input.color / PI;

    float3 stellarRadiance = max(gPush.sunColorIntensity.rgb, 0.0)
        * max(gPush.sunColorIntensity.a, 0.0);
    float3 direct = (diffuse + specular) * noL * stellarRadiance;

    // A very small material-independent bounce floor preserves shape readability without
    // coloring the vacuum clear background. A later irradiance probe can replace this value.
    float3 indirect = input.color * 0.012;
    return float4(direct + indirect, 1.0);
}
