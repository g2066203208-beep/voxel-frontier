import csv, hashlib, re, struct, zipfile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
CASE_ROOT = ROOT / 'CASES'

def read_header(path):
    with path.open('rb') as f:
        fid, nl, nc, nt = struct.unpack('<hhii', f.read(12))
        t0, dt = struct.unpack('<2d', f.read(16))
        f.seek(4*nc + 4*nc, 1)
        dl = struct.unpack('<i', f.read(4))[0]
        f.seek(dl + (nc+1)*nl*2, 1)
        return nt, dt, t0 + (nt-1)*dt

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def damping_values(path):
    txt = path.read_text(encoding='utf-8', errors='ignore')
    vals = {}
    for label in ('TwrFADmp(1)','TwrFADmp(2)','TwrSSDmp(1)','TwrSSDmp(2)'):
        m = re.search(r'^\s*([-+0-9.eE]+)\s+' + re.escape(label) + r'(?=\s|$)', txt, re.M)
        if not m:
            raise RuntimeError(f'missing {label}: {path}')
        vals[label] = float(m.group(1))
    return vals

def main():
    cases = sorted([p for p in CASE_ROOT.iterdir() if p.is_dir() and p.name.startswith('U')])
    expected = {'TwrFADmp(1)':4.6350,'TwrFADmp(2)':5.5344,'TwrSSDmp(1)':4.6341,'TwrSSDmp(2)':5.5282}
    damp_rows=[]; outb_rows=[]; errors=[]
    for c in cases:
        towers = c/'C02R3R2_158M_Tower.dat'; outb = c/'DTU_10MW_RWT.outb'
        try:
            vals=damping_values(towers)
            ok=all(abs(vals[k]-v)<5e-7 for k,v in expected.items())
        except Exception as e:
            vals={}; ok=False; errors.append(str(e))
        damp_rows.append({'case_id':c.name, **vals, 'status':'PASS' if ok else 'FAIL'})
        try:
            nt,dt,tend=read_header(outb); good=(nt>0 and abs(tend-700.0)<1e-6 and abs(dt-0.05)<1e-9)
        except Exception as e:
            nt=0;dt=0;tend=0;good=False;errors.append(str(e))
        outb_rows.append({'case_id':c.name,'n_samples':nt,'dt_s':dt,'t_end_s':tend,'status':'PASS' if good else 'FAIL'})
    with (ROOT/'FORMAL_36CASE_ACTUAL_DAMPING_RAINFLOW.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(damp_rows[0])); w.writeheader(); w.writerows(damp_rows)
    with (ROOT/'FORMAL_36CASE_OUTB_TIME_AUDIT_RAINFLOW.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(outb_rows[0])); w.writeheader(); w.writerows(outb_rows)
    expected_cases=36
    del_rows=list(csv.DictReader((ROOT/'05_LOAD_DEL_M4_ALL36.csv').open(encoding='utf-8')))
    group_rows=list(csv.DictReader((ROOT/'06_LOAD_DEL_M4_GROUP_SUMMARY.csv').open(encoding='utf-8')))
    qa_rows=list(csv.DictReader((ROOT/'02_CHANNEL_MAPPING_QA_RAINFLOW.csv').open(encoding='utf-8')))
    gates={
      'FORMAL_36CASE_INPUT_MATRIX': len(cases)==expected_cases,
      'FORMAL_DAMPING_ACTUAL_READBACK': len(damp_rows)==36 and all(r['status']=='PASS' for r in damp_rows),
      'OUTB_700S_DT0.05_AUDIT': len(outb_rows)==36 and all(r['status']=='PASS' for r in outb_rows),
      'CHANNEL_INDEX_CORRECTION_QA': len(qa_rows)==33 and all(r['status']=='PASS' for r in qa_rows),
      'RAINFLOW_CYCLE_LEDGER': len(del_rows)==72 and Path(ROOT/'03_RAINFLOW_CYCLE_LEDGER.csv').stat().st_size>0,
      'DEL_M4_ALL36': len(del_rows)==72,
      'DEL_GROUPS_3X2X2': len(group_rows)==12 and all(int(r['n_seeds'])==6 for r in group_rows),
      'GOODMAN_CORRECTION': False,
      'TURBSIM_RERUN': False,
      'OPENFAST_RERUN': False,
    }
    with (ROOT/'01_GATE_REPORT.md').open('w',encoding='utf-8') as f:
        f.write('# Rainflow + Load-DEL 正式审计门禁\n\n')
        f.write(f'生成时间：{datetime.now().isoformat(timespec="seconds")}\n\n')
        f.write('输入为已完成的正式对象化阻尼 36 个 OpenFAST `.outb`；本轮不重跑 OpenFAST，也不重跑 TurbSim。\n\n')
        f.write('| Gate | Status |\n|---|---|\n')
        for k,v in gates.items(): f.write(f'| `{k}` | **{"PASS" if v else ("NOT APPLIED" if k in ("GOODMAN_CORRECTION","TURBSIM_RERUN","OPENFAST_RERUN") else "FAIL")}** |\n')
        f.write('\n## 固定口径\n\n- 统计窗口：100–700 s（600 s）；输出步长：0.05 s。\n- Rainflow：ASTM E1049-85(2017) 风格 stack 计数；循环记录含 range、amplitude、mean、count（0.5/1.0）。\n- 正式载荷通道：`TwrBsMxt`、`TwrBsMyt`。\n- 载荷 DEL：钢塔比较口径 `m=4`，`Neq=100000`；未做 Goodman 均值修正。\n- 该 DEL 是载荷比较指标，不是混凝土/钢材疲劳寿命；材料寿命需另行采用 S–N、Miner 和材料应力。\n\n')
        if errors: f.write('## Errors\n\n' + '\n'.join(f'- {e}' for e in errors) + '\n')
    with (ROOT/'11_METHOD_AND_EVIDENCE.md').open('w',encoding='utf-8') as f:
        f.write('# Rainflow + Load-DEL 方法与证据\n\n')
        f.write('## 数据来源\n\n')
        f.write('36 个正式对象化塔架阻尼 OpenFAST 工况的 `.outb`，对应三组 URef、NTM/ETM 和 S01–S06。原始 `.bts` 风场复用，不在本轮重跑。\n\n')
        f.write('## 通道与索引\n\n')
        f.write('`.outb` 头部 `names[0]` 为 `Time`，数据列采用 `names.index(channel)-1`；本轮脚本统一使用该修正映射，并提供 3 个代表工况、33 个通道映射 QA 记录。\n\n')
        f.write('## 计算\n\n')
        f.write('对 100–700 s 信号做 ASTM 风格雨流计数，保存循环账本和范围直方图。载荷 DEL 使用 `DEL=(sum(count*range^m)/Neq)^(1/m)`，其中钢塔比较斜率 `m=4`、`Neq=1e5`，不做 Goodman 修正。\n\n')
        f.write('## 解释边界\n\n')
        f.write('`m=4` 仅用于 STEEL-TOWER LOAD-DEL COMPARISON。结果不能直接表述为材料疲劳寿命，也不能外推 20 年寿命。\n\n')
        f.write('## 参考依据\n\n')
        f.write('- ASTM E1049-85(2017), *Standard Practices for Cycle Counting in Fatigue Analysis*, https://www.astm.org/e1049-85r17.html\n')
        f.write('- Guma et al. (2021), *Wind Energy Science*, 6, 93–110, https://doi.org/10.5194/wes-6-93-2021\n\n')
        f.write('## 输出文件\n\n')
        f.write('`01_GATE_REPORT.md`, `02_CHANNEL_MAPPING_QA_RAINFLOW.csv`, `03_RAINFLOW_CYCLE_LEDGER.csv`, `04_RAINFLOW_RANGE_HISTOGRAM.csv`, `05_LOAD_DEL_M4_ALL36.csv`, `06_LOAD_DEL_M4_GROUP_SUMMARY.csv`, `07_DEL_CONTROL_RANKING.csv`, `08_CONTROLLER_RESPONSE_CORRECTED.csv`, `09_NTM_ETM_DEL_COMPARISON.csv`。\n')
    files=[]
    for p in sorted(ROOT.iterdir()):
        if p.is_file() and p.name != '10_SHA256_MANIFEST.csv' and not p.name.endswith('.zip'):
            files.append({'file':p.name,'bytes':p.stat().st_size,'sha256':sha256(p)})
    with (ROOT/'10_SHA256_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['file','bytes','sha256']); w.writeheader(); w.writerows(files)
    print('gates', sum(bool(x) for x in gates.values()), '/', len(gates), 'damping', len(damp_rows), 'outb', len(outb_rows))
    print('zip-ready files', len(files))

if __name__ == '__main__': main()
