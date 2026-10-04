1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:03:08
   For use by Supplied by Team-SolidSQUAD under license from Dassault Systemes or its subsidiary.

 T026 new reconstructed tower plus recovered distributed rigid RNA; SI units     
                                                                                 
 STEP    1     INCREMENT     1     STEP TIME    0.00    


                        S T E P       1     S T A T I C   A N A L Y S I S


                                                                                          

     AUTOMATIC TIME CONTROL WITH -
          A SUGGESTED INITIAL TIME INCREMENT OF                5.000E-02
          AND A TOTAL TIME PERIOD OF                            1.00    
          THE MINIMUM TIME INCREMENT ALLOWED IS                1.000E-08
          THE MAXIMUM TIME INCREMENT ALLOWED IS                0.100    

     LINEAR EQUATION SOLVER TYPE         DIRECT SPARSE

 CONVERGENCE TOLERANCE PARAMETERS FOR FORCE    
     CRITERION FOR RESIDUAL FORCE     FOR A NONLINEAR PROBLEM          5.000E-03
     CRITERION FOR DISP.    CORRECTION IN A NONLINEAR PROBLEM          1.000E-02
     INITIAL VALUE OF TIME AVERAGE FORCE                               1.000E-02
     AVERAGE FORCE     IS TIME AVERAGE FORCE    
     ALTERNATE CRIT. FOR RESIDUAL FORCE     FOR A NONLINEAR PROBLEM    2.000E-02
     CRITERION FOR ZERO FORCE     RELATIVE TO TIME AVRG. FORCE         1.000E-05
     CRITERION FOR RESIDUAL FORCE     WHEN THERE IS ZERO FLUX          1.000E-05
     CRITERION FOR DISP.    CORRECTION WHEN THERE IS ZERO FLUX         1.000E-03
     CRITERION FOR RESIDUAL FORCE     FOR A LINEAR INCREMENT           1.000E-08
     FIELD CONVERSION RATIO                                             1.00    
     CRITERION FOR ZERO FORCE     REL. TO TIME AVRG. MAX. FORCE        1.000E-05
     CRITERION FOR ZERO DISP.    RELATIVE TO CHARACTERISTIC LENGTH     1.000E-08

 CONVERGENCE TOLERANCE PARAMETERS FOR MOMENT   
     CRITERION FOR RESIDUAL MOMENT    FOR A NONLINEAR PROBLEM          5.000E-03
     CRITERION FOR ROTATION CORRECTION IN A NONLINEAR PROBLEM          1.000E-02
     INITIAL VALUE OF TIME AVERAGE MOMENT                              1.000E-02
     AVERAGE MOMENT    IS TIME AVERAGE MOMENT   
     ALTERNATE CRIT. FOR RESIDUAL MOMENT    FOR A NONLINEAR PROBLEM    2.000E-02
     CRITERION FOR ZERO MOMENT    RELATIVE TO TIME AVRG. MOMENT        1.000E-05
     CRITERION FOR RESIDUAL MOMENT    WHEN THERE IS ZERO FLUX          1.000E-05
     CRITERION FOR ROTATION CORRECTION WHEN THERE IS ZERO FLUX         1.000E-03
     CRITERION FOR RESIDUAL MOMENT    FOR A LINEAR INCREMENT           1.000E-08
     FIELD CONVERSION RATIO                                             1.00    
     CRITERION FOR ZERO MOMENT    REL. TO TIME AVRG. MAX. MOMENT       1.000E-05

     VOLUMETRIC STRAIN COMPATIBILITY TOLERANCE FOR HYBRID SOLIDS       1.000E-05
     AXIAL STRAIN COMPATIBILITY TOLERANCE FOR HYBRID BEAMS             1.000E-05
     TRANS. SHEAR STRAIN COMPATIBILITY TOLERANCE FOR HYBRID BEAMS      1.000E-05
     SOFT CONTACT CONSTRAINT COMPATIBILITY TOLERANCE FOR P>P0          5.000E-03
     SOFT CONTACT CONSTRAINT COMPATIBILITY TOLERANCE FOR P=0.0         0.100    
     CONTACT FORCE ERROR TOLERANCE FOR CONVERT SDI=YES                 1.00    
     DISPLACEMENT COMPATIBILITY TOLERANCE FOR DCOUP ELEMENTS           1.000E-05
     ROTATION COMPATIBILITY TOLERANCE FOR DCOUP ELEMENTS               1.000E-05

 EQUILIBRIUM WILL BE CHECKED FOR SEVERE DISCONTINUITY ITERATIONS

 TIME INCREMENTATION CONTROL PARAMETERS:
     FIRST EQUILIBRIUM ITERATION FOR CONSECUTIVE DIVERGENCE CHECK              4
     EQUILIBRIUM ITERATION AT WHICH LOG. CONVERGENCE RATE CHECK BEGINS         8
     EQUILIBRIUM ITERATION AFTER WHICH ALTERNATE RESIDUAL IS USED              9
     MAXIMUM EQUILIBRIUM ITERATIONS ALLOWED                                   16
     EQUILIBRIUM ITERATION COUNT FOR CUT-BACK IN NEXT INCREMENT               10
     MAXIMUM EQUILIB. ITERS IN TWO INCREMENTS FOR TIME INCREMENT INCREASE      4
     MAXIMUM ITERATIONS FOR SEVERE DISCONTINUITIES                            50
     MAXIMUM ATTEMPTS ALLOWED IN AN INCREMENT                                  5
     MAXIMUM DISCON. ITERS IN TWO INCREMENTS FOR TIME INCREMENT INCREASE      50
     MAXIMUM CONTACT AUGMENTATIONS FOR *SURFACE BEHAVIOR,AUGMENTED LAGRANGE   50
     CUT-BACK FACTOR AFTER DIVERGENCE                                 0.2500    
     CUT-BACK FACTOR FOR TOO SLOW CONVERGENCE                         0.5000    
     CUT-BACK FACTOR AFTER TOO MANY EQUILIBRIUM ITERATIONS            0.7500    
     CUT-BACK FACTOR AFTER TOO MANY SEVERE DISCONTINUITY ITERATIONS   0.2500    
     CUT-BACK FACTOR AFTER PROBLEMS IN ELEMENT ASSEMBLY               0.2500    
     INCREASE FACTOR AFTER TWO INCREMENTS THAT CONVERGE QUICKLY        1.500    
     MAX. TIME INCREMENT INCREASE FACTOR ALLOWED                       1.500    
     MAX. TIME INCREMENT INCREASE FACTOR ALLOWED (DYNAMICS)            1.250    
     MAX. TIME INCREMENT INCREASE FACTOR ALLOWED (DIFFUSION)           2.000    
     MINIMUM TIME INCREMENT RATIO FOR EXTRAPOLATION TO OCCUR          0.1000    
     MAX. RATIO OF TIME INCREMENT TO STABILITY LIMIT                   1.000    
     FRACTION OF STABILITY LIMIT FOR NEW TIME INCREMENT               0.9500    
     TIME INCREMENT INCREASE FACTOR BEFORE A TIME POINT                1.000    
     GLOBAL STABILIZATION CONTROL IS NOT USED

          PRINT OF INCREMENT NUMBER, TIME, ETC., EVERY    1  INCREMENTS

     THE MAXIMUM NUMBER OF INCREMENTS IN THIS STEP IS                     500

          LARGE DISPLACEMENT THEORY WILL BE USED

          UNSYMMETRIC MATRIX STORAGE AND SOLUTION WILL BE USED

     LINEAR EXTRAPOLATION WILL BE USED

     CHARACTERISTIC ELEMENT LENGTH      3.04    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     PARALLEL CONTACT TRACKING ENABLED


     COLLECTING MODEL CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS
 
     CONTACT INITIAL STRESS CALCULATIONS ARE TURNED ON IN ZEROINC


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  5.000E-02
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            4437
                              2            4608
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  57ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.630E+03   TIME AVG. FORCE       2.630E+03
 LARGEST SCALED RESIDUAL FORCE     -1.120E+03   AT NODE        189   DOF  3
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -1.120E+03
 LARGEST INCREMENT OF DISP.        -8.909E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -8.909E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.546E+04   TIME AVG. MOMENT      3.546E+04
 LARGEST SCALED RESIDUAL MOMENT     -16.1       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -16.1    
 LARGEST INCREMENT OF ROTATION     -6.217E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -6.217E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -4.512E-07
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  32ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.629E+03   TIME AVG. FORCE       2.629E+03
 LARGEST SCALED RESIDUAL FORCE     -0.238       AT NODE         70   DOF  2
   INSTANCE: SSEG_03-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -0.238    
 LARGEST INCREMENT OF DISP.        -8.951E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.154E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.570E+04   TIME AVG. MOMENT      3.570E+04
 LARGEST SCALED RESIDUAL MOMENT    -9.353E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -9.353E-02
 LARGEST INCREMENT OF ROTATION     -6.241E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.470E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  5.000E-02,  FRACTION OF STEP COMPLETED  5.000E-02
 STEP TIME COMPLETED       5.000E-02,  TOTAL TIME COMPLETED        5.000E-02


  INCREMENT     2 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  5.000E-02
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  30ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.992E+03   TIME AVG. FORCE       4.311E+03
 LARGEST SCALED RESIDUAL FORCE       190.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       190.    
 LARGEST INCREMENT OF DISP.        -9.035E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -8.403E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.169E+05   TIME AVG. MOMENT      2.263E+05
 LARGEST SCALED RESIDUAL MOMENT    -0.222       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.222    
 LARGEST INCREMENT OF ROTATION     -6.291E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -5.001E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  22ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.992E+03   TIME AVG. FORCE       4.311E+03
 LARGEST SCALED RESIDUAL FORCE      2.923E-02   AT NODE         74   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      2.923E-02
 LARGEST INCREMENT OF DISP.        -9.035E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.865E-07   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.170E+05   TIME AVG. MOMENT      2.263E+05
 LARGEST SCALED RESIDUAL MOMENT    -6.676E-03   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -6.676E-03
 LARGEST INCREMENT OF ROTATION     -6.292E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.788E-09   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          TIME INCREMENT MAY NOW INCREASE TO    7.500E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  5.000E-02,  FRACTION OF STEP COMPLETED  0.100    
 STEP TIME COMPLETED       0.100    ,  TOTAL TIME COMPLETED        0.100    


  INCREMENT     3 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  7.500E-02
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  26ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.038E+04   TIME AVG. FORCE       6.334E+03
 LARGEST SCALED RESIDUAL FORCE       363.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       363.    
 LARGEST INCREMENT OF DISP.        -1.371E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -1.603E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     7.372E+05   TIME AVG. MOMENT      3.966E+05
 LARGEST SCALED RESIDUAL MOMENT    -0.639       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.639    
 LARGEST INCREMENT OF ROTATION     -9.533E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -9.534E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -2.267E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  30ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.038E+04   TIME AVG. FORCE       6.334E+03
 LARGEST SCALED RESIDUAL FORCE      6.742E-02   AT NODE         64   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      6.742E-02
 LARGEST INCREMENT OF DISP.        -1.371E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -1.404E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     7.373E+05   TIME AVG. MOMENT      3.966E+05
 LARGEST SCALED RESIDUAL MOMENT    -1.785E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -1.785E-02
 LARGEST INCREMENT OF ROTATION     -9.533E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -8.049E-09   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          TIME INCREMENT MAY NOW INCREASE TO    0.100    

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  7.500E-02,  FRACTION OF STEP COMPLETED  0.175    
 STEP TIME COMPLETED       0.175    ,  TOTAL TIME COMPLETED        0.175    


  INCREMENT     4 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  29ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.625E+04   TIME AVG. FORCE       8.814E+03
 LARGEST SCALED RESIDUAL FORCE       692.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       692.    
 LARGEST INCREMENT OF DISP.        -1.859E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.061E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.175E+06   TIME AVG. MOMENT      5.911E+05
 LARGEST SCALED RESIDUAL MOMENT     -1.63       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.63    
 LARGEST INCREMENT OF ROTATION     -1.289E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -1.820E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -6.061E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  30ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.625E+04   TIME AVG. FORCE       8.814E+03
 LARGEST SCALED RESIDUAL FORCE      0.130       AT NODE         74   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.130    
 LARGEST INCREMENT OF DISP.        -1.860E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.621E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.175E+06   TIME AVG. MOMENT      5.912E+05
 LARGEST SCALED RESIDUAL MOMENT    -4.957E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -4.957E-02
 LARGEST INCREMENT OF ROTATION     -1.290E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.075E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.275    
 STEP TIME COMPLETED       0.275    ,  TOTAL TIME COMPLETED        0.275    


  INCREMENT     5 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  29ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.218E+04   TIME AVG. FORCE       1.149E+04
 LARGEST SCALED RESIDUAL FORCE       813.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       813.    
 LARGEST INCREMENT OF DISP.        -1.896E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.610E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.624E+06   TIME AVG. MOMENT      7.978E+05
 LARGEST SCALED RESIDUAL MOMENT     -1.90       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.90    
 LARGEST INCREMENT OF ROTATION     -1.311E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.145E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -8.082E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  42ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.218E+04   TIME AVG. FORCE       1.149E+04
 LARGEST SCALED RESIDUAL FORCE      0.139       AT NODE         84   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.139    
 LARGEST INCREMENT OF DISP.        -1.896E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.327E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.625E+06   TIME AVG. MOMENT      7.979E+05
 LARGEST SCALED RESIDUAL MOMENT    -6.019E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -6.019E-02
 LARGEST INCREMENT OF ROTATION     -1.311E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.480E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.375    
 STEP TIME COMPLETED       0.375    ,  TOTAL TIME COMPLETED        0.375    


  INCREMENT     6 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  23ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.813E+04   TIME AVG. FORCE       1.426E+04
 LARGEST SCALED RESIDUAL FORCE       841.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       841.    
 LARGEST INCREMENT OF DISP.        -1.933E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.739E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.087E+06   TIME AVG. MOMENT      1.013E+06
 LARGEST SCALED RESIDUAL MOMENT     -1.96       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.96    
 LARGEST INCREMENT OF ROTATION     -1.333E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.219E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -8.421E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  32ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.813E+04   TIME AVG. FORCE       1.426E+04
 LARGEST SCALED RESIDUAL FORCE     -0.159       AT NODE         79   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -0.159    
 LARGEST INCREMENT OF DISP.        -1.934E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.540E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.087E+06   TIME AVG. MOMENT      1.013E+06
 LARGEST SCALED RESIDUAL MOMENT    -6.540E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -6.540E-02
 LARGEST INCREMENT OF ROTATION     -1.334E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.602E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.475    
 STEP TIME COMPLETED       0.475    ,  TOTAL TIME COMPLETED        0.475    


  INCREMENT     7 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  53ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.408E+04   TIME AVG. FORCE       1.709E+04
 LARGEST SCALED RESIDUAL FORCE       870.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       870.    
 LARGEST INCREMENT OF DISP.        -1.973E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.874E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.563E+06   TIME AVG. MOMENT      1.234E+06
 LARGEST SCALED RESIDUAL MOMENT     -2.03       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -2.03    
 LARGEST INCREMENT OF ROTATION     -1.357E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.298E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -8.782E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  32ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.408E+04   TIME AVG. FORCE       1.709E+04
 LARGEST SCALED RESIDUAL FORCE      0.165       AT NODE         74   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.165    
 LARGEST INCREMENT OF DISP.        -1.973E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.767E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.563E+06   TIME AVG. MOMENT      1.234E+06
 LARGEST SCALED RESIDUAL MOMENT    -6.970E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -6.970E-02
 LARGEST INCREMENT OF ROTATION     -1.357E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.731E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.575    
 STEP TIME COMPLETED       0.575    ,  TOTAL TIME COMPLETED        0.575    


  INCREMENT     8 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  27ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.004E+04   TIME AVG. FORCE       1.996E+04
 LARGEST SCALED RESIDUAL FORCE       901.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       901.    
 LARGEST INCREMENT OF DISP.        -2.013E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.016E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.053E+06   TIME AVG. MOMENT      1.462E+06
 LARGEST SCALED RESIDUAL MOMENT     -2.09       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -2.09    
 LARGEST INCREMENT OF ROTATION     -1.381E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.380E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -9.154E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  34ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.004E+04   TIME AVG. FORCE       1.996E+04
 LARGEST SCALED RESIDUAL FORCE     -0.182       AT NODE         69   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -0.182    
 LARGEST INCREMENT OF DISP.        -2.014E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.008E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.053E+06   TIME AVG. MOMENT      1.462E+06
 LARGEST SCALED RESIDUAL MOMENT    -7.569E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -7.569E-02
 LARGEST INCREMENT OF ROTATION     -1.381E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.869E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.675    
 STEP TIME COMPLETED       0.675    ,  TOTAL TIME COMPLETED        0.675    


  INCREMENT     9 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  44ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.603E+04   TIME AVG. FORCE       2.286E+04
 LARGEST SCALED RESIDUAL FORCE       933.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       933.    
 LARGEST INCREMENT OF DISP.        -2.055E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.165E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.557E+06   TIME AVG. MOMENT      1.694E+06
 LARGEST SCALED RESIDUAL MOMENT     -2.16       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -2.16    
 LARGEST INCREMENT OF ROTATION     -1.406E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.466E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -9.549E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  35ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.603E+04   TIME AVG. FORCE       2.286E+04
 LARGEST SCALED RESIDUAL FORCE      0.182       AT NODE         64   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.182    
 LARGEST INCREMENT OF DISP.        -2.056E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.264E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.557E+06   TIME AVG. MOMENT      1.694E+06
 LARGEST SCALED RESIDUAL MOMENT    -8.078E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -8.078E-02
 LARGEST INCREMENT OF ROTATION     -1.406E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -3.015E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.775    
 STEP TIME COMPLETED       0.775    ,  TOTAL TIME COMPLETED        0.775    


  INCREMENT    10 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  37ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.201E+04   TIME AVG. FORCE       2.577E+04
 LARGEST SCALED RESIDUAL FORCE       967.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       967.    
 LARGEST INCREMENT OF DISP.        -2.099E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.322E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.076E+06   TIME AVG. MOMENT      1.933E+06
 LARGEST SCALED RESIDUAL MOMENT     -2.24       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -2.24    
 LARGEST INCREMENT OF ROTATION     -1.432E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.557E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -9.972E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  35ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.201E+04   TIME AVG. FORCE       2.577E+04
 LARGEST SCALED RESIDUAL FORCE      0.202       AT NODE         64   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.202    
 LARGEST INCREMENT OF DISP.        -2.100E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.536E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.076E+06   TIME AVG. MOMENT      1.933E+06
 LARGEST SCALED RESIDUAL MOMENT    -8.694E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -8.694E-02
 LARGEST INCREMENT OF ROTATION     -1.432E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -3.171E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.875    
 STEP TIME COMPLETED       0.875    ,  TOTAL TIME COMPLETED        0.875    


  INCREMENT    11 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  35ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.799E+04   TIME AVG. FORCE       2.870E+04
 LARGEST SCALED RESIDUAL FORCE      1.003E+03   AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      1.003E+03
 LARGEST INCREMENT OF DISP.        -2.145E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.486E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.610E+06   TIME AVG. MOMENT      2.176E+06
 LARGEST SCALED RESIDUAL MOMENT     -2.31       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -2.31    
 LARGEST INCREMENT OF ROTATION     -1.458E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.652E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -1.041E-07
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  29ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.800E+04   TIME AVG. FORCE       2.870E+04
 LARGEST SCALED RESIDUAL FORCE      0.212       AT NODE         64   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.212    
 LARGEST INCREMENT OF DISP.        -2.145E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.827E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.610E+06   TIME AVG. MOMENT      2.176E+06
 LARGEST SCALED RESIDUAL MOMENT    -9.360E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -9.360E-02
 LARGEST INCREMENT OF ROTATION     -1.459E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -3.338E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.975    
 STEP TIME COMPLETED       0.975    ,  TOTAL TIME COMPLETED        0.975    


  INCREMENT    12 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.500E-02
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  25ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.978E+04   TIME AVG. FORCE       3.129E+04
 LARGEST SCALED RESIDUAL FORCE       163.       AT NODE        189   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       163.    
 LARGEST INCREMENT OF DISP.        -5.436E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -7.267E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.746E+06   TIME AVG. MOMENT      2.390E+06
 LARGEST SCALED RESIDUAL MOMENT    -8.273E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -8.273E-02
 LARGEST INCREMENT OF ROTATION     -3.690E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -4.287E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION   -6.281E-09
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.021e+08
        SOLVER ELAPSED TIME:  28ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.978E+04   TIME AVG. FORCE       3.129E+04
 LARGEST SCALED RESIDUAL FORCE      2.023E-02   AT NODE        104   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      2.023E-02
 LARGEST INCREMENT OF DISP.        -5.436E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -2.369E-07   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.746E+06   TIME AVG. MOMENT      2.390E+06
 LARGEST SCALED RESIDUAL MOMENT    -3.103E-03   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -3.103E-03
 LARGEST INCREMENT OF ROTATION     -3.690E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -1.357E-09   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  2.500E-02,  FRACTION OF STEP COMPLETED   1.00    
 STEP TIME COMPLETED        1.00    ,  TOTAL TIME COMPLETED         1.00    
