struct PushConstants
{
    float4x4 viewProj;
    // xyz = camera position, w = normalized local atmosphere density [0,1].
    float4 cameraPosition;
    // xyz = direction toward the sun, w = local solar elevation cosine [-1,1].
    float4 sunDirection;
    float4 sunColorIntensity;
    float4 objectRotation;
};

[[vk::push_constant]] ConstantBuffer<PushConstants> gPush;

struct SkyVertexOutput
{
    float4 position : SV_Position;
    float2 uv : TEXCOORD0;
};

float3 filmicToneMap(float3 x)
{
    x = max(x, 0.0);
    return saturate((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14));
}

[shader("vertex")]
SkyVertexOutput skyVertexMain(uint vertexId : SV_VertexID)
{
    // Single fullscreen triangle: three generated vertices, no vertex/index buffer fetch.
    float2 p = vertexId == 0 ? float2(-1.0, -1.0)
        : (vertexId == 1 ? float2(3.0, -1.0) : float2(-1.0, 3.0));
    SkyVertexOutput output;
    output.position = float4(p, 0.999999, 1.0);
    output.uv = p * 0.5 + 0.5;
    return output;
}

[shader("fragment")]
float4 skyFragmentMain(SkyVertexOutput input) : SV_Target
{
    float atmosphere = saturate(gPush.cameraPosition.w);
    float solarElevation = clamp(gPush.sunDirection.w, -1.0, 1.0);
    float daylight = smoothstep(-0.10, 0.18, solarElevation);
    float twilight = 1.0 - smoothstep(0.02, 0.36, abs(solarElevation + 0.035));
    float night = 1.0 - daylight;

    // uv.y is screen height. Low screen area acts as the horizon because this is a deliberately
    // cheap art-direction pass rather than a ray-marched atmosphere.
    float horizonAmount = pow(saturate(1.0 - input.uv.y), 1.55);
    float zenithAmount = 1.0 - horizonAmount;

    float3 zenithDay = float3(0.12, 0.34, 0.58);
    float3 horizonDay = float3(0.48, 0.62, 0.66);
    float3 zenithNight = float3(0.012, 0.020, 0.052);
    float3 horizonNight = float3(0.035, 0.050, 0.082);
    float3 twilightWarm = float3(0.90, 0.38, 0.16);

    float3 zenith = lerp(zenithNight, zenithDay, daylight);
    float3 horizon = lerp(horizonNight, horizonDay, daylight);
    horizon = lerp(horizon, twilightWarm, twilight * 0.72);

    float3 sky = lerp(zenith, horizon, horizonAmount);
    // Atmospheric density fades the clear-sky saturation and lifts the horizon without needing
    // any volume texture or ray marching.
    float haze = atmosphere * horizonAmount;
    sky = lerp(sky, float3(0.55, 0.61, 0.61), haze * (0.16 + 0.20 * daylight));

    // Tiny sun-height-dependent glow band. This is not a fake sun disk; it only shapes the
    // horizon color relationship so the world receives a coherent warm/cool atmosphere.
    sky += twilightWarm * twilight * horizonAmount * 0.11;
    sky *= 0.78 + 0.34 * daylight + 0.06 * atmosphere;

    return float4(filmicToneMap(sky), 1.0);
}
