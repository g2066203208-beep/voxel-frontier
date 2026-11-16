#include "interface.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace joint {
namespace {
void validate(const Parameters& p,double gap,const std::array<double,2>& ds,
              const State& old) {
  if (!(std::isfinite(p.normal_stiffness) && p.normal_stiffness>0 &&
        std::isfinite(p.tangent_stiffness) && p.tangent_stiffness>0 &&
        std::isfinite(p.mu_peak) && p.mu_peak>=0 &&
        std::isfinite(p.mu_residual) && p.mu_residual>=0 &&
        p.mu_peak>=p.mu_residual &&
        std::isfinite(p.weakening_distance) && p.weakening_distance>0 &&
        std::isfinite(gap) && std::isfinite(ds[0]) && std::isfinite(ds[1]) &&
        std::isfinite(old.traction[0]) && std::isfinite(old.traction[1]) &&
        std::isfinite(old.accumulated_slip) && old.accumulated_slip>=0))
    throw std::invalid_argument("nonphysical/invalid interface-point input");
}
double coefficient(const Parameters& p,double accumulated,Law law) {
  if(law==Law::ConstantCoulomb) return p.mu_peak;
  return p.mu_residual+(p.mu_peak-p.mu_residual)*
         std::exp(-accumulated/p.weakening_distance);
}
}
Response update(const Parameters& p,State& state,double gap,
                const std::array<double,2>& ds,Law law) {
  validate(p,gap,ds,state);
  Response out;
  out.normal_pressure=p.normal_stiffness*std::max(0.0,-gap);
  if(out.normal_pressure==0.0) {
    state.traction={0.0,0.0};
    state.closed=false;
    return out;
  }
  out.closed=true;
  const auto prev=state.closed?state.traction:std::array<double,2>{0.0,0.0};
  const std::array<double,2> trial{
    prev[0]+p.tangent_stiffness*ds[0],prev[1]+p.tangent_stiffness*ds[1]};
  const double magnitude=std::hypot(trial[0],trial[1]);
  const double limit=out.normal_pressure*coefficient(p,state.accumulated_slip,law);
  if(magnitude<=limit+1.e-11*std::max(1.0,limit)) {
    state.traction=trial;
    out.shear_traction=trial;
    out.mobilized_mu=coefficient(p,state.accumulated_slip,law);
    state.closed=true;
    return out;
  }
  // Reject an unverified nonmonotonic local return-map domain.
  if(law==Law::IllustrativeWeakening &&
     p.tangent_stiffness<=out.normal_pressure*
       (p.mu_peak-p.mu_residual)/p.weakening_distance)
    throw std::domain_error("softening return map outside verified monotonic domain");
  const auto residual=[&](double gamma){
    return magnitude-p.tangent_stiffness*gamma-
      out.normal_pressure*coefficient(p,state.accumulated_slip+gamma,law);
  };
  double lo=0.0,hi=magnitude/p.tangent_stiffness;
  for(int i=0;i<100;++i) {
    double mid=0.5*(lo+hi);
    if(residual(mid)>0) lo=mid; else hi=mid;
  }
  const double gamma=0.5*(lo+hi);
  state.accumulated_slip+=gamma;
  out.incremental_plastic_slip=gamma;
  out.mobilized_mu=coefficient(p,state.accumulated_slip,law);
  const double strength=out.normal_pressure*out.mobilized_mu;
  out.shear_traction={strength*trial[0]/magnitude,
                      strength*trial[1]/magnitude};
  state.traction=out.shear_traction;
  state.closed=true;out.sliding=true;
  return out;
}
} // namespace joint
