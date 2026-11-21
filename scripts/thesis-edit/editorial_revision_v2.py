#!/usr/bin/env python3
"""Editorial revision of the 2026-11-21 seven-chapter Word snapshot.

This is not an Abaqus result generator, and it does not modify the canonical
six-chapter research source.  It generates one internally consistent Word+JSON
web workbench baseline with documented source-versus-model distinctions.
"""
import argparse, copy, hashlib, json, re
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE=Path(__file__).resolve().parents[2]
PART_PREFIX="10MW-thesis-academic-revision-20261121.part"
PUBLISH_PREFIX="10MW-thesis-editorial-v2-20261121.part"
SRC_JSON=BASE/"public/thesis-studio/editor-data/latest-manuscript.json"
DEST_JSON=BASE/"public/thesis-studio/editor-data/editorial-manuscript-v2.json"
OUT=BASE/"public/thesis-studio/downloads"
WORK=BASE/"_generated-thesis-workbench"
CONCRETE=[
(1,3.64,8.17,280.,108,108),(2,7.28,8.01,280.,108,108),
(3,10.92,7.85,280.,108,108),(4,14.56,7.70,282.5,108,108),
(5,18.20,7.54,287.5,96,96),(6,21.84,7.36,295.,96,96),
(7,25.48,7.22,302.5,96,96),(8,29.12,7.06,307.5,96,96),
(9,32.76,6.90,312.5,96,96),(10,36.40,6.74,320.,96,96),
(11,40.04,6.58,327.5,96,96),(12,43.68,6.42,332.5,90,90),
(13,47.32,6.26,337.5,90,90),(14,50.96,6.10,345.,90,90),
(15,54.60,5.94,352.5,90,90),(16,58.24,5.78,357.5,84,84),
(17,61.88,5.70,360.,84,84),(18,65.52,5.70,360.,84,84),
(19,69.16,5.70,360.,84,84),(20,72.78,5.70,340.,84,84),
(21,76.44,5.70,320.,76,76),(22,80.08,5.70,320.,76,76),
(23,83.72,5.70,320.,76,76),(24,87.36,5.70,320.,76,76),
(25,91.00,5.70,290.,76,76),(26,94.64,5.70,260.,76,76),
(27,98.28,5.70,260.,76,76),(28,101.92,5.70,260.,76,76),
(29,105.56,5.70,354.,76,76),(30,109.20,5.45,414.,76,76),
(31,112.00,4.97,500.,76,76)]
STEEL=[(1,123.50,4.66,38.),(2,135.00,4.58,37.),(3,146.50,4.50,36.),(4,158.00,4.42,35.)]
assert len(CONCRETE)==31 and len(STEEL)==4

