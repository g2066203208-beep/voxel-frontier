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

struct SceneUniform
{
    // xyz world-space center, w radius in meters.
    float4 fogCenterRadius;
    // rgb in-scattering tint, w extinction coefficient sigma_e [1/m].
    float4 fogColorExtinction;
};

[[vk::push_constant]] ConstantBuffer<PushConstants> gPush;
[[vk::binding(0, 0)]] ConstantBuffer<SceneUniform> gScene;

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

float localFogPathLength(float3 relativeSurfacePosition)
{
    float radius = max(gScene.fogCenterRadius.w, 0.0);
    float extinction = max(gScene.fogColorExtinction.w, 0.0);
    float rayLength = length(relativeSurfacePosition);
    if (radius <= 0.0 || extinction <= 0.0 || rayLength <= 1.0e-5)
        return 0.0;

    float3 rayDirection = relativeSurfacePosition / rayLength;
    float3 cameraToCenter = gPush.cameraPosition.xyz - gScene.fogCenterRadius.xyz;
    float b = dot(cameraToCenter, rayDirection);
    float c = dot(cameraToCenter, cameraToCenter) - radius * radius;
    float discriminant = b * b - c;
    if (discriminant <= 0.0)
        return 0.0;

    float root = sqrt(discriminant);
    float entry = max(0.0, -b - root);
    float exit = min(rayLength, -b + root);
    return max(0.0, exit - entry);
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
    float3 h = normalize(l + v);

    float noL = saturate(dot(n, l));
    float noV = saturate(dot(n, v));
    float noH = saturate(dot(n, h));
    float voH = saturate(dot(v, h));

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
    float3 indirect = input.color * 0.012;
    float3 surfaceRadiance = direct + indirect;

    // Homogeneous local participating medium: analytic ray/sphere bounds and exact
    // Beer-Lambert transmittance. No ray marching or 3D volume texture is required.
    float pathLength = localFogPathLength(input.relativePosition);
    float extinction = max(gScene.fogColorExtinction.w, 0.0);
    float transmittance = exp(-extinction * pathLength);
    float3 fogColor = max(gScene.fogColorExtinction.rgb, 0.0);
    float daylight = saturate(0.18 + 0.82 * gPush.sunColorIntensity.a / 2.2);
    float3 inScattering = fogColor * daylight * (1.0 - transmittance);
    return float4(surfaceRadiance * transmittance + inScattering, 1.0);
}
