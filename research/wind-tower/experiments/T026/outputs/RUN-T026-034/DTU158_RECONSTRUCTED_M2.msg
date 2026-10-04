1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:14:56
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

     CHARACTERISTIC ELEMENT LENGTH      1.58    

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
                              1            10309
                              2            10496
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  102ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.034E+03   TIME AVG. FORCE       1.034E+03
 LARGEST SCALED RESIDUAL FORCE      -540.       AT NODE        587   DOF  3
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      -540.    
 LARGEST INCREMENT OF DISP.        -8.879E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -8.879E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.546E+04   TIME AVG. MOMENT      3.546E+04
 LARGEST SCALED RESIDUAL MOMENT      8.40       AT NODE         56   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT      8.40    
 LARGEST INCREMENT OF ROTATION     -6.187E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -6.187E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    4.881E-07
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  99ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.034E+03   TIME AVG. FORCE       1.034E+03
 LARGEST SCALED RESIDUAL FORCE     -0.106       AT NODE        209   DOF  2
   INSTANCE: SSEG_03-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -0.106    
 LARGEST INCREMENT OF DISP.        -8.920E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.148E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.570E+04   TIME AVG. MOMENT      3.570E+04
 LARGEST SCALED RESIDUAL MOMENT    -6.528E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -6.528E-02
 LARGEST INCREMENT OF ROTATION     -6.212E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.463E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  5.000E-02,  FRACTION OF STEP COMPLETED  5.000E-02
 STEP TIME COMPLETED       5.000E-02,  TOTAL TIME COMPLETED        5.000E-02


  INCREMENT     2 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  5.000E-02
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  191ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.459E+03   TIME AVG. FORCE       1.746E+03
 LARGEST SCALED RESIDUAL FORCE       127.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       127.    
 LARGEST INCREMENT OF DISP.        -9.004E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -8.393E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.169E+05   TIME AVG. MOMENT      2.263E+05
 LARGEST SCALED RESIDUAL MOMENT    -0.136       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.136    
 LARGEST INCREMENT OF ROTATION     -6.261E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -4.986E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  154ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.459E+03   TIME AVG. FORCE       1.746E+03
 LARGEST SCALED RESIDUAL FORCE     -3.225E-02   AT NODE        706   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -3.225E-02
 LARGEST INCREMENT OF DISP.        -9.005E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.789E-07   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.170E+05   TIME AVG. MOMENT      2.263E+05
 LARGEST SCALED RESIDUAL MOMENT    -6.817E-03   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -6.817E-03
 LARGEST INCREMENT OF ROTATION     -6.262E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.745E-09   AT NODE          1   DOF  4
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
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  82ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.938E+03   TIME AVG. FORCE       2.477E+03
 LARGEST SCALED RESIDUAL FORCE       242.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       242.    
 LARGEST INCREMENT OF DISP.        -1.367E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -1.601E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     7.372E+05   TIME AVG. MOMENT      3.966E+05
 LARGEST SCALED RESIDUAL MOMENT    -0.393       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.393    
 LARGEST INCREMENT OF ROTATION     -9.488E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -9.507E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    8.158E-09
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  77ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.938E+03   TIME AVG. FORCE       2.477E+03
 LARGEST SCALED RESIDUAL FORCE     -3.643E-02   AT NODE        489   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -3.643E-02
 LARGEST INCREMENT OF DISP.        -1.367E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -1.383E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     7.373E+05   TIME AVG. MOMENT      3.966E+05
 LARGEST SCALED RESIDUAL MOMENT    -2.350E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -2.350E-02
 LARGEST INCREMENT OF ROTATION     -9.488E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -7.925E-09   AT NODE          1   DOF  4
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
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  98ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      6.003E+03   TIME AVG. FORCE       3.359E+03
 LARGEST SCALED RESIDUAL FORCE       461.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       461.    
 LARGEST INCREMENT OF DISP.        -1.853E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.057E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.175E+06   TIME AVG. MOMENT      5.911E+05
 LARGEST SCALED RESIDUAL MOMENT    -0.985       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.985    
 LARGEST INCREMENT OF ROTATION     -1.283E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -1.815E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.016E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  190ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      6.003E+03   TIME AVG. FORCE       3.359E+03
 LARGEST SCALED RESIDUAL FORCE      8.492E-02   AT NODE        237   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      8.492E-02
 LARGEST INCREMENT OF DISP.        -1.853E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.565E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.175E+06   TIME AVG. MOMENT      5.912E+05
 LARGEST SCALED RESIDUAL MOMENT    -6.329E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -6.329E-02
 LARGEST INCREMENT OF ROTATION     -1.283E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.043E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.275    
 STEP TIME COMPLETED       0.275    ,  TOTAL TIME COMPLETED        0.275    


  INCREMENT     5 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  171ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      8.216E+03   TIME AVG. FORCE       4.330E+03
 LARGEST SCALED RESIDUAL FORCE       542.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       542.    
 LARGEST INCREMENT OF DISP.        -1.889E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.607E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.624E+06   TIME AVG. MOMENT      7.978E+05
 LARGEST SCALED RESIDUAL MOMENT     -1.14       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.14    
 LARGEST INCREMENT OF ROTATION     -1.305E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.139E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.233E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  175ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      8.217E+03   TIME AVG. FORCE       4.330E+03
 LARGEST SCALED RESIDUAL FORCE     -9.672E-02   AT NODE        188   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -9.672E-02
 LARGEST INCREMENT OF DISP.        -1.890E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.261E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.625E+06   TIME AVG. MOMENT      7.979E+05
 LARGEST SCALED RESIDUAL MOMENT    -7.683E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -7.683E-02
 LARGEST INCREMENT OF ROTATION     -1.305E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.442E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.375    
 STEP TIME COMPLETED       0.375    ,  TOTAL TIME COMPLETED        0.375    


  INCREMENT     6 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  219ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.049E+04   TIME AVG. FORCE       5.358E+03
 LARGEST SCALED RESIDUAL FORCE       561.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       561.    
 LARGEST INCREMENT OF DISP.        -1.927E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.736E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.087E+06   TIME AVG. MOMENT      1.013E+06
 LARGEST SCALED RESIDUAL MOMENT     -1.17       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.17    
 LARGEST INCREMENT OF ROTATION     -1.327E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.214E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.309E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  590ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.050E+04   TIME AVG. FORCE       5.358E+03
 LARGEST SCALED RESIDUAL FORCE      0.107       AT NODE        195   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.107    
 LARGEST INCREMENT OF DISP.        -1.928E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.471E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.087E+06   TIME AVG. MOMENT      1.013E+06
 LARGEST SCALED RESIDUAL MOMENT    -8.308E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -8.308E-02
 LARGEST INCREMENT OF ROTATION     -1.328E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.562E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.475    
 STEP TIME COMPLETED       0.475    ,  TOTAL TIME COMPLETED        0.475    


  INCREMENT     7 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  136ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.279E+04   TIME AVG. FORCE       6.419E+03
 LARGEST SCALED RESIDUAL FORCE       580.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       580.    
 LARGEST INCREMENT OF DISP.        -1.966E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.871E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.563E+06   TIME AVG. MOMENT      1.234E+06
 LARGEST SCALED RESIDUAL MOMENT     -1.20       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.20    
 LARGEST INCREMENT OF ROTATION     -1.350E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.292E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.387E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  278ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.279E+04   TIME AVG. FORCE       6.420E+03
 LARGEST SCALED RESIDUAL FORCE     -0.106       AT NODE        209   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -0.106    
 LARGEST INCREMENT OF DISP.        -1.967E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.694E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.563E+06   TIME AVG. MOMENT      1.234E+06
 LARGEST SCALED RESIDUAL MOMENT    -8.950E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -8.950E-02
 LARGEST INCREMENT OF ROTATION     -1.351E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.690E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.575    
 STEP TIME COMPLETED       0.575    ,  TOTAL TIME COMPLETED        0.575    


  INCREMENT     8 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  204ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.519E+04   TIME AVG. FORCE       7.516E+03
 LARGEST SCALED RESIDUAL FORCE       601.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       601.    
 LARGEST INCREMENT OF DISP.        -2.007E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.013E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.053E+06   TIME AVG. MOMENT      1.462E+06
 LARGEST SCALED RESIDUAL MOMENT     -1.23       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.23    
 LARGEST INCREMENT OF ROTATION     -1.374E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.374E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.468E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  126ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.519E+04   TIME AVG. FORCE       7.516E+03
 LARGEST SCALED RESIDUAL FORCE     -0.110       AT NODE        188   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -0.110    
 LARGEST INCREMENT OF DISP.        -2.008E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.932E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.053E+06   TIME AVG. MOMENT      1.462E+06
 LARGEST SCALED RESIDUAL MOMENT    -9.665E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -9.665E-02
 LARGEST INCREMENT OF ROTATION     -1.375E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.825E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.675    
 STEP TIME COMPLETED       0.675    ,  TOTAL TIME COMPLETED        0.675    


  INCREMENT     9 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  179ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.762E+04   TIME AVG. FORCE       8.638E+03
 LARGEST SCALED RESIDUAL FORCE       622.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       622.    
 LARGEST INCREMENT OF DISP.        -2.049E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.162E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.557E+06   TIME AVG. MOMENT      1.694E+06
 LARGEST SCALED RESIDUAL MOMENT     -1.26       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.26    
 LARGEST INCREMENT OF ROTATION     -1.399E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.461E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.550E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  157ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.762E+04   TIME AVG. FORCE       8.638E+03
 LARGEST SCALED RESIDUAL FORCE     -0.114       AT NODE        188   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -0.114    
 LARGEST INCREMENT OF DISP.        -2.050E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.184E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.557E+06   TIME AVG. MOMENT      1.694E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.105       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.105    
 LARGEST INCREMENT OF ROTATION     -1.400E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.970E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.775    
 STEP TIME COMPLETED       0.775    ,  TOTAL TIME COMPLETED        0.775    


  INCREMENT    10 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  149ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.999E+04   TIME AVG. FORCE       9.774E+03
 LARGEST SCALED RESIDUAL FORCE       645.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       645.    
 LARGEST INCREMENT OF DISP.        -2.093E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.319E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.076E+06   TIME AVG. MOMENT      1.933E+06
 LARGEST SCALED RESIDUAL MOMENT     -1.29       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.29    
 LARGEST INCREMENT OF ROTATION     -1.425E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.551E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.637E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  173ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.999E+04   TIME AVG. FORCE       9.774E+03
 LARGEST SCALED RESIDUAL FORCE      0.117       AT NODE        174   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.117    
 LARGEST INCREMENT OF DISP.        -2.093E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.453E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.076E+06   TIME AVG. MOMENT      1.933E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.112       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.112    
 LARGEST INCREMENT OF ROTATION     -1.425E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -3.124E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.875    
 STEP TIME COMPLETED       0.875    ,  TOTAL TIME COMPLETED        0.875    


  INCREMENT    11 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  137ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.237E+04   TIME AVG. FORCE       1.092E+04
 LARGEST SCALED RESIDUAL FORCE       669.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       669.    
 LARGEST INCREMENT OF DISP.        -2.138E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.484E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.610E+06   TIME AVG. MOMENT      2.176E+06
 LARGEST SCALED RESIDUAL MOMENT     -1.33       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT     -1.33    
 LARGEST INCREMENT OF ROTATION     -1.452E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.647E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.728E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  160ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.238E+04   TIME AVG. FORCE       1.092E+04
 LARGEST SCALED RESIDUAL FORCE      0.124       AT NODE        174   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      0.124    
 LARGEST INCREMENT OF DISP.        -2.139E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.740E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.611E+06   TIME AVG. MOMENT      2.176E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.122       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.122    
 LARGEST INCREMENT OF ROTATION     -1.452E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -3.288E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.975    
 STEP TIME COMPLETED       0.975    ,  TOTAL TIME COMPLETED        0.975    


  INCREMENT    12 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.500E-02
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  206ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.414E+04   TIME AVG. FORCE       1.202E+04
 LARGEST SCALED RESIDUAL FORCE       108.       AT NODE        587   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       108.    
 LARGEST INCREMENT OF DISP.        -5.420E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -7.266E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.747E+06   TIME AVG. MOMENT      2.390E+06
 LARGEST SCALED RESIDUAL MOMENT    -3.629E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -3.629E-02
 LARGEST INCREMENT OF ROTATION     -3.673E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -4.281E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    6.217E-10
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.129e+09
        SOLVER ELAPSED TIME:  211ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.414E+04   TIME AVG. FORCE       1.202E+04
 LARGEST SCALED RESIDUAL FORCE      3.751E-02   AT NODE         76   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      3.751E-02
 LARGEST INCREMENT OF DISP.        -5.420E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -2.334E-07   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.747E+06   TIME AVG. MOMENT      2.390E+06
 LARGEST SCALED RESIDUAL MOMENT    -4.345E-03   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -4.345E-03
 LARGEST INCREMENT OF ROTATION     -3.674E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -1.336E-09   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  2.500E-02,  FRACTION OF STEP COMPLETED   1.00    
 STEP TIME COMPLETED        1.00    ,  TOTAL TIME COMPLETED         1.00    
