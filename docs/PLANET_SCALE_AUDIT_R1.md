# Planet Scale Audit R1 — Earthlike Aster

This document records the current whole-planet audit and the target scale contract for the next terrain-generation revision. It is intentionally kept on the audit branch until the generator satisfies the contract.

## Current production inputs

- Mean spherical radius: 6,371 km
- Diameter: 12,742 km
- Surface area implied by the sphere: 510.0645 million km²
- Maximum authored land elevation: +8,850 m
- Maximum authored ocean depth: -11,000 m
- Current gameplay atmosphere boundary: 100 km
- Current optical scattering shell: 145 km
- Plate cells: 14

## Current measured output — default seed 0x71A9F20D

500,000 equal-area Fibonacci sphere samples plus a 1-degree connected-component audit produced:

- Land: 31.94% = 162.9146 million km²
- Ocean: 68.06% = 347.1499 million km²
- Mean ocean depth: 5,390.5 m
- Ocean depth P50/P90/P99: 5,601.7 / 7,163.0 / 7,970.0 m
- Maximum sampled ocean depth: 10,372.1 m
- Land elevation P50/P90/P99: 1,295.2 / 3,472.0 / 8,850.0 m
- Maximum sampled land elevation: 8,850.0 m
- Four continent-scale connected land components at 1-degree resolution: 72.80, 54.51, 17.85 and 17.68 million km²
- No medium/small island hierarchy is resolved at that scale.

The P99 land elevation hitting the hard +8,850 m clamp is an explicit failure: Everest-class elevation is being used as a broad saturation ceiling rather than as an exceptionally rare local extreme.

## Current characteristic terrain wavelengths

For the current spherical 3-D noise frequencies, the approximate great-circle base wavelengths are:

- climate: 1,539.6 km
- regional relief: 55.6 km
- hills: 29.7 km
- local relief: 12.5 km
- canyon detail: 4.88 km
- dunes: 1.54 km
- micro relief: 0.77 km
- fine relief: 0.32 km

These scales explain the visual regression result: several masks exist numerically, but their geometry is dominated by relatively local noise instead of being organized by continent-, orogen-, basin- and watershed-scale structures.

## Earth reference envelope used for design

Authoritative references used for the contract:

- NASA Earth Facts: Earth equatorial diameter about 12,756 km; ocean about 71% of the surface; mean ocean depth about 3.6 km; inner core radius about 1,221 km; outer core thickness about 2,300 km; mantle about 2,900 km; average land crust about 30 km and ocean crust about 5 km.
- NOAA Ocean Exploration: mean ocean depth 3,682 m; Challenger Deep about 10,935 m.
- NOAA/ARL geodesy FAQ: Earth is oblate, approximately 6,378.1 km equatorial radius and 6,356.8 km polar radius.
- USGS global crust synthesis: deep-ocean crust commonly 6–7 km; continental crust 16–80 km with a weighted mean near 41 km.
- USGS Dynamic Earth: tectonic plates generally contain combinations of continental and oceanic lithosphere; a whole plate must not be treated as simply “continental” or “oceanic”.
- NASA atmospheric layers: troposphere ~0–12 km, stratosphere ~12–50 km, mesosphere ~50–80/85 km, thermosphere to roughly 600–700 km, exosphere extending to ~10,000 km.
- USGS: Andes length about 7,564 km; mid-ocean ridge network about 64,374 km.
- Barnes, Lehman & Mulla (2014): Priority-Flood depression handling / watershed labeling for DEM hydrology.
- WorldEngine: plate simulation -> noise -> precipitation/rain shadow -> erosion -> humidity/permeability -> biome.

## Production scale contract for the next generator

### 1. Planet geometry

Keep the gameplay mean radius at 6,371 km. It is already Earth-scale and gives a correct ~510 million km² surface. Oblateness is a later optional precision upgrade; it must not be faked by vertically exaggerating terrain.

### 2. Interior profile

The celestial body must gain an explicit interior profile independent of surface terrain:

- inner-core radius target: ~1,221 km
- outer-core outer radius target: ~3,480–3,520 km
- mantle extends from core-mantle boundary to the Moho
- oceanic crust target: ~5–7 km typical
- continental crust target: ~30–45 km typical, with much thicker roots possible beneath major orogens

