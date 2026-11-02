#!/usr/bin/env python3
"""Source-locked 21-year ERA5 + real 18 NTM load-level m4 diagnosis.

This derives ONLY the observed-bin part of an annual-hour-weighted load
fourth-moment, NOT an all-wind-bin annual DEL, concrete or steel fatigue,
Miner damage, or formal IEC DLC1.2 approval. No simulation is run.
"""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BIN=HERE/"S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv"
BIN_RECEIPT=HERE/"S10_ERA5_2005_2025_HUB_BIN_RECEIPT_20261031.json"
COVER=HERE/"S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv"
COVER_RECEIPT=HERE/"S10_ERA5_21BIN_6SEED_COVERAGE_RECEIPT_20261031.json"
DEL=HERE/"S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv"
DEL_RECEIPT=HERE/"S06_18NTM_ORIGINAL_LOAD_DEL_RECEIPT_20261031.json"

def hash_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_csv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def check(ok,msg):
    if not ok:raise ValueError(msg)

def q(v,n=10):
    return round(v,n)

def run():
    b=json.loads(BIN_RECEIPT.read_text())
    covrec=json.loads(COVER_RECEIPT.read_text())
    dr=json.loads(DEL_RECEIPT.read_text())
    check(hash_file(BIN)==b["output_sha256"],"SOURCE_ERA5_BIN_SHA_MISMATCH")
    check(hash_file(DEL)==dr["result_sha256"],"SOURCE_18_NTM_ORIGINAL_LOAD_DEL_SHA_MISMATCH")
    check(hash_file(COVER)==covrec["output_csv_sha256"],"SOURCE_COVERAGE_MATRIX_SHA_MISMATCH")
    check(b["n_hours"]==184080 and b["operating_hours_4_to_25"]==106900,"ERA5_HOUR_SCOPE_CHANGED")
    check(dr["original_outb_count"]==18 and dr["result_rows"]==1080,"ORIGINAL_SOURCE_IDENTITY_INCOMPLETE")
    check(covrec["summary"]["formal_dlc12_verified_slots"]==0,"DLC12_NOT_ALLOWED_AS_VERIFIED")
    winds=read_csv(BIN);coverage=read_csv(COVER);raw=read_csv(DEL)
    check(len(winds)==31 and len(coverage)==126 and len(raw)==1080,"SOURCE_ROW_COUNT_MISMATCH")
    hours={int(r["bin_lower_mps"]):int(r["hours"]) for r in winds}
    check(sum(hours.values())==184080 and sum(hours.get(i,0) for i in range(4,25))==106900,"ERA5_HOURS_SUM_MISMATCH")
    by_group={}
    expected_channels=["TwrBsMxt","TwrBsMyt"]
    for rec in raw:
        if rec["channel"] not in expected_channels:continue
        case=rec["case"]
        parts=case.split("_")
        check(len(parts)==3 and parts[1]=="NTM" and parts[2].startswith("S"),"SOURCE_CASE_ROLE_CHANGED")
        speed={"U09p343881":9.343881,"U11p4":11.4,"U19p202140":19.202140}.get(parts[0])
        check(speed is not None,"UNEXPECTED_SOURCE_WIND_IDENTITY")
        slot=int(speed)
        seed=parts[2]
        key=(slot,rec["channel"])
        check(rec["unit"]=="(kN-m)" and int(rec["n_samples"])==12001
              and float(rec["t0_s"])==100 and float(rec["t1_s"])==700
              and float(rec["dt_s"])==0.05,"SOURCE_SIGNAL_IDENTITY_CHANGED")
        check(rec["outb_sha256"] and len(rec["outb_sha256"])==64,"OUTB_SHA_MISSING")
        check(float(rec["DEL_m4_Nref600"])>0,"BAD_DEL")
        check((slot,seed) in {(int(x["bin_lower_mps"]),x["seed_id"]) for x in coverage
            if x["historical_case_id"]==case and x["outb_sha256"]==rec["outb_sha256"]},"SEED_CASE_SHA_NOT_IN_126_COVERAGE")
        bucket=by_group.setdefault(key,{})
        check(seed not in bucket,"DUPLICATE_NTM_SEED")
        bucket[seed]=float(rec["DEL_m4_Nref600"])/1000.0 # MN-m
    check(set(by_group)=={(i,ch) for i in (9,11,19) for ch in expected_channels},"WRONG_3BIN_2CHANNEL_DATA")
    for key,seed_values in by_group.items():
        check(set(seed_values)=={"S01","S02","S03","S04","S05","S06"},"SEED_MISSING_"+str(key))
    old_summary=covrec["summary"]
    check(old_summary["archived_bin_site_hours"]==sum(hours[i] for i in (9,11,19))==7164,
         "COVERED_BIN_HOURS_CHANGED")
    check(old_summary["diagnostic_operating_hours"]==106900 and old_summary["unrepresented_operating_hours"]==99736,
         "PRIOR_OPERATING_SCOPE_DIFFERENCE")
    rows=[]
    aggregate={}
    for channel in expected_channels:
        out=[]
        for wind in (9,11,19):
            values=by_group[(wind,channel)]
            m4=sum(v**4 for v in values.values())/6
            power=m4**.25
            mean=sum(values.values())/6
            # Bin means of six 600-s windows, not six independent 21y climate samples.
            p=hours[wind]/184080
            p_cond=hours[wind]/106900
            weighted=p*m4
            subset_powers=[(sum(values[k]**4 for k in keys)/3)**.25
                           for keys in itertools.combinations(sorted(values),3)]
            # Combinations 3 of 6 produce 20 finite-sample subset estimates.
            # They are *not* a confidence interval for the long-run population.
            check(len(subset_powers)==20,"SUBSET_ENUM_FAIL")
            out.append({"channel":channel,"wind_bin_mps":wind,"historical_wind_mps":
                {9:9.343881,11:11.4,19:19.20214}[wind],
                "historic_era5_hours_21y":hours[wind],
                "p_of_all_hours":q(p,12),"p_of_diagnostic_operating_hours":q(p_cond,12),
                "six_seed_power_mean_DEL_m4_MNm":q(power,9),
                "six_seed_arithmetic_mean_DEL_MNm":q(mean,9),
                "six_seed_m4_mean_MNm4":q(m4,9),
                "known_bin_contribution_p_all_times_m4_MNm4":q(weighted,10),
                "three_of_six_power_mean_min_MNm":q(min(subset_powers),9),
                "three_of_six_power_mean_max_MNm":q(max(subset_powers),9),
                "num_3_of_6_subsets":len(subset_powers),
                "formal_DLC12_status":"NOT_VALIDATED",
                "material_damage_status":"NOT_COMPUTABLE"})
        # Exact 20^3 independent subset combinations across three bins.
        options={}
        for wind in (9,11,19):
            values=by_group[(wind,channel)]
            options[wind]=[(sum(values[k]**4 for k in comb)/3) for comb in itertools.combinations(sorted(values),3)]
        candidate=[sum((hours[i]/184080)*moments[j] for j,i in enumerate((9,11,19)))
                   for moments in itertools.product(*(options[i] for i in (9,11,19)))]
        check(len(candidate)==8000,"COMBINED_EXACT_FINITE_SUBSETS_NOT_8000")
        total=sum(hours[int(r["wind_bin_mps"])]/184080*float(r["six_seed_m4_mean_MNm4"])
                  for r in out)
        # 19-bin has TWO ERA5 hours in twenty-one years: tiny probability, not proven zero.
        agg={"channel":channel,"covered_bins":[9,11,19],
             "covered_observed_hours_21y":7164,
             "covered_probability_all_era5_hours":q(7164/184080,12),
             "covered_probability_given_diagnostic_operation":q(7164/106900,12),
             "unrepresented_observed_diagnostic_operation_fraction":q(99736/106900,12),
             "annual_hours_8760_from_these_3_bins":q(8760*7164/184080,9),
             "known_bin_partial_all_hour_weighted_m4_MNm4":q(total,9),
             "known_bin_partial_all_hour_weighted_m4_3of6_min_MNm4":q(min(candidate),9),
             "known_bin_partial_all_hour_weighted_m4_3of6_max_MNm4":q(max(candidate),9),
             "3of6_joint_subset_combinations":len(candidate),
             "known_bin_partial_m4_percent_split":{str(int(r["wind_bin_mps"])):q(100*(hours[int(r["wind_bin_mps"])]/184080*float(r["six_seed_m4_mean_MNm4"]))/total,6) for r in out},
             "total_annual_fatigue_damage":"UNDEFINED_MISSING_18_OF_21_DIAGNOSTIC_BINS_AND_LOCAL_MATERIAL_STRESSES",
             "formal_DLC12_2025_edition":"NOT_VERIFIED",
             "error_scope":"3-of-6 finite-sample subset envelope only, not statistical confidence interval; bins/ERA5/quantization/model uncertainty outside",
             "interpretation":"partial site-hour-weighted load m4 intensity only; not a complete-year DEL nor local material Miner damage"}
        rows+=out
        aggregate[channel]=agg
    check(len(rows)==6,"BAD_OUT_ROW_COUNT")
    receipt={
      "status":"S10_REAL_18_NTM_SITE_WEIGHTED_PARTIAL_M4_SOURCE_DIAGNOSTIC_ONLY",
      "SOURCE":{"era5_31bin_sha256":hash_file(BIN),
                "original_18NTM_1080rows_sha256":hash_file(DEL),
                "21bin_126seed_slots_sha256":hash_file(COVER),
                "original_OUTB_S06_receipt_sha256":hash_file(DEL_RECEIPT)},
      "READING_LEVEL":"This run reads archived 31-bin ERA5-derived CSV, SHA-verified 1080-row OUTB-derived load-DEL and 126-row source coverage; prior run reads 18 actual OpenFAST OUTB and original ERA5 workbook; no new original CDS or new OpenFAST solve",
      "SOURCE_OBSERVATIONS":{"era5_hours":184080,"operating_hours_4_to_25_DIAGNOSTIC":106900,
           "archived_NTM_cases":18,"covered_bins":[9,11,19],"total_21_wind_bins":21,
           "formal_verified_DLC12_slots":0,"uncovered_operating_hours":99736,
           "bins_4_through_8_hour_share_of_operating":q(sum(hours[i] for i in range(4,9))/106900,12),
           "untested_18_of_21_bins":"no known load m4 available, no zero-fill permitted"},
      "RESULTS":aggregate,
      "REFS":[
       {"id":"REF011","doi":"10.5194/wes-4-479-2019","reading":"full-text journal HTML §2.2, §2.4, §4.1.3 and §3.3.2 personally reviewed this turn","transfer":"multiple seeds per wind speed, seed convergence and wind probability as method; 5MW/30-seed sensitivity not direct 10MW data"},
       {"id":"REF018","doi":"10.1016/j.engstruct.2025.120295","reading":"publisher title/volume/abstract and prior archived user complete-PDF method audit; NOT new full PDF read this turn","transfer":"2025 segmental PT concrete tower fatigue workflow motivates material separation; no numeric life transferred"},
       {"id":"REF083","doi":"10.1002/er.6382","reading":"publisher open-access full HTML methods/limitations personally reviewed this turn; prior user PDF audit inherited","transfer":"hourly dynamic shear from ERA5 10m/100m for site wind climate, not measured Jiayu source"},
       {"id":"REF080","doi":"10.1016/j.renene.2018.03.056","reading":"publisher abstract + prior user PDF method audit inherited","transfer":"ERA5 wind climate baseline only, not high-frequency wind loading"},
       {"id":"REF090","doi":"10.1016/j.rser.2022.112741","reading":"publisher abstract/highlights + prior full PDF review inherited","transfer":"reanalysis site uncertainty, no numeric Jiayu error estimate"},
       {"id":"REF132","standard":"IEC 61400-1:2019 Ed4.0","reading":"repository original licensed 172pp edition review inherited; not reopened authorized original now","transfer":"base-2019 DLC1.2/NTM identity only; pending 2025 amendment compliance check"},
       {"id":"REF048","standard":"IEC 61400-1:2019+AMD1:2025 Ed4.1 corrected 2026-10",
         "uri":"https://webstore.iec.ch/en/publication/111042","reading":"IEC official current product metadata (edition, 2026-10 correction, 358pp) personally reviewed; full clauses NOT read","transfer":"amendment may change NTM distribution/DLC scope; cannot claim 2025 formal validation"},
       {"id":"REF049","standard":"IEC 61400-6:2020+AMD1:2025 Ed1.1",
         "uri":"https://webstore.iec.ch/en/publication/107942","reading":"IEC official current product metadata, 311pp, tower & foundation scope; full clauses NOT read","transfer":"no structural compliance asserted"}
      ],
      "STANDARD":"2019 base text review inherited; 2025 consolidated IEC full text NOT available this run; 4-25m/s and 1m/s bins planning assumptions not claimed IEC mandatory",
      "OFFICIAL":"OpenFAST native outputs inherited original-source verification + IEC official edition pages, no new solver",
      "RUN":"GitHub Actions Python stdlib m4 probability diagnostic 3bins x6seed x2tower channels, exhaustive 3-of-6 subsets, no Abaqus",
      "FIG":"No new physical figure",
      "TAB":"6-row per-bin m4 intensity and two-channel annual-hour-weighted covered-only moments",
      "ERROR_BUDGET":"source int16 half-step recorded upstream; seed-subset finite sensitivity only; 93.3% diagnostic operating hours outside empirical bins; ERA5 site bias and bin center mismatch unquantified",
      "HOLD":"Formal DLC1.2 and materials life unverified: 18 of 21 assumed operating bins not sampled, no material stress history, standard 2025 clauses unread",
      "PHYSICAL_PASS":False,
      "MATERIAL_FATIGUE_PASS":False
    }
    return rows,receipt

def main():
    p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);args=p.parse_args()
    rows,receipt=run();args.output_dir.mkdir(parents=True,exist_ok=True)
    dst=args.output_dir/"S10_REAL_18NTM_3BIN_PARTIAL_M4_BY_CHANNEL_20261102.csv"
    with dst.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
    receipt["TAB_CSV_SHA256"]=hash_file(dst)
    (args.output_dir/"S10_REAL_18NTM_3BIN_PARTIAL_M4_RECEIPT_20261102.json").write_text(json.dumps(receipt,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"result":receipt["status"],"rows":len(rows),"coverage":receipt["SOURCE_OBSERVATIONS"],
          "channels":receipt["RESULTS"],"csv_sha256":receipt["TAB_CSV_SHA256"]},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