1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:03:59
   For use by Supplied by Team-SolidSQUAD under license from Dassault Systemes or its subsidiary.

 T026 new reconstructed tower plus recovered distributed rigid RNA; SI units     
                                                                                 
 STEP    2     INCREMENT     1     STEP TIME    0.00    


                        S T E P       2     C A L C U L A T I O N   O F   E I G E N V A L U E S

                                            F O R   N A T U R A L   F R E Q U E N C I E S



                                                                                          

     THE LANCZOS EIGENSOLVER IS USED FOR THIS ANALYSIS
     SYSTEM DATA WILL BE WRITTEN TO THE .SIM FILE

     Abaqus WILL COMPUTE UNCOUPLED
      STRUCTURAL AND ACOUSTIC MODES
     NUMBER OF EIGENVALUES                     30
     HIGHEST FREQUENCY OF INTEREST                  1.00000E+18
     MAXIMUM NUMBER OF STEPS WITHIN RUN               35
     BLOCK SIZE FOR LANCZOS PROCEDURE                  7
     THE EIGENVECTORS ARE SCALED SO THAT 
      THE GENERALIZED MASS IN EACH VECTOR IS UNITY
                              INITIAL STRESS AND DISPLACEMENT EFFECTS ARE
                              INCLUDED IN THE STIFFNESS MATRIX

     THIS IS A LINEAR PERTURBATION STEP.
     ALL LOADS ARE DEFINED AS CHANGE IN LOAD TO THE REFERENCE STATE

          LARGE DISPLACEMENT THEORY WILL BE USED

     EXTRAPOLATION WILL NOT BE USED

     CHARACTERISTIC ELEMENT LENGTH      3.04    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

     CHECK POINT  START OF SOLVER     
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            4352
                              2            4693
 
 SMP LANCZOS SOLVER RUNNING ON 1 HOST USING 2 THREADS
 
 NEW DIRECT SPARSE SOLVER WILL BE USED.
  
 COMPUTER PRECISION USED BY ABAQUS       2.22045e-16
 CONVERGENCE CRITERION FOR LANCZOS RUN   1.81899e-12
  
 NUMBER OF EQUATIONS                                                           16848
 NUMBER OF UNRESTRAINED DEGREES OF FREEDOM                                     11460
 HEURISTIC SCALE FOR THE FIRST NONZERO EIGENVALUES (PROBLEM SCALE)   1.96231e-02
 INITIAL SHIFT VALUE                                                 0.00000e+00
  
 NUMBER OF CPUS USED BY DIRECT SOLVER     2
  
 NUMBER OF NEGATIVE EIGENVALUES     0
 NUMBER OF POSITIVE EIGENVALUES     16848
 NUMBER OF NEGATIVE EIGENVALUES NOT ASSOCIATED WITH LAGRANGE MULTIPLIERS     0
 NUMBER OF LAGRANGE MULTIPLIERS     0
  
 COMPUTATIONAL INTERVAL FOR THE INITIAL LANCZOS RUN
 
 EIGENVALUES NEEDED TO THE RIGHT OF SHIFT VALUE   30
 EIGENVALUES NEEDED TO THE LEFT OF SHIFT VALUE     0
 RIGHT BOUNDARY OF THE COMPUTATIONAL INTERVAL   3.95574e+37
 LEFT BOUNDARY OF THE COMPUTATIONAL INTERVAL   -3.95574e+37
  
 LANCZOS RUN TERMINATED. NUMBER OF STEPS:   16
 TERMINATION BASED ON THE COST-PER-EIGENVALUE CRITERION
  
 NUMBER OF ACCEPTED EIGENVALUES   32
  
 ACCEPTED EIGENVALUES
   7.23401e-01  7.29335e-01  1.97476e+01  2.17632e+01  2.49085e+01  1.00747e+02
   1.22949e+02  3.78809e+02  4.06227e+02  1.16381e+03  1.33285e+03  1.35307e+03
   2.25146e+03  2.25146e+03  2.45377e+03  3.39618e+03  3.41992e+03  6.63504e+03
   6.66146e+03  7.05998e+03  7.41543e+03  7.41543e+03  1.06193e+04  1.18170e+04
   1.18355e+04  1.55389e+04  1.99320e+04  1.99509e+04  2.61460e+04  2.82398e+04
   2.97176e+04  2.97436e+04
  
 FACTORIZATION WITH NEW SHIFT VALUE IS REQUIRED
  
 TRUST INTERVALS AFTER LANCZOS RUN AND COMPRESSION
  
 NUMBER OF TRUST INTERVALS    1
  
 -------------------------------------------------------------------------------------
 | KEY | INSIDE |      INERTIAS     |  SENTINELS  |   OUTSIDE   |  NEED TO FIND      |
 |      ENDS OF INTERVAL     |     ENDS OF SENTINEL      |   COMPUTATIONAL INTERVAL  |
 -------------------------------------------------------------------------------------
 |  +  |      0 |        0        0 |     0     0 |     0     0 |      0    30       |
 | -3.95574e+37  0.00000e+00 | -3.95574e+37  0.00000e+00 | -3.95574e+37  3.95574e+37 |
 -------------------------------------------------------------------------------------
  
 DATA FOR CHOOSING SHIFT
  
 NUMBER OF EIGENVALUES NEEDED IN THE PRIMARY TRUST INTERVAL   30
  
 NUMBER OF MODES FORMING SENTINEL TO THE RIGHT   26
 SHIFT RIGHT         2.26280e+04
  
 NUMBER OF MODES FORMING SENTINEL TO THE LEFT     0
 SHIFT LEFT          0.00000e+00
  
 SHIFTING TO THE RIGHT DIRECTION
 NEW SHIFT           2.26280e+04
  
 NUMBER OF NEGATIVE EIGENVALUES    31
 NUMBER OF POSITIVE EIGENVALUES     16817
 NUMBER OF NEGATIVE EIGENVALUES NOT ASSOCIATED WITH LAGRANGE MULTIPLIERS    31
 NUMBER OF LAGRANGE MULTIPLIERS     0
  
 NEW LANCZOS RUN IS REQUIRED
  
 TYPE OF RUN: EXPAND THE TRUST INTERVAL TO THE RIGHT
 EIGENVALUES NEEDED TO THE RIGHT     0
 EIGENVALUES NEEDED TO THE LEFT      3
 RIGHT BOUNDARY OF THE INTERVAL   2.26280e+04
 LEFT BOUNDARY OF THE INTERVAL    1.55389e+04
  
 TRUST INTERVALS AFTER FACTORIZATION AND COMPRESSION
  
 -------------------------------------------------------------------------------------
 | KEY | INSIDE |      INERTIAS     |  SENTINELS  |   OUTSIDE   |  NEED TO FIND      |
 |      ENDS OF INTERVAL     |     ENDS OF SENTINEL      |   COMPUTATIONAL INTERVAL  |
 -------------------------------------------------------------------------------------
 |  +  |      0 |        0        0 |     0    26 |     0    32 |      0    30       |
 | -3.95574e+37  0.00000e+00 | -3.95574e+37  1.55389e+04 | -3.95574e+37  3.95574e+37 |
 -------------------------------------------------------------------------------------
 |  -  |      0 |       31       31 |     0     0 |     0     0 |      3     0       |
 |  2.26280e+04  2.26280e+04 |  2.26280e+04  2.26280e+04 |  1.55389e+04  2.26280e+04 |
 -------------------------------------------------------------------------------------
  
 LANCZOS RUN TERMINATED. NUMBER OF STEPS:    7
 ALL THE EIGENVALUES REQUESTED ON THIS LANCZOS RUN ARE FOUND
  
 NUMBER OF ACCEPTED EIGENVALUES   35
  
 ACCEPTED EIGENVALUES
   7.23401e-01  7.29335e-01  1.97476e+01  2.17632e+01  2.49085e+01  1.00747e+02
   1.22949e+02  3.78809e+02  4.06227e+02  1.16381e+03  1.33285e+03  1.35307e+03
   2.25146e+03  2.25146e+03  2.45377e+03  3.39618e+03  3.41992e+03  6.63504e+03
   6.66146e+03  7.05998e+03  7.41543e+03  7.41543e+03  1.06193e+04  1.18170e+04
   1.18355e+04  1.55389e+04  1.55389e+04  1.99320e+04  1.99509e+04  2.18357e+04
   2.18357e+04  2.61460e+04  2.82398e+04  2.97176e+04  2.97436e+04
  
 THE REQUIRED NUMBER OF EIGENVALUES IS FOUND
  
 FINAL TRUST INTERVALS AFTER SUCCESSFUL LANCZOS RUN
  
 NUMBER OF TRUST INTERVALS    1
  
 -------------------------------------------------------------------------------------
 | KEY | INSIDE |      INERTIAS     |  SENTINELS  |   OUTSIDE   |  NEED TO FIND      |
 |      ENDS OF INTERVAL     |     ENDS OF SENTINEL      |   COMPUTATIONAL INTERVAL  |
 -------------------------------------------------------------------------------------
 |  +  |     31 |        0       31 |     0     0 |     0     0 |      0     0       |
 | -3.95574e+37  2.26280e+04 | -3.95574e+37  2.26280e+04 | -3.95574e+37  2.26280e+04 |
 -------------------------------------------------------------------------------------
  
 FIRST EIGENVALUE REQUESTED BY THE USER     1
  
 EIGENVALUES REQUESTED BY THE USER
   7.23401e-01  7.29335e-01  1.97476e+01  2.17632e+01  2.49085e+01  1.00747e+02
   1.22949e+02  3.78809e+02  4.06227e+02  1.16381e+03  1.33285e+03  1.35307e+03
   2.25146e+03  2.25146e+03  2.45377e+03  3.39618e+03  3.41992e+03  6.63504e+03
   6.66146e+03  7.05998e+03  7.41543e+03  7.41543e+03  1.06193e+04  1.18170e+04
   1.18355e+04  1.55389e+04  1.55389e+04  1.99320e+04  1.99509e+04  2.18357e+04
  
 EIGENVALUE EXTRACTION USING THE LANCZOS EIGENSOLVER IS COMPLETE
 NUMBER OF LANCZOS RUNS       :   2
 NUMBER OF LANCZOS STEPS      :  23
 NUMBER OF FACTORIZATIONS     :   2
 NUMBER OF BACK SUBSTITUTIONS :  24

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   2.4000    
       ELAPSED SYSTEM TIME (SEC)    =  0.20000    
       ELAPSED TOTAL CPU TIME (SEC) =   2.6000    
       ELAPSED WALLCLOCK TIME (SEC) =            9
