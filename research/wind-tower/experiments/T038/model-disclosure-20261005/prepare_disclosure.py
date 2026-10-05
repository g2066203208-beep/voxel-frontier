"""Prepare the audit deliverables and source-file identity; no model edits."""
from pathlib import Path
import csv, hashlib, json

ROOT=Path(__file__).resolve().parent
PREFIX='research/wind-tower/'
SOURCE=Path('D:/MC/cae仿真/大型混塔式风力机的建模与可靠度分析_何泽瑜.pdf')
DEST=PREFIX+'references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf'
raw=SOURCE.read_bytes();digest=hashlib.sha256(raw).hexdigest()
assert digest=='85fb7d2e35a039e38e4b442deadab6ce7ddbf8bf0e57885de0238d92113f511c'
assert len(raw)==10193750 and raw.startswith(b'%PDF-')
refs={
 'He2024':{'ref_id':'REF008','title':'大型混塔式风力机的建模与可靠度分析','author':'何泽瑜','year':2024,'institution':'湖南大学',
  'local_source':str(SOURCE),'repository_path':DEST,'bytes':len(raw),'sha256':digest,'pages':90,
  'reading_this_audit':'PDF33–35；全篇页数与原件身份由本轮来源审查确认，不新增全90页科学审读声明',
  'prior_repository_state':'Current tree, references manifests and literature_master said binary pending; no same-source hash found in archive manifest.',
  'publication':'Exact complete user-provided reference PDF included in this publication; completion requires the publisher byte-readback receipt. This is a reference thesis, not the user manuscript.'},
 'DTU2013':{'title':'Description of the DTU 10 MW Reference Wind Turbine','source':'Report-I-0092',
  'repository_path':PREFIX+'references/baselines-and-site-20261004/dtu-report/DTU_Wind_Energy_Report-I-0092.pdf',
  'storage':'Git LFS','sha256':'55aac8cae8f656cdc4aa73afd3f5dedc45345079168476289eb49f000efd8017','bytes':10815847,
  'new_reading':'Local PDF65,67 by provenance reviewer; actual remote LFS PDF header probe in reference-lfs-accessibility.json.'},
 'Xu2025':{'title':'Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach',
  'doi':'10.1016/j.renene.2025.122475','repository_path':PREFIX+'references/user-provided/Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach.pdf',
  'scope':'Existing T037 PDF3–4 source audit used as background; no new whole-paper review this task.'},
 'Cheng2024':{'title':'Intelligent analysis of dynamic characteristics of steel-concrete hybrid wind turbine tower based on adaptive vibration mode',
  'doi':'10.1016/j.istruc.2024.107235','repository_path':PREFIX+'references/user-provided/Intelligent analysis of dynamic characteristics of steel-concrete hybrid wind turbine tower based on adaptive vibration mode.pdf',
  'scope':'T038-S1 actual PDF3–9 method reading, with separately identified local-copy SHA; no byte-equivalence claim between that copy and repository copy.'},
 'Abaqus':{'record':PREFIX+'experiments/T038/validation-sample-20261005/method-source-review.md',
  'scope':'Previously directly checked official keyword/output definitions; not evidence of physical parameter calibration.'}}
