#pragma once
#include <array>
namespace joint {
// SI: pressure/traction Pa, gap and slip m, k_n/k_t Pa/m.
// Independent constitutive-point benchmark; not a finite-element solver.
struct Parameters {
  double normal_stiffness=1.0e10, tangent_stiffness=1.0e9;
  double mu_peak=0.65, mu_residual=0.35, weakening_distance=0.003;
};
struct State {
  std::array<double,2> traction{0.0,0.0};
  double accumulated_slip=0.0;
  bool closed=false;
};
struct Response {
  double normal_pressure=0.0;
  std::array<double,2> shear_traction{0.0,0.0};
  double mobilized_mu=0.0, incremental_plastic_slip=0.0;
  bool closed=false, sliding=false;
};
enum class Law { ConstantCoulomb, IllustrativeWeakening };
// Not an Abaqus user subroutine, nor a validated constitutive law.
Response update(const Parameters& p,State& history,double gap,
                const std::array<double,2>& slip_increment,Law law);
} // namespace joint
