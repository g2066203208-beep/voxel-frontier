#!/usr/bin/env python3
"""T091: source-locked static copies for the ONE Jiayu research studio.
Research branch is read-only. Never runs Abaqus, changes a scientific model,
or substitutes reconstructed curves for real source samples.
"""
from __future__ import annotations
import csv, hashlib, importlib.util, io, json, os, pathlib, subprocess, sys, tempfile, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[2]
STUDIO=ROOT/"public"/"thesis-studio"
OUT=STUDIO/"primary-data"
BRANCH="research/t080-seismic-integration-gates-20261022"
REF="refs/remotes/origin/"+BRANCH
PREFIX="research/wind-tower/"
FILES=[
 ("era5-wind-bins","ERA5衍生风速频率（31箱）","风资源", "experiments/T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv",31,"bin_lower_mps","p_all_hours","p_conditional_4_to_25","2005–2025衍生工作簿统计，161.368806m动态风切变估计；不是原始184080行ERA5 GRIB/NetCDF。"),
 ("era5-direction","ERA5 100m风向16方位","风资源","experiments/T062/S12_R5_ERA5_100M_DIRECTION_16SECTOR_20261109.csv",16,"sector","all_pct","high_v100_ge_p95_pct","100m风速的16方位与高风速P95样本占比；不等于161m风向。"),
 ("esm-spectrum","真实ESM NVL记录的46周期衍生谱","地震源", "experiments/T079/real-records/S05_ESM_NVL_PSA_PSD_46PERIOD_20261107.csv",46,"period_s","RotD50_PSA_m_s2","RotD100_PSA_m_s2","IT-2012-0008 NVL记录，ESM MP处理波导出的单自由度反应谱；不是场址目标设计谱或混塔响应。"),
 ("esm-component-peaks","ESM三分量同刻加速度峰值","地震源","experiments/T079/real-records/S08_ESM_IT2012_NVL_3COMP_COINCIDENT_PEAKS_20261101.csv",5,"metric","peak_m_s2",None,"事件IT-2012-0008，台站NVL，单位m/s²；同刻峰值，不能按单轴最大值拼造三分量峰值。"),
 ("ntm18-load-summary","18组NTM真实历史塔底统计","风荷载","experiments/T062/S06_NTM18_THREE_QOI_18CASE_20261109.csv",18,"case","peak_My_MNm","DEL4_My_MNm","OpenFAST历史结构反力统计；不是已经区分的纯塔身外气动力，更不是材料年疲劳寿命。"),
 ("ntm18-annual-clock","18组NTM工况风箱与年度时钟","风荷载","experiments/T062/S10_NTM18_600S_ANNUAL_BLOCK_CLOCK_20261114.csv",18,"case_id","annual_bin_hours_all_hours","annual_600s_block_repeats_per_seed","年度风速权重与600s时程重复次数仅为来源账本，不代表完整DLC1.2准入或矿工Miner寿命。"),
 ("bf1-30-frequencies","BF1旧成功模型30阶模态","结构历史","experiments/T082/BF1_GRAVITY_MODAL_20261115/BF1_MODAL_30_FREQUENCIES.csv",30,"mode_number","frequency_cycles_per_time_unit",None,"T082旧弹簧接缝模型的历史成功结果；绝非R6全塔新接触模型的模态。"),
 ("bf1-rebar-31","BF1分支31段配筋设计表","结构历史","experiments/T077/T077_FORMAL_31SEG_REBAR_BF1.csv",31,"segment","max_utilization",None,"T077设计分支，不等于2026-11-14本机恢复环筋后的最终逐段原生计算。"),
 ("wind-36-envelopes","36历史风工况六分量包络","风荷载","experiments/T072/T072_FORMAL_36CASE_BASE_ENVELOPE.csv",36,None,None,None,"36历史风工况载荷包络；其来源与真实结构疲劳输入需分别审查。"),
]
CHAPTERS=[
 ("01","绪论","manuscript/final-thesis/chapters/01_绪论.md"),
 ("02","研究对象与模型","manuscript/final-thesis/chapters/02_研究对象_精细有限元模型与分层验证.md"),
 ("03","风环境与随机风载","manuscript/final-thesis/chapters/03_场址风环境与整机随机风控制载荷.md"),
 ("04","风致疲劳性能","manuscript/final-thesis/chapters/04_10MW混合塔架风致疲劳性能分析.md"),
 ("05","参数敏感性与优化","manuscript/final-thesis/chapters/05_疲劳控制参数敏感性与结构优化.md"),
 ("06","结论与展望","manuscript/final-thesis/chapters/06_结论与展望.md")
]
def call(*a):
 return subprocess.run(a,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
def source(rel):
 return call("git","show",REF+":"+PREFIX+rel)
def provenance(rel,blob):
 return {"path":PREFIX+rel,"git_blob_sha":call("git","rev-parse",REF+":"+PREFIX+rel).decode().strip(),"sha256":hashlib.sha256(blob).hexdigest(),"bytes":len(blob)}
def copy(rel,outname):
 blob=source(rel)
 p=OUT/outname;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob)
 return blob,provenance(rel,blob)