REWRITES={
139:"针对10 MW级陆上风机预应力混凝土—钢混合塔架的风致动力响应和结构优化问题，本文选取DTU 10 MW公开参考风机与总高158 m的混合塔架组成研究模型，其中混凝土段112 m、钢塔段46 m。依据文献原型的分段几何、材料分区及可核实构造，建立Abaqus有限元模型，并以材料单轴试件、推覆响应和低阶模态进行分层校核。历史复现模型第一对水平弯曲频率为0.13718 Hz，与文献报告值0.1361 Hz的相对偏差约0.79%。两组推覆模型在0～0.901 m的共同收敛区间内反力—位移曲线基本一致，但均未达到4 m的目标位移；损伤后极限承载力及网格无关性因此不作定量判断。\n\n采用2005—2025年ERA5逐小时资料表征嘉鱼地区的长期风况，研究点100 m高度的平均风速为4.299 m/s。根据10 m和100 m逐时风速计算风切变指数，将100 m风速外推至组合模型的161.368806 m轮毂高度，并据此提取代表性风速及历史高风样本。采用TurbSim生成正常湍流（NTM）与极端湍流（ETM）风场，以三个平均风速水平、两类湍流和每类六个随机种子构成36组研究工况；单组模拟700 s，采用100～700 s时间窗统计响应。该工况集用于运行响应筛选，不等同于全风速范围的设计认证载荷集。\n\n对风轮—机舱总成（RNA）开展质量、质心和惯量的跨软件核对。统一坐标系与塔顶参考点后，Abaqus与OpenFAST的RNA质量相差约0.0043%，但质心位置仍相差约0.536 m，质心惯量存在约3.49%的差异。在统一158 m塔架跨度的降阶模态比较中，含RNA状态下OpenFAST的四个水平弯曲频率比相应Abaqus结果高约8.96%～14.99%，表明质量总量吻合并不足以保证空间动力等效。历史OpenFAST阻尼敏感性计算亦显示，部分塔顶响应变化可达到随机种子离散的同等量级。\n\n现阶段已形成原型参数来源核对、有限元低阶动力校核、场址风况统计与随机风工况筛选的计算基础。针对精细接缝响应、材料疲劳损伤及优化后结构性能的结论，仍须以具有一致初始状态和载荷输入的高保真联合计算及独立复核为依据。",
142:"This study addresses wind-induced response analysis and structural optimisation of a prestressed concrete–steel hybrid tower for a 10 MW onshore wind turbine. The research model combines the publicly documented DTU 10 MW reference turbine with a 158 m hybrid tower, comprising a 112 m concrete section and a 46 m steel section. An Abaqus finite-element model is developed from the traceable segment geometry, material zones and available construction information. Its basic response is assessed using uniaxial material calculations, pushover analysis and modal comparison. The first horizontal bending frequency pair of the historical reproduction model is 0.13718 Hz, approximately 0.79% above the published 0.1361 Hz reference. Two pushover calculations provide similar force–displacement curves over their common converged range of 0–0.901 m, but neither reaches the prescribed 4 m displacement. Ultimate resistance beyond the converged range and post-damage mesh objectivity are therefore not inferred.\n\nHourly ERA5 data from 2005 to 2025 are used to characterise the long-term wind environment of Jiayu, China. The mean wind speed at 100 m is 4.299 m/s. An hourly wind-shear exponent derived from the 10 m and 100 m series is used to extrapolate the 100 m observations to the assembled model's 161.368806 m hub height. Three representative mean-wind-speed levels are considered with normal and extreme turbulence models (NTM and ETM) and six random seeds for each combination, producing 36 research cases in TurbSim. Each simulation spans 700 s; response statistics are evaluated over 100–700 s. These cases are intended for operating-response screening rather than full-range design-load certification.\n\nThe spatial representation of the rotor–nacelle assembly (RNA) is examined by comparing total mass, centre of mass and inertia between Abaqus and OpenFAST. After consistent transformation to a common tower-top reference point, the total RNA masses differ by approximately 0.0043%, whereas the centres of mass differ by about 0.536 m and the centroidal inertias by approximately 3.49%. In a common-span reduced-order modal comparison, the four RNA-on horizontal bending frequencies predicted by OpenFAST remain about 8.96–14.99% higher than their Abaqus counterparts. Agreement in mass alone is thus insufficient to establish spatial dynamic equivalence. An archived OpenFAST damping-sensitivity study also indicates that selected tower-top response changes can be comparable to the dispersion associated with different turbulence seeds.\n\nThe completed work establishes a documented geometric baseline, preliminary structural and dynamic checks, a site-wind characterisation and a reproducible random-wind screening framework. Quantitative conclusions concerning local joint behaviour, material fatigue and optimised structural performance remain conditional on further high-fidelity coupled analyses and independent validation.",
179:"全文以结构模型核验、随机风载荷识别、材料疲劳分析与优化复核为主线。第二章给出158 m混合塔的建模依据、预应力与接缝处理及分层验证；第三章依据嘉鱼ERA5风况、TurbSim入流与OpenFAST运行响应筛选代表工况；第四章评价整体响应及控制部位的材料疲劳；第五、六章进一步研究参数敏感性、优化方案和独立复核。尚未完成的高保真联合计算及材料寿命评估，均不作为既有实算结论。",
180:"研究对象为DTU 10 MW公开参考机组与158 m混合塔的研究性组合，并非嘉鱼实际在役机组。嘉鱼长期再分析风况用于描述环境背景，IEC湍流工况用于整机随机响应计算；两类数据来源与用途分别列明。",
181:"后续章节以可复算的输入、求解过程和结果为依据评价结构性能，区分已完成的数值验证与待开展的材料疲劳、结构优化及联合模型复核。模型适用范围和计算不确定性随对应结果一并报告。",
183:"本章建立158 m预应力混凝土—钢混合塔架的有限元模型。首先核对原型几何、材料及预应力和连接参数的来源，再描述初始平衡、材料级试验、整体推覆与低阶模态分析，并据此确定模型适用于后续动力分析的范围。对尚未完成网格收敛验证的损伤后响应，不作极限承载力判断。",
185:"研究模型由DTU 10 MW参考机组与158 m混合塔架组合构成，其中混凝土塔段高112 m、钢塔段高46 m，分别划分为31节与4节。风机主要参数依据DTU技术报告[2]，塔架分段几何与材料分区依据何泽瑜[1]的公开学位论文。表2-1列出总体参数；混凝土和钢塔各节的原始参数分别见表2-2和表2-3。两项来源并非同一实际工程机组，转子—机舱总成（RNA）的质量、质心和惯量需在模型中独立校核。",
188:"混凝土塔段采用CSEG_01～CSEG_31编码，钢塔段采用SSEG_01～SSEG_04编码，各段几何基准分别取自文献[1]表3-2与表3-3。钢塔尺寸原表第二列标为“半径”，对应数值为4.66～4.42 m；若据字面理解为半径，首节钢塔直径为9.32 m，明显大于112 m处混凝土塔顶4.97 m的外径，也与原文图3-4、图3-5的收分形态不一致。为建立几何连续的研究模型，本文暂将该列数值解释为外径，但在来源表中保留原始“半径”表头。该处理属于本文的几何重建假设，尚不能视为原作者已确认的更正。混凝土与钢塔实体分别采用C3D8R和C3D8I单元，其数值适用性按后文验证结果限定。",
189:"原型表格明确给出了分节尺寸及内、外排纵筋根数，但没有完整公开普通钢筋直径、箍筋与拉筋配置、保护层或预应力股数。因此，文献直接给定的数据与本文按规范和数值模型需要选取的构造参数分别登记；涉及结构响应的重建参数还需进行相应验证。",
190:"混凝土塔段采用C65与C70两类材料，其中底部第1、2节为C70，其余29节为C65。弹性模量分别取37.0 GPa与36.5 GPa，密度均为2400 kg/m³，泊松比均为0.20；钢塔材料按参考模型中的S345材料身份设置。混凝土非线性采用塑性损伤模型（CDP），拉压包络与损伤变量依据GB 50010及文献[32]建立，并通过固定的CSV/INC输入文件保证参数可复核。",
197:"历史BF1模型中，普通钢筋用T3D2桁架单元模拟，采用Embedded约束与混凝土实体连接，等效为钢筋与混凝土之间完全黏结。该模型实际截面赋材为S345，材料库中虽另有HRB500定义，但未被该组钢筋截面调用。上述设置仅描述已运行的BF1历史模型，不能与另行设计的T057 HRB335配筋方案视为同一材料配置；两者的承载响应应分别验证。",
198:"BF1历史模型以36根独立T3D2预应力构件表示预应力体系，单根截面积140 mm²，弹性模量195 GPa，初始应力1280 MPa，对应名义总初始轴力6.4512 MN。该计算身份与T057候选设计中的36组、每组8股、单股140 mm²（名义总力51.6096 MN）不同，不能将两组计算结果互相替代。BF1保留SPRING2等效连接供历史响应比较，接触模型另将30道混凝土水平缝设为法向硬接触、切向罚函数摩擦（研究取值μ=0.5）；钢—混转换段和钢塔节间保持Tie连接。接缝摩擦系数及连接理想化的影响，需在相应结构响应中评价。",
203:"BF1接触模型依次施加预应力初始应力场、结构及RNA重力，并在重力平衡后释放为压紧接缝而临时施加的约束。塔底和预应力筋下端仍保持规定的锚固边界；随后在该平衡状态上进行模态分析。该分析流程与T057正式候选模型的力学初态须分别记录，不得以BF1平衡结果替代T057验收。",
204:"BF1释放后平衡状态的记录质量约为2.630667×10⁶ kg，总重力为25.806843 MN；塔底与预应力筋下锚固的竖向反力分别为32.130927 MN和−6.324084 MN，合计25.806843 MN。预应力构件平均轴向应力约1257.15～1260.76 MPa，按36×140 mm²计算的总轴力约6.345134 MN。30道水平接缝在该算例中保持压紧，接触压力约1.761～4.972 MPa。上述数值只适用于BF1模型及其计算初态。",
209:"完成C65、C70材料级单轴数值试件检查后，采用相同材料输入开展整塔位移控制推覆分析。算例保持塔架几何、网格、RNA、配筋、预应力、SPRING2连接、重力初态及4 m塔顶目标位移不变。输入检查通过，但非线性求解在达到4 m之前因负特征值、迭代发散和连续增量缩减终止。因此，仅将收敛区间内的荷载—位移响应用于模型核对，不把终止点视为结构极限承载状态。",
210:"基准推覆的最后收敛步时间为0.225281，对应4 m线性位移幅值下的塔顶位移0.901126 m，而不是“0.225 m”。该换算与ODB提取位移一致；后续分析统一采用实际塔顶位移作为横坐标。首个已保存损伤帧只能表明输出采样间隔内已产生损伤，不能据此确定精确起裂时刻。",
213:"为考察收敛控制设置的影响，在保持材料、结构参数、边界、加载幅值及网格不变的情况下，对推覆步执行一次*Controls, reset。复核算例的Gravity步仍保留原有收敛控制；两组计算的差异仅在推覆步控制参数，因此可比较其收敛过程，而不能把该复核视为材料或网格独立验证。",
214:"基准与收敛控制复核算例的最后收敛点分别为（0.901126 m，555.694 kN）和（0.928000 m，558.319 kN）。在共同位移区间内，反力最大绝对差约1.320 kN，均方根差约0.131 kN；首个已保存拉损伤均出现在约0.673 m处，两者在约0.913 m附近出现负特征值。由此可见，重置收敛控制仅使收敛终点略有延后，未消除损伤后的求解不稳定性。",
217:"图2-1表明，两组推覆算例在0～0.901126 m范围内的反力—位移曲线基本重合。收敛控制重置对前损伤及初始损伤阶段的整体响应影响较小；由于两组模型均在约0.9 m后终止，尚不能确定更大位移下的承载力下降规律及其网格无关性。",
219:"表2-3归纳两组推覆分析的关键事件。首个已保存拉损伤及负特征值位置接近，说明结果对本次收敛控制重置不敏感；这一现象不足以区分材料软化、接缝失稳和网格敏感性等可能因素，需依赖进一步的针对性计算。",
222:"图2-2所示人工应变能占总内能的比例（ALLAE/ALLIE）在共同分析区间内处于10⁻³%量级，基准与复核算例最终分别约为0.00291%和0.00307%。该比值仅说明人工应变能相对于模型内能较小；推覆后段的负特征值和增量缩减仍需结合接触状态、损伤场及网格独立性判断，不能仅据能量比确定失稳性质。",
225:"当前尚未形成来源与输入一致、可复算的粗细网格对照结果，故不报告网格收敛结论。质量及低阶模态可用于整体动力学初步比对；约0.673 m后出现的损伤以及约0.9 m附近的非线性求解终止尚不具备网格客观性证据，不用于推定极限承载力或破坏位移。",
228:"基于重力及预应力平衡状态，采用Lanczos算法提取30阶无阻尼模态。历史复现模型第一对水平弯曲频率为0.13718 Hz，相对于文献[1]所列Abaqus频率0.1361 Hz的偏差约0.79%。该结果支持整体质量与低阶弹性刚度的一致性判断，但不足以验证局部接触、材料软化或高阶动态响应。30阶水平有效质量参与率的计算结果作为模态覆盖指标单独报告。",
232:"图2-3比较了历史复现模型与文献[1]的一阶水平弯曲频率，差值约0.00108 Hz（0.79%）。该吻合仅为整体低阶动力特性的验证，不能推广为损伤后行为或网格收敛的证明。",
235:"图2-4给出了前30阶模态在X和Z两个水平向的累计有效质量参与率，分别为94.8322%与94.8341%。这一结果说明所取模态对水平惯性有较高覆盖率；正式瞬态分析仍需比较不同模态截断或时间积分设置下的位移、内力及关键截面响应。",
236:"本节0.13718 Hz对应历史文献复现模型。第三章另一套用于OpenFAST降阶比较的空间RNA模型，前四阶频率分别为SS1=0.13513 Hz、FA1=0.13568 Hz、SS2=0.70700 Hz和FA2=0.74218 Hz，其中Abaqus U1（X向）对应OpenFAST侧向（SS），U3（Z向）对应前后向（FA）。两组模型的边界、惯量与使用目的不同，频率不能直接混并。",
245:"文献[116]讨论了混合塔混凝土与钢塔的阻尼差异，并以分材料模态贡献推导等效阻尼。该文案例采用混凝土段5%、钢塔段2%的基准阻尼；本文只借鉴其计算方法，将这两个数值作为明确标注的参考假设，并针对158 m研究塔架重新计算。文献案例的模态阻尼结果不移植为本研究结论；GB/T 42600—2023与IEC 61400-6:2020+AMD1:2025仅作为标准背景，不替代对象化阻尼识别。"
}