1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:04:15
   For use by Supplied by Team-SolidSQUAD under license from Dassault Systemes or its subsidiary.

 T026 new reconstructed tower plus recovered distributed rigid RNA; SI units     
                                                                                 
 STEP    3     INCREMENT     1     STEP TIME    0.00    


                        S T E P       3     S T A T I C   A N A L Y S I S


                                                                                          

          FIXED TIME INCREMENTS
          TIME INCREMENT IS                                    2.220E-16
          TIME PERIOD IS                                       2.220E-16

     LINEAR EQUATION SOLVER TYPE         DIRECT SPARSE

     THIS IS A LINEAR PERTURBATION STEP.
     ALL LOADS ARE DEFINED AS CHANGE IN LOAD TO THE REFERENCE STATE

          LARGE DISPLACEMENT THEORY WILL BE USED

          UNSYMMETRIC MATRIX STORAGE AND SOLUTION WILL BE USED

     EXTRAPOLATION WILL NOT BE USED

     CHARACTERISTIC ELEMENT LENGTH      3.04    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.220E-16
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            4437
                              2            4608
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      9.781e+07
        SOLVER ELAPSED TIME:  37ms

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  2.220E-16,  FRACTION OF STEP COMPLETED   1.00    
 STEP TIME COMPLETED       2.220E-16,  TOTAL TIME COMPLETED         1.00    
