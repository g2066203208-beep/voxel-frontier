from pathlib import Path
from datetime import datetime,timezone
from zipfile import ZipFile,ZIP_DEFLATED
import csv,hashlib,json,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'outputs'
RUNROOT=Path('D:/Codex-research-validation/T038S1')
OUT.mkdir(exist_ok=True)
result=json.loads((ROOT/'verification-results.json').read_text(encoding='utf-8'))
assert result['all_required_checks_pass']
cards=json.loads((ROOT/'run-cards.json').read_text(encoding='utf-8'))
trials=[]
for case,dt in [('MOTION',.001),('MOTION_H2',.0005),('MOTION_H40',.000025)]:
    item=json.loads((ROOT/('verification-'+case+'.json')).read_text(encoding='utf-8'))
    r=item['motion']
    trials.append({'job':'RNA_R2_'+case,'dt_s':dt,'samples':r['samples'],'max_abs_error_J':max(r['matrix_route_max_abs_error_J'],r['CG_route_max_abs_error_J']),'relative_error':max(r['matrix_route_relative_to_peak'],r['CG_route_relative_to_peak']),'pass':r['pass']})
for c in cards:
    folder=Path(c['directory'])
    if c['job'] in ['RNA_R2_MATRIX','RNA_R2_GRAVITY','RNA_R2_MOTION_H40']:
        c['status']='numerical-verification-pass/scope-limited'
    else:c['status']='solver-completed/kinetic-budget-not-met'
    final_note=' Final acceptance: see verification-results and preserved timestep trials; D08 remains OPEN.'
    if final_note not in c['notes']:c['notes']+=final_note
    (folder/'ResearchCard.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'run-cards.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')

# Standalone scientific figure based solely on this task's actual results.
font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams['font.family']=font.get_name()
plt.rcParams['axes.unicode_minus']=False
data=np.genfromtxt(ROOT/'kinetic-energy-MOTION_H40.csv',delimiter=',',names=True)
fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
ax=axes[0]
ax.plot(data['time_s'],data['target_from_O_velocity_J'],color='#243b53',lw=1.8,label='由输出速度和目标惯量计算')
ax.plot(data['time_s'][::8],data['solver_ALLKE_J'][::8],'o',mfc='none',mec='#b45309',ms=5,label='Abaqus ALLKE（细步）')
ax.set(xlabel='时间 / s',ylabel='动能 / J',title='规定混合运动：101个共同输出时刻')
ax.legend(fontsize=8,frameon=False);ax.grid(alpha=.2)
ax=axes[1]
xs=[t['dt_s'] for t in trials];ys=[t['relative_error'] for t in trials]
ax.loglog(xs,ys,'o-',color='#0f766e',lw=1.5,label='实际最大动能差 / 峰值')
ax.loglog(xs,[ys[0]*(x/xs[0])**2 for x in xs],'--',color='#64748b',lw=1,label='二阶趋势参考')
ax.axhline(1e-6,color='#b91c1c',ls=':',label=r'求解前预算 $10^{-6}$')
for x,y,label in zip(xs,ys,['初始：未达标','半步：未达标','细步：通过']):
    ax.annotate(label,(x,y),xytext=(-5 if x==xs[0] else 5,7),ha='right' if x==xs[0] else 'left',textcoords='offset points',fontsize=8)
ax.set(xlabel='积分步长 / s',ylabel='归一动能偏差',title='目标和预算固定，仅细化时间步')
ax.set_xlim(1.6e-5,2e-3);ax.set_ylim(1e-7,2e-3)
ax.legend(fontsize=8,frameon=False,loc='lower right');ax.grid(which='both',alpha=.2)
fig.suptitle('RNA独立数值小样：质量表示的动能检查',fontsize=14)
figure=ROOT/'rna-kinetic-energy-verification.png'
fig.savefig(figure,dpi=180);fig.savefig(ROOT/'rna-kinetic-energy-verification.pdf');plt.close(fig)

# Explicit erratum; frozen T038 target and original source records remain traceable.
source=json.loads((ROOT/'source-identity-review.json').read_text(encoding='utf-8'))
erratum={'field':'openfast-rna-current.json.archive_summary.blade_mass_kg','old_value_kg':2600752.25,'corrected_archived_printed_blade_mass_kg':41732.34,'source':'Actual R2 ED.sum: blade mass line53; old field incorrectly matched Mass Incl. Platform line64','cause':'Over-broad substring match in historical extract_openfast_rna.py','impact':'Does not enter reconstructed target m/CG/J; independent mass-point rebuild confirms target unchanged','source_review_sha256':hashlib.sha256((ROOT/'source-identity-review.json').read_bytes()).hexdigest(),'resolution':'Explicit source-metadata erratum; do not use old blade_mass summary field. Frozen original source/target hashes remain unchanged.'}
(ROOT/'source-summary-erratum.json').write_text(json.dumps(erratum,ensure_ascii=False,indent=2),encoding='utf-8')

# Store raw solver outputs in small lossless archives, with exact-byte manifests.
bundle_dir=ROOT/'raw-bundles';bundle_dir.mkdir(exist_ok=True)
bundle_manifest=[]
for card in cards:
    folder=Path(card['directory'])
    allowed={'.inp','.dat','.msg','.sta','.odb','.mtx','.sim'}
    names={'execution.log','execution-start.json','execution-record.json','ResearchCard.json','odb-extract.json'}
    chosen=[p for p in sorted(folder.iterdir()) if p.is_file() and (p.suffix.lower() in allowed or p.name in names)]
    manifest=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in chosen]
    archive=bundle_dir/(card['job']+'.zip')
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for p in chosen:z.write(p,p.name)
        z.writestr('RAW_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with ZipFile(archive) as z:
        assert z.testzip() is None
        for entry in manifest:assert hashlib.sha256(z.read(entry['name'])).hexdigest()==entry['sha256']
    bundle_manifest.append({'job':card['job'],'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'members':manifest})
(ROOT/'raw-bundle-manifest.json').write_text(json.dumps(bundle_manifest,ensure_ascii=False,indent=2),encoding='utf-8')

trial_table='\n'.join('|'+f"{t['dt_s']:.7g}|{t['samples']}|{t['max_abs_error_J']:.9g}|{t['relative_error']:.9g}|"+('通过' if t['pass'] else '未达原预算')+'|' for t in trials)
max_matrix=max(r['relative_to_block_scale'] for r in result['matrix_blocks'])
max_gravity=max(r['relative_to_nonzero_scale'] for r in result['gravity'])
final_energy=trials[-1]['relative_error']
report=f'''# RNA独立小样验证：结果、真实依据与适用范围

日期：2026-10-05。任务：T038-S1。**本步独立数值验证完成；整塔/运行RNA适用性尚未据此通过。**

## 1. 实际完成了什么

在用户本机Abaqus/Standard 2025执行5次独立求解：质量矩阵、固定参考点重力、原步长规定运动、半步长规定运动及细步长规定运动。5次均正常完成，原始MSG均报告0输入警告、0分析警告、0错误。

三类最终核验均满足求解前登记的数值预算。初始及半步规定运动虽正常完成，但动能未达到预算；这两次作为未达标结果保留，没有删除，也没有放宽容差或调整质量/惯量来使结果通过。

本步没有修改M2整塔，没有运行OpenFAST风况，没有开展材料疲劳寿命计算。原M2输入SHA仍为`{result['source_M2_unchanged_sha256']}`。

## 2. 真实参考方法，以及本研究自己的部分

**Cheng Y.等（2024），Structures 68，107235，DOI：[10.1016/j.istruc.2024.107235](https://doi.org/10.1016/j.istruc.2024.107235)。** 本轮实际核读PDF第3–9页相关内容并核图。第6–7页§4.1及图5采用机舱、转子两个参考点，分别设置集中质量和转动惯量，并刚性运动学耦合到塔顶；第7页§5.1与第9页图7/表4比较PM、EPM、EPMJ和EDPMJ。当前单偏心集中质量加惯量的表示概念上接近EPMJ。

该论文不提供本机组的数值、不披露MASS/ROTARYI关键词，文中未报告本小样所用的完整6×6质量矩阵提取、重力与动能核验流程。不能说本步是对该文算例的复现。

该文PDF在仓库参考文献目录中存在，已核对当前快照的路径、大小和Git对象，记录见`reference-github-presence.json`。本轮方法核读使用另一本地PDF副本，来源SHA256见`literature-method-source-public.json`；两个副本字节数不同，不声称逐字节相同。

**Abaqus官方方法**提供质心节点MASS、六分量ROTARYI、六自由度KINEMATIC耦合、MATRIX GENERATE/MPC=YES、GRAV、RF/RM/V/VR/ALLKE以及隐式积分/幅值曲线的确切定义。逐项章节和链接见`method-source-review.md`。目标RNA参数来自已逐字节复核的R2归档与T038输入重建；刚体质量矩阵、平行轴和动能等价由本项目解析推导并交叉核验。

1e-9的矩阵预算、1e-6的反力/动能预算属于求解前公开登记的数值实施预算。它们不是论文数值、规范限值或实际机组的工程误差门槛。详细来源范围见`literature-method-source-public.md`和`RESEARCH_CARD.md`。

## 3. 小样对象

- 总质量：676753.2907231401 kg。
- 公共塔顶O：(0,158,0) m，Abaqus +Y竖直。
- 整体质心G：约(0,160.78358803030605,−0.8729624988915398) m。
- 在G赋MASS和完整质心惯量，通过六自由度运动学耦合连接O；使用原始惯量张量非对角符号。
- 目标状态：未变形、内部相对运动锁定的R2独立float64重建。它不是原OpenFAST求解器直接导出的完整高精度矩阵，也不代表叶片柔性、旋转和气弹响应。

R2原ED.sum质量与本次float64目标仍差0.040723140119 kg；本次没有消除或掩盖这个既有来源差异。

## 4. 实际结果

|检查|实际差异|预登记预算|结果|
|---|---:|---:|---|
|质量矩阵：平移、偏心耦合、转动分别按同量纲块比较|最大归一误差{max_matrix:.4g}|1e-9|通过|
|从求解器矩阵反求m/CG/JG|质量和CG在记录精度内一致；JG归一误差3.8232e-16|质量/JG 1e-9；CG 1e-8 m|通过|
|重力支座合力与O点反力矩|最大归一误差{max_gravity:.4g}|1e-6|通过|
|细步规定运动ALLKE，两条解析路线|最大归一误差{final_energy:.4g}|1e-6|通过|

重力试验给定a=(0,−9.81,0) m/s²；支座RF2实际6638950.0 N、目标6638949.781994005 N；RM1实际5795554.0 N·m、目标5795554.191704930 N·m。差值与ODB单精度输出分辨率一致，偏心反力矩方向正确。

矩阵文件实际只含O点1–6六个独立自由度，15个非零下三角项；按显式节点/自由度标签恢复对称矩阵，没有把重复对称项加倍。

## 5. 动能未达标如何处理

|积分步长/s|输出样本|两条路线最大绝对动能差/J|按峰值归一差异|判定|
|---:|---:|---:|---:|---|
{trial_table}

两条路线分别使用O点实际输出速度与目标M6、G点实际输出平动/转动速度与m/JG。初始与半步误差约呈四分之一关系；细步在101个共同输出时刻满足原预算。细步实际执行4000个增量，场/历史每40增量保存一次，不能把这101点结论宣称为逐增量全部输出检查。

规定运动的输出速度与Newmark增量更新速度存在可诊断的离散差异。官方隐式动力学理论及实际原步/半步诊断支持这一解释；本步保留原V/VR—ALLKE验收定义，并用细步实际结果达到预算，没有通过改换定义掩盖原失败。该检查是规定运动下的质量/耦合/动能核验，不是整塔自由振动或运行风况的时间步收敛试验。

![动能与步长检查](rna-kinetic-energy-verification.png)

## 6. 发现并保留的其他问题

- 旧`openfast-rna-current.json`单叶质量摘要字段误匹配了ED.sum整机总质量；正确单叶打印值为41732.340 kg。目标m/CG/J由真实分布与组件字段组装，不使用该错误字段。独立组件重组再次确认目标不受影响；`source-summary-erratum.json`明确勘误，原始指纹保留。
- 首次两次ODB抽取因float32不能直接JSON序列化失败；已显式转换数值类型后重新读取同一ODB。没有重跑求解或修改输入。失败脚本和错误记录保留。

## 7. 对下一步的实际意义

在本小样设定与登记的数值预算内，本步结果证明：指定的R2冻结RNA质量算子能够在Abaqus中用集中质量、完整惯量及偏心耦合正确表达。它为后续选择整塔RNA表示提供了可复算的数值证据。

接入整塔之前仍需审定载荷自由体：若Abaqus承受已包含RNA重力/惯性的完整塔顶截面内力，就不能再重复计入同一RNA作用。真实柔性/旋转/气弹影响、当前整塔阻尼、载荷映射和疲劳输入仍各有独立验证任务；BASE001、D08及疲劳寿命状态不自动升级。

## 8. 文件与复现

- 原始求解目录：`D:/Codex-research-validation/T038S1/`。
- 每个作业原INP、DAT、MSG、STA、ODB、矩阵及执行记录以无损ZIP归档；`raw-bundle-manifest.json`登记逐文件SHA256。
- `build_sample.py`生成最初三输入；`register_refinement.py`生成有记录的时间步对照；`run_sample.py`记录本机执行；`extract_odb.py`读取实际ODB；`verify_sample.py`复算全部比较；`assemble_delivery.py`生成图表与交付。
- `source-identity-review`、两份独立结果审查和方法来源记录保留每项依据与适用范围。文献原PDF页面、论文正文和导师材料未进入本公开包。
- 环境：求解与ODB抽取使用Abaqus/Standard 2025及其自带Python；数值后处理使用Python和NumPy；本报告绘图实际使用Python 3.13、NumPy 2.2.5、Matplotlib 3.10.3及Windows微软雅黑字体。发布脚本另需已认证GitHub CLI。
- 脚本保留本轮实际Windows路径，下载后不是开箱即用的跨平台软件包。仅复查已有结果时，可将ZIP分别解压至对应作业目录并读取JSON/CSV；重新求解应复制到新的工作目录，避免覆盖原始记录。`build_sample.py`还依赖T038的`comparison-results/rna-comparison.json`；动能诊断脚本保留原`work/step3-rna-20261005`位置假设，异机复现需调整路径。
'''
(ROOT/'RESULTS.md').write_text(report,encoding='utf-8')
local_report=OUT/'RNA独立小样验证_结果与依据_20261005.md'
local_report.write_text(report.replace('(rna-kinetic-energy-verification.png)','('+str(figure).replace('\\','/')+')'),encoding='utf-8')

mapping={}
names=['RESULTS.md','RESEARCH_CARD.md','frozen-target.json','run-cards.json','build_sample.py','run_sample.py','extract_odb.py','extract_odb-v1-failed.py','verify_sample.py','register_refinement.py','assemble_delivery.py','source-identity-review.json','source-identity-review.md','literature-method-source-public.json','literature-method-source-public.md','source-summary-erratum.json','postprocess-failures.json','verification-results.json','solver-M6-at-O.csv','raw-bundle-manifest.json','rna-kinetic-energy-verification.png','rna-kinetic-energy-verification.pdf','independent-result-review.json','independent-result-review.md','independent-initial-motion-energy.csv','independent-final-result-review.json','independent-final-result-review.md','independent-H40-energy.csv','refinement-H2-preregistered.json','refinement-H40-preregistered.json']
for name in names:
    if (ROOT/name).exists():mapping[name]=str(ROOT/name)
mapping['reference-github-presence.json']=str(ROOT/'reference-github-presence.json')
for case in ['MOTION','MOTION_H2','MOTION_H40']:
    for name in ['verification-'+case+'.json','kinetic-energy-'+case+'.csv']:mapping[name]=str(ROOT/name)
for p in bundle_dir.glob('*.zip'):mapping['raw-bundles/'+p.name]=str(p)
for source_name,dest_name in [('prepared-fixture-method-source-review.md','method-source-review.md'),('prescribed-motion-ke-diagnostic-review.md','prescribed-motion-ke-diagnostic-review.md'),('diagnose_prescribed_motion_ke.py','diagnose_prescribed_motion_ke.py'),('prescribed-motion-ke-diagnostic.json','prescribed-motion-ke-diagnostic.json'),('prescribed-motion-ke-diagnostic-RNA_R2_MOTION_H2.json','prescribed-motion-ke-diagnostic-RNA_R2_MOTION_H2.json'),('prescribed-motion-ke-diagnostic-RNA_R2_MOTION_H40.json','prescribed-motion-ke-diagnostic-RNA_R2_MOTION_H40.json')]:
    p=ROOT.parent/'step3-rna-20261005'/source_name
    if p.exists():mapping[dest_name]=str(p)
(ROOT/'finish-map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
delivery={'generated_utc':datetime.now(timezone.utc).isoformat(),'local_report':str(local_report),'solver_jobs':len(cards),'raw_archives':[{'name':r['archive'],'bytes':r['bytes']} for r in bundle_manifest],'figure':str(figure),'all_required_checks_pass':True,'motion_trials':trials,'published_files_planned':len(mapping)}
(ROOT/'delivery-manifest.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(delivery,ensure_ascii=False,indent=2))