def put_text(p,text):
    assert not p._p.xpath('.//m:oMath') and not p._p.xpath('.//w:drawing'),"Do not flatten equations/figures"
    p.text=text

def add_before(anchor,text,style="Normal",small=False):
    p=anchor.insert_paragraph_before(text,style=style)
    if small:
        p.paragraph_format.space_after=Pt(3)
        for r in p.runs:r.font.size=Pt(9)
    if style=="表题":
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next=True
    return p

def put_table(anchor,headers,data,widths):
    d=anchor.part.document
    tab=d.add_table(rows=1,cols=len(headers))
    tab.style="Table Grid";tab.alignment=WD_TABLE_ALIGNMENT.CENTER;tab.autofit=False
    # Three-rule academic table: strong outer lines and subtle horizontal row
    # separators, with no vertical rules.
    borders=OxmlElement("w:tblBorders")
    for edge in ("top","bottom","insideH","insideV","left","right"):
        item=OxmlElement("w:"+edge)
        item.set(qn("w:val"),"single" if edge in ("top","bottom","insideH") else "nil")
        if edge in ("top","bottom","insideH"):
            item.set(qn("w:sz"),"10" if edge in ("top","bottom") else "4")
            item.set(qn("w:color"),"333333" if edge in ("top","bottom") else "A6B0B8")
        borders.append(item)
    tab._tbl.tblPr.append(borders)
    for col,w in zip(tab.columns,widths):col.width=Cm(w)
    for i,v in enumerate(headers):tab.rows[0].cells[i].text=v
    for item in data:
        row=tab.add_row()
        for i,v in enumerate(item):row.cells[i].text=str(v)
    for ri,row in enumerate(tab.rows):
        props=row._tr.get_or_add_trPr()
        no=OxmlElement("w:cantSplit");props.append(no)
        if ri==0:
            h=OxmlElement("w:tblHeader");h.set(qn("w:val"),"true");props.append(h)
        for ci,cell in enumerate(row.cells):
            cell.width=Cm(widths[ci])
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for para in cell.paragraphs:
                para.alignment=WD_ALIGN_PARAGRAPH.CENTER
                para.paragraph_format.line_spacing=1
                para.paragraph_format.space_before=Pt(1)
                para.paragraph_format.space_after=Pt(1)
                for run in para.runs:
                    run.font.size=Pt(8.5 if ri==0 else 9)
                    run.bold=(ri==0)
    anchor._p.addprevious(tab._tbl)
    return tab

