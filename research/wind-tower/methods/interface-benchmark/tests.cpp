#include "interface.hpp"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
using namespace joint;
static unsigned count=0;
void check(bool yes,const char* name){
  if(!yes)throw std::runtime_error(std::string("FAIL: ")+name);
  ++count;
}
void close(double a,double b,double tol,const char* name){
  check(std::abs(a-b)<=tol*std::max({1.0,std::abs(a),std::abs(b)}),name);
}
int main(){
try {
  Parameters p;p.mu_peak=.5;p.mu_residual=.3;
  State a;
  auto r=update(p,a,1.e-5,{.001,0},Law::ConstantCoulomb);
  check(!r.closed&&!r.sliding,"open status");
  close(r.normal_pressure,0,1.e-13,"open normal");
  close(r.shear_traction[0],0,1.e-13,"open shear");
  r=update(p,a,-1.e-4,{.0002,0},Law::ConstantCoulomb);
  close(r.normal_pressure,1.e6,1.e-12,"normal pressure");
  check(r.closed&&!r.sliding,"stick status");
  close(r.shear_traction[0],.2e6,1.e-12,"elastic predictor");
  r=update(p,a,-1.e-4,{.001,0},Law::ConstantCoulomb);
  check(r.sliding,"switch to sliding");
  close(r.shear_traction[0],.5e6,1.e-12,"Coulomb cap");
  close(r.incremental_plastic_slip,.0007,1.e-12,"closed form return map");
  close(a.accumulated_slip,.0007,1.e-12,"cumulative history");
  r=update(p,a,-1.e-4,{0,0},Law::ConstantCoulomb);
  close(r.shear_traction[0],.5e6,1.e-12,"stationary hold");
  r=update(p,a,-1.e-4,{-0.0004,0},Law::ConstantCoulomb);
  close(r.shear_traction[0],.1e6,1.e-12,"reverse shear stick");
  r=update(p,a,.0001,{.01,0},Law::ConstantCoulomb);
  check(!r.closed,"interface opens");
  close(a.traction[0],0,1.e-13,"shear released on opening");
  check(a.accumulated_slip>0,"plastic history retained");
  State b;
  r=update(p,b,-1.e-4,{.002,.001},Law::ConstantCoulomb);
  close(std::hypot(r.shear_traction[0],r.shear_traction[1]),.5e6,1.e-12,"vector traction norm");
  close(r.shear_traction[0]/r.shear_traction[1],2,1.e-12,"vector slip direction");
  State c;p.mu_peak=.65;p.mu_residual=.35;p.weakening_distance=.003;
  r=update(p,c,-1.e-4,{.002,0},Law::IllustrativeWeakening);
  check(r.sliding,"illustrative weakening slides");
  check(r.mobilized_mu<.65&&r.mobilized_mu>.35,"bounded law");
  close(r.shear_traction[0],r.mobilized_mu*r.normal_pressure,1.e-12,"weakening envelope");
  close(r.shear_traction[0]+p.tangent_stiffness*r.incremental_plastic_slip,
        2.e6,1.e-12,"implicit yield consistency");
  const double earlier=c.accumulated_slip;
  r=update(p,c,-1.e-4,{.001,0},Law::IllustrativeWeakening);
  check(c.accumulated_slip>=earlier&&r.mobilized_mu<=.65,"history monotonicity");
  bool rejected=false;
  try{Parameters bad=p;bad.tangent_stiffness=1.e6;State d;
      update(bad,d,-1.e-4,{1.0,0},Law::IllustrativeWeakening);}
  catch(const std::domain_error&){rejected=true;}
  check(rejected,"nonmonotonic return map rejected");
  rejected=false;
  try{Parameters bad=p;bad.mu_peak=-.1;State d;
      update(bad,d,-1.e-4,{0,0},Law::ConstantCoulomb);}
  catch(const std::invalid_argument&){rejected=true;}
  check(rejected,"negative friction rejected");
  std::cout<<"PASS "<<count<<" independent mathematical assertions\n";
  return 0;
} catch(const std::exception& ex){std::cerr<<ex.what()<<'\n';return 1;}
}