def rows_for(blob,expected):
 text=blob.decode("utf-8-sig")
 reader=list(csv.DictReader(io.StringIO(text)))
 if len(reader)!=expected or not reader or any(None in r for r in reader):
  raise RuntimeError(f"source CSV changed expected={expected} got={len(reader)}")
 return reader
def esm_waveform():
 wave=OUT/"esm-it2012-nvl-3comp.csv"
 source_script="experiments/T079/s05_esm_public_processed_pair.py"
 receipt=json.loads(source("experiments/T079/real-records/S08_ESM_IT2012_NVL_MP_ACCEL_SI_SOURCE_RECEIPT.json"))
 try:
  with tempfile.TemporaryDirectory() as td:
   script=pathlib.Path(td)/"esm_source.py";script.write_bytes(source(source_script))
   spec=importlib.util.spec_from_file_location("esm_source",script)
   mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
   request=urllib.request.Request(mod.url(),headers={"User-Agent":"CAE-paper-studio-source-attribution/1.0","Accept":"application/zip"})
   with urllib.request.urlopen(request,timeout=55) as res:
    raw=res.read(30_000_001)
   if len(raw)>30_000_000:raise RuntimeError("ESM ZIP too large")
   meta=mod.inspect_zip(raw)
   if {m["dyna_selected_header_fields"]["STREAM"] for m in meta}!={"HNE","HNN","HNZ"}:
    raise RuntimeError("ESM component identity mismatch")
   licenses={m["dyna_selected_header_fields"]["DATA_LICENSE"] for m in meta}
   if len(licenses)!=1 or not next(iter(licenses)).upper().startswith("CC-BY"):
    raise RuntimeError("no confirmed ESM attribution license")
   data,gate=mod.export_s08_acceleration_si(raw,strict_real=True)
   if gate["csv_sha256"]!=receipt["csv_sha256"] or gate["npts"]!=32040 or gate["dt_s"]!=0.005:
    raise RuntimeError("archived 3-component export SHA/grid mismatch")
   wave.write_bytes(data)
   return {"status":"VERIFIED_FULLRATE_32040","src":"./primary-data/esm-it2012-nvl-3comp.csv",
     "rows":32040,"dt_s":0.005,"source":"ESM v3 DOI:10.13127/esm.3; processed MP ACC, NVL IT-2012-0008",
     "license":next(iter(licenses)),"csv_sha256":gate["csv_sha256"],
     "original_numeric_sha256":gate["numeric_source_sha256_by_stream"],
     "source_zip_sha256":gate["source_zip_sha256"],
     "warning":"真实处理波、未施设计谱匹配及幅值/坐标变换，不代表正式场址地震输入或全塔地震结果"}
 except Exception as ex:
  msg=type(ex).__name__+": "+str(ex)[:220]
  print("T091 ESM original full-rate source gate not passed:",msg,file=sys.stderr)
  if wave.exists() and hashlib.sha256(wave.read_bytes()).hexdigest()==receipt.get("csv_sha256"):
   return {"status":"RETAINED_PREVIOUSLY_VERIFIED","src":"./primary-data/esm-it2012-nvl-3comp.csv",
           "rows":32040,"dt_s":0.005,"csv_sha256":receipt["csv_sha256"],
           "warning":"沿用已核验原始波；本次官方源重取失败："+msg}
  return {"status":"FULLRATE_NOT_AVAILABLE","src":None,"rows":0,"reason":msg,
          "warning":"有原始波身份和SHA凭据，但站内未取得完整32040点，不会以反应谱或代理时程冒充"}
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 datasets=[]
 for id,title,group,path,n,x,y,y2,note in FILES:
  data,p=copy(path,f"{id}.csv")
  tab=rows_for(data,n)
  if id=="era5-wind-bins" and sum(int(r["hours"]) for r in tab)!=184080:
   raise RuntimeError("ERA5 184080 hourly count mismatch")
  datasets.append({"id":id,"title":title,"group":group,"src":"./primary-data/"+id+".csv",
    "n":n,"x":x,"y":y,"y2":y2,"note":note,"provenance":p})
 chapters=[]
 for id,title,path in CHAPTERS:
  data,p=copy(path,f"manuscript/{id}.md")
  if len(data)<2000:raise RuntimeError("chapter unexpectedly short: "+id)
  chapters.append({"id":id,"title":title,"src":"./primary-data/manuscript/"+id+".md","provenance":p})
 model,mp=copy("models/CURRENT_TOWER_SETTINGS_20261114.json","model-settings-20261114.json")
 if len(json.loads(model).get("sections",[]))!=9:raise RuntimeError("92-item model snapshot changed")
 manifest={"schema":1,"task":"T091","research_branch":BRANCH,
  "research_commit":call("git","rev-parse",REF).decode().strip(),
  "scientific_status":"SOURCE DATA DISPLAY; not new simulation or accepted design wave",
  "datasets":datasets,"chapters":chapters,"model_settings":{"src":"./primary-data/model-settings-20261114.json",
  "scope":"2026-11-14 Codex-reported 92-parameter snapshot; NOT R6 current physical model","provenance":mp},
  "waveform":esm_waveform()}
 (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("T091 sources:",len(datasets),"chapters:",len(chapters),
       "seismic_waveform:",manifest["waveform"]["status"],
       "commit:",manifest["research_commit"])
if __name__=="__main__":main()