1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:16:16
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

     CHARACTERISTIC ELEMENT LENGTH      1.58    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

     CHECK POINT  START OF SOLVER     
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            10496
                              2            10309
 
 SMP LANCZOS SOLVER RUNNING ON 1 HOST USING 2 THREADS
 
 NEW DIRECT SPARSE SOLVER WILL BE USED.
  
 COMPUTER PRECISION USED BY ABAQUS       2.22045e-16
 CONVERGENCE CRITERION FOR LANCZOS RUN   1.81899e-12
  
 NUMBER OF EQUATIONS                                                           71220
 NUMBER OF UNRESTRAINED DEGREES OF FREEDOM                                     48000
 HEURISTIC SCALE FOR THE FIRST NONZERO EIGENVALUES (PROBLEM SCALE)   6.33410e-03
 INITIAL SHIFT VALUE                                                 0.00000e+00
  
 NUMBER OF CPUS USED BY DIRECT SOLVER     2
  
 NUMBER OF NEGATIVE EIGENVALUES     0
 NUMBER OF POSITIVE EIGENVALUES     71220
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
   7.21714e-01  7.27600e-01  1.97863e+01  2.17889e+01  2.51368e+01  1.01049e+02
   1.23376e+02  3.78761e+02  4.06315e+02  1.15581e+03  1.33381e+03  1.35410e+03
   1.68981e+03  1.68981e+03  2.46930e+03  3.39928e+03  3.42320e+03  6.01804e+03
   6.01804e+03  6.64129e+03  6.66750e+03  7.02977e+03  8.26327e+03  8.26327e+03
   1.05850e+04  1.05850e+04  1.06655e+04  1.18686e+04  1.18868e+04  2.00487e+04
   2.00677e+04  2.62601e+04
  
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
  
 NUMBER OF MODES FORMING SENTINEL TO THE RIGHT   29
 SHIFT RIGHT         1.73830e+04
  
 NUMBER OF MODES FORMING SENTINEL TO THE LEFT     0
 SHIFT LEFT          0.00000e+00
  
 SHIFTING TO THE RIGHT DIRECTION
 NEW SHIFT           1.73830e+04
  
 NUMBER OF NEGATIVE EIGENVALUES    31
 NUMBER OF POSITIVE EIGENVALUES     71189
 NUMBER OF NEGATIVE EIGENVALUES NOT ASSOCIATED WITH LAGRANGE MULTIPLIERS    31
 NUMBER OF LAGRANGE MULTIPLIERS     0
  
 NEW LANCZOS RUN IS REQUIRED
  
 TYPE OF RUN: EXPAND THE TRUST INTERVAL TO THE RIGHT
 EIGENVALUES NEEDED TO THE RIGHT     0
 EIGENVALUES NEEDED TO THE LEFT      2
 RIGHT BOUNDARY OF THE INTERVAL   1.73830e+04
 LEFT BOUNDARY OF THE INTERVAL    1.18868e+04
  
 TRUST INTERVALS AFTER FACTORIZATION AND COMPRESSION
  
 -------------------------------------------------------------------------------------
 | KEY | INSIDE |      INERTIAS     |  SENTINELS  |   OUTSIDE   |  NEED TO FIND      |
 |      ENDS OF INTERVAL     |     ENDS OF SENTINEL      |   COMPUTATIONAL INTERVAL  |
 -------------------------------------------------------------------------------------
 |  +  |      0 |        0        0 |     0    29 |     0    32 |      0    30       |
 | -3.95574e+37  0.00000e+00 | -3.95574e+37  1.18868e+04 | -3.95574e+37  3.95574e+37 |
 -------------------------------------------------------------------------------------
 |  -  |      0 |       31       31 |     0     0 |     0     0 |      2     0       |
 |  1.73830e+04  1.73830e+04 |  1.73830e+04  1.73830e+04 |  1.18868e+04  1.73830e+04 |
 -------------------------------------------------------------------------------------
  
 LANCZOS RUN TERMINATED. NUMBER OF STEPS:    7
 ALL THE EIGENVALUES REQUESTED ON THIS LANCZOS RUN ARE FOUND
  
 NUMBER OF ACCEPTED EIGENVALUES   34
  
 ACCEPTED EIGENVALUES
   7.21714e-01  7.27600e-01  1.97863e+01  2.17889e+01  2.51368e+01  1.01049e+02
   1.23376e+02  3.78761e+02  4.06315e+02  1.15581e+03  1.33381e+03  1.35410e+03
   1.68981e+03  1.68981e+03  2.46930e+03  3.39928e+03  3.42320e+03  6.01804e+03
   6.01804e+03  6.64129e+03  6.66750e+03  7.02977e+03  8.26327e+03  8.26327e+03
   1.05850e+04  1.05850e+04  1.06655e+04  1.18686e+04  1.18868e+04  1.60090e+04
   1.60090e+04  2.00487e+04  2.00677e+04  2.62601e+04
  
 THE REQUIRED NUMBER OF EIGENVALUES IS FOUND
  
 FINAL TRUST INTERVALS AFTER SUCCESSFUL LANCZOS RUN
  
 NUMBER OF TRUST INTERVALS    1
  
 -------------------------------------------------------------------------------------
 | KEY | INSIDE |      INERTIAS     |  SENTINELS  |   OUTSIDE   |  NEED TO FIND      |
 |      ENDS OF INTERVAL     |     ENDS OF SENTINEL      |   COMPUTATIONAL INTERVAL  |
 -------------------------------------------------------------------------------------
 |  +  |     31 |        0       31 |     0     0 |     0     0 |      0     0       |
 | -3.95574e+37  1.73830e+04 | -3.95574e+37  1.73830e+04 | -3.95574e+37  1.73830e+04 |
 -------------------------------------------------------------------------------------
  
 FIRST EIGENVALUE REQUESTED BY THE USER     1
  
 EIGENVALUES REQUESTED BY THE USER
   7.21714e-01  7.27600e-01  1.97863e+01  2.17889e+01  2.51368e+01  1.01049e+02
   1.23376e+02  3.78761e+02  4.06315e+02  1.15581e+03  1.33381e+03  1.35410e+03
   1.68981e+03  1.68981e+03  2.46930e+03  3.39928e+03  3.42320e+03  6.01804e+03
   6.01804e+03  6.64129e+03  6.66750e+03  7.02977e+03  8.26327e+03  8.26327e+03
   1.05850e+04  1.05850e+04  1.06655e+04  1.18686e+04  1.18868e+04  1.60090e+04
  
 EIGENVALUE EXTRACTION USING THE LANCZOS EIGENSOLVER IS COMPLETE
 NUMBER OF LANCZOS RUNS       :   2
 NUMBER OF LANCZOS STEPS      :  23
 NUMBER OF FACTORIZATIONS     :   2
 NUMBER OF BACK SUBSTITUTIONS :  24

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   2.8000    
       ELAPSED SYSTEM TIME (SEC)    =  0.30000    
       ELAPSED TOTAL CPU TIME (SEC) =   3.1000    
       ELAPSED WALLCLOCK TIME (SEC) =           11
