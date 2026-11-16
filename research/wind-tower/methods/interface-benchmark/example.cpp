#include "interface.hpp"
#include <iomanip>
#include <iostream>
using namespace joint;
// Synthetic reproducibility only. Never label these points as experiments.
int main(){
  Parameters p; State constant, weakening;
  std::cout<<"step,synthetic_slip_m,p_Pa,coulomb_tau_Pa,hypothetical_tau_Pa,hypothetical_mu\n";
  for(int i=1;i<=15;++i){
    auto c=update(p,constant,-.0001,{.0002,0},Law::ConstantCoulomb);
    auto w=update(p,weakening,-.0001,{.0002,0},Law::IllustrativeWeakening);
    std::cout<<i<<','<<std::setprecision(9)<<i*.0002<<','<<c.normal_pressure
             <<','<<c.shear_traction[0]<<','<<w.shear_traction[0]
             <<','<<w.mobilized_mu<<'\n';
  }
}
