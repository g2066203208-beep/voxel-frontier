struct VertexInput
{
    float3 position : POSITION;
    float3 normal : NORMAL;
    float3 color : COLOR0;
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

static const float kShadowHalfExtent = 72.0;
static const float kShadowDepthRange = 180.0;

float3 rotateByQuaternion(float3 v, float4 q)
{
    float3 t = 2.0 * cross(q.xyz, v);
    return v + q.w * t + cross(q.xyz, t);
}

void shadowBasis(float3 lightDirection, out float3 right, out float3 up)
{
    float3 helper = abs(lightDirection.y) < 0.94
        ? float3(0.0, 1.0, 0.0)
        : float3(1.0, 0.0, 0.0);
    right = normalize(cross(helper, lightDirection));
    up = normalize(cross(lightDirection, right));
}

[shader("vertex")]
float4 shadowVertexMain(VertexInput input) : SV_Position
{
    float3 worldPosition = rotateByQuaternion(input.position, gPush.objectRotation);
    float3 relative = worldPosition - gPush.cameraPosition.xyz;
    float3 l = normalize(gPush.sunDirection.xyz);
    float3 right;
    float3 up;
    shadowBasis(l, right, up);

    float x = dot(relative, right) / kShadowHalfExtent;
    float y = dot(relative, up) / kShadowHalfExtent;
    // Directional-light depth: points toward the light are closer and therefore receive smaller depth.
    float depth = saturate(0.5 - dot(relative, l) / kShadowDepthRange);
    return float4(x, y, depth, 1.0);
}
