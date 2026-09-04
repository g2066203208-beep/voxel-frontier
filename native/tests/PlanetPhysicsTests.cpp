#include "vf/physics/PhysicsWorld.hpp"
#include "vf/physics/ShallowWater.hpp"
#include "vf/player/PlanetCamera.hpp"
#include "vf/world/PlanetSurface.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string_view>

#include <glm/geometric.hpp>

namespace {
[[noreturn]] void fail(std::string_view message) { std::cerr << "PLANET PHYSICS TEST FAILURE: " << message << '\n'; std::exit(1); }
void require(bool condition, std::string_view message) { if (!condition) fail(message); }

void testCubeSphereProjection() {
    for (std::uint32_t face = 0; face < 6U; ++face) for (double u : {-1.0, -0.25, 0.0, 0.75, 1.0}) for (double v : {-1.0, 0.0, 1.0})
        require(std::abs(glm::length(vf::cubeSphereDirection(face, u, v)) - 1.0) < 1.0e-12, "cube-sphere direction must be normalized");
}
void testPlanetSurfaceDeterminism() {
    vf::PlanetDefinition definition{}; definition.seed = 99; definition.radius = 200.0; definition.maxElevation = 20.0;
    const auto a = vf::buildPlanetSurface(definition, 12U); const auto b = vf::buildPlanetSurface(definition, 12U);
    require(a.vertices.size() == 6U * 13U * 13U, "planet vertex count mismatch");
    require(a.indices.size() == 6U * 12U * 12U * 6U, "planet index count mismatch");
    require(a.vertices.size() == b.vertices.size() && a.indices == b.indices, "planet topology must be deterministic");
    for (std::size_t i = 0; i < a.vertices.size(); i += 37U) {
        require(glm::length(a.vertices[i].position - b.vertices[i].position) < 1.0e-6F, "planet positions must be deterministic");
        const double r = glm::length(glm::dvec3{a.vertices[i].position});
        require(r >= definition.radius - definition.maxElevation - 1.0e-3, "planet vertex fell below legacy height bound");
        require(r <= definition.radius + definition.maxElevation + 1.0e-3, "planet vertex exceeded legacy height bound");
    }
}
void testEarthLikeRelief() {
    vf::PlanetDefinition d{}; d.seed = 0x71A9F20DULL; d.radius = 6371000.0; d.maxElevation = 8849.0; d.maxOceanDepthMeters = 11000.0;
    bool land=false,ocean=false,mountain=false,plateau=false,trench=false,volcano=false,river=false; double mn=1e30,mx=-1e30;
    for (std::uint32_t face=0; face<6U; ++face) for (int y=0;y<=48;++y) for(int x=0;x<=48;++x) {
        const double u=-1.0+2.0*x/48.0, v=-1.0+2.0*y/48.0; const auto s=vf::samplePlanetTerrain(d,vf::cubeSphereDirection(face,u,v));
        mn=std::min(mn,s.elevationMeters); mx=std::max(mx,s.elevationMeters); land=land||s.elevationMeters>100.0; ocean=ocean||s.elevationMeters<-500.0;
        mountain=mountain||s.mountain>0.55; plateau=plateau||s.plateau>0.45; trench=trench||s.trench>0.55; volcano=volcano||s.volcano>0.45; river=river||s.river>0.45;
    }
    require(land&&ocean,"Earth-like terrain must contain land and ocean"); require(mountain,"terrain must contain mountain belts");
    require(plateau,"terrain must contain plateaus"); require(trench,"bathymetry must contain trenches"); require(volcano,"terrain must contain volcanoes"); require(river,"terrain must contain river valleys");
    require(mn>=-d.maxOceanDepthMeters-1e-6,"bathymetry exceeded configured depth"); require(mx<=d.maxElevation+1e-6,"terrain exceeded configured elevation");
}
void testOceanSurfaceGeometry() {
    vf::PlanetDefinition d{}; d.radius=6371000.0; d.maxElevation=8849.0; d.maxOceanDepthMeters=11000.0; d.seaLevelElevationMeters=12.0;
    const auto mesh=vf::buildOceanSurfacePatch(d,{0,1,0},20000.0,24U); require(!mesh.vertices.empty()&&!mesh.indices.empty(),"ocean patch must be renderable");
    const double expected=d.radius+d.seaLevelElevationMeters; for(std::size_t i=0;i<mesh.vertices.size();i+=29U) {
        require(std::abs(glm::length(glm::dvec3{mesh.vertices[i].position})-expected)<1.0,"ocean vertices must stay on mean sea level");
        require(mesh.vertices[i].material.z>0.5F&&mesh.vertices[i].material.x<0.0F,"ocean must use water/transparent material path");
    }
}
void testRadialCamera() {
    vf::PlanetDefinition d{}; d.radius=240.0; d.maxElevation=18.0; vf::PlanetCamera camera{d}; const double initial=camera.altitude(); require(initial>=1.70&&initial<=1.80,"camera spawn eye height");
    vf::PlanetMovementInput toggle{}; toggle.toggleFlight=true; camera.update(toggle,1.0/60.0); require(camera.flightMode(),"flight toggle");
    vf::PlanetMovementInput ascend{}; ascend.vertical=1.0; ascend.sprint=true; camera.update(ascend,0.05); require(camera.altitude()>initial+3.0,"flight ascend"); require(std::abs(glm::length(camera.up())-1.0)<1e-12,"up normalized");
}
void testGroundedCameraCoRotates() {
    vf::PlanetDefinition d{}; d.radius=240.0; d.maxElevation=0.0; vf::CelestialSystem c; vf::CelestialBody p{}; p.radiusMeters=d.radius; p.massKg=9.81*p.radiusMeters*p.radiusMeters/vf::CelestialSystem::kGravitationalConstant; p.gameplaySurfaceGravityMps2=9.81; p.gravityInfluenceRadiusMeters=900; p.spinAxis={0,1,0}; p.spinRateRadPerSecond=0.01; const auto id=c.addBody(p);
    vf::PlanetCamera camera{d,&c,id}; const auto initial=camera.position(); vf::PlanetMovementInput idle{}; for(int i=0;i<240;++i){c.step(1.0/120.0);camera.update(idle,1.0/120.0);} require(camera.grounded(),"camera grounded"); require(glm::length(camera.position()-initial)>1.0,"grounded camera co-rotates"); require(std::abs(camera.altitude()-1.75)<0.05,"co-rotation vertical stability");
}
vf::PhysicsEnvironment makeVacuum(){ vf::PhysicsEnvironment e{}; e.planet.radius=100; e.planet.maxElevation=0; e.planet.atmosphereHeight=50; e.surfaceGravity=0; e.atmosphere.seaLevelPressurePa=0; e.atmosphere.gustAmplitude=0; e.atmosphere.prevailingWind={}; e.ocean.enabled=false; return e; }
void testFixedStepAndMomentum(){ auto e=makeVacuum(); vf::PhysicsWorld a{e},b{e}; vf::RigidBodyDesc d{}; d.mass=4;d.position={150,0,0};d.linearVelocity={3,-2,.5};d.linearDamping=0;d.angularDamping=0;d.aerodynamics.referenceArea=0;auto ai=a.createRigidBody(d),bi=b.createRigidBody(d);a.advance(1.0/60.0);b.advance(1.0/120.0);b.advance(1.0/120.0);require(glm::length(a.body(ai)->position-b.body(bi)->position)<1e-12,"fixed step");require(glm::length(a.body(ai)->linearMomentum()-glm::dvec3{12,-8,2})<1e-10,"momentum");}
void testRigidBodyCollisionMomentum(){auto e=makeVacuum();vf::PhysicsWorld w{e};vf::RigidBodyDesc a{};a.mass=2;a.position={150,-2,0};a.linearVelocity={0,5,0};a.collisionShape=vf::CollisionShape::sphere(.5);a.linearDamping=0;a.angularDamping=0;a.material.friction=0;a.material.restitution=.6;a.aerodynamics.referenceArea=0;auto b=a;b.mass=1;b.position={150,2,0};b.linearVelocity={0,-2,0};auto ai=w.createRigidBody(a),bi=w.createRigidBody(b);auto p=a.mass*a.linearVelocity+b.mass*b.linearVelocity;for(int i=0;i<120;++i)w.stepFixed();require(glm::length(w.body(ai)->linearMomentum()+w.body(bi)->linearMomentum()-p)<1e-7,"collision momentum");}
void testRadialGravityAndFriction(){vf::PhysicsEnvironment e{};e.planet.radius=100;e.planet.maxElevation=0;e.surfaceGravity=9.81;e.atmosphere.seaLevelPressurePa=0;e.ocean.enabled=false;vf::PhysicsWorld w{e};vf::RigidBodyDesc d{};d.mass=10;d.position={0,101,0};d.linearVelocity={8,0,0};d.collisionShape=vf::CollisionShape::sphere(1);d.linearDamping=0;d.material.friction=.9;d.material.restitution=0;d.aerodynamics.referenceArea=0;auto id=w.createRigidBody(d);for(int i=0;i<120;++i)w.stepFixed();require(glm::length(w.body(id)->linearVelocity)<8,"ground friction");require(glm::length(w.body(id)->position)>=100.999,"planet contact");}
void testAtmosphere(){vf::PhysicsEnvironment e{};e.planet.radius=1000;e.planet.atmosphereHeight=2000;e.surfaceGravity=9.81;e.weather.stormIntensity=.6;auto sea=e.sampleAtmosphere({0,1000,0},12),high=e.sampleAtmosphere({0,1500,0},12);require(sea.temperatureK>high.temperatureK&&sea.pressurePa>high.pressurePa&&sea.densityKgPerM3>high.densityKgPerM3,"atmosphere falls with altitude");require(glm::length(sea.windVelocity)>.1,"wind nonzero");}
void testBuoyancy(){vf::PhysicsEnvironment e{};e.planet.radius=100;e.planet.maxElevation=0;e.surfaceGravity=9.81;e.atmosphere.seaLevelPressurePa=0;e.ocean.enabled=true;e.ocean.surfaceRadius=110;e.ocean.densityKgPerM3=1000;vf::PhysicsWorld w{e};vf::RigidBodyDesc d{};d.mass=350;d.position={0,109,0};d.collisionShape=vf::CollisionShape::sphere(1);d.linearDamping=0;d.aerodynamics.referenceArea=0;d.buoyancy.enabled=true;d.buoyancy.displacedVolume=1;d.buoyancy.fluidDragCoefficient=.2;d.buoyancy.fluidReferenceArea=1;auto id=w.createRigidBody(d);for(int i=0;i<12;++i)w.stepFixed();require(glm::dot(w.body(id)->linearVelocity,glm::normalize(w.body(id)->position))>0,"buoyancy upward");}
void testShallowWater(){vf::ShallowWaterGrid water{4,1,1};water.cell(0,0).bedElevation=2;water.cell(1,0).bedElevation=1;water.cell(2,0).bedElevation=0;water.cell(3,0).bedElevation=-.5;water.addWater(0,0,1.5);double initial=water.totalWaterVolume();for(int i=0;i<240;++i)water.step(1.0/120.0,9.81);require(water.cell(3,0).waterDepth>0,"water downhill");require(std::abs(water.totalWaterVolume()-initial)<1e-9,"water conservation");}
}
int main(){testCubeSphereProjection();testPlanetSurfaceDeterminism();testEarthLikeRelief();testOceanSurfaceGeometry();testRadialCamera();testGroundedCameraCoRotates();testFixedStepAndMomentum();testRigidBodyCollisionMomentum();testRadialGravityAndFriction();testAtmosphere();testBuoyancy();testShallowWater();std::cout<<"vf_planet_physics_tests: PASS\n";return 0;}
