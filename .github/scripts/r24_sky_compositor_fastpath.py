#!/usr/bin/env python3
"""Refine the R24 SkyView path after r24_hillaire_skyview_lut.py.

The Hillaire-style LUT removed the full-resolution atmosphere integration, but the first profile
showed that high-frequency compositor work (ray reconstruction, daylight stars, and solar basis
construction) still dominated llvmpipe. This pass keeps stars/sun crisp while moving/avoiding work:
  * reconstruct the unnormalised view ray once per fullscreen vertex and interpolate it;
  * skip procedural stars during atmospheric daylight, computed once on CPU per frame;
  * replace pow(x,5)/pow(h,24) star math with multiplication chains;
  * reject almost every pixel before constructing the solar tangent basis.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CPP = ROOT / "native/src/render/VulkanRenderer.cpp"
SHADER = ROOT / "native/shaders/planet.slang"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"{label}: already materialized")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one source match, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: materialized")


replace_once(
    SHADER,
    """struct FullscreenOutput
{
    float4 position : SV_Position;
    float2 uv : TEXCOORD0;
};
""",
    """struct FullscreenOutput
{
    float4 position : SV_Position;
    float2 uv : TEXCOORD0;
    // Perspective ray before normalization is affine across the screen. Interpolate it instead of
    // multiplying the inverse view-projection matrix for every SkyView/final-sky pixel.
    float3 viewRay : TEXCOORD1;
};
""",
    "fullscreen interpolated view ray",
)

replace_once(
    SHADER,
    """    output.position = float4(p, 0.0, 1.0);
    output.uv = p * float2(0.5, -0.5) + 0.5;
    return output;
}
""",
    """    output.position = float4(p, 0.0, 1.0);
    output.uv = p * float2(0.5, -0.5) + 0.5;
    float4 worldFar = mul(gPush.matrix, float4(p, 1.0, 1.0));
    output.viewRay = worldFar.xyz / max(abs(worldFar.w), 1.0e-7);
    return output;
}
""",
    "fullscreen vertex ray reconstruction",
)

# The SkyView materializer creates exactly two active per-fragment calls: low-res atmosphere and
# full-res compositor. Keep the old helper for contract/debug compatibility; production calls use
# the interpolated ray.
shader = SHADER.read_text(encoding="utf-8")
needle = "float3 ray = reconstructWorldRay(input.uv);"
count = shader.count(needle)
if count == 2:
    SHADER.write_text(shader.replace(needle, "float3 ray = normalize(input.viewRay);"), encoding="utf-8")
    print("fragment inverse-VP ray reconstruction: moved to vertex stage")
elif count == 0 and shader.count("float3 ray = normalize(input.viewRay);") >= 2:
    print("fragment inverse-VP ray reconstruction: already materialized")
else:
    raise SystemExit(f"fragment ray replacement: expected two calls, got {count}")

replace_once(
    SHADER,
    """float3 proceduralStars(float3 ray)
{
    float3 cell = floor(ray * 1450.0);
    float h = hash31(cell);
    float star = smoothstep(0.9968, 0.9999, h);
    float galactic = pow(saturate(1.0 - abs(ray.y * 0.72 + ray.z * 0.24)), 5.0);
    star += smoothstep(0.9982, 0.99995, hash31(cell * 0.43 + 17.0)) * galactic * 0.75;
    float temperature = hash31(cell + 91.7);
    float3 tint = lerp(float3(1.0, 0.70, 0.48), float3(0.65, 0.80, 1.0), temperature);
    return tint * star * (0.55 + 2.8 * pow(h, 24.0));
}
""",
    """float3 proceduralStars(float3 ray)
{
    float3 cell = floor(ray * 1450.0);
    float h = hash31(cell);
    float star = smoothstep(0.9968, 0.9999, h);
    float galacticBase = saturate(1.0 - abs(ray.y * 0.72 + ray.z * 0.24));
    float galactic2 = galacticBase * galacticBase;
    float galactic4 = galactic2 * galactic2;
    float galactic = galactic4 * galacticBase;
    star += smoothstep(0.9982, 0.99995, hash31(cell * 0.43 + 17.0)) * galactic * 0.75;
    float temperature = hash31(cell + 91.7);
    float3 tint = lerp(float3(1.0, 0.70, 0.48), float3(0.65, 0.80, 1.0), temperature);
    // Integer exponent: multiplication is exact for the intended polynomial and avoids a generic
    // transcendental pow implementation on software and older GPUs.
    float h2 = h * h;
    float h4 = h2 * h2;
    float h8 = h4 * h4;
    float h16 = h8 * h8;
    float h24 = h16 * h8;
    return tint * star * (0.55 + 2.8 * h24);
}
""",
    "polynomial star fast path",
)

replace_once(
    SHADER,
    """float3 proceduralSun(float3 ray, float3 sunDir, bool hitsGround)
{
    if (hitsGround) return float3(0.0, 0.0, 0.0);
    float sunAngularRadius = clamp(abs(gPush.data1.w), 0.0001, 1.45);
    float3 helper = abs(sunDir.y) < 0.92 ? float3(0.0, 1.0, 0.0) : float3(1.0, 0.0, 0.0);
""",
    """float3 proceduralSun(float3 ray, float3 sunDir, bool hitsGround)
{
    if (hitsGround) return float3(0.0, 0.0, 0.0);
    float sunAngularRadius = clamp(abs(gPush.data1.w), 0.0001, 1.45);
    // The detailed solar shader only contributes inside 1.85 apparent radii. Reject the rest of
    // the screen using a dot product before cross/normalize/sin/atan/FBM. The quadratic cosine
    // approximation is conservative for large radii, so it never clips the authored corona.
    float gateRadius = min(1.85 * sunAngularRadius, 1.45);
    float conservativeCosGate = 1.0 - 0.5 * gateRadius * gateRadius;
    if (dot(ray, sunDir) < conservativeCosGate)
        return float3(0.0, 0.0, 0.0);
    float3 helper = abs(sunDir.y) < 0.92 ? float3(0.0, 1.0, 0.0) : float3(1.0, 0.0, 0.0);
""",
    "solar cone early rejection",
)

# Both low-res and final sky receive a normalized direction from CPU already.
shader = SHADER.read_text(encoding="utf-8")
old_sun = "float3 sunDir = normalize(gPush.data1.xyz);"
count = shader.count(old_sun)
if count >= 2:
    SHADER.write_text(shader.replace(old_sun, "float3 sunDir = gPush.data1.xyz;"), encoding="utf-8")
    print(f"normalized sun direction reuse: materialized ({count} sites)")
elif shader.count("float3 sunDir = gPush.data1.xyz;") >= 2:
    print("normalized sun direction reuse: already materialized")
else:
    raise SystemExit("normalized sun direction reuse: expected SkyView/final sky sites")

replace_once(
    SHADER,
    """    if (!hitsGround)
    {
        highFrequency += proceduralStars(ray);
        highFrequency += proceduralSun(ray, sunDir, false);
    }
""",
    """    if (!hitsGround)
    {
        // data0.w is a per-frame physically motivated visibility scalar: atmosphere daylight masks
        // stars before we pay any hash/polynomial cost, while space and night keep crisp stars.
        if (gPush.data0.w > 0.001)
            highFrequency += proceduralStars(ray) * gPush.data0.w;
        highFrequency += proceduralSun(ray, sunDir, false);
    }
""",
    "daylight star rejection",
)

replace_once(
    CPP,
    """    skyPush.matrix = glm::inverse(viewProjection);
    skyPush.data0 = glm::vec4(glm::vec3(cameraPosition - environment.planetCenter), 1.0F);
    skyPush.data1 = glm::vec4(
        safeNormalizeFloat(environment.sunDirectionToLight),
        std::clamp(environment.sunAngularRadiusRadians, 0.0001F, 1.45F));
""",
    """    skyPush.matrix = glm::inverse(viewProjection);
    const glm::vec3 cameraPlanet = glm::vec3(cameraPosition - environment.planetCenter);
    const glm::vec3 skySunDirection = safeNormalizeFloat(environment.sunDirectionToLight);
    const float cameraPlanetRadius = glm::length(cameraPlanet);
    const float atmosphereTopRadius = static_cast<float>(
        environment.planetRadius + environment.atmosphereHeight);
    const glm::vec3 localUp = cameraPlanetRadius > 1.0F
        ? cameraPlanet / cameraPlanetRadius : glm::vec3{0.0F, 1.0F, 0.0F};
    const float sunElevationSine = glm::dot(localUp, skySunDirection);
    // Stars are physically overwhelmed by Rayleigh/Mie daylight inside the atmosphere. Evaluate
    // the expensive procedural catalogue only at night/twilight; above the atmosphere it remains
    // fully visible. Smooth twilight avoids temporal popping at sunrise/sunset.
    const float daylightMask = std::clamp(
        (sunElevationSine + 0.12F) / 0.18F, 0.0F, 1.0F);
    const float starVisibility = cameraPlanetRadius >= atmosphereTopRadius
        ? 1.0F : (1.0F - daylightMask);
    skyPush.data0 = glm::vec4(cameraPlanet, starVisibility);
    skyPush.data1 = glm::vec4(
        skySunDirection,
        std::clamp(environment.sunAngularRadiusRadians, 0.0001F, 1.45F));
""",
    "CPU daylight star visibility",
)

# Postconditions.
shader = SHADER.read_text(encoding="utf-8")
cpp = CPP.read_text(encoding="utf-8")
checks = {
    "vertex ray": "float3 viewRay : TEXCOORD1;" in shader,
    "no active fragment inverse vp": shader.count("float3 ray = reconstructWorldRay(input.uv);") == 0,
    "star pow24 removed": "pow(h, 24.0)" not in shader,
    "galactic pow5 removed": "pow(saturate(1.0 - abs(ray.y" not in shader,
    "sun cone gate": "conservativeCosGate" in shader,
    "daylight star gate": "gPush.data0.w > 0.001" in shader,
    "cpu star visibility": "const float starVisibility" in cpp,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("postcondition failure: " + ", ".join(failed))
print("R24 full-resolution sky compositor fast path materialized successfully")
