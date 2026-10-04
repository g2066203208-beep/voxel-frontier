1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:19:05
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

     CHARACTERISTIC ELEMENT LENGTH     0.896    

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
                              1            23221
                              2            22784
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  845ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       412.       TIME AVG. FORCE        412.    
 LARGEST SCALED RESIDUAL FORCE      -325.       AT NODE       1331   DOF  3
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      -325.    
 LARGEST INCREMENT OF DISP.        -8.882E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -8.882E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.546E+04   TIME AVG. MOMENT      3.546E+04
 LARGEST SCALED RESIDUAL MOMENT      9.68       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT      9.68    
 LARGEST INCREMENT OF ROTATION     -6.185E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -6.185E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  638ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       412.       TIME AVG. FORCE        412.    
 LARGEST SCALED RESIDUAL FORCE     -6.910E-02   AT NODE        467   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -6.910E-02
 LARGEST INCREMENT OF DISP.        -8.924E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.162E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.570E+04   TIME AVG. MOMENT      3.570E+04
 LARGEST SCALED RESIDUAL MOMENT    -5.337E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -5.337E-02
 LARGEST INCREMENT OF ROTATION     -6.210E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.469E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  5.000E-02,  FRACTION OF STEP COMPLETED  5.000E-02
 STEP TIME COMPLETED       5.000E-02,  TOTAL TIME COMPLETED        5.000E-02


  INCREMENT     2 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  5.000E-02
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  745ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.143E+03   TIME AVG. FORCE        777.    
 LARGEST SCALED RESIDUAL FORCE       95.4       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       95.4    
 LARGEST INCREMENT OF DISP.        -9.008E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -8.422E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.170E+05   TIME AVG. MOMENT      2.263E+05
 LARGEST SCALED RESIDUAL MOMENT    -8.358E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -8.358E-02
 LARGEST INCREMENT OF ROTATION     -6.260E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -5.000E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  1.2s

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.143E+03   TIME AVG. FORCE        777.    
 LARGEST SCALED RESIDUAL FORCE      3.209E-02   AT NODE        242   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      3.209E-02
 LARGEST INCREMENT OF DISP.        -9.009E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.783E-07   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.170E+05   TIME AVG. MOMENT      2.263E+05
 LARGEST SCALED RESIDUAL MOMENT    -9.626E-03   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -9.626E-03
 LARGEST INCREMENT OF ROTATION     -6.260E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.741E-09   AT NODE          1   DOF  4
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
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  563ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.985E+03   TIME AVG. FORCE       1.180E+03
 LARGEST SCALED RESIDUAL FORCE       182.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       182.    
 LARGEST INCREMENT OF DISP.        -1.367E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -1.606E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     7.372E+05   TIME AVG. MOMENT      3.966E+05
 LARGEST SCALED RESIDUAL MOMENT    -0.247       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.247    
 LARGEST INCREMENT OF ROTATION     -9.485E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -9.534E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    4.016E-09
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  635ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.985E+03   TIME AVG. FORCE       1.180E+03
 LARGEST SCALED RESIDUAL FORCE      4.071E-02   AT NODE        638   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      4.071E-02
 LARGEST INCREMENT OF DISP.        -1.367E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -1.381E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     7.373E+05   TIME AVG. MOMENT      3.967E+05
 LARGEST SCALED RESIDUAL MOMENT    -3.004E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -3.004E-02
 LARGEST INCREMENT OF ROTATION     -9.486E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -7.915E-09   AT NODE          1   DOF  4
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
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  775ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.108E+03   TIME AVG. FORCE       1.662E+03
 LARGEST SCALED RESIDUAL FORCE       347.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       347.    
 LARGEST INCREMENT OF DISP.        -1.854E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.068E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.175E+06   TIME AVG. MOMENT      5.912E+05
 LARGEST SCALED RESIDUAL MOMENT    -0.614       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.614    
 LARGEST INCREMENT OF ROTATION     -1.283E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -1.820E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    9.812E-09
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  717ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.108E+03   TIME AVG. FORCE       1.662E+03
 LARGEST SCALED RESIDUAL FORCE      6.181E-02   AT NODE        332   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      6.181E-02
 LARGEST INCREMENT OF DISP.        -1.854E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.562E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.175E+06   TIME AVG. MOMENT      5.912E+05
 LARGEST SCALED RESIDUAL MOMENT    -8.141E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -8.141E-02
 LARGEST INCREMENT OF ROTATION     -1.283E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.041E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.275    
 STEP TIME COMPLETED       0.275    ,  TOTAL TIME COMPLETED        0.275    


  INCREMENT     5 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  615ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.242E+03   TIME AVG. FORCE       2.178E+03
 LARGEST SCALED RESIDUAL FORCE       408.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       408.    
 LARGEST INCREMENT OF DISP.        -1.891E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.620E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.625E+06   TIME AVG. MOMENT      7.979E+05
 LARGEST SCALED RESIDUAL MOMENT    -0.688       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.688    
 LARGEST INCREMENT OF ROTATION     -1.305E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.146E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.044E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  948ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.242E+03   TIME AVG. FORCE       2.178E+03
 LARGEST SCALED RESIDUAL FORCE     -7.540E-02   AT NODE        467   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -7.540E-02
 LARGEST INCREMENT OF DISP.        -1.891E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.257E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.625E+06   TIME AVG. MOMENT      7.979E+05
 LARGEST SCALED RESIDUAL MOMENT    -9.919E-02   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -9.919E-02
 LARGEST INCREMENT OF ROTATION     -1.305E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.439E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.375    
 STEP TIME COMPLETED       0.375    ,  TOTAL TIME COMPLETED        0.375    


  INCREMENT     6 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  496ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.380E+03   TIME AVG. FORCE       2.712E+03
 LARGEST SCALED RESIDUAL FORCE       422.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       422.    
 LARGEST INCREMENT OF DISP.        -1.928E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.750E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.087E+06   TIME AVG. MOMENT      1.013E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.697       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.697    
 LARGEST INCREMENT OF ROTATION     -1.327E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.221E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.065E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  883ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.380E+03   TIME AVG. FORCE       2.712E+03
 LARGEST SCALED RESIDUAL FORCE     -7.722E-02   AT NODE        467   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -7.722E-02
 LARGEST INCREMENT OF DISP.        -1.929E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.467E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.088E+06   TIME AVG. MOMENT      1.013E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.107       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.107    
 LARGEST INCREMENT OF ROTATION     -1.327E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.560E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.475    
 STEP TIME COMPLETED       0.475    ,  TOTAL TIME COMPLETED        0.475    


  INCREMENT     7 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  747ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      6.519E+03   TIME AVG. FORCE       3.256E+03
 LARGEST SCALED RESIDUAL FORCE       436.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       436.    
 LARGEST INCREMENT OF DISP.        -1.968E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -3.887E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.563E+06   TIME AVG. MOMENT      1.234E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.705       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.705    
 LARGEST INCREMENT OF ROTATION     -1.350E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.300E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.086E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  742ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      6.520E+03   TIME AVG. FORCE       3.256E+03
 LARGEST SCALED RESIDUAL FORCE     -7.896E-02   AT NODE        431   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -7.896E-02
 LARGEST INCREMENT OF DISP.        -1.968E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.691E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.564E+06   TIME AVG. MOMENT      1.234E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.116       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.116    
 LARGEST INCREMENT OF ROTATION     -1.351E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.688E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.575    
 STEP TIME COMPLETED       0.575    ,  TOTAL TIME COMPLETED        0.575    


  INCREMENT     8 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  908ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      7.660E+03   TIME AVG. FORCE       3.806E+03
 LARGEST SCALED RESIDUAL FORCE       452.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       452.    
 LARGEST INCREMENT OF DISP.        -2.009E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.030E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.053E+06   TIME AVG. MOMENT      1.462E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.712       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.712    
 LARGEST INCREMENT OF ROTATION     -1.374E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.382E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.106E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  676ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      7.660E+03   TIME AVG. FORCE       3.806E+03
 LARGEST SCALED RESIDUAL FORCE     -7.857E-02   AT NODE        503   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -7.857E-02
 LARGEST INCREMENT OF DISP.        -2.009E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.929E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.054E+06   TIME AVG. MOMENT      1.462E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.125       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.125    
 LARGEST INCREMENT OF ROTATION     -1.375E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.824E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.675    
 STEP TIME COMPLETED       0.675    ,  TOTAL TIME COMPLETED        0.675    


  INCREMENT     9 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  921ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      8.801E+03   TIME AVG. FORCE       4.361E+03
 LARGEST SCALED RESIDUAL FORCE       468.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       468.    
 LARGEST INCREMENT OF DISP.        -2.051E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.180E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.558E+06   TIME AVG. MOMENT      1.695E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.718       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.718    
 LARGEST INCREMENT OF ROTATION     -1.399E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.469E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.125E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  838ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      8.802E+03   TIME AVG. FORCE       4.361E+03
 LARGEST SCALED RESIDUAL FORCE      7.760E-02   AT NODE       1295   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      7.760E-02
 LARGEST INCREMENT OF DISP.        -2.051E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.182E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.558E+06   TIME AVG. MOMENT      1.695E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.135       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.135    
 LARGEST INCREMENT OF ROTATION     -1.400E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.969E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.775    
 STEP TIME COMPLETED       0.775    ,  TOTAL TIME COMPLETED        0.775    


  INCREMENT    10 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  431ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      9.944E+03   TIME AVG. FORCE       4.920E+03
 LARGEST SCALED RESIDUAL FORCE       485.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       485.    
 LARGEST INCREMENT OF DISP.        -2.095E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.338E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.077E+06   TIME AVG. MOMENT      1.933E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.721       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.721    
 LARGEST INCREMENT OF ROTATION     -1.425E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.560E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.141E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  359ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      9.944E+03   TIME AVG. FORCE       4.920E+03
 LARGEST SCALED RESIDUAL FORCE     -8.945E-02   AT NODE        431   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE     -8.945E-02
 LARGEST INCREMENT OF DISP.        -2.095E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.452E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.077E+06   TIME AVG. MOMENT      1.933E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.147       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.147    
 LARGEST INCREMENT OF ROTATION     -1.426E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -3.123E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.875    
 STEP TIME COMPLETED       0.875    ,  TOTAL TIME COMPLETED        0.875    


  INCREMENT    11 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  615ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.109E+04   TIME AVG. FORCE       5.480E+03
 LARGEST SCALED RESIDUAL FORCE       503.       AT NODE       1331   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       503.    
 LARGEST INCREMENT OF DISP.        -2.140E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -4.504E-04   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.612E+06   TIME AVG. MOMENT      2.176E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.724       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.724    
 LARGEST INCREMENT OF ROTATION     -1.452E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -2.657E-06   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.156E-08
          MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  697ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.109E+04   TIME AVG. FORCE       5.480E+03
 LARGEST SCALED RESIDUAL FORCE      9.340E-02   AT NODE        332   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      9.340E-02
 LARGEST INCREMENT OF DISP.        -2.141E-02   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -5.739E-06   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.612E+06   TIME AVG. MOMENT      2.176E+06
 LARGEST SCALED RESIDUAL MOMENT    -0.159       AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -0.159    
 LARGEST INCREMENT OF ROTATION     -1.453E-04   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -3.287E-08   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.975    
 STEP TIME COMPLETED       0.975    ,  TOTAL TIME COMPLETED        0.975    


  INCREMENT    12 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.500E-02
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  505ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.142E+04   TIME AVG. FORCE       5.975E+03
 LARGEST SCALED RESIDUAL FORCE       81.6       AT NODE        467   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE       81.6    
 LARGEST INCREMENT OF DISP.        -5.425E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -7.301E-05   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.748E+06   TIME AVG. MOMENT      2.391E+06
 LARGEST SCALED RESIDUAL MOMENT    -2.238E-02   AT NODE         35   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -2.238E-02
 LARGEST INCREMENT OF ROTATION     -3.674E-05   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
 LARGEST CORRECTION TO ROTATION    -4.298E-07   AT NODE          1   DOF  4
   INSTANCE: {assembly node}                                                                 
          THE MOMENT    EQUILIBRIUM RESPONSE WAS LINEAR IN THIS INCREMENT
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.755e+09
        SOLVER ELAPSED TIME:  898ms

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.142E+04   TIME AVG. FORCE       5.975E+03
 LARGEST SCALED RESIDUAL FORCE      3.130E-02   AT NODE       1565   DOF  2
   INSTANCE: SSEG_04-1                                                                       
  CORRESPONDING RESIDUAL FORCE      3.130E-02
 LARGEST INCREMENT OF DISP.        -5.426E-03   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
 LARGEST CORRECTION TO DISP.       -2.334E-07   AT NODE         20   DOF  3
   INSTANCE: RNA_MASS_SKELETON_OFFICIAL-1                                                    
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.748E+06   TIME AVG. MOMENT      2.391E+06
 LARGEST SCALED RESIDUAL MOMENT    -6.683E-03   AT NODE         62   DOF  4
   INSTANCE:                                                                                 
  CORRESPONDING RESIDUAL MOMENT    -6.683E-03
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

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:22:20
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

     CHARACTERISTIC ELEMENT LENGTH     0.896    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

     CHECK POINT  START OF SOLVER     
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            22528
                              2            23477
 
 SMP LANCZOS SOLVER RUNNING ON 1 HOST USING 2 THREADS
 
 NEW DIRECT SPARSE SOLVER WILL BE USED.
  
 COMPUTER PRECISION USED BY ABAQUS       2.22045e-16
 CONVERGENCE CRITERION FOR LANCZOS RUN   1.81899e-12
  
 NUMBER OF EQUATIONS                                                          186528
 NUMBER OF UNRESTRAINED DEGREES OF FREEDOM                                    125364
 HEURISTIC SCALE FOR THE FIRST NONZERO EIGENVALUES (PROBLEM SCALE)   2.97978e-03
 INITIAL SHIFT VALUE                                                 0.00000e+00
  
 NUMBER OF CPUS USED BY DIRECT SOLVER     2
  
 NUMBER OF NEGATIVE EIGENVALUES     0
 NUMBER OF POSITIVE EIGENVALUES    186528
 NUMBER OF NEGATIVE EIGENVALUES NOT ASSOCIATED WITH LAGRANGE MULTIPLIERS     0
 NUMBER OF LAGRANGE MULTIPLIERS     0
  
 COMPUTATIONAL INTERVAL FOR THE INITIAL LANCZOS RUN
 
 EIGENVALUES NEEDED TO THE RIGHT OF SHIFT VALUE   30
 EIGENVALUES NEEDED TO THE LEFT OF SHIFT VALUE     0
 RIGHT BOUNDARY OF THE COMPUTATIONAL INTERVAL   3.95574e+37
 LEFT BOUNDARY OF THE COMPUTATIONAL INTERVAL   -3.95574e+37
  
 LANCZOS RUN TERMINATED. NUMBER OF STEPS:   16
 TERMINATION BASED ON THE COST-PER-EIGENVALUE CRITERION
  
 NUMBER OF ACCEPTED EIGENVALUES   31
  
 ACCEPTED EIGENVALUES
   7.19259e-01  7.25109e-01  1.97686e+01  2.17610e+01  2.52138e+01  1.01002e+02
   1.23345e+02  3.77894e+02  4.05461e+02  1.15170e+03  1.33078e+03  1.35106e+03
   1.61147e+03  1.61147e+03  2.47359e+03  3.39098e+03  3.41490e+03  5.77434e+03
   5.77434e+03  6.62379e+03  6.64988e+03  7.01221e+03  7.44176e+03  7.44176e+03
   8.83799e+03  8.83799e+03  1.06768e+04  1.18483e+04  1.18663e+04  2.00245e+04
   2.00435e+04
  
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
 SHIFT RIGHT         1.54269e+04
  
 NUMBER OF MODES FORMING SENTINEL TO THE LEFT     0
 SHIFT LEFT          0.00000e+00
  
 SHIFTING TO THE RIGHT DIRECTION
 NEW SHIFT           1.54269e+04
  
 NUMBER OF NEGATIVE EIGENVALUES    31
 NUMBER OF POSITIVE EIGENVALUES    186497
 NUMBER OF NEGATIVE EIGENVALUES NOT ASSOCIATED WITH LAGRANGE MULTIPLIERS    31
 NUMBER OF LAGRANGE MULTIPLIERS     0
  
 NEW LANCZOS RUN IS REQUIRED
  
 TYPE OF RUN: EXPAND THE TRUST INTERVAL TO THE RIGHT
 EIGENVALUES NEEDED TO THE RIGHT     0
 EIGENVALUES NEEDED TO THE LEFT      2
 RIGHT BOUNDARY OF THE INTERVAL   1.54269e+04
 LEFT BOUNDARY OF THE INTERVAL    1.18663e+04
  
 TRUST INTERVALS AFTER FACTORIZATION AND COMPRESSION
  
 -------------------------------------------------------------------------------------
 | KEY | INSIDE |      INERTIAS     |  SENTINELS  |   OUTSIDE   |  NEED TO FIND      |
 |      ENDS OF INTERVAL     |     ENDS OF SENTINEL      |   COMPUTATIONAL INTERVAL  |
 -------------------------------------------------------------------------------------
 |  +  |      0 |        0        0 |     0    29 |     0    31 |      0    30       |
 | -3.95574e+37  0.00000e+00 | -3.95574e+37  1.18663e+04 | -3.95574e+37  3.95574e+37 |
 -------------------------------------------------------------------------------------
 |  -  |      0 |       31       31 |     0     0 |     0     0 |      2     0       |
 |  1.54269e+04  1.54269e+04 |  1.54269e+04  1.54269e+04 |  1.18663e+04  1.54269e+04 |
 -------------------------------------------------------------------------------------
  
 LANCZOS RUN TERMINATED. NUMBER OF STEPS:    9
 ALL THE EIGENVALUES REQUESTED ON THIS LANCZOS RUN ARE FOUND
  
 NUMBER OF ACCEPTED EIGENVALUES   33
  
 ACCEPTED EIGENVALUES
   7.19259e-01  7.25109e-01  1.97686e+01  2.17610e+01  2.52138e+01  1.01002e+02
   1.23345e+02  3.77894e+02  4.05461e+02  1.15170e+03  1.33078e+03  1.35106e+03
   1.61147e+03  1.61147e+03  2.47359e+03  3.39098e+03  3.41490e+03  5.77434e+03
   5.77434e+03  6.62379e+03  6.64988e+03  7.01221e+03  7.44176e+03  7.44176e+03
   8.83799e+03  8.83799e+03  1.06768e+04  1.18483e+04  1.18663e+04  1.27241e+04
   1.27241e+04  2.00245e+04  2.00435e+04
  
 THE REQUIRED NUMBER OF EIGENVALUES IS FOUND
  
 FINAL TRUST INTERVALS AFTER SUCCESSFUL LANCZOS RUN
  
 NUMBER OF TRUST INTERVALS    1
  
 -------------------------------------------------------------------------------------
 | KEY | INSIDE |      INERTIAS     |  SENTINELS  |   OUTSIDE   |  NEED TO FIND      |
 |      ENDS OF INTERVAL     |     ENDS OF SENTINEL      |   COMPUTATIONAL INTERVAL  |
 -------------------------------------------------------------------------------------
 |  +  |     31 |        0       31 |     0     0 |     0     0 |      0     0       |
 | -3.95574e+37  1.54269e+04 | -3.95574e+37  1.54269e+04 | -3.95574e+37  1.54269e+04 |
 -------------------------------------------------------------------------------------
  
 FIRST EIGENVALUE REQUESTED BY THE USER     1
  
 EIGENVALUES REQUESTED BY THE USER
   7.19259e-01  7.25109e-01  1.97686e+01  2.17610e+01  2.52138e+01  1.01002e+02
   1.23345e+02  3.77894e+02  4.05461e+02  1.15170e+03  1.33078e+03  1.35106e+03
   1.61147e+03  1.61147e+03  2.47359e+03  3.39098e+03  3.41490e+03  5.77434e+03
   5.77434e+03  6.62379e+03  6.64988e+03  7.01221e+03  7.44176e+03  7.44176e+03
   8.83799e+03  8.83799e+03  1.06768e+04  1.18483e+04  1.18663e+04  1.27241e+04
  
 EIGENVALUE EXTRACTION USING THE LANCZOS EIGENSOLVER IS COMPLETE
 NUMBER OF LANCZOS RUNS       :   2
 NUMBER OF LANCZOS STEPS      :  25
 NUMBER OF FACTORIZATIONS     :   2
 NUMBER OF BACK SUBSTITUTIONS :  26

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   7.9000    
       ELAPSED SYSTEM TIME (SEC)    =  0.80000    
       ELAPSED TOTAL CPU TIME (SEC) =   8.7000    
       ELAPSED WALLCLOCK TIME (SEC) =           22
