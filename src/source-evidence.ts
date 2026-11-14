// Original document evidence images, not manuscript-produced simulation figures.
// Filenames and file sizes were read from the GitHub research branch on 2026-11-14.
const IMAGE_INDEX = [
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-22.png",
    "rel": "he-zeyu-tower-original/he-22.png",
    "sourceSize": 265389
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-23.png",
    "rel": "he-zeyu-tower-original/he-23.png",
    "sourceSize": 332578
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-24.png",
    "rel": "he-zeyu-tower-original/he-24.png",
    "sourceSize": 421458
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-33.png",
    "rel": "he-zeyu-tower-original/he-33.png",
    "sourceSize": 470591
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-34.png",
    "rel": "he-zeyu-tower-original/he-34.png",
    "sourceSize": 166339
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-35.png",
    "rel": "he-zeyu-tower-original/he-35.png",
    "sourceSize": 500988
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-36.png",
    "rel": "he-zeyu-tower-original/he-36.png",
    "sourceSize": 395485
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-44.png",
    "rel": "he-zeyu-tower-original/he-44.png",
    "sourceSize": 537084
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-45.png",
    "rel": "he-zeyu-tower-original/he-45.png",
    "sourceSize": 471760
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-46.png",
    "rel": "he-zeyu-tower-original/he-46.png",
    "sourceSize": 414259
  },
  {
    "category": "何泽瑜原文",
    "categoryId": "he",
    "filename": "he-78.png",
    "rel": "he-zeyu-tower-original/he-78.png",
    "sourceSize": 473294
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF001_DTU10MW_p13_key_parameters.png",
    "rel": "ch1-ch3/REF001_DTU10MW_p13_key_parameters.png",
    "sourceSize": 187373
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF001_DTU10MW_p33_operational_parameters.png",
    "rel": "ch1-ch3/REF001_DTU10MW_p33_operational_parameters.png",
    "sourceSize": 221085
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF005_Li2023_p01_abstract_global_local_two_scale.png",
    "rel": "ch1-ch3/REF005_Li2023_p01_abstract_global_local_two_scale.png",
    "sourceSize": 464479
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF005_Li2023_p05_C3D8R_T3D2_tendon_and_fracture_energy.png",
    "rel": "ch1-ch3/REF005_Li2023_p05_C3D8R_T3D2_tendon_and_fracture_energy.png",
    "sourceSize": 403249
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF005_Li2023_p07_load_displacement_and_stress_validation.png",
    "rel": "ch1-ch3/REF005_Li2023_p07_load_displacement_and_stress_validation.png",
    "sourceSize": 478900
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF005_Li2023_p09_fullscale_two_scale_modal_and_unbonded_tendon.png",
    "rel": "ch1-ch3/REF005_Li2023_p09_fullscale_two_scale_modal_and_unbonded_tendon.png",
    "sourceSize": 618755
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF005_Li2023_p10_local_stress_and_mesh_requirement.png",
    "rel": "ch1-ch3/REF005_Li2023_p10_local_stress_and_mesh_requirement.png",
    "sourceSize": 409608
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF008_He2024_p33_reinforcement_and_PT_model.png",
    "rel": "ch1-ch3/REF008_He2024_p33_reinforcement_and_PT_model.png",
    "sourceSize": 470589
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF008_He2024_p34_31segment_rebar_table.png",
    "rel": "ch1-ch3/REF008_He2024_p34_31segment_rebar_table.png",
    "sourceSize": 166337
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF008_He2024_p35_tower_geometry_and_model.png",
    "rel": "ch1-ch3/REF008_He2024_p35_tower_geometry_and_model.png",
    "sourceSize": 500986
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF009_Brown2024_p05_tower_frequency_validation.png",
    "rel": "ch1-ch3/REF009_Brown2024_p05_tower_frequency_validation.png",
    "sourceSize": 448079
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF009_Brown2024_p07_modal_validation.png",
    "rel": "ch1-ch3/REF009_Brown2024_p07_modal_validation.png",
    "sourceSize": 500004
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF009_Brown2024_p10_10min_inflow_bins.png",
    "rel": "ch1-ch3/REF009_Brown2024_p10_10min_inflow_bins.png",
    "sourceSize": 541253
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF009_Brown2024_p13_operability_validation.png",
    "rel": "ch1-ch3/REF009_Brown2024_p13_operability_validation.png",
    "sourceSize": 610286
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF009_Brown2024_p15_DEL_validation.png",
    "rel": "ch1-ch3/REF009_Brown2024_p15_DEL_validation.png",
    "sourceSize": 465077
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF009_Brown2024_p17_tower_base_load_validation.png",
    "rel": "ch1-ch3/REF009_Brown2024_p17_tower_base_load_validation.png",
    "sourceSize": 629379
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF010_Cheng2024_p03_RNA_eccentricity_inertia_prestress_model.png",
    "rel": "ch1-ch3/REF010_Cheng2024_p03_RNA_eccentricity_inertia_prestress_model.png",
    "sourceSize": 370549
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF010_Cheng2024_p07_FE_model_and_RNA_mass_properties.png",
    "rel": "ch1-ch3/REF010_Cheng2024_p07_FE_model_and_RNA_mass_properties.png",
    "sourceSize": 535566
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF010_Cheng2024_p09_RNA_simplification_frequency_effect.png",
    "rel": "ch1-ch3/REF010_Cheng2024_p09_RNA_simplification_frequency_effect.png",
    "sourceSize": 458369
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF039_Frequency2023_p23_FE_model.png",
    "rel": "ch1-ch3/REF039_Frequency2023_p23_FE_model.png",
    "sourceSize": 218575
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF039_Frequency2023_p25_mesh_sensitivity.png",
    "rel": "ch1-ch3/REF039_Frequency2023_p25_mesh_sensitivity.png",
    "sourceSize": 210641
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF039_Frequency2023_p29_frequency_comparison.png",
    "rel": "ch1-ch3/REF039_Frequency2023_p29_frequency_comparison.png",
    "sourceSize": 236808
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF046_ROSCO_p04_workflow_and_operating_regions.png",
    "rel": "ch1-ch3/REF046_ROSCO_p04_workflow_and_operating_regions.png",
    "sourceSize": 453553
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF046_ROSCO_p06_controller_logic.png",
    "rel": "ch1-ch3/REF046_ROSCO_p06_controller_logic.png",
    "sourceSize": 453766
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF046_ROSCO_p13_near_rated_time_domain_response.png",
    "rel": "ch1-ch3/REF046_ROSCO_p13_near_rated_time_domain_response.png",
    "sourceSize": 462411
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF046_ROSCO_p17_DLC_operational_comparison.png",
    "rel": "ch1-ch3/REF046_ROSCO_p17_DLC_operational_comparison.png",
    "sourceSize": 568471
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF061_Xu2025_p03_DTU10MW_and_hybrid_tower_lineage.png",
    "rel": "ch1-ch3/REF061_Xu2025_p03_DTU10MW_and_hybrid_tower_lineage.png",
    "sourceSize": 241001
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF061_Xu2025_p10_Abaqus_model_and_pushover_validation.png",
    "rel": "ch1-ch3/REF061_Xu2025_p10_Abaqus_model_and_pushover_validation.png",
    "sourceSize": 597212
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF061_Xu2025_p11_linear_nonlinear_model_comparison.png",
    "rel": "ch1-ch3/REF061_Xu2025_p11_linear_nonlinear_model_comparison.png",
    "sourceSize": 628080
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF080_ERA5_p03_100m_wind_and_dataset_comparison.png",
    "rel": "ch1-ch3/REF080_ERA5_p03_100m_wind_and_dataset_comparison.png",
    "sourceSize": 683070
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF080_ERA5_p07_model_performance.png",
    "rel": "ch1-ch3/REF080_ERA5_p07_model_performance.png",
    "sourceSize": 457961
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF080_ERA5_p08_PSD_and_individual_turbine_results.png",
    "rel": "ch1-ch3/REF080_ERA5_p08_PSD_and_individual_turbine_results.png",
    "sourceSize": 516402
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF090_ReanalysisReview_p08_uncertainty_by_height_and_location.png",
    "rel": "ch1-ch3/REF090_ReanalysisReview_p08_uncertainty_by_height_and_location.png",
    "sourceSize": 390296
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF090_ReanalysisReview_p10_reanalysis_bias_RMSE_correlation.png",
    "rel": "ch1-ch3/REF090_ReanalysisReview_p10_reanalysis_bias_RMSE_correlation.png",
    "sourceSize": 297661
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF090_ReanalysisReview_p11_ERA5_comparative_performance.png",
    "rel": "ch1-ch3/REF090_ReanalysisReview_p11_ERA5_comparative_performance.png",
    "sourceSize": 331552
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF093_DynamicAlpha_p04_tower_validation_method.png",
    "rel": "ch1-ch3/REF093_DynamicAlpha_p04_tower_validation_method.png",
    "sourceSize": 551590
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF093_DynamicAlpha_p05_measured_vs_ERA5_alpha.png",
    "rel": "ch1-ch3/REF093_DynamicAlpha_p05_measured_vs_ERA5_alpha.png",
    "sourceSize": 467950
  },
  {
    "category": "模型、风场与整机文献",
    "categoryId": "source",
    "filename": "REF093_DynamicAlpha_p06_dynamic_alpha_vs_one_seventh.png",
    "rel": "ch1-ch3/REF093_DynamicAlpha_p06_dynamic_alpha_vs_one_seventh.png",
    "sourceSize": 429965
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF002_Kenna2019_p205_steel_concrete_fatigue_design_requirement.png",
    "rel": "fatigue-ch4/REF002_Kenna2019_p205_steel_concrete_fatigue_design_requirement.png",
    "sourceSize": 225687
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF002_Kenna2019_p206_rainflow_Miner_and_separate_material_fatigue.png",
    "rel": "fatigue-ch4/REF002_Kenna2019_p206_rainflow_Miner_and_separate_material_fatigue.png",
    "sourceSize": 251764
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p03_Fig04_sectional_stress_fatigue.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p03_Fig04_sectional_stress_fatigue.png",
    "sourceSize": 348691
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p04_Fig06_07_wind_probability_and_timeseries.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p04_Fig06_07_wind_probability_and_timeseries.png",
    "sourceSize": 576943
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p05_Fig09_azimuth_damage.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p05_Fig09_azimuth_damage.png",
    "sourceSize": 420651
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p06_Fig10_windbin_damage_and_rainflow_method.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p06_Fig10_windbin_damage_and_rainflow_method.png",
    "sourceSize": 585547
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p07_Fig11_mean_stress_correction.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p07_Fig11_mean_stress_correction.png",
    "sourceSize": 518259
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p08_Fig13_14_cycle_damage_and_initial_prestress.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p08_Fig13_14_cycle_damage_and_initial_prestress.png",
    "sourceSize": 432091
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p10_Fig17_18_concrete_and_steel_damage.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p10_Fig17_18_concrete_and_steel_damage.png",
    "sourceSize": 533600
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p11_Fig20_SPPT_stress_timeseries.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p11_Fig20_SPPT_stress_timeseries.png",
    "sourceSize": 369933
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF018_Huang2025_p13_Fig24_26_project_factor_sensitivity.png",
    "rel": "fatigue-ch4/REF018_Huang2025_p13_Fig24_26_project_factor_sensitivity.png",
    "sourceSize": 310796
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF023_Qu2026_p04_Fig01_bidirectional_fatigue_framework.png",
    "rel": "fatigue-ch4/REF023_Qu2026_p04_Fig01_bidirectional_fatigue_framework.png",
    "sourceSize": 885230
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF023_Qu2026_p13_Fig04_Weibull_wind_distribution.png",
    "rel": "fatigue-ch4/REF023_Qu2026_p13_Fig04_Weibull_wind_distribution.png",
    "sourceSize": 361769
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF023_Qu2026_p16_Fig06_tendon_load_spectrum.png",
    "rel": "fatigue-ch4/REF023_Qu2026_p16_Fig06_tendon_load_spectrum.png",
    "sourceSize": 522989
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF023_Qu2026_p17_Table07_tendon_annual_damage.png",
    "rel": "fatigue-ch4/REF023_Qu2026_p17_Table07_tendon_annual_damage.png",
    "sourceSize": 421513
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF023_Qu2026_p18_Fig07_08_tendon_fatigue_life.png",
    "rel": "fatigue-ch4/REF023_Qu2026_p18_Fig07_08_tendon_fatigue_life.png",
    "sourceSize": 369150
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF023_Qu2026_p20_Fig09_10_Weibull_and_relaxation_effect.png",
    "rel": "fatigue-ch4/REF023_Qu2026_p20_Fig09_10_Weibull_and_relaxation_effect.png",
    "sourceSize": 404765
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF023_Qu2026_p21_Table08_concrete_annual_damage.png",
    "rel": "fatigue-ch4/REF023_Qu2026_p21_Table08_concrete_annual_damage.png",
    "sourceSize": 513835
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF023_Qu2026_p24_Fig15_16_min_concrete_and_coupled_life.png",
    "rel": "fatigue-ch4/REF023_Qu2026_p24_Fig15_16_min_concrete_and_coupled_life.png",
    "sourceSize": 483022
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF036_Kim2019_p04_Fig04_joint_section_and_fatigue_load.png",
    "rel": "fatigue-ch4/REF036_Kim2019_p04_Fig04_joint_section_and_fatigue_load.png",
    "sourceSize": 539252
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF036_Kim2019_p06_Fig07_specimens_and_reinforcement.png",
    "rel": "fatigue-ch4/REF036_Kim2019_p06_Fig07_specimens_and_reinforcement.png",
    "sourceSize": 651307
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF036_Kim2019_p07_two_million_cycle_test_method.png",
    "rel": "fatigue-ch4/REF036_Kim2019_p07_two_million_cycle_test_method.png",
    "sourceSize": 589579
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF036_Kim2019_p08_Fig10_cyclic_load_displacement.png",
    "rel": "fatigue-ch4/REF036_Kim2019_p08_Fig10_cyclic_load_displacement.png",
    "sourceSize": 637135
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF041_Wang2025_p16_Fig17_joint_contact_stress.png",
    "rel": "fatigue-ch4/REF041_Wang2025_p16_Fig17_joint_contact_stress.png",
    "sourceSize": 524205
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF041_Wang2025_p20_Fig19_fatigue_verification_area.png",
    "rel": "fatigue-ch4/REF041_Wang2025_p20_Fig19_fatigue_verification_area.png",
    "sourceSize": 399590
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF041_Wang2025_p21_Table04_reference_stress_and_damage.png",
    "rel": "fatigue-ch4/REF041_Wang2025_p21_Table04_reference_stress_and_damage.png",
    "sourceSize": 588044
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF143_Zhao2023_p08_Fig09_flange_principal_stress.png",
    "rel": "fatigue-ch4/REF143_Zhao2023_p08_Fig09_flange_principal_stress.png",
    "sourceSize": 878966
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF143_Zhao2023_p09_Fig10_11_Table02_damage_and_SCF.png",
    "rel": "fatigue-ch4/REF143_Zhao2023_p09_Fig10_11_Table02_damage_and_SCF.png",
    "sourceSize": 463369
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF143_Zhao2023_p11_Fig16_fatigue_assessment_process.png",
    "rel": "fatigue-ch4/REF143_Zhao2023_p11_Fig16_fatigue_assessment_process.png",
    "sourceSize": 295818
  },
  {
    "category": "材料疲劳原文",
    "categoryId": "fatigue",
    "filename": "REF143_Zhao2023_p13_Table05_07_annual_and_weld_damage.png",
    "rel": "fatigue-ch4/REF143_Zhao2023_p13_Table05_07_annual_and_weld_damage.png",
    "sourceSize": 374889
  },
  {
    "category": "学位论文对照",
    "categoryId": "thesis",
    "filename": "REF006_LiShouzhen_p095_gravity_second_order_dynamic_conclusions.png",
    "rel": "comparison-theses/REF006_LiShouzhen_p095_gravity_second_order_dynamic_conclusions.png",
    "sourceSize": 429006
  },
  {
    "category": "学位论文对照",
    "categoryId": "thesis",
    "filename": "REF007_LiZeyu_p149_Ch6_time_domain_fatigue_method.png",
    "rel": "comparison-theses/REF007_LiZeyu_p149_Ch6_time_domain_fatigue_method.png",
    "sourceSize": 516050
  },
  {
    "category": "学位论文对照",
    "categoryId": "thesis",
    "filename": "REF007_LiZeyu_p151_Ch6_SN_curves.png",
    "rel": "comparison-theses/REF007_LiZeyu_p151_Ch6_SN_curves.png",
    "sourceSize": 292078
  },
  {
    "category": "学位论文对照",
    "categoryId": "thesis",
    "filename": "REF007_LiZeyu_p152_Ch6_fatigue_analysis_regions.png",
    "rel": "comparison-theses/REF007_LiZeyu_p152_Ch6_fatigue_analysis_regions.png",
    "sourceSize": 222302
  },
  {
    "category": "学位论文对照",
    "categoryId": "thesis",
    "filename": "REF007_LiZeyu_p157_Ch6_fatigue_results.png",
    "rel": "comparison-theses/REF007_LiZeyu_p157_Ch6_fatigue_results.png",
    "sourceSize": 450267
  },
  {
    "category": "学位论文对照",
    "categoryId": "thesis",
    "filename": "REF007_LiZeyu_p159_Ch6_fatigue_life_table_and_summary.png",
    "rel": "comparison-theses/REF007_LiZeyu_p159_Ch6_fatigue_life_table_and_summary.png",
    "sourceSize": 518828
  }
] as const;
const GITHUB_IMAGE_BASE = 'https://raw.githubusercontent.com/g2066203208-beep/voxel-frontier/e214c9c785b17fff6644bc335f6d3945317db267/research/wind-tower/references/evidence-screenshots/';
const h = (s: unknown) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'} as Record<string,string>)[c]);
export const evidenceImageCount = IMAGE_INDEX.length;
export function sourceEvidencePage(): string {
 const cards=IMAGE_INDEX.map((f,i) => {
   const alt = f.category + ' / ' + f.filename;
   const src = GITHUB_IMAGE_BASE + f.rel.split('/').map(encodeURIComponent).join('/');
   const pretty = f.filename.replace(/\.png$/i,'').replaceAll('_',' ');
   return '<figure class="source-figure" data-source-card="' + i + '"><button type="button" data-evidence-open="' + i + '" aria-label="原位放大 '+h(alt)+'"><img loading="lazy" decoding="async" src="'+h(src)+'" alt="'+h(alt)+'"></button><figcaption><strong>'+h(pretty)+'</strong><small>'+h(f.category)+' · 原始文献页截图</small></figcaption></figure>';
 }).join('');
 return '<div class="evidence-page"><header class="evidence-title"><div class="eyebrow">PRIMARY SOURCE / ORIGINAL PAGE EVIDENCE</div><h1>参考文献原页证据库</h1><p>85张原始论文页截图在当前工作室直接阅读、筛选和放大，不跳转GitHub。截图用于研究方法核查，不作为本文原创计算结果。</p></header>'+
 '<section class="evidence-tools"><label for="evidence-category">文献类型</label><select id="evidence-category"><option value="all">全部原页（85）</option><option value="he">何泽瑜原文（11）</option><option value="source">模型、风场与整机（38）</option><option value="fatigue">疲劳文献（30）</option><option value="thesis">学位论文对照（6）</option></select><input id="evidence-search" type="search" placeholder="检索REF编号、作者、原文页或图号" aria-label="检索参考原页"/><output id="evidence-count" aria-live="polite">85 / 85</output></section>'+
 '<div class="evidence-grid" id="evidence-grid">'+cards+'</div><p class="evidence-no-result" id="evidence-empty" hidden>没有符合条件的原页。</p>'+
 '<div id="evidence-viewer" class="evidence-viewer" hidden><div class="evidence-viewer-bar"><span id="evidence-caption"></span><button type="button" id="evidence-close" aria-label="关闭原页放大">关闭</button></div><div class="evidence-viewer-image"><img id="evidence-large" alt="原文页放大"></div></div>'+
 '<p class="evidence-rights">资料范围：GitHub研究分支现存的11+38+30+6张关键原页，不是何泽瑜整本90页的逐页图片，也不是全部文献PDF全文。原著作权及引用归原作者或出版方；禁止将证据截图冒充论文原创图。</p></div>';
}
export function mountSourceEvidence(root: HTMLElement): void {
 const search=root.querySelector<HTMLInputElement>('#evidence-search'), category=root.querySelector<HTMLSelectElement>('#evidence-category'), count=root.querySelector<HTMLOutputElement>('#evidence-count'), empty=root.querySelector<HTMLElement>('#evidence-empty');
 const viewer=root.querySelector<HTMLElement>('#evidence-viewer'), image=root.querySelector<HTMLImageElement>('#evidence-large'), caption=root.querySelector<HTMLElement>('#evidence-caption');
 if(!search||!category||!count||!empty||!viewer||!image||!caption)return;
 const cards=Array.from(root.querySelectorAll<HTMLElement>('[data-source-card]'));
 const filter=() => {
   const q=search.value.trim().toLowerCase(); let shown=0;
   cards.forEach((card,i) => {const f=IMAGE_INDEX[i], ok=(category.value==='all'||f.categoryId===category.value)&&(!q||(f.filename+' '+f.category).toLowerCase().includes(q)); card.hidden=!ok; if(ok)shown++;});
   count.textContent=shown+' / '+IMAGE_INDEX.length; empty.hidden=shown>0;
 };
 search.addEventListener('input',filter);category.addEventListener('change',filter);
 root.querySelectorAll<HTMLButtonElement>('[data-evidence-open]').forEach(button=>button.addEventListener('click',()=>{
   const n=Number(button.dataset.evidenceOpen), f=IMAGE_INDEX[n]; if(!f)return;
   image.src=GITHUB_IMAGE_BASE+f.rel.split('/').map(encodeURIComponent).join('/'); image.alt=f.category+' / '+f.filename;
   caption.textContent=f.category+' · '+f.filename;viewer.hidden=false;viewer.scrollIntoView({block:'nearest'});
 }));
 root.querySelector<HTMLButtonElement>('#evidence-close')?.addEventListener('click',()=>{viewer.hidden=true;image.removeAttribute('src');});
}
