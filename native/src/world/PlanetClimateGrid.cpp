#include "vf/world/PlanetClimateGrid.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include <glm/geometric.hpp>

namespace vf {
namespace {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kSigma = 5.670374419e-8;

[[nodiscard]] double saturate(double value) noexcept {
    return std::clamp(value, 0.0, 1.0);
}

[[nodiscard]] double smooth01(double edge0, double edge1, double value) noexcept {
    if (edge1 <= edge0) return value >= edge1 ? 1.0 : 0.0;
    const double x = saturate((value - edge0) / (edge1 - edge0));
    return x * x * (3.0 - 2.0 * x);
}

[[nodiscard]] glm::dvec3 safeNormalize(
    const glm::dvec3& value,
    const glm::dvec3& fallback = {0.0, 1.0, 0.0}) noexcept {
    const double l2 = glm::dot(value, value);
    return l2 > 1.0e-18 ? value / std::sqrt(l2) : fallback;
}

} // namespace

PlanetClimateGrid::PlanetClimateGrid(
    PlanetDefinition planet,
    PlanetClimateConfig config,
    double spinRateRadPerSecond) {
    reset(planet, config, spinRateRadPerSecond);
}

void PlanetClimateGrid::reset(
    PlanetDefinition planet,
    PlanetClimateConfig config,
    double spinRateRadPerSecond) {
    planet_ = planet;
    config_ = config;
    latBands_ = std::clamp<std::uint32_t>(config_.latitudeBands, 8U, 128U);
    lonBands_ = std::clamp<std::uint32_t>(config_.longitudeBands, 16U, 256U);
    spinRateRadPerSecond_ = std::isfinite(spinRateRadPerSecond) ? spinRateRadPerSecond : 0.0;
    cells_.assign(static_cast<std::size_t>(latBands_) * lonBands_, {});

    for (std::uint32_t lat = 0; lat < latBands_; ++lat) {
        const double latitude = latitudeAt(lat);
        const double polar = std::abs(std::sin(latitude));
        for (std::uint32_t lon = 0; lon < lonBands_; ++lon) {
            PlanetClimateCell& cell = cells_[index(lat, lon)];
            const PlanetTerrainSample terrain = samplePlanetTerrain(planet_, directionAt(lat, lon));
            const bool ocean = terrain.submerged(planet_);
            cell.temperatureK = 300.0 - 42.0 * polar * polar
                - std::max(0.0, terrain.elevationMeters - planet_.seaLevelElevationMeters) * config_.lapseRateKPerM;
            cell.temperatureK = std::clamp(cell.temperatureK, 205.0, 315.0);
            cell.specificHumidity = ocean ? 0.010 : 0.006;
            cell.cloudFraction = ocean ? 0.38 : 0.24;
            cell.windEastNorthMps = {};
        }
    }
}

std::size_t PlanetClimateGrid::index(std::uint32_t lat, std::uint32_t lon) const noexcept {
    lon %= lonBands_;
    lat = std::min(lat, latBands_ - 1U);
    return static_cast<std::size_t>(lat) * lonBands_ + lon;
}

double PlanetClimateGrid::latitudeAt(std::uint32_t lat) const noexcept {
    const double t = (static_cast<double>(lat) + 0.5) / static_cast<double>(latBands_);
    return -0.5 * kPi + t * kPi;
}

glm::dvec3 PlanetClimateGrid::directionAt(std::uint32_t lat, std::uint32_t lon) const noexcept {
    const double latitude = latitudeAt(lat);
    const double longitude = -kPi + 2.0 * kPi
        * (static_cast<double>(lon) + 0.5) / static_cast<double>(lonBands_);
    const double c = std::cos(latitude);
    return {c * std::cos(longitude), std::sin(latitude), c * std::sin(longitude)};
}

double PlanetClimateGrid::saturationSpecificHumidity(
    double temperatureK,
    double pressurePa) const noexcept {
    const double temperatureC = temperatureK - 273.15;
    const double denominator = std::max(1.0, temperatureC + 243.04);
    const double saturationVaporPressure = 610.94
        * std::exp(17.625 * temperatureC / denominator);
    const double capped = std::min(saturationVaporPressure, pressurePa * 0.95);
    return std::clamp(
        0.622 * capped / std::max(1.0, pressurePa - 0.378 * capped),
        0.0,
        0.08);
}

void PlanetClimateGrid::step(
    double deltaSeconds,
    const glm::dvec3& sunDirectionBodyLocalInput,
    double stellarIrradianceWm2) {
    if (cells_.empty() || !std::isfinite(deltaSeconds) || deltaSeconds <= 0.0) return;
    const double dt = std::clamp(deltaSeconds, 0.0, 600.0);
    const double irradiance = std::max(0.0, stellarIrradianceWm2);
    const glm::dvec3 sunDirection = safeNormalize(sunDirectionBodyLocalInput, {1.0, 0.0, 0.0});
    const double radius = std::max(1.0, planet_.radius);
    const double dLat = kPi / static_cast<double>(latBands_);
    const double dLon = 2.0 * kPi / static_cast<double>(lonBands_);

    const std::vector<PlanetClimateCell> old = cells_;

    for (std::uint32_t lat = 0; lat < latBands_; ++lat) {
        const double latitude = latitudeAt(lat);
        const double cosLat = std::max(0.08, std::cos(latitude));
        const double f = 2.0 * spinRateRadPerSecond_ * std::sin(latitude);
        const double dy = radius * dLat;
        const double dx = radius * cosLat * dLon;
        const std::uint32_t latSouth = lat > 0U ? lat - 1U : lat;
        const std::uint32_t latNorth = lat + 1U < latBands_ ? lat + 1U : lat;

        for (std::uint32_t lon = 0; lon < lonBands_; ++lon) {
            const std::uint32_t lonWest = (lon + lonBands_ - 1U) % lonBands_;
            const std::uint32_t lonEast = (lon + 1U) % lonBands_;
            const PlanetClimateCell& center = old[index(lat, lon)];
            const PlanetClimateCell& west = old[index(lat, lonWest)];
            const PlanetClimateCell& east = old[index(lat, lonEast)];
            const PlanetClimateCell& south = old[index(latSouth, lon)];
            const PlanetClimateCell& north = old[index(latNorth, lon)];
            PlanetClimateCell next = center;

            const glm::dvec3 direction = directionAt(lat, lon);
            const PlanetTerrainSample terrain = samplePlanetTerrain(planet_, direction);
            const bool ocean = terrain.submerged(planet_);
            const double mu = std::max(0.0, glm::dot(direction, sunDirection));

            double surfaceAlbedo = ocean ? config_.baseOceanAlbedo : config_.baseLandAlbedo;
            surfaceAlbedo = std::max(surfaceAlbedo, 0.62 * terrain.glacier);
            surfaceAlbedo = std::clamp(
                surfaceAlbedo + config_.cloudAlbedoContribution * center.cloudFraction,
                0.02,
                0.85);
            const double shortwaveAtSurface = irradiance * mu
                * (1.0 - config_.clearSkyShortwaveAbsorption)
                * (1.0 - surfaceAlbedo);

            const double qsat = saturationSpecificHumidity(
                center.temperatureK,
                config_.seaLevelPressurePa);
            const double relativeHumidity = qsat > 1.0e-8
                ? saturate(center.specificHumidity / qsat)
                : 0.0;
            const double greenhouseEmissivity = std::clamp(
                0.58 + 0.25 * relativeHumidity + 0.12 * center.cloudFraction,
                0.0,
                0.94);
            const double emittedLongwave = config_.surfaceEmissivity * kSigma
                * std::pow(std::max(90.0, center.temperatureK), 4.0);
            // One-layer grey atmosphere: roughly half of atmospheric longwave returns downward.
            const double netLongwaveLoss = emittedLongwave * (1.0 - 0.5 * greenhouseEmissivity);

            const double heatCapacity = ocean
                ? config_.oceanVolumetricHeatCapacityJPerM3K * config_.oceanMixedLayerDepthMeters
                : config_.landHeatCapacityJPerM2K;

            const double laplaceT =
                (east.temperatureK - 2.0 * center.temperatureK + west.temperatureK) / (dx * dx)
                + (north.temperatureK - 2.0 * center.temperatureK + south.temperatureK) / (dy * dy);
            const double heatTransport = config_.horizontalThermalDiffusivityM2PerS * laplaceT;
            const double radiativeTendency = (shortwaveAtSurface - netLongwaveLoss)
                / std::max(1.0, heatCapacity);
            next.temperatureK = std::clamp(
                center.temperatureK + dt * (radiativeTendency + heatTransport),
                170.0,
                340.0);

            // Reduced primitive-equation momentum: horizontal thermal/geopotential gradient,
            // Coriolis and linear drag. This creates a causal wind field from temperature contrasts
            // rather than an authored global wind vector or a sinusoidal gust clock.
            const double gradTEast = (east.temperatureK - west.temperatureK) / (2.0 * dx);
            const double gradTNorth = (north.temperatureK - south.temperatureK) / (2.0 * dy);
            const double pressureAccelEast = -config_.dryAirGasConstant * gradTEast;
            const double pressureAccelNorth = -config_.dryAirGasConstant * gradTNorth;
            const double drag = 1.0 / std::max(1.0, config_.windDragTimeSeconds);
            const double u = center.windEastNorthMps.x;
            const double v = center.windEastNorthMps.y;
            next.windEastNorthMps.x = u + dt * (pressureAccelEast + f * v - drag * u);
            next.windEastNorthMps.y = v + dt * (pressureAccelNorth - f * u - drag * v);
            const double windSpeed = glm::length(next.windEastNorthMps);
            if (windSpeed > 85.0) next.windEastNorthMps *= 85.0 / windSpeed;

            double humidityTendency = 0.0;
            if (ocean && center.specificHumidity < qsat) {
                humidityTendency += (qsat - center.specificHumidity)
                    / std::max(1.0, config_.oceanEvaporationTimeSeconds);
            }
            const double neighborHumidity = 0.25 * (
                east.specificHumidity + west.specificHumidity
                + north.specificHumidity + south.specificHumidity);
            humidityTendency += (neighborHumidity - center.specificHumidity)
                / std::max(1.0, config_.moistureMixTimeSeconds);

            double precipitationQ = 0.0;
            const double condensationThreshold = 0.82 * qsat;
            if (center.specificHumidity > condensationThreshold) {
                precipitationQ = (center.specificHumidity - condensationThreshold)
                    / std::max(1.0, config_.precipitationTimeSeconds);
                humidityTendency -= precipitationQ;
            }
            next.specificHumidity = std::clamp(
                center.specificHumidity + dt * humidityTendency,
                0.0,
                0.08);
            const double nextQsat = saturationSpecificHumidity(
                next.temperatureK,
                config_.seaLevelPressurePa);
            const double nextRh = nextQsat > 1.0e-8
                ? saturate(next.specificHumidity / nextQsat)
                : 0.0;
            next.cloudFraction = smooth01(0.62, 0.96, nextRh);
            next.precipitationRateKgPerM2S = std::max(0.0, precipitationQ);

            cells_[index(lat, lon)] = next;
        }
    }
}

PlanetClimateSample PlanetClimateGrid::sample(
    const glm::dvec3& directionBodyLocalInput,
    double altitudeMeters) const noexcept {
    PlanetClimateSample result{};
    if (cells_.empty()) return result;

    const glm::dvec3 direction = safeNormalize(directionBodyLocalInput);
    const double latitude = std::asin(std::clamp(direction.y, -1.0, 1.0));
    double longitude = std::atan2(direction.z, direction.x);
    if (longitude < -kPi) longitude += 2.0 * kPi;
    if (longitude >= kPi) longitude -= 2.0 * kPi;

    const double latCoord = (latitude + 0.5 * kPi) / kPi * latBands_ - 0.5;
    const double lonCoord = (longitude + kPi) / (2.0 * kPi) * lonBands_ - 0.5;
    const int lat0i = static_cast<int>(std::floor(latCoord));
    const int lon0i = static_cast<int>(std::floor(lonCoord));
    const double ty = latCoord - std::floor(latCoord);
    const double tx = lonCoord - std::floor(lonCoord);

    const auto clampLat = [&](int value) {
        return static_cast<std::uint32_t>(std::clamp(value, 0, static_cast<int>(latBands_) - 1));
    };
    const auto wrapLon = [&](int value) {
        int wrapped = value % static_cast<int>(lonBands_);
        if (wrapped < 0) wrapped += static_cast<int>(lonBands_);
        return static_cast<std::uint32_t>(wrapped);
    };
    const std::uint32_t lat0 = clampLat(lat0i);
    const std::uint32_t lat1 = clampLat(lat0i + 1);
    const std::uint32_t lon0 = wrapLon(lon0i);
    const std::uint32_t lon1 = wrapLon(lon0i + 1);

    const PlanetClimateCell& c00 = cells_[index(lat0, lon0)];
    const PlanetClimateCell& c10 = cells_[index(lat0, lon1)];
    const PlanetClimateCell& c01 = cells_[index(lat1, lon0)];
    const PlanetClimateCell& c11 = cells_[index(lat1, lon1)];
    const auto bilerp = [&](double a00, double a10, double a01, double a11) {
        const double a0 = a00 + (a10 - a00) * tx;
        const double a1 = a01 + (a11 - a01) * tx;
        return a0 + (a1 - a0) * ty;
    };

    const double surfaceTemperature = bilerp(
        c00.temperatureK, c10.temperatureK, c01.temperatureK, c11.temperatureK);
    const double humidity = bilerp(
        c00.specificHumidity, c10.specificHumidity, c01.specificHumidity, c11.specificHumidity);
    const double cloud = bilerp(
        c00.cloudFraction, c10.cloudFraction, c01.cloudFraction, c11.cloudFraction);
    const double precip = bilerp(
        c00.precipitationRateKgPerM2S,
        c10.precipitationRateKgPerM2S,
        c01.precipitationRateKgPerM2S,
        c11.precipitationRateKgPerM2S);
    const glm::dvec2 wind{
        bilerp(c00.windEastNorthMps.x, c10.windEastNorthMps.x, c01.windEastNorthMps.x, c11.windEastNorthMps.x),
        bilerp(c00.windEastNorthMps.y, c10.windEastNorthMps.y, c01.windEastNorthMps.y, c11.windEastNorthMps.y),
    };

    altitudeMeters = std::max(0.0, altitudeMeters);
    result.temperatureK = std::max(150.0, surfaceTemperature - config_.lapseRateKPerM * altitudeMeters);
    const double scaleHeight = config_.dryAirGasConstant * std::max(150.0, surfaceTemperature) / 9.80665;
    result.pressurePa = config_.seaLevelPressurePa
        * std::exp(-altitudeMeters / std::max(1.0, scaleHeight));
    result.densityKgPerM3 = result.pressurePa
        / (config_.dryAirGasConstant * std::max(1.0, result.temperatureK));
    const double qsat = saturationSpecificHumidity(result.temperatureK, std::max(1.0, result.pressurePa));
    result.relativeHumidity = qsat > 1.0e-8 ? saturate(humidity / qsat) : 0.0;
    result.cloudFraction = cloud;
    // 1 kg m^-2 equals 1 mm liquid water.
    result.precipitationRateMmPerHour = precip * 3600.0;

    const glm::dvec3 east = safeNormalize(glm::dvec3{-direction.z, 0.0, direction.x}, {1.0, 0.0, 0.0});
    const glm::dvec3 north = safeNormalize(glm::cross(direction, east), {0.0, 0.0, 1.0});
    result.windBodyLocalMps = east * wind.x + north * wind.y;
    return result;
}

} // namespace vf