1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:22:54
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

     CHARACTERISTIC ELEMENT LENGTH     0.896    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.220E-16
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            23477
                              2            22528
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.714e+09
        SOLVER ELAPSED TIME:  448ms

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  2.220E-16,  FRACTION OF STEP COMPLETED   1.00    
 STEP TIME COMPLETED       2.220E-16,  TOTAL TIME COMPLETED         1.00    
1

   Abaqus 2025                                  Date 04-Oct-2026   Time 20:23:01
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

     CHARACTERISTIC ELEMENT LENGTH     0.896    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING   2 THREADS ON 1 DOMAIN

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.220E-16
 
     INITIAL ELEMENT LOAD BALANCE
            DOMAIN    1     THREAD    NUMBER OF ELEMENTS
                              1            23040
                              2            22965

 ***NOTE: DURING THE BACK SUBSTITUTION AN ELEMENT ENCOUNTERED A LOAD APPLIED TO 
          A DEGREE OF FREEDOM THAT DID NOT HAVE ANY STIFFNESS.  A NEW 
          DECOMPOSITION WILL BE DONE TO ATTEMPT TO CORRECT THE PROBLEM.
 
	UNSYMMETRIC PURE THREAD-BASED DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST x 1 MPI RANK PER HOST x 2 THREADS PER RANK
        NUMBER OF EQUATIONS:  126624
        NUMBER OF RHS:        1
        NUMBER OF FLOPS:      6.714e+09
        SOLVER ELAPSED TIME:  601ms

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  2.220E-16,  FRACTION OF STEP COMPLETED   1.00    
 STEP TIME COMPLETED       2.220E-16,  TOTAL TIME COMPLETED         1.00    


          THE ANALYSIS HAS BEEN COMPLETED



     ANALYSIS SUMMARY:
     TOTAL OF         15  INCREMENTS
                       0  CUTBACKS IN AUTOMATIC INCREMENTATION
                      26  ITERATIONS INCLUDING CONTACT ITERATIONS IF PRESENT
                      54  PASSES THROUGH THE EQUATION SOLVER OF WHICH 
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
       USER TIME (SEC)      =     1.36E+02
       SYSTEM TIME (SEC)    =      6.7    
       TOTAL CPU TIME (SEC) =     1.42E+02
       WALLCLOCK TIME (SEC) =          245
       MEMORY PEAK (GB)     =            0
