"""Read-only audit of the frozen M2 INP/DAT; writes only this report directory.

Run with Python 3; only the standard library is required. No solver is called.
Line references are one-based in the exact SHA-256 identified source files.
"""
from __future__ import annotations

import collections
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INP = Path('D:/Codex-research-validation/T026/tower/DTU158_RECONSTRUCTED_M2/DTU158_RECONSTRUCTED_M2.inp')
DAT = INP.with_suffix('.dat')
G1 = INP.parent.parent / 'DTU158_RECONSTRUCTED_G1/DTU158_RECONSTRUCTED_G1.inp'
EXPECTED_INP_SHA256='428a8bb567a52200311ebb1a2019a71c304d1c427ce761f0c836e4fc46fe50f1'


def read_blocks(path):
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    blocks = []
    for number, raw in enumerate(lines, 1):
        text = raw.strip()
        if not text or text.startswith('**'):
            continue
        if text.startswith('*'):
            fields = [s.strip() for s in text.split(',')]
            block = dict(keyword=fields[0][1:].upper(), line=number, raw=raw,
                         options={}, flags=[], data=[], data_lines=[], raw_data=[])
            for field in fields[1:]:
                if '=' in field:
                    key, value = field.split('=', 1)
                    block['options'][key.strip().upper()] = value.strip()
                elif field:
                    block['flags'].append(field.upper())
            blocks.append(block)
        else:
            blocks[-1]['data'].append([v.strip() for v in text.split(',') if v.strip()])
            blocks[-1]['data_lines'].append(number)
            blocks[-1]['raw_data'].append(raw)
    return lines, blocks


def annotate(blocks):
    part = material = step = None
    assembly = False
    for block in blocks:
        key, opt = block['keyword'], block['options']
        if key == 'PART': part = opt['NAME']
        if key == 'ASSEMBLY': assembly = True
        if key == 'MATERIAL': material = opt['NAME']
        if key in ('BOUNDARY', 'INITIAL CONDITIONS', 'STEP'): material = None
        if key == 'STEP': step = opt['NAME']
        block.update(part=part, material=material, step=step, assembly=assembly)
        if key == 'END PART': part = None
        if key == 'END ASSEMBLY': assembly = False
        if key == 'END STEP': step = None


def vals(block):
    return [[float(v) for v in row] for row in block['data']]


def labels(block):
    if 'GENERATE' in block['flags']:
        return [i for row in block['data'] for i in range(int(row[0]), int(row[1])+1, int(row[2]) if len(row)>2 else 1)]
    return [int(v) if v.isdigit() else v for row in block['data'] for v in row]


def source(path):
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), lines=len(raw.splitlines()))


def part_geometry(blocks, name):
    selected = [b for b in blocks if b['part'] == name]
    nodes, elements = {}, []
    for b in selected:
        if b['keyword'] == 'NODE':
            for line, row in zip(b['data_lines'], b['data']):
                nodes[int(row[0])] = dict(xyz=[float(x) for x in row[1:4]], line=line)
        if b['keyword'] == 'ELEMENT':
            elements.extend(dict(id=int(row[0]), nodes=[int(x) for x in row[1:]],
                                 type=b['options']['TYPE'], line=line)
                            for line, row in zip(b['data_lines'], b['data']))
    return selected, nodes, elements


def ring_stats(points):
    # Coordinate output is rounded to about 1e-7 m. Cluster radii at 1e-5 m.
    groups = collections.defaultdict(list)
    for point in points:
        groups[round(math.hypot(point[0], point[2]), 5)].append(point)
    return [dict(radius_m=r, node_count=len(p),
                 unique_positions_at_1e_5_m=len({tuple(round(x, 5) for x in v) for v in p}))
            for r, p in sorted(groups.items())]