def body_text(el):
    return "".join(x.text or "" for x in el.xpath(".//w:t"))
def normalize_doc(source,old_json):
    doc=Document(source)
    pre=list(doc.element.body.iterchildren())
    # Keep every original XML element for stable index mapping despite inserted rows.
    ref_by_id={int(b["word_body_index"]): b for chapter in old_json["chapters"] for b in chapter["blocks"]}
    assert len(ref_by_id)==sum(len(c["blocks"]) for c in old_json["chapters"])
    assert doc.paragraphs[187].text.startswith("2.2 混凝土塔段")
    assert "何泽瑜" in doc.paragraphs[185].text
    assert doc.paragraphs[218].text.startswith("表2-3")
    assert all(not doc.paragraphs[i]._p.xpath('.//m:oMath') for i in REWRITES)
    for idx,value in REWRITES.items():put_text(doc.paragraphs[idx],value)
    # Repair an original erroneous in-text table reference before subsequent renumbering.
    for p in doc.paragraphs:
        if p.text.startswith("表2-3归纳两组推覆"):pass
        if p.text.startswith("表2-4把"):put_text(p,p.text.replace("表2-4把","表2-3把",1))
    for p in doc.paragraphs:
        if "表2-" in p.text:
            new=re.sub(r"表\s*2-(\d{1,2})(?!\d)",lambda m:"表2-"+str(int(m.group(1))+2) if int(m.group(1))>=2 else m.group(0),p.text)
            if new!=p.text:put_text(p,new)
    # The references newly authored in 2.1 describe the inserted tables;
    # they must not inherit the renumbering applied to pre-existing captions.
    put_text(doc.paragraphs[185],REWRITES[185])
    for p in doc.paragraphs:
        if p.text.startswith("表2-5  基准推覆"):p.style="表题"
        if p.text.startswith("图2-2  基准推覆"):p.style="图题"
        if p.text.startswith("表2-6  第二章最终数值验证验证条件"):
            put_text(p,"表2-6  第二章数值模型验证结果及适用范围")
    anchor=next(p for p in doc.paragraphs if p.text.startswith("2.2 混凝土塔段有限元建模") and p.style.name=="论文一级标题")
    added=[]
    added.append(add_before(anchor,"文献[1]表3-2、表3-3分别列出混凝土段与钢塔段的分节尺寸。为便于几何模型独立重建，表2-2和表2-3保留原文数值与表头；具体模型材料、配筋及预应力假设另述。"))
    caption=add_before(anchor,"表2-2  参考混凝土塔段分节几何与纵筋数量（据文献[1]表3-2）","表题")
    caption.paragraph_format.page_break_before=True
    added.append(caption)
    data=[("C%02d"%i,"%.2f"%h,"%.2f"%d,"%.2f"%w,str(inner),str(outer)) for i,h,d,w,inner,outer in CONCRETE]
    added.append(put_table(anchor,["段号","段顶标高/m","外径/m","壁厚/mm","内排纵筋/根","外排纵筋/根"],data,[2.1,2.8,1.9,2.3,2.8,2.8]))
    added.append(add_before(anchor,"注：标高为分段顶面高度；内、外排纵筋数量为文献直接披露值。纵筋直径及其他构造参数未由该表给出。",small=True))
    added.append(add_before(anchor,"表2-3  参考钢塔段分节尺寸（据文献[1]表3-3）","表题"))
    added.append(put_table(anchor,["段号","段顶标高/m","原文列名“半径”/m","壁厚/mm"],
                        [("S%02d"%i,"%.2f"%h,"%.2f"%r,"%.2f"%w) for i,h,r,w in STEEL],[2.1,3.7,5.7,3.2]))
    added.append(add_before(anchor,"注：第二列沿用原文“半径”表头。本文依据相邻塔段几何连续性暂按外径重建，相关解释见2.2节。",small=True))
    post=list(doc.element.body.iterchildren())
    by_element={id(e):i for i,e in enumerate(post)}
    # lxml identity is stable for these nodes within one tree; fallback index from order.
    old_to_new={}
    prev=-1
    for ix,el in enumerate(pre):
        try:
            j=post.index(el)
        except ValueError:
            raise RuntimeError("Original Word body element was unexpectedly removed")
        assert j>prev
        old_to_new[ix]=j;prev=j
    new_blocks=[]
    for seq,item in enumerate(added,1):
        el=item._tbl if hasattr(item,"_tbl") else item._p
        ix=post.index(el)
        if hasattr(item,"_tbl"):
            new_blocks.append({"id":"rev2_table_%02d"%seq,"kind":"table","style":"Table Grid",
            "rows":[[c.text for c in row.cells] for row in item.rows],
            "has_media":False,"has_math":False,"word_body_index":ix})
        else:
            kind="text"
            new_blocks.append({"id":"rev2_text_%02d"%seq,"kind":kind,"style":item.style.name,
            "text":item.text,"has_media":False,"has_math":False,"word_body_index":ix})
    amended=copy.deepcopy(old_json)
    # Original body positions and text are rewritten without losing anchored media/equations.
    for ch in amended["chapters"]:
        revised=[]
        for block in ch["blocks"]:
            oldix=block["word_body_index"];newix=old_to_new[oldix]
            block["word_body_index"]=newix
            if block["kind"]!="table":
                # Use the Word text only for explicitly revised paragraphs; untouched
                # mathematics and special runs keep their existing text-layer representation.
                if body_text(pre[oldix])!=body_text(post[newix]):
                    block["text"]=body_text(post[newix])
                else:
                    # For changed text, XML nodes stay at same identity; map through the actual para text.
                    paragraph=post[newix]
                    t=body_text(paragraph)
                    if t!=block.get("text") and not block.get("has_math") and not block.get("has_media"):
                        block["text"]=t
            revised.append(block)
        if ch["id"]=="02":
            revised+=new_blocks
            revised.sort(key=lambda b:b["word_body_index"])
        ch["blocks"]=revised
    return doc,amended,new_blocks