(ROOT/'reference-sources.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2),encoding='utf-8')
rows=[
 ['MD01','塔身来源','用户历史INP→G1→M2/M3；CSEG01原生几何局部重建','来源确认','model-provenance-review.md','实际文件及Part文本传承','非DTU官方158m整塔；中间CAE变化原因未明'],
 ['MD02','混凝土塔身','31段/112m；C3D8R 13392','已建模/全局验证有限','mesh-geometry-review.md','几何、网格、既有基态模态柔度','局部损伤/疲劳/网格客观性未验'],
 ['MD03','钢塔身','4段/46m；C3D8I 1728','已建模/警告保留','mesh-geometry-review.md','几何及既有全局网格对照','1512元素长宽比>100；局部应力未验'],
 ['MD04','普通纵筋','31组5440个T3D2；约25mm；S345','已建模/构造依据未全闭合','reinforcement-material-contact-review.md','面积、材料分配和Embedded','直径/牌号适用性、跨段连续性待审'],
 ['MD05','环向筋/箍筋','未发现显式有效钢筋网定义','未实现','mesh-geometry-review.md','完整输入关键词与构件检查','非结构质量不能代替其刚度'],
 ['MD06','钢筋混凝土关系','31组Embedded全粘结','等效约束','reinforcement-material-contact-review.md','实际卡片和宿主','没有粘结滑移/拔出'],
 ['MD07','预应力筋','36×140mm²；每根一个112m T3D2','已建模/简化','reinforcement-material-contact-review.md','初应力及端部边界','无孔道接触/中间导向/筋材塑性；36根依据待核'],
 ['MD08','PT锚固/损失','底固定、顶部108方程、1280MPa初应力','等效实现','reinforcement-material-contact-review.md','平衡后S11已有记录','无锚具实体、锚固滑移、长期损失全过程'],
 ['MD09','混凝土本构','C70两段+C65其余；CDP黏性1e-5','已赋值/物理适用域待验','reinforcement-material-contact-review.md','完整曲线和截面引用','材料实测、多轴标定、软化/断裂能待闭合'],
 ['MD10','钢与纵筋本构','S345；E200GPa；345/365/420MPa','已赋值/来源差异保留','reinforcement-material-contact-review.md','输入塑性卡','不能混写HRB335/HRB500或E206GPa'],
 ['MD11','混凝土接缝','30道×6自由度SPRING2=180','等效线性连接','reinforcement-material-contact-review.md','逐接缝K与RP连接','无开闭/摩擦；刚度标定未闭合'],
 ['MD12','钢混与钢段连接','1+3处Tie','等效绑定','reinforcement-material-contact-review.md','四对表面与ADJUST','无法兰/螺栓/焊缝实体及接触'],
 ['MD13','物理接触','无Contact/Contact Pair/Surface Interaction/Friction','未实现','reinforcement-material-contact-review.md','整份无Include输入检查','不可报告CPRESS/COPEN/滑移或脱开'],
 ['MD14','RNA整塔当前实现','28B31整体Rigid Body；673998.493138kg','刚体质量分布','model-provenance-review.md','实际输入与既有整塔求解','非柔性旋转气弹模型'],
 ['MD15','新RNA数值小样','MASS+ROTARYI；676753.290723kg；无塔','三类数值核验通过','../validation-sample-20261005/RESULTS.md','真实5次求解含2次预算失败','尚未写回M2；不能关闭D08'],
 ['MD16','基础与支承','混凝土底ENCASTRE+PT底3平移固定','固定边界','reinforcement-material-contact-review.md','实际边界行','无基础/土体/SSI模型'],
 ['MD17','非结构质量','4622.69+33004.8+2172.73=39800.22kg','已赋值/分项来源待核','reinforcement-material-contact-review.md','三项NSM实际输入','不能补足缺失构件刚度或重复计入RNA'],
 ['MD18','既有M2求解','重力、30阶模态、双向1kN线性扰动','实际已执行/范围有限','historical-run-evidence-summary.json','原INP/DAT/ODB哈希一致','未据此完成生产时程、开裂、承载力和疲劳'],
 ['MD19','网格验证','G1/M2/M3已有低阶频率与全局柔度对照','部分指标通过','historical-run-evidence-summary.json','M2→M3原0.5%预算','不是局部应力/疲劳/峰后收敛'],
 ['MD20','OpenFAST R2','第三方移植+158m研究塔卡；历史36case','归档/历史结果可追溯','model-provenance-review.md','前次归档逐字节核对','本步未重跑/未恢复完整入口；新RNA未与之整塔统一'],
 ['MD21','疲劳输入与寿命','本步未新建生产疲劳计算','未完成本步验证','README.md','当前四步骤不含生产时程','不能用材料卡/模态结果替代应力时程及疲劳方法验收'],
 ['MD22','来源原文补齐','REF008何泽瑜完整90页PDF','本次入库并要求字节回读','reference-sources.json','原件SHA256与既有阅读来源相同','只补源文件；不改变几何语义冲突及参数待核状态'],
 ['MD23','M2结构阻尼','无DAMPING/MODAL DAMPING/DYNAMIC卡；仅静力与频率步骤','本输入未实施生产动力阻尼','README.md','完整INP关键词逐行核查','CDP黏性不等于结构阻尼，不能直接移用OpenFAST阻尼']]
with (ROOT/'model-component-register.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['item_id','component','actual_implementation','status','evidence','completed_evidence','open_limits']);w.writerows(rows)
print(json.dumps({'components':len(rows),'reference_id':'REF008','pdf_bytes':len(raw),'pdf_sha256':digest},ensure_ascii=False))