1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:04:17
   For use by Supplied by Team-SolidSQUAD under license from Dassault Systemes or its subsidiary.

 T026 new reconstructed tower plus recovered distributed rigid RNA; SI units     
                                                                                 
 STEP    4     INCREMENT     1     STEP TIME    0.00    


                        S T E P       4     S T A T I C   A N A L Y S I S


                                                                                          

          FIXED TIME INCREMENTS
          TIME INCREMENT IS                                    2.220E-16
          TIME PERIOD IS                                       2.220E-16

     LINEAR EQUATION SOLVER TYPE         DIRECT SPARSE

     THIS IS A LINEAR PERTURBATION STEP.
     ALL LOADS ARE DEFINED AS CHANGE IN LOAD TO THE REFERENCE STATE

          LARGE DISPLACEMENT THEORY WILL BE USED

          UNSYMMETRIC MATRIX STORAGE AND SOLUTION WILL BE USED

     EXTRAPOLATION WILL NOT BE USED

     CHARACTERISTIC ELEMENT LENGTH      3.04    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.220E-16
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            4608
                              2            4437

 ***NOTE: DURING THE BACK SUBSTITUTION AN ELEMENT ENCOUNTERED A LOAD APPLIED TO 
          A DEGREE OF FREEDOM THAT DID NOT HAVE ANY STIFFNESS.  A NEW 
          DECOMPOSITION WILL BE DONE TO ATTEMPT TO CORRECT THE PROBLEM.
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  11856
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      9.781e+07
        SOLVER ELAPSED TIME:  142ms

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  2.220E-16,  FRACTION OF STEP COMPLETED   1.00    
 STEP TIME COMPLETED       2.220E-16,  TOTAL TIME COMPLETED         1.00    


          THE ANALYSIS HAS BEEN COMPLETED



     ANALYSIS SUMMARY:
     TOTAL OF         15  INCREMENTS
                       0  CUTBACKS IN AUTOMATIC INCREMENTATION
                      26  ITERATIONS INCLUDING CONTACT ITERATIONS IF PRESENT
                      52  PASSES THROUGH THE EQUATION SOLVER OF WHICH 
                      28  INVOLVE MATRIX DECOMPOSITION, INCLUDING
                       0  DECOMPOSITION(S) OF THE MASS MATRIX
                       1  REORDERING OF EQUATIONS TO MINIMIZE WAVEFRONT
                       0  ADDITIONAL RESIDUAL EVALUATIONS FOR LINE SEARCHES
                       0  ADDITIONAL OPERATOR EVALUATIONS FOR LINE SEARCHES
                      11  WARNING MESSAGES DURING USER INPUT PROCESSING
                       0  WARNING MESSAGES DURING ANALYSIS
                       0  ANALYSIS WARNINGS ARE NUMERICAL PROBLEM MESSAGES
                       0  ANALYSIS WARNINGS ARE NEGATIVE EIGENVALUE MESSAGES
                       0  ERROR MESSAGES



     JOB TIME SUMMARY
       USER TIME (SEC)      =      36.    
       SYSTEM TIME (SEC)    =      3.0    
       TOTAL CPU TIME (SEC) =      39.    
       WALLCLOCK TIME (SEC) =           75
       MEMORY PEAK (GB)     =            0