1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:16:34
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

     CHARACTERISTIC ELEMENT LENGTH      1.58    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.220E-16
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            10496
                              2            10309
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.103e+09
        SOLVER ELAPSED TIME:  248ms

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  2.220E-16,  FRACTION OF STEP COMPLETED   1.00    
 STEP TIME COMPLETED       2.220E-16,  TOTAL TIME COMPLETED         1.00    
1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:16:38
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

     CHARACTERISTIC ELEMENT LENGTH      1.58    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.220E-16
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            10496
                              2            10309

 ***NOTE: DURING THE BACK SUBSTITUTION AN ELEMENT ENCOUNTERED A LOAD APPLIED TO 
          A DEGREE OF FREEDOM THAT DID NOT HAVE ANY STIFFNESS.  A NEW 
          DECOMPOSITION WILL BE DONE TO ATTEMPT TO CORRECT THE PROBLEM.
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  48756
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      1.103e+09
        SOLVER ELAPSED TIME:  235ms

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
                      12  WARNING MESSAGES DURING USER INPUT PROCESSING
                       0  WARNING MESSAGES DURING ANALYSIS
                       0  ANALYSIS WARNINGS ARE NUMERICAL PROBLEM MESSAGES
                       0  ANALYSIS WARNINGS ARE NEGATIVE EIGENVALUE MESSAGES
                       0  ERROR MESSAGES



     JOB TIME SUMMARY
       USER TIME (SEC)      =      54.    
       SYSTEM TIME (SEC)    =      2.8    
       TOTAL CPU TIME (SEC) =      57.    
       WALLCLOCK TIME (SEC) =          109
       MEMORY PEAK (GB)     =            0
