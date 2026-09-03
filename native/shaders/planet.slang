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
};

struct PushConstants
{
    float4x4 viewProj;
    float4 sunDirection;
};

[[vk::push_constant]] ConstantBuffer<PushConstants> gPush;

[shader("vertex")]
VertexOutput vertexMain(VertexInput input)
{
    VertexOutput output;
    output.position = mul(gPush.viewProj, float4(input.position, 1.0));
    output.normal = input.normal;
    output.color = input.color;
    return output;
}

[shader("fragment")]
float4 fragmentMain(VertexOutput input) : SV_Target
{
    float3 n = normalize(input.normal);
    float3 l = normalize(-gPush.sunDirection.xyz);
    float diffuse = saturate(dot(n, l));
    float hemisphere = 0.35 + 0.25 * saturate(n.y * 0.5 + 0.5);
    float lighting = hemisphere + diffuse * 0.70;
    return float4(input.color * lighting, 1.0);
}
