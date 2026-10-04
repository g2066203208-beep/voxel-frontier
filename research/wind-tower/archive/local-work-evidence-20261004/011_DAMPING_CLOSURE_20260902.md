# DTU158 damping closure

`EQ18_FINAL=PASS`. The formal Eq.(18) branch is `FORMAL_EFFECTIVE_EI`: concrete wall plus ordinary embedded longitudinal-rebar bending stiffness. PT is not separately added to linear material EI, avoiding duplicate treatment of its prestress/geometric-stiffness influence already present in the frozen gravity/modal state.

Final engineering equivalent modal damping ratios are SS1=4.6341%, FA1=4.6350%, SS2=5.5282% and FA2=5.5344%. The applied method is Li Shouzhen et al. (2024), Eq.(16)–(18), with concrete and steel baseline damping ratios of 5% and 2%, respectively. These are engineering equivalent structural modal damping ratios, not measured damping.

One global Rayleigh pair was fitted by Eq.(19) to the arithmetic mean targets of the first and second horizontal modal pairs: alpha=0.0634885913260676 s^-1 and beta=0.0212358837749239 s. The individual fit residuals are retained in `RAYLEIGH_PARAMETER_FIT.csv`.

The non-production Abaqus 2025 modal free-decay job `DTU158_RAYLEIGH_FREE_DECAY_VALIDATION_R2` used 30 inherited modes and a 10 kN, 0.10–0.20 s horizontal pulse in U1 and U3. It completed with zero errors. Decay estimates at the RNA reference point are U1=4.6703% and U3=4.6569%, respectively 0.036 and 0.022 percentage points above the Eq.(18) first-pair targets. `RAYLEIGH_VALIDATION=PASS`.

This closure does not modify OpenFAST, TurbSim, or any production Abaqus model. A subsequent non-production OpenFAST 1 NTM + 1 ETM regression may assess response sensitivity before deciding on any 36-case rerun.

