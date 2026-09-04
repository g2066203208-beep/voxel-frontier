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

float3 agxInset(float3 v)
{
    return float3(
        0.842479062253094 * v.x + 0.0784335999999992 * v.y + 0.0792237451477643 * v.z,
        0.0423282422610123 * v.x + 0.878468636469772 * v.y + 0.0791661274605434 * v.z,
        0.0423756549057051 * v.x + 0.0784336 * v.y + 0.879142973793104 * v.z);
}

float3 agxOutset(float3 v)
{
    return float3(
        1.19687900512017 * v.x - 0.0980208811401368 * v.y - 0.0990297440797205 * v.z,
       -0.0528968517574562 * v.x + 1.15190312990417 * v.y - 0.0989611768448433 * v.z,
       -0.0529716355144438 * v.x - 0.0980434501171241 * v.y + 1.15107367264116 * v.z);
}

float3 agxContrastApprox(float3 x)
{
    float3 x2 = x * x;
    float3 x4 = x2 * x2;
    return 15.5 * x4 * x2
        - 40.14 * x4 * x
        + 31.96 * x4
        - 6.868 * x2 * x
        + 0.4298 * x2
        + 0.1191 * x
        - 0.00232;
}

float3 toneMapAgX(float3 color)
{
    const float minEv = -12.47393;
    const float maxEv = 4.026069;
    float3 v = agxInset(max(color, 0.0));
    v = clamp(log2(max(v, 1.0e-10)), minEv, maxEv);
    v = (v - minEv) / (maxEv - minEv);
    v = agxContrastApprox(v);
    v = agxOutset(v);
    float luma = dot(v, float3(0.2126, 0.7152, 0.0722));
    v = lerp(float3(luma, luma, luma), v, 0.96);
    return saturate(v);
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

    // Deliberately analytical sky: no cubemap, volume texture, ray marching or cloud texture.
    // The sharper zenith-to-horizon density curve adds aerial depth without making the image busy.
    float horizonAmount = pow(saturate(1.0 - input.uv.y), 1.36);
    float horizonVeil = pow(horizonAmount, 2.15);

    float3 zenithDay = float3(0.075, 0.25, 0.56);
    float3 midDay = float3(0.19, 0.43, 0.69);
    float3 horizonDay = float3(0.47, 0.60, 0.66);
    float3 zenithNight = float3(0.010, 0.017, 0.050);
    float3 horizonNight = float3(0.030, 0.045, 0.080);
    float3 twilightWarm = float3(0.94, 0.34, 0.105);

    float3 zenith = lerp(zenithNight, zenithDay, daylight);
    float3 horizon = lerp(horizonNight, horizonDay, daylight);
    float3 sky = lerp(zenith, midDay, smoothstep(0.05, 0.52, horizonAmount) * daylight * 0.42);
    sky = lerp(sky, horizon, smoothstep(0.40, 1.0, horizonAmount));
    sky = lerp(sky, twilightWarm, twilight * horizonVeil * 0.66);

    // Haze lifts only the lowest atmosphere. The upper sky stays saturated, creating the same
    // warm-horizon / cool-zenith separation that also drives terrain ambient reflections.
    float3 hazeColor = lerp(float3(0.37, 0.50, 0.60), float3(0.72, 0.42, 0.24), twilight * 0.72);
    float haze = atmosphere * horizonVeil;
    sky = lerp(sky, hazeColor, haze * (0.17 + 0.20 * daylight));

    // Broad low-cost solar atmosphere glow. It is a vertical scattering band, not a fake image
    // texture, and therefore adds no sampling cost or temporal noise.
    sky += twilightWarm * twilight * horizonVeil * 0.095;
    sky *= 0.82 + 0.30 * daylight + 0.055 * atmosphere;

    return float4(toneMapAgX(sky * 1.03), 1.0);
}