def deterministic_docx(path):
    # python-docx uses current ZIP entry timestamps by default. Fix them so that
    # identical Word XML produces the same source SHA and does not invalidate
    # browser edit histories on successive CI rebuilds.
    temp=path.with_suffix(".repack.docx")
    with ZipFile(path,"r") as src, ZipFile(temp,"w") as dest:
        for item in src.infolist():
            meta=ZipInfo(item.filename,(1980,1,1,0,0,0))
            meta.compress_type=ZIP_DEFLATED
            meta.external_attr=item.external_attr
            meta.create_system=item.create_system
            dest.writestr(meta,src.read(item.filename),compress_type=ZIP_DEFLATED,compresslevel=6)
    temp.replace(path)

def build(args):
    WORK.mkdir(parents=True,exist_ok=True)
    if args.source:
        source=Path(args.source)
    else:
        parts=[OUT/(PART_PREFIX+str(i).zfill(2)+".bin") for i in range(1,16)]
        for p in parts:assert p.exists(),str(p)
        source=WORK/"original.docx"
        with source.open("wb") as f:
            for p in parts:f.write(p.read_bytes())
    src=source.read_bytes()
    expected="4441c083c5f0e8a1a313de04383c7e9a171d0be01560114d262f086e08c2f3b1"
    assert hashlib.sha256(src).hexdigest()==expected,"Refusing to alter an unknown Word source."
    old=json.loads(SRC_JSON.read_text(encoding="utf8"))
    assert old["source"]["sha256"]==expected
    doc,updated,added=normalize_doc(source,old)
    dest=WORK/"10MW混塔论文_第二章原型参数与学术表述修订V2_20261121.docx"
    doc.save(dest)
    deterministic_docx(dest)
    newbytes=dest.read_bytes()
    updated["source"].update({"name":dest.name,"sha256":hashlib.sha256(newbytes).hexdigest(),
        "bytes":len(newbytes),
        "docx":None,"docx_parts_pattern":"./downloads/10MW-thesis-editorial-v2-20261121.partNN.bin","docx_parts":15,
        "pdf":"./downloads/10MW-thesis-editorial-v2-20261121.pdf",
        "extraction":"Original Word drawings, equations and body order preserved; chapter 2 original tables and editorial revisions integrated; independent scientific validation still required."})
    DEST_JSON.write_text(json.dumps(updated,ensure_ascii=False,separators=(",",":")),encoding="utf8")
    # Publish in the established fifteen-chunk layout; avoid a redundant ~40MB Git blob.
    size=(len(newbytes)+14)//15
    for i in range(15):
        path=OUT/(PUBLISH_PREFIX+str(i+1).zfill(2)+".bin")
        path.write_bytes(newbytes[i*size:(i+1)*size])
    audit={"base_sha256":expected,"revised_sha256":updated["source"]["sha256"],
        "original_blocks":sum(map(lambda c:len(c["blocks"]),old["chapters"])),
        "revised_blocks":sum(map(lambda c:len(c["blocks"]),updated["chapters"])),
        "new_blocks":len(added),"concrete_segments":31,"steel_segments":4,
        "scope":"Editorial revisions to 2026-11-21 seven-chapter snapshot; not canonical T057/T070 run"}
    (WORK/"audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(audit,ensure_ascii=False,indent=2),flush=True)
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--source")
    build(ap.parse_args())