These layers are initially authoritative metadata for future mining, drilling, geothermal, density, seismic and magnetic gameplay; they do not need to be rendered as concentric visible shells during normal play.

### 3. Atmosphere semantics

Do not use one 100 km number as “all atmosphere”. Separate physical/gameplay layers:

- troposphere/weather: ~0–12 km
- stratosphere: ~12–50 km
- mesosphere: ~50–85 km
- conventional space/Karman gameplay boundary: 100 km
- thermosphere/ionosphere: extend to hundreds of km
- exosphere: very thin tail to thousands of km

Visible blue optical scattering must remain concentrated close to the planet; the renderer must not draw a 10,000 km solid blue shell.

### 4. Land/ocean budget

Default Earthlike seeds should target:

- land fraction: 28.5–30.5%
- ocean fraction: 69.5–71.5%
- land area at this radius: roughly 145–156 million km²
- ocean area: roughly 354–365 million km²

Tectonic plates and continental crust must be separate fields. A tectonic plate may carry oceanic and continental lithosphere.

### 5. Bathymetry

Default-seed targets:

- mean ocean depth: 3.4–4.0 km
- abyssal plains: mostly ~3–6 km
- continental shelf: shallow, typically ending around ~200 m depth; gameplay shelf widths should predominantly be tens to low hundreds of km
- trenches: narrow, rare, locally reaching ~8–11 km
- mid-ocean ridges: long connected systems, not isolated circular bumps

### 6. Land elevation

The maximum +8.85 km value is a ceiling, not a common target.

For default Earthlike worlds:

- median land elevation should be in the low hundreds of metres to about 1 km, not ~1.3 km by default
- broad lowlands must dominate habitable continents
- major plateaus may sit around ~1–4 km
- major ranges commonly rise a few kilometres above surrounding terrain
- >7 km elevations must be exceptional and spatially tiny
- the 99th percentile must not equal the hard elevation clamp

### 7. Hierarchical landform sizes

Every landform has both a *province/network extent* and a *local cross-section scale*.

Game-design target envelopes, grounded in Earth magnitudes but tuned for readable gameplay:

- continental landmasses: ~1,000–10,000+ km scale
- microcontinents / very large islands: ~100–2,000 km scale
- island arcs/hotspot chains: hundreds to a few thousand km long, with individual islands much smaller
- mountain chains/orogenic belts: hundreds to several thousand km long; tens to several hundred km wide
- hill provinces: tens to hundreds of km; local relief commonly ~50–300 m
- plateaus/basins: hundreds to thousands of km
- canyons: local widths from sub-km to tens of km and depth from tens of metres to >1 km, embedded in drainage systems tens to hundreds of km long
- dune fields: provinces tens to hundreds of km, individual dune wavelengths from tens of metres to low kilometres depending dune type
- rivers: generated as connected drainage networks. Regional rivers should commonly span hundreds to thousands of km; rare major systems may approach ~4,000–6,500 km. They must monotonically drain according to the processed DEM except where lakes/reservoirs are deliberately modeled.

These are gameplay generation envelopes, not claims that every Earth landform lies in these exact ranges.

### 8. Hydrology acceptance rule

The existing trigonometric “river mask” is not a production river system. The next production hydrology stage must be based on a coarse spherical DEM, depression handling (Priority-Flood or equivalent), downhill flow direction and flow accumulation. River geometry, valleys, wetlands and biome moisture must consume the same watershed authority.

### 9. Island and coastline hierarchy

A default planet must not reduce to four smooth giant blobs. It needs hierarchical geography:

- several major continental masses
- smaller continental fragments / large islands
- volcanic island chains and arcs
- peninsulas, bays, straits, shelves and archipelagos

Small-scale coastline roughness must be subordinate to the macro crust geometry; noise alone must never decide continents.

### 10. Visual/gameplay exaggeration policy

Preserve real-world order of magnitude for planet, continents, oceans, major ranges, drainage basins and major rivers. Stylization may then amplify *local readability* rather than changing world scale:

- near-field ridge/cliff/canyon silhouette: roughly 1.2–1.8x visual emphasis where slope stability and collision remain valid
- color/material/vegetation contrast may be stronger than Earth satellite imagery
- large-scale height and horizontal extent must remain in plausible Earthlike order of magnitude

The goal is “a believable planet with readable adventure terrain”, not a physically exact GIS Earth and not a full-size sphere covered in miniature procedural noise.