def write_markdown(r):
    rows=[]
    def add(s=''):rows.append(s)
    def table(headers, data):
        add('| '+' | '.join(headers)+' |')
        add('| '+' | '.join('---' for _ in headers)+' |')
        for row in data:add('| '+' | '.join(str(v) for v in row)+' |')
        add()
    def card(m,key):return next(c for c in m['cards'] if c['keyword']==key)
    def g(value):return f'{value:.8g}'
    add('# 当前 M2 的配筋、材料、连接与分析范围：输入文件直接核验')
    add()
    add('本报告逐条解析当前 `DTU158_RECONSTRUCTED_M2.inp` 和同名 `.dat`；本轮没有运行求解器、修改模型或使用旧报告替代源文件核验。以下 `L` 均为本节所列 SHA-256 对应文件的一基行号。数值采用模型约定的 SI 制（m、kg、s、N、Pa）；Abaqus 本身不内置单位转换。')
    add()
    table(['源文件','SHA-256','行数'],[(s['path'],s['sha256'],s['lines']) for s in r['sources'].values()])
    add('可复核解析器：`parse_material_contacts.py`，只用 Python 标准库。可传 `--inp`、`--dat`、`--g1`、`--output-dir` 指定本地路径；脚本核对当前 M2 的冻结 SHA-256，拒绝套用固定文字到另一个输入。机器可读全表：`reinforcement-material-contact-review.json`，保留关键字原文、逐行数据、行号、实例平移及参数表。')
    add()
    add('## 必须如实披露的结论')
    add()
    add('- 这是当前重构分支 M2 的具体定义。源文件证明的“实际已设置”与材料试验、公开基准或真实工程的“已经验证”不是同一件事。当前材料和接头参数不能仅凭名称归为 DTU 官方设计。')
    add('- 31 段普通纵筋共 5440 个 T3D2，全部使用 S345；存在但未被截面引用的 HRB500_BASELINE 卡不能作为“已配置 HRB500 钢筋”的依据。')
    add('- 每段纵筋为两圈离散长杆，分别 Embedded 到该段混凝土。段间没有直接钢筋拼接、套筒、焊接或黏结滑移定义；通过混凝土端面运动学耦合和接口弹簧传力。')
    add('- 36 根预应力筋各只有一个 112 m 长 T3D2，截面 140 mm²，底部平动固定、顶部方程锚固，初应力 1280 MPa。没有沿程 Embedded、孔道接触、摩擦、张拉施工过程或预应力损失模型。')
    add('- 混凝土定义了 CDP；30 个混凝土接口使用线性 SPRING2，4 个钢段/过渡接口使用 Tie。没有接触开闭、摩擦滑移、接缝压碎或螺栓松脱的显式机制。')
    add('- 当前 4 个步骤仅为重力平衡、重力基态上的 30 阶模态和两个 1 kN 线性扰动柔度工况；没有风时程动力、疲劳或倒塌承载力工况。')
    add('- DAT 显示分析完成，同时报告 12 条警告，包括 1512 个单元长宽比大于 100；不能披露为“零警告”或据此宣布模型完美。')
    add()
    add('## 材料卡与实际引用')
    add()
    data=[]
    for m in r['materials']:
        den=card(m,'DENSITY');elas=card(m,'ELASTIC')
        use=m['assignments']
        if m['name']=='C65':where='CSEG_03–31（29 段）'
        elif m['name']=='C70':where='CSEG_01–02（2 段）'
        elif m['name']=='S345':where='RBLONG_01–31 + SSEG_01–04（35 个截面）'
        elif m['name']=='STRAND_1860':where='PT_36x15p2（1 个截面）'
        elif not use:where='无截面引用，未启用'
        else:where='RNA_MASS_SKELETON_OFFICIAL 的 1 个 B31 分组'
        data.append((m['name'],f'L{m["line"]}',den['data'][0][0],elas['data'][0][0],elas['data'][0][1],where))
    table(['材料','材料卡','ρ / kg·m⁻³','E / Pa','ν','实际用途'],data)
    add('C70 的截面引用为 L1391、L2715；C65 从 L4039 到 L41111 的 29 个混凝土截面；钢筒 S345 截面为 L59148、L60364、L61580、L62796。各纵筋截面及行号见下表。')
    add()
    table(['材料','塑性卡','输入的（应力 Pa，塑性应变）','含义与限制'],[
        ('S345','L68722','(345000000, 0); (365000000, 0.002); (420000000, 0.02)','同时用于钢筒和普通纵筋；无显式损伤/断裂演化卡'),
        ('HRB500_BASELINE','L68679','(500000000, 0); (550000000, 0.02)','卡存在但无截面引用，不参加当前模型响应'),
        ('STRAND_1860','无','仅 ρ=7850，E=1.95e11，ν=0.3','名称中的 1860 未实现为屈服、极限强度或断裂本构')])
    add('RNA 的七种高密度材料是分布质量载体。L68579 将全部 RNA 梁声明为刚体；这些弹性常数和人为密度不代表真实叶片复合材料、机舱壳体或弹性叶片动力学。')
    add()
    add('### C65/C70 的完整 CDP 曲线')
    add()
    add('两种 CDP 参数均为：膨胀角 30°，偏心率 0.1，fb0/fc0=1.16，K=0.666667，黏性参数 1e-5。对应关键字为 C65 L68589、C70 L68634。数值黏性参数不等于结构阻尼标定。拉伸软化关键字没有 `TYPE=DISPLACEMENT` 或 `TYPE=GFI`，当前输入为应力—开裂应变表；没有以断裂能输入的显式网格正则化设置。')
    add()
    for m in r['materials']:
        if m['name'] not in ('C65','C70'):continue
        add(f'**{m["name"]} 压缩硬化与压缩损伤**')
        add()
        hard=card(m,'CONCRETE COMPRESSION HARDENING');dam=card(m,'CONCRETE COMPRESSION DAMAGE')
        add(f'硬化关键字 L{hard["line"]}；损伤关键字 L{dam["line"]}。')
        add()
        table(['σc / Pa','非弹性应变','dc','硬化数据行','损伤数据行'],[
            (h[0],h[1],d[0],f'L{hl}',f'L{dl}') for h,d,hl,dl in zip(hard['data'],dam['data'],hard['data_lines'],dam['data_lines'])])
        add(f'**{m["name"]} 拉伸软化与拉伸损伤**')
        add()
        hard=card(m,'CONCRETE TENSION STIFFENING');dam=card(m,'CONCRETE TENSION DAMAGE')
        add(f'拉伸软化关键字 L{hard["line"]}；损伤关键字 L{dam["line"]}。')
        add()
        table(['σt / Pa','开裂应变','dt','软化数据行','损伤数据行'],[
            (h[0],h[1],d[0],f'L{hl}',f'L{dl}') for h,d,hl,dl in zip(hard['data'],dam['data'],hard['data_lines'],dam['data_lines'])])
    add('这些表说明当前输入具备相应本构形式，不能替代材料试验校准、压拉循环检验、网格敏感性评价，也不能证明本次重力/模态工况已经验证破坏演化。')
    add()
    add('## 31 段普通纵筋与分段连续性')
    add()
    add('全部 RBLONG 的单元类型为 T3D2、材料为 S345、每根面积 0.000490874 m²（490.874 mm²，等效直径约 25.000004 mm）。共 10880 个节点、5440 个长杆单元；每个纵筋节点只属于该段一个杆单元，杆单元从该段底到顶。每段有两圈不同半径的纵筋，表内圈/外圈根数直接按节点半径聚类得到，半径容差为 1e-5 m。所有高度已加上实例平移，避免将部件局部坐标当成全塔坐标。')
    add()
    table(['段','全局 Y 范围/m','内圈+外圈根数','内/外半径 底→顶/m','T3D2 卡','截面卡','Embedded 卡'],[
        (x['part'],f'{x["y_min_m"]:.2f}–{x["y_max_m"]:.2f}',
         '+'.join(str(b['node_count']) for b in x['bottom_rings']),
         '/'.join(g(b['radius_m']) for b in x['bottom_rings'])+' → '+'/'.join(g(b['radius_m']) for b in x['top_rings']),
         f'L{x["element_keyword_lines"][0]}',f'L{x["section_line"]}',f'L{x["embedded_keyword_line"]}') for x in r['reinforcement']])
    add('31 个 Embedded 约束（L66885–L66975）分别把 `RBLONG_i-1.SET_ALL` 嵌入 `CSEG_i-1.SET_ALL`。该定义约束钢筋跟随宿主位移，未提供钢筋—混凝土黏结滑移规律。按全部部件与 T3D2 连接检查，显式杆系仅有 RBLONG 和 PT，没有环向箍筋杆件；也没有 `*REBAR` 或 `*REBAR LAYER` 定义。不能写成“完整纵筋＋箍筋实体配筋模型”。')
    add()
    add('相邻段的 RBLONG 分属不同实例，节点身份不共享。30 个界面中，26 个界面的端点位置在 1e-5 m 容差内逐根对应，但几何重合不产生直接连接；下表四个变配筋界面只部分对应。完整 30 接口最短距离和端点计数保存在 JSON。')
    add()
    table(['界面','下段/上段根数','重合端点数','下段端点到上段最近端点的最大距离/m'],[
        (f'J{x["interface"]:02}',f'{x["lower_endpoint_count"]}/{x["upper_endpoint_count"]}',x['geometric_coincidences_within_1e_5_m'],g(x['nearest_distance_max_m']))
        for x in r['reinforcement_continuity'] if x['geometric_coincidences_within_1e_5_m']!=x['lower_endpoint_count']])
    add('无直接钢筋搭接、套筒、焊接、跨接方程或连接器定义。当前钢筋段间传力依赖其 Embedded 混凝土宿主，以及混凝土端面的 RP 耦合和接口弹簧；不能据此声称已模拟真实配筋连接构造或锚固破坏。')
    add()
    add('## 36 根预应力筋：锚固、初应力与省略项')
    add()
    p=r['prestressing']
    table(['项','实际设置','证据'],[
        ('部件/单元','PT_36x15p2；72 节点、36 个 T3D2；每根一个单元','部件 L41118；单元 L41192'),
        ('几何','Y=0 至 112 m；长 112 m；环向半径约 1.75 m','节点 L41119 起；完整 36 根坐标见 JSON'),
        ('截面','每根 0.00014 m²=140 mm²，36 根合计 0.00504 m²','L41240–L41241'),
        ('材料','STRAND_1860 线弹性，无塑性、断裂或松弛卡','L68726–L68730'),
        ('底端','SET_PT_BOTTOM_GEOM 的 U1、U2、U3 分别固定','L68735–L68738'),
        ('顶端','36×3=108 个方程，把顶端平动与法兰 RP 平动/转动相关联','L66978–L67660'),
        ('法兰 RP','装配节点 62=(0,112,0)；耦合 CSEG_31 顶面','节点 L63444；Coupling L66693；Kinematic L66694'),
        ('初应力','INITIAL CONDITIONS,TYPE=STRESS；1280 MPa，作用于全部 PT 单元','L68746–L68747'),
        ('名义初始力',f'{g(p["nominal_initial_force_per_tendon_N"])} N/根；总计 {g(p["nominal_initial_force_all_tendons_N"])} N','由输入 σ₀A 计算，不是求解后的有效预应力')])
    add('顶端方程示例（第 1 根，L66978–L66995）：`u1 − U1 + 0.598535·UR2 = 0`；`u2 − U2 − 0.598535·UR1 − 1.64446·UR3 = 0`；`u3 − U3 + 1.64446·UR2 = 0`。大写自由度属于 SET_FLANGE_RP，转角系数由截面偏置产生。108 个方程的全部系数保存在 JSON。')
    add()
    add('预应力筋没有 Embedded，属于由两端约束实现的端部锚固、沿程不黏结理想化。没有孔道壁、锚具局部受压、接触摩擦、钢束分丝、屈服断裂、锚具回缩、张拉次序、温度张拉、松弛/收缩/徐变损失或重新张拉的过程定义。初应力经重力平衡后的实际剩余值必须从对应结果另行核验，不能把 1280 MPa 直接当作已验证的运营有效值。')
    add()
    add('## 混凝土接头、Tie 与 Tower→RNA 连接')
    add()
    add('共有 62 个 Coupling，均后接无显式自由度数据行的 `*KINEMATIC`：30 个混凝土界面各有上下端面两个 RP 耦合（60 个），另有混凝土顶法兰和塔顶 RNA 两个。报告按原始语法披露：未显式选择自由度，采用关键字默认的适用运动学自由度；没有将其误记为输入了明确的“1–6”数据行。')
    add()
    add('30 个界面各用两个同位置 RP 节点、6 个 SPRING2，共 180 个线性弹簧。DOF1、2、3 的刚度均为 1e14 N/m；DOF5（绕竖直 Y 轴）的刚度均为 1e14 N·m/rad；DOF4、6（两向弯曲）的刚度见表。未使用 `NONLINEAR`、仅受拉/仅受压、摩擦或损伤选项。')
    add()
    data=[]
    for j in range(1,31):
        spring=[s for s in r['springs'] if s['joint']==j]
        s1=next(s for s in spring if s['dof']==1);s4=next(s for s in spring if s['dof']==4);s6=next(s for s in spring if s['dof']==6)
        cs=[c for c in r['couplings'] if re.search(fr'CPL_J{j:02}_',c['options']['CONSTRAINT NAME'])]
        data.append((f'J{j:02}',f'{s1["node_coordinates"][0][1]:.2f}',
            '/'.join(str(n) for n in s1['nodes']),g(s4['stiffness']),g(s6['stiffness']),
            '/'.join('L'+str(c['line']) for c in cs),f'L{s1["keyword_line"]}–L{s6["keyword_line"]}'))
    table(['界面','Y/m','两 RP 节点','K4 / N·m·rad⁻¹','K6 / N·m·rad⁻¹','上下端面 Coupling','6 个 Spring 卡范围'],data)
    add('这套线性弹簧与刚化端面保留了有限的整体接头柔度，也对截面端面施加运动学刚化；它没有以接触压力、开口和滑移描述真实接缝。很大的 1e14 刚度仍是有限数值，不应误写成真实试验测得的无限刚性。以上输入本身也没有给出接口刚度的试验或文献校准证据。')
    add()
    table(['Tie','关键字行','第一表面','第二表面','选项'],[
        (t['options']['NAME'],f'L{t["line"]}',t['data'][0][0],t['data'][0][1],'ADJUST=YES') for t in r['ties']])
    add('Tie 将对应表面约束在一起；没有显式螺栓、法兰分离或摩擦承载机制。DAT 四条 Tie 警告说明微小调整节点未全部打印，不能写为“完全没有调整”。')
    add()
    table(['连接','实际引用与自由度形式','证据'],[
        ('塔顶→RNA','COUPLING_RNA_TOP：SSEG_04-1.SURF_TOP → _PickedSet230；该集合为装配节点 1=(0,160,0)','Coupling L66690；Kinematic L66691；集合 L66567；节点 L63322'),
        ('RNA 内部','SET_RNA_RP 同样引用装配节点 1；RNA 全部 B31 质量载体设为刚体','SET_RNA_RP L66218；Rigid Body L68579'),
        ('混凝土顶→PT 锚点','CSEG_31-1.SURF_TOP → SET_FLANGE_RP（装配节点 62），PT 顶节点另经方程关联','Coupling L66693；Equation L66978 起')])
    add('当前 M2 的 RNA 仍是分布刚性 B31 质量载体，不能将另一个独立 RNA 小样本试验的 MASS/ROTARYI、阻尼或能量检查结果当作本 M2 已替换或已验证。')
    add()
    add('三项非结构质量仍在：混凝土集合 L67673–L67674 为 4622.69 kg，L67675–L67676 为 33004.8 kg；钢筒集合 L67677–L67678 为 2172.73 kg，合计 39800.22 kg。这些质量项不增加相应构造的实体刚度、接触或破坏机制。')
    add()
    add('## 约束、载荷和可支持的分析范围')
    add()
    add('竖直方向为 +Y，重力为 −Y。塔底 `CSEG_01-1.FACE_BOTTOM, ENCASTRE` 位于 L68740–L68741；当前无土体、基础柔度或地基相互作用定义。PT 底端固定另见 L68735–L68738。')
    add()
    table(['步骤','步骤关键字','求解/载荷定义','可支持的说明'],[
        ('Gravity','L68752：NLGEOM=YES, INC=500','STATIC L68753：0.05,1,1e-8,0.1；DLOAD L68755：全模型 GRAV,9.81,0,-1,0','静力重力平衡；1 是步的伪时间，不是 1 s 风激励'),
        ('Modal_From_Gravity','L68767：PERTURBATION','FREQUENCY L68768：Lanczos，MASS 归一化，30 阶','围绕重力基态的线性扰动模态'),
        ('Flex_X','L68774：PERTURBATION','STATIC L68775；CLOAD L68776：SET_RNA_RP,1,1000','塔顶 X 向 1 kN 线性扰动柔度'),
        ('Flex_Z','L68784：PERTURBATION','STATIC L68785；CLOAD L68786：SET_RNA_RP,3,1000','塔顶 Z 向 1 kN 线性扰动柔度')])
    add('全文件关键字扫描得到以下卡均为 0；这不否认模型已有 Embedded、Tie 或接头弹簧，只明确列出没有实现的机制。')
    add()
    table(['扫描关键字','数量'],[(k,v) for k,v in r['specified_keyword_counts'].items()])
    add('因此当前 M2 不包含接触开闭/摩擦、物理结构阻尼输入、风载幅值时程、瞬态动力过程、材料疲劳、温度/徐变/收缩过程或倒塌承载力步骤。仅有 CDP 参数与损伤场输出请求，不能宣称已建立并验证上述能力。输出 `DAMAGET/DAMAGEC` 也不意味着钢材或预应力筋具备混凝土损伤本构。')
    add()
    add('## DAT 中的 12 条警告与完成标志')
    add()
    def assessment(w):
        t=w['text']
        if 'TWO-DIMENSIONAL' in t:return '二维厚度与接触的一般提示；当前已解析单元为三维实体/杆梁/弹簧，未定义接触。不能将此提示误解为已存在摩擦接触。'
        if 'TIE PAIR' in t:return 'Tie 的微小位置调整节点未全部打印；提示输出省略，不等于约束失败，也不等于零调整。'
        if 'aspect ratio' in t:return '1512 个单元长宽比 >100；需要在网格披露中保留，不能称作零质量警告。'
        if 'INTEGRATION AND SECTION' in t:return '被声明为刚体的可变形类型元素不输出积分点/截面点变量；不能据此要求刚性 RNA 的材料应力结果。'
        if 'NLGEOM' in t:return '后续扰动步纳入重力基态几何非线性影响；属于基态继承说明，不能误写为独立全非线性风响应。'
        return '保留原始提示，未在本轮消除。'
    table(['DAT 行','原始警告','含义'],[(f'L{w["line"]}',w['text'],assessment(w)) for w in r['dat_warnings']])
    add('DAT L4151 为 `THE ANALYSIS HAS BEEN COMPLETED`；L4156 为 `WITH 12 WARNING MESSAGES ON THE DAT FILE`。这证明该作业完成，不证明所有材料、接触、疲劳或工程安全假设均有效。本报告没有重新求解，也没有凭 DAT 代替完整 ODB 结果核验。')
    add()
    add('## 生成脚本与继承关系的核对范围')
    add()
    add('已读取 `C:/Users/REME/Documents/Codex/2026-10-03/lia/work/chapter2-completion/build_fused_baseline.py`：L4 的塔筒来源为 `D:/MC/DTU158_MODAL_20260909_103944/DTU158_MODAL_CHECK.inp`，L5 的 RNA 来源为恢复候选 `T026_RECOVERED_RNA_CANDIDATE.inp`；该脚本生成 G1，L81 的模型标题明确写入 reconstructed，L84 的记录称保留原塔材料/配筋/PT/弹簧/Tie/耦合/边界，并恢复分布刚性 RNA。该记录仅用于追踪来源，不替代实际输入比较。')
    add()
    c=r['comparison_with_g1']
    if c:
        add(f'本解析器另外直接比较 G1（SHA-256 `{c["source"]["sha256"]}`）与 M2 的材料、截面、弹簧、方程、Tie、Embedded、Coupling、刚体、非结构质量、边界、初应力和步骤/载荷定义；比较结果如下（忽略行号，未把网格/集合/表面拓扑混在这项比对中）：')
        add()
        table(['关键字','G1 数量','M2 数量','定义完全一致'],[(k,v['g1_count'],v['m2_count'],'是' if v['ordered_definitions_identical'] else '否') for k,v in c['per_keyword'].items()])
    else:
        add('本次复运行没有可访问的 G1 文件，因此未重做 G1/M2 继承定义比较。使用 --g1 提供文件可启用此项。')
    add('所以这里披露的是保留已有定义的重构/网格衍生模型，不能声称这些参数全部由本轮从公开 DTU 文档重新推导，也不能把现有用户资产和新增重构工作混为一谈。本报告不对未提供来源的工程参数作“官方”“实测”或“已验证”的背书。')
    add()
    (ROOT/'reinforcement-material-contact-review.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')


def main():
    global INP,DAT,G1,ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inp',type=Path,default=INP)
    parser.add_argument('--dat',type=Path)
    parser.add_argument('--g1',type=Path,default=G1)
    parser.add_argument('--output-dir',type=Path,default=ROOT)
    args=parser.parse_args()
    INP=args.inp.resolve();DAT=(args.dat or INP.with_suffix('.dat')).resolve()
    G1=args.g1.resolve();ROOT=args.output_dir.resolve()
    if source(INP)['sha256']!=EXPECTED_INP_SHA256:
        raise ValueError('Input identity differs from audited M2; do not reuse frozen narrative for a changed model.')
    ROOT.mkdir(parents=True,exist_ok=True)
    lines, bs = read_blocks(INP)
    annotate(bs)
    bykey = collections.defaultdict(list)
    for block in bs: bykey[block['keyword']].append(block)
    part_names = [b['options']['NAME'] for b in bykey['PART']]
    truss_parts={b['part'] for b in bykey['ELEMENT'] if b['options']['TYPE'].upper()=='T3D2'}
    assert truss_parts=={f'RBLONG_{i:02}' for i in range(1,32)}|{'PT_36x15p2'}
    material_names = [b['options']['NAME'] for b in bykey['MATERIAL']]
    assignments = [dict(part=b['part'], line=b['line'], keyword=b['keyword'],
                        options=b['options'], data=b['data'])
                   for b in bs if 'MATERIAL' in b['options']]
    materials = []
    for name in material_names:
        cards = [b for b in bs if b['material'] == name]
        materials.append(dict(name=name, line=cards[0]['line'], cards=cards,
                              assignments=[a for a in assignments if a['options']['MATERIAL'].upper() == name.upper()]))

    assembly_nodes, assembly_nsets = {}, {}
    for b in bs:
        if b['assembly'] and not b['part']:
            if b['keyword'] == 'NODE':
                for line, row in zip(b['data_lines'], b['data']):
                    assembly_nodes[int(row[0])] = dict(xyz=[float(x) for x in row[1:4]], line=line)
            if b['keyword'] == 'NSET':
                assembly_nsets[b['options']['NSET'].upper()] = dict(line=b['line'],
                    instance=b['options'].get('INSTANCE'), labels=labels(b))

    rebar = []
    endpoints = {}
    instances={b['options']['PART']:b for b in bykey['INSTANCE']}
    for name in part_names:
        if not name.startswith('RBLONG_'): continue
        selected, nodes, elements = part_geometry(bs, name)
        instance=instances[name]
        # All current RBLONG instances have either no transform or one translation.
        # Refuse to silently use local coordinates if a rotation is ever introduced.
        assert len(instance['data'])<=1
        translation=[float(x) for x in instance['data'][0]] if instance['data'] else [0.,0.,0.]
        assert len(translation)==3
        for n in nodes.values(): n['xyz']=[a+b for a,b in zip(n['xyz'],translation)]
        section = next(b for b in selected if b['keyword'] == 'SOLID SECTION')
        lo = min(v['xyz'][1] for v in nodes.values())
        hi = max(v['xyz'][1] for v in nodes.values())
        ends = {side:[v['xyz'] for v in nodes.values() if abs(v['xyz'][1]-y)<1e-6]
                for side, y in [('bottom',lo),('top',hi)]}
        endpoints[name] = ends
        connectivity = collections.Counter(n for e in elements for n in e['nodes'])
        em = next(b for b in bykey['EMBEDDED ELEMENT'] if b['data'][0][0].upper().startswith(name.upper()+'-1.'))
        area=float(section['data'][0][0])
        rebar.append(dict(part=name, part_line=selected[0]['line'], nodes=len(nodes), elements=len(elements),
            instance_line=instance['line'],translation_m=translation,
            element_keyword_lines=[b['line'] for b in selected if b['keyword']=='ELEMENT'],
            element_types=dict(collections.Counter(e['type'] for e in elements)),
            y_min_m=lo,y_max_m=hi,section_line=section['line'],area_m2=area,
            equivalent_circular_diameter_mm=math.sqrt(4*area/math.pi)*1000,
            material=section['options']['MATERIAL'],
            node_element_degree_histogram=dict(collections.Counter(connectivity.values())),
            all_elements_span_segment=all(abs(nodes[e['nodes'][0]]['xyz'][1]-nodes[e['nodes'][1]]['xyz'][1])>hi-lo-1e-5 for e in elements),
            bottom_rings=ring_stats(ends['bottom']),top_rings=ring_stats(ends['top']),
            embedded_keyword_line=em['line'],host=em['options']['HOST ELSET']))

    continuity=[]
    for i in range(1,31):
        n1,n2=f'RBLONG_{i:02}',f'RBLONG_{i+1:02}'
        low,high=endpoints[n1]['top'],endpoints[n2]['bottom']
        distances=[min(math.dist(a,b) for b in high) for a in low]
        continuity.append(dict(interface=i,lower=n1,upper=n2,lower_endpoint_count=len(low),upper_endpoint_count=len(high),
            geometric_coincidences_within_1e_5_m=sum(d<1e-5 for d in distances),
            nearest_distance_min_m=min(distances),nearest_distance_max_m=max(distances),
            shared_node_identity=False,
            explicit_direct_bar_splice_equation_tie_or_connector=False,
            interpretation='Separate part-instance node identities; force passes through each embedded host and the host interface constraints/springs. Coordinate coincidence is not a direct bar splice.'))

    pt_name='PT_36x15p2'
    selected,nodes,elements=part_geometry(bs,pt_name)
    ptsec=next(b for b in selected if b['keyword']=='SOLID SECTION')
    ptarea=float(ptsec['data'][0][0])
    pt_ics=[b for b in bykey['INITIAL CONDITIONS'] if any('SET_PT_ALL_ELEMS' in ','.join(row) for row in b['data'])]
    stress=float(pt_ics[0]['data'][0][1])
    pt=dict(part=pt_name,part_line=selected[0]['line'],node_count=len(nodes),element_count=len(elements),
        element_keyword_lines=[b['line'] for b in selected if b['keyword']=='ELEMENT'],
        elements=[dict(**e,coordinates=[nodes[n]['xyz'] for n in e['nodes']],
                    length_m=math.dist(*(nodes[n]['xyz'] for n in e['nodes']))) for e in elements],
        section=ptsec,material='STRAND_1860',area_per_tendon_m2=ptarea,
        radius_min_m=min(math.hypot(*[v['xyz'][i] for i in (0,2)]) for v in nodes.values()),
        radius_max_m=max(math.hypot(*[v['xyz'][i] for i in (0,2)]) for v in nodes.values()),
        initial_stress=pt_ics,nominal_initial_stress_Pa=stress,
        nominal_initial_force_per_tendon_N=stress*ptarea,
        nominal_initial_force_all_tendons_N=stress*ptarea*len(elements),
        boundary_cards=[b for b in bykey['BOUNDARY'] if any('PT_' in ','.join(row) for row in b['data'])],
        equations=bykey['EQUATION'],
        distributed_embedding_present=any('PT_36' in str(b).upper() for b in bykey['EMBEDDED ELEMENT']))

    springs=[]
    for b in bykey['SPRING']:
        elset=b['options']['ELSET']
        match=re.search(r'J(\d+)_DOF(\d+)',elset)
        eb=next(x for x in bykey['ELEMENT'] if x['options'].get('ELSET','').upper()==elset.upper())
        node_ids=[int(n) for n in eb['data'][0][1:]]
        springs.append(dict(joint=int(match[1]),dof=int(match[2]),keyword_line=b['line'],
            data_lines=b['data_lines'],stiffness=float(b['data'][1][0]),
            unit='N/m' if int(match[2])<4 else 'N m/rad',options=b['options'],flags=b['flags'],
            element_keyword_line=eb['line'],element=int(eb['data'][0][0]),nodes=node_ids,
            node_coordinates=[assembly_nodes[n]['xyz'] for n in node_ids]))

    couplings=[]
    for b in bykey['COUPLING']:
        nb=bs[bs.index(b)+1]
        couplings.append(dict(**b,reference_set_resolution=assembly_nsets.get(b['options']['REF NODE'].upper()),
                              following_card=nb))
    steps=[]
    for b in bykey['STEP']:
        steps.append(dict(name=b['options']['NAME'],line=b['line'],options=b['options'],flags=b['flags'],
                          cards=[x for x in bs if x['step']==b['options']['NAME']]))

    absent_keywords=['CONTACT','CONTACT PAIR','SURFACE INTERACTION','FRICTION','SURFACE BEHAVIOR',
        'CONNECTOR SECTION','CONNECTOR BEHAVIOR','REBAR','REBAR LAYER','PRE-TENSION SECTION',
        'DAMPING','DYNAMIC','VISCO','CREEP','EXPANSION','TEMPERATURE','AMPLITUDE','CONCRETE TENSION STIFFENING, TYPE=GFI']
    # TYPE options must be inspected separately; a comma option is not a keyword.
    absent_keywords.remove('CONCRETE TENSION STIFFENING, TYPE=GFI')
    presence={k:len(bykey[k]) for k in absent_keywords}
    lines_dat=DAT.read_text(encoding='utf-8',errors='replace').splitlines()
    warnings=[]
    for i, line in enumerate(lines_dat):
        if '***WARNING:' not in line: continue
        context=[line.strip()]
        for following in lines_dat[i+1:i+7]:
            if not following.strip() or following.lstrip().startswith('*'): break
            context.append(following.strip())
        warnings.append(dict(line=i+1,text=' '.join(context)))
    completion=[dict(line=i+1,text=s.strip()) for i,s in enumerate(lines_dat)
                if 'ANALYSIS HAS BEEN COMPLETED' in s or 'WARNING MESSAGES ON THE DAT FILE' in s]

    comparison={}
    if G1.is_file():
        _,gbs=read_blocks(G1)
        annotate(gbs)
        # Physical definition comparison excludes mesh/set/surface topology blocks.
        keys=['MATERIAL','DENSITY','ELASTIC','PLASTIC','CONCRETE DAMAGED PLASTICITY',
              'CONCRETE COMPRESSION HARDENING','CONCRETE TENSION STIFFENING',
              'CONCRETE COMPRESSION DAMAGE','CONCRETE TENSION DAMAGE','SOLID SECTION',
              'BEAM SECTION','COUPLING','KINEMATIC','EMBEDDED ELEMENT','EQUATION','TIE',
              'NONSTRUCTURAL MASS','SPRING','RIGID BODY','BOUNDARY','INITIAL CONDITIONS',
              'STEP','STATIC','FREQUENCY','DLOAD','CLOAD']
        def signature(b):return (b['part'],b['material'],b['step'],b['options'],b['flags'],b['data'])
        comparison=dict(source=source(G1),per_keyword={key:dict(
            g1_count=sum(b['keyword']==key for b in gbs),m2_count=len(bykey[key]),
            ordered_definitions_identical=[signature(b) for b in gbs if b['keyword']==key]==[signature(b) for b in bykey[key]]) for key in keys})
    report=dict(scope='Read-only INP and DAT definition audit; no solver execution or ODB-derived outcome validation.',
        sources=dict(inp=source(INP),dat=source(DAT)),
        truss_parts=sorted(truss_parts),
        keyword_counts=dict(collections.Counter(b['keyword'] for b in bs)),
        material_assignments=assignments,materials=materials,
        unused_materials=[m['name'] for m in materials if not m['assignments']],
        reinforcement=rebar,reinforcement_total_elements=sum(r['elements'] for r in rebar),
        reinforcement_continuity=continuity,prestressing=pt,springs=springs,couplings=couplings,
        ties=bykey['TIE'],embedded=bykey['EMBEDDED ELEMENT'],
        rigid_bodies=bykey['RIGID BODY'],nonstructural_mass=bykey['NONSTRUCTURAL MASS'],
        assembly_nodes=assembly_nodes,boundaries=bykey['BOUNDARY'],steps=steps,
        specified_keyword_counts=presence,dat_warnings=warnings,dat_completion=completion,
        comparison_with_g1=comparison)
    out=ROOT/'reinforcement-material-contact-review.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write_markdown(report)
    print(json.dumps(dict(output=str(out),rebar_elements=report['reinforcement_total_elements'],
        unused_materials=report['unused_materials'],counts={k:len(bykey[k]) for k in ['COUPLING','EMBEDDED ELEMENT','EQUATION','SPRING','TIE','STEP']},
        dat_warning_count=len(warnings),g1_comparison_all_equal=all(v['ordered_definitions_identical'] for v in comparison.get('per_keyword',{}).values()) if comparison else None),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
