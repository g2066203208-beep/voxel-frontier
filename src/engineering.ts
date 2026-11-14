import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const repo = 'https://github.com/g2066203208-beep/voxel-frontier';
const safe = (x: unknown) => String(x ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
export function researchPage() {
 const branch = repo + '/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/';
 const audit = branch + 'governance/RESEARCH_GLOBAL_AUDIT_20261114.md';
 const model = branch + 'models/CURRENT_TOWER_SETTINGS_20261114.md';
 const refs = repo + '/tree/research/t080-seismic-integration-gates-20261022/research/wind-tower/references/';
 const chapters = repo + '/tree/research/t080-seismic-integration-gates-20261022/research/wind-tower/manuscript/final-thesis/chapters/';
 const docx = repo + '/tree/research/t080-seismic-integration-gates-20261022/research/wind-tower/manuscript/source-uploads/2026-11-13/original-docx/';
 const delivery = branch + 'manuscript/final-thesis/deliverables/20261114/';
 return `<div class="page-heading"><div><div class="eyebrow">158M HYBRID TOWER / VERIFIED RESEARCH INDEX</div><h1>10 MW混合塔架 · 研究总览</h1>
 <p>2026-11-14核查 · 本页显示GitHub研究分支的实际成果与未验事项，不以测试绿灯代替物理验收。</p></div>
 <a class="button primary" href="${audit}" target="_blank" rel="noopener">完整问题台账</a></div>
 <section class="tower-metrics">
 <div class="tower-metric"><span>当前真实模型</span><strong>158 m</strong><small>Codex MCP读取确认 · BF1、31组环筋</small></div>
 <div class="tower-metric"><span>论文工作稿</span><strong>6章</strong><small>三版原始Word保留 · 新版265页研究稿已归档</small></div>
 <div class="tower-metric"><span>历史风工况</span><strong>36</strong><small>18 NTM + 18 ETM</small></div>
 <div class="tower-metric"><span>31段ETM时程</span><strong>4组</strong><small>历史共1,488,124行 · 跨批同态HOLD</small></div>
 <div class="tower-metric"><span>12阶段正式验收</span><strong>0 / 12</strong><small>已有来源、方法成果不能抹零</small></div>
 <div class="tower-metric"><span>规划正式DLC1.2</span><strong>0 / 126</strong><small>126是研究暂定矩阵，非IEC固定标准</small></div>
 </section>
 <section class="panel research-intro"><h2>当前模型与历史物理基线</h2>
 <p>Codex已原生确认 <code>TOWER_AND_FOUNDATION_SEPARATE.cae</code> 的92项当前配置：31组纵筋与环筋、BF1初始6.4512 MN、30处线性接缝、E-only已配置。当前工程Jobs=0；历史PT平衡后6.359523 MN和Gravity/30阶模态来自独立修复工程。T057 BF8与旧T070三维基准不是当前工程。</p>
 <div class="research-links"><a href="#" data-view="current-model" class="button primary">在工作室内查看92项设置</a><a href="${model}" target="_blank" rel="noopener">模型来源档案</a></div></section>
 <section class="panel research-intro"><h2>六章现行稿</h2><div class="tower-table-wrap"><table class="tower-parameter-table">
 <thead><tr><th>章节</th><th>有来源的现有成果</th><th>关键未闭合结论</th></tr></thead><tbody>
 <tr><th>Ch1 绪论</th><td>文献与研究问题链</td><td>投稿创新需原文边界核定</td></tr>
 <tr><th>Ch2 模型</th><td>原型参数、当前BF1与T057历史候选分开</td><td>不同版本的正式物理适用性</td></tr>
 <tr><th>Ch3 随机风</th><td>ERA5及36历史工况、NTM/ETM时程</td><td>正式全风速与纯风外载来源</td></tr>
 <tr><th>Ch4 疲劳</th><td>48,070条载荷循环及名义应力筛查</td><td>材料点年Miner/寿命</td></tr>
 <tr><th>Ch5 优化</th><td>DOE/代理/算法验证</td><td>真实设计点Pareto优化</td></tr>
 <tr><th>Ch6 结论</th><td>历史筛查、统计限制与展望</td><td>风震/材料/优化新物理结论</td></tr>
 </tbody></table></div><div class="research-links"><a href="${chapters}" target="_blank" rel="noopener">现行六章全文</a><a class="button primary" href="${delivery}DTU10MW_158m_CURRENT_six_chapter_research_20261114.docx" target="_blank" rel="noopener">265页新版Word</a><a href="${delivery}DTU10MW_158m_CURRENT_six_chapter_research_20261114.pdf" target="_blank" rel="noopener">265页PDF</a><a href="${docx}" target="_blank" rel="noopener">历史三版Word</a></div></section>
 <section class="panel research-intro"><h2>当前高优先级问题</h2>
 <p><strong>已修正文稿：</strong>Ch3一个及Ch4三个被旧装配器排除的新增小节，已经移动回正文；Ch4§4.10.1章节层级已校正。Ch2已明确当前BF1与历史BF8分支不同。</p>
 <p><strong>仍未解决：</strong>旧装配器过期问题已由现行源SHA锁构建替代；新版265页Word/PDF已归档，但尚非送审版，完整人工视觉与格式终审未通过；跨批600s同态及气动力/惯性分解未闭合；E-only完整地震未运行、W/E/WE、材料Miner及真实结构优化均不能宣称通过。</p>
 <p><strong>资料核实：</strong>何泽瑜原始90页PDF与11张关键原页均已入GitHub；现存85张关键原页已经在同一个工作室直接显示与放大，未把全部PDF整本转成图片；原作者权属与引文终审继续保留。</p>
 <div class="research-links"><a class="button primary" href="${audit}" target="_blank" rel="noopener">查看14条证据问题及处理状态</a><a href="#" data-view="source-evidence" class="button primary">工作室内查看85张原始证据图</a><a href="${refs}" target="_blank" rel="noopener">原始PDF文件目录</a></div>
 </section><p class="tower-source-footer">研究分支PR #42仍Draft；正式Pages只由main部署，本页代码已提交不等于官网已同步。资料原图引用须保留原作者和许可边界。</p>`;
}

export function engineeringPage() {
  const inp = repo + '/blob/main/research/wind-tower/experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp';
  return `<section class="tower-evidence"><h2>历史T070基准 · 非当前工程</h2><p>此页的三维数据来自旧T070父本与原始RNA显示外壳，不能视为2026-11-14双模型工程的几何、配筋、Job或地震配置实测图。当前工程的92项报告配置请使用左侧“当前工程设置 · 11.14”；此处仅保留历史模型来源展示。</p></section><div class="page-heading"><div><div class="eyebrow">HISTORICAL T070 / FINITE ELEMENT REFERENCE</div><h1>历史T070三维参考模型</h1><p>默认同时展示两种RNA身份：塔架有限元数据来自历史 T070 求解父模型；计算中真正生效的是 R2 空间等效RNA（MASS + 完整ROTARYI + 偏心CG + 6DOF耦合），原始 Abaqus CAE 的三片叶片、机舱与 spinner/轮毂仅作为完整外形叠加显示。这样网页看起来是完整风机，但不会把显示外壳误当成求解RNA。</p></div><a class="button primary" href="${repo}/blob/main/research/wind-tower/geometry/DTU158_TOWER_RNA_FULL_ASSEMBLY.step" target="_blank" rel="noopener">完整风机 STEP</a></div><div class="engineering-layout"><section class="panel viewer-panel"><div class="viewer-controls"><button class="button" id="model-reset">轴测</button><button class="button" id="model-front">正视</button><button class="button" id="model-side">侧视</button><button class="button" id="model-top">俯视</button><label><input type="checkbox" id="model-mesh" checked/> 外表面网格</label><label><input type="checkbox" id="model-transparent"/> 半透明</label><button class="button" id="model-rebar-check">钢筋检查</button><button class="button" id="model-rna-focus">聚焦完整 RNA</button><label><input type="checkbox" id="model-rna-active" checked/> 计算RNA（R2空间惯性）</label><label><input type="checkbox" id="model-foundation" checked/> 等效基础固定面</label><label><input type="checkbox" id="model-isolate"/> 隔离选中</label><button class="button" id="model-png">导出 PNG</button></div><div id="model-canvas"><p id="model-loading" role="status">正在读取完整风机 Abaqus 网格…</p></div><p class="viewer-caption">拖动旋转 · 滚轮缩放 · 右键平移 · 点击实体可选中部件。叶片、机舱和 spinner/轮毂来自原始 Abaqus CAE 导出的实际表面网格；塔架来自当前混塔有限元输入。</p></section><aside class="panel model-details"><h2>T070历史基准装配</h2><div id="model-report" role="status">加载中…</div><h3>显示层</h3><div class="layer-grid" id="model-layers"><label><input type="checkbox" data-cat="concrete" checked/> 混凝土塔段</label><label><input type="checkbox" data-cat="steel" checked/> 钢塔段</label><label><input type="checkbox" data-cat="rebar" checked/> 普通纵向钢筋</label><label><input type="checkbox" data-cat="hoop" checked/> 当前环向钢筋候选</label><label><input type="checkbox" data-cat="tiebar"/> 当前拉筋候选</label><label><input type="checkbox" data-cat="prestress" checked/> 预应力筋</label><label><input type="checkbox" data-cat="joint" checked/> 接头弹簧</label><label><input type="checkbox" data-cat="rna-source" checked/> 完整RNA外壳（三叶片/机舱/spinner，仅显示）</label></div><label>部件 / 实例 <select id="model-part"><option value="">全部部件</option></select></label><div id="part-details"></div><h3>RNA双身份</h3><div class="rna-details"><p class="model-note"><strong>求解有效：</strong>R2空间等效RNA，保留总质量、偏心质心与完整三维转动惯量，并通过塔顶6DOF耦合参与Abaqus计算。</p><p><strong>完整外形：</strong>三片叶片、机舱与spinner/轮毂来自原始Abaqus CAE表面网格，只用于在线查看和论文示意，不参与当前T070求解，避免与等效RNA重复计质量/惯量。</p></div><div id="rna-details" class="rna-details">加载中…</div><h3>纵筋几何审计</h3><div id="rebar-audit" class="rna-details">加载中…</div><h3>预应力PT来源状态</h3><div id="pt-source" class="rna-details">加载中…</div><h3>模型文件</h3><div class="research-links model-links"><a href="${repo}/blob/main/research/wind-tower/geometry/DTU158_TOWER_RNA_FULL_ASSEMBLY.step" target="_blank" rel="noopener">完整风机 STEP</a><a href="${repo}/blob/main/research/wind-tower/archive/local-large-assets-20261004/abaqus-dtu-models/DTU158_HybridTower_v29_RNA_DISTRIBUTED_OFFICIAL.cae" target="_blank" rel="noopener">完整 RNA CAE v29</a><a href="${repo}/blob/main/research/wind-tower/archive/local-large-assets-20261004/abaqus-dtu-models/DTU158_HybridTower_v28_RNA_DISTRIBUTED_OFFICIAL.cae" target="_blank" rel="noopener">完整 RNA CAE v28</a><a href="${inp}" target="_blank" rel="noopener">当前T070求解 INP</a><a href="${import.meta.env.BASE_URL}research/source-rna-model-report.json" target="_blank" rel="noopener">RNA 网格报告</a></div></aside></div>`;
}

export async function mountEngineering(host: HTMLElement): Promise<()=>void> {
  let alive = true, frame = 0;
  const controller = new AbortController();
  let renderer: THREE.WebGLRenderer | undefined, controls: OrbitControls | undefined;
  const geometries: THREE.BufferGeometry[] = [], materials: THREE.Material[] = [];
  const canvasHost = host.querySelector<HTMLElement>('#model-canvas')!;
  const resizeObserver = new ResizeObserver(()=>resize());
  let camera: THREE.PerspectiveCamera;
  let clickHandler: ((e:PointerEvent)=>void) | undefined;
  const dispose = () => {
    alive=false; controller.abort(); cancelAnimationFrame(frame); controls?.dispose();
    if(clickHandler && renderer) renderer.domElement.removeEventListener('pointerdown',clickHandler);
    geometries.forEach(g=>g.dispose()); materials.forEach(m=>m.dispose()); renderer?.dispose(); resizeObserver.disconnect();
  };
  function resize() {
    if(!renderer || !camera) return;
    const w=Math.max(canvasHost.clientWidth,1), h=Math.max(canvasHost.clientHeight,1);
    camera.aspect=w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h);
  }
  async function json(file:string,gzip=false) {
    const response = await fetch(`${import.meta.env.BASE_URL}research/${file}`,{signal:controller.signal});
    if(!response.ok) throw Error(`读取失败 HTTP ${response.status}`);
    if(gzip && !response.headers.get('Content-Encoding')?.includes('gzip')) {
      return JSON.parse(await new Response(response.body!.pipeThrough(new DecompressionStream('gzip'))).text());
    }
    return response.json();
  }
  try {
    const [data, report, sourceRna, sourceRnaReport, rebarAudit, t046Overlay, t046Report, ptTrace] = await Promise.all([json('abaqus-model.json.gz',true),json('abaqus-model-report.json'),json('source-rna-model.json.gz',true),json('source-rna-model-report.json'),json('rebar-audit.json'),json('t046-rebar-overlay.json.gz',true),json('t046-rebar-report.json'),json('t047-pt-bundle-sensitivity.json')]);
    if(!alive || !canvasHost.isConnected) { dispose(); return dispose; }

    const scene=new THREE.Scene();
    scene.background=new THREE.Color('#edf1ef');
    scene.add(new THREE.HemisphereLight(0xffffff,0x5b6660,2.5));
    const light=new THREE.DirectionalLight(0xffffff,3.2); light.position.set(80,180,120); scene.add(light);
    const root=new THREE.Group(); scene.add(root);

    const categoryColor:Record<string,string>={concrete:'#b9b7ae',steel:'#5f7896',rebar:'#725747',hoop:'#b7463d',tiebar:'#8b6b51',prestress:'#d69a3b',joint:'#8b63a5','rna-source':'#4f9688',other:'#7b8881'};
    type Visual={name:string;category:string;kind:string;surface?:THREE.Mesh;wire?:THREE.LineSegments;line?:THREE.LineSegments;material?:THREE.MeshStandardMaterial;info:any;baseOpacity?:number};
    const visuals:Visual[]=[];
    const pickMeshes:THREE.Mesh[]=[];

    for(const g of data.groups as any[]) {
      const color=categoryColor[g.category] || categoryColor.other;
      if(g.kind==='solid') {
        const geom=new THREE.BufferGeometry();
        geom.setAttribute('position',new THREE.Float32BufferAttribute(g.positions,3));
        geom.setIndex(g.triangles); geom.computeVertexNormals(); geometries.push(geom);
        const mat=new THREE.MeshStandardMaterial({color,roughness:.72,metalness:g.category==='steel' ? .28 : .04,side:THREE.DoubleSide,transparent:true,opacity:1});
        materials.push(mat);
        const surface=new THREE.Mesh(geom,mat); surface.userData.visualName=g.name; root.add(surface); pickMeshes.push(surface);
        const wireGeom=new THREE.BufferGeometry();
        wireGeom.setAttribute('position',new THREE.Float32BufferAttribute(g.positions,3));
        wireGeom.setIndex(g.lineIndices); geometries.push(wireGeom);
        const wireMat=new THREE.LineBasicMaterial({color:'#33413a',transparent:true,opacity:.42}); materials.push(wireMat);
        const wire=new THREE.LineSegments(wireGeom,wireMat); root.add(wire);
        visuals.push({name:g.name,category:g.category,kind:g.kind,surface,wire,material:mat,info:g});
      } else {
        const lineGeom=new THREE.BufferGeometry();
        lineGeom.setAttribute('position',new THREE.Float32BufferAttribute(g.positions,3)); lineGeom.setIndex(g.lineIndices); geometries.push(lineGeom);
        const lineMat=new THREE.LineBasicMaterial({color,transparent:true,opacity:.92}); materials.push(lineMat);
        const line=new THREE.LineSegments(lineGeom,lineMat); line.userData.visualName=g.name; root.add(line);
        visuals.push({name:g.name,category:g.category,kind:g.kind,line,info:g});
      }
    }


    for(const g of sourceRna.groups as any[]) {
      const sourceColor=g.subtype==='blade'?'#4f9688':g.subtype==='nacelle'?'#647da4':g.subtype==='spinner'?'#d4943d':'#688078';
      const geom=new THREE.BufferGeometry();
      geom.setAttribute('position',new THREE.Float32BufferAttribute(g.positions,3));
      geom.setIndex(g.triangles); geom.computeVertexNormals(); geometries.push(geom);
      const mat=new THREE.MeshStandardMaterial({color:sourceColor,roughness:.68,metalness:g.subtype==='nacelle' ? .18 : .05,side:THREE.DoubleSide,transparent:true,opacity:.82});
      materials.push(mat);
      const surface=new THREE.Mesh(geom,mat); surface.userData.visualName=g.name; root.add(surface); pickMeshes.push(surface);
      const wireGeom=new THREE.BufferGeometry();
      wireGeom.setAttribute('position',new THREE.Float32BufferAttribute(g.positions,3));
      wireGeom.setIndex(g.lineIndices); geometries.push(wireGeom);
      const wireMat=new THREE.LineBasicMaterial({color:'#2f4540',transparent:true,opacity:.25}); materials.push(wireMat);
      const wire=new THREE.LineSegments(wireGeom,wireMat); root.add(wire);
      visuals.push({name:g.name,category:'rna-source',kind:'surface',surface,wire,material:mat,info:{...g,displayRole:'原始 Abaqus RNA 表面网格（完整外形显示；不参与当前T070求解）'},baseOpacity:.82});
    }

    const t046Groups=[{name:'CURRENT_HOOP_CANDIDATE',category:'hoop',positions:t046Overlay.hoop.positions,info:{nodes:0,elements:t046Overlay.hoop.elements,elementTypes:['T3D2'],displayRole:'当前父模型继承的环向钢筋候选；网页单独叠加显示以便检查，最终Task2结果生成后替换'}},{name:'CURRENT_TIE_CANDIDATE',category:'tiebar',positions:t046Overlay.tie.positions,info:{nodes:0,elements:t046Overlay.tie.elements,elementTypes:['T3D2'],displayRole:'当前父模型继承的拉筋候选；网页单独叠加显示以便检查，最终Task2结果生成后替换'}}];
    for(const g of t046Groups){
      const geom=new THREE.BufferGeometry();
      geom.setAttribute('position',new THREE.Float32BufferAttribute(g.positions,3)); geometries.push(geom);
      const mat=new THREE.LineBasicMaterial({color:categoryColor[g.category],transparent:true,opacity:g.category==='hoop' ? .9 : .65}); materials.push(mat);
      const line=new THREE.LineSegments(geom,mat); root.add(line);
      visuals.push({name:g.name,category:g.category,kind:'line',line,info:g.info});
    }

    const foundationGroup=new THREE.Group(); scene.add(foundationGroup);
    const foundationGeom=new THREE.CircleGeometry(4.45,96); foundationGeom.rotateX(-Math.PI/2); geometries.push(foundationGeom);
    const foundationMat=new THREE.MeshBasicMaterial({color:'#4f5960',transparent:true,opacity:.12,side:THREE.DoubleSide,depthWrite:false}); materials.push(foundationMat);
    const foundationDisk=new THREE.Mesh(foundationGeom,foundationMat); foundationDisk.position.y=-0.012; foundationGroup.add(foundationDisk);
    const foundationRingGeom=new THREE.RingGeometry(4.15,4.45,96); foundationRingGeom.rotateX(-Math.PI/2); geometries.push(foundationRingGeom);
    const foundationRingMat=new THREE.MeshBasicMaterial({color:'#353f45',transparent:true,opacity:.45,side:THREE.DoubleSide}); materials.push(foundationRingMat);
    const foundationRing=new THREE.Mesh(foundationRingGeom,foundationRingMat); foundationRing.position.y=-0.01; foundationGroup.add(foundationRing);
    const rnaGroup=new THREE.Group(); scene.add(rnaGroup);
    const markerMaterialTop=new THREE.MeshStandardMaterial({color:'#355d7a',roughness:.35}); materials.push(markerMaterialTop);
    const markerMaterialCg=new THREE.MeshStandardMaterial({color:'#b56d2a',roughness:.35}); materials.push(markerMaterialCg);
    // RNA inertia glyph: symbolic visualization of the active MASS+ROTARYI operator, not physical blade geometry.
    const inertiaWireMaterial=new THREE.MeshBasicMaterial({color:'#9a5422',wireframe:true,transparent:true,opacity:.42}); materials.push(inertiaWireMaterial);
    const markerGeometryTop=new THREE.SphereGeometry(.55,24,16), markerGeometryCg=new THREE.SphereGeometry(.75,24,16); geometries.push(markerGeometryTop,markerGeometryCg);
    if(data.rna?.towerTop) {
      const m=new THREE.Mesh(markerGeometryTop,markerMaterialTop); m.position.fromArray(data.rna.towerTop); rnaGroup.add(m);
    }
    if(data.rna?.rnaCg) {
      const m=new THREE.Mesh(markerGeometryCg,markerMaterialCg); m.position.fromArray(data.rna.rnaCg); rnaGroup.add(m);
    }
    if(data.rna?.rnaCg && data.rna?.rotaryInertia && data.rna?.mass) {
      const I=data.rna.rotaryInertia.map((x:number)=>Number(x)), mass=Number(data.rna.mass);
      const ax=Math.sqrt(Math.max(0,5*(I[1]+I[2]-I[0])/(2*mass)));
      const ay=Math.sqrt(Math.max(0,5*(I[0]+I[2]-I[1])/(2*mass)));
      const az=Math.sqrt(Math.max(0,5*(I[0]+I[1]-I[2])/(2*mass)));
      const inertiaGlyphGeometry=new THREE.SphereGeometry(1,28,18); geometries.push(inertiaGlyphGeometry);
      const glyph=new THREE.Mesh(inertiaGlyphGeometry,inertiaWireMaterial);
      glyph.scale.set(ax,ay,az); glyph.position.fromArray(data.rna.rnaCg); rnaGroup.add(glyph);
      glyph.userData.visualRole='RNA inertia glyph';
    }
    if(data.rna?.towerTop && data.rna?.rnaCg) {
      const lg=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3().fromArray(data.rna.towerTop),new THREE.Vector3().fromArray(data.rna.rnaCg)]); geometries.push(lg);
      const lm=new THREE.LineDashedMaterial({color:'#8b5a2b',dashSize:.35,gapSize:.2}); materials.push(lm);
      const line=new THREE.Line(lg,lm); line.computeLineDistances(); rnaGroup.add(line);
    }

    const bounds=new THREE.Box3(new THREE.Vector3(Math.min(data.bounds.min[0],sourceRna.bounds.min[0]),Math.min(data.bounds.min[1],sourceRna.bounds.min[1]),Math.min(data.bounds.min[2],sourceRna.bounds.min[2])),new THREE.Vector3(Math.max(data.bounds.max[0],sourceRna.bounds.max[0]),Math.max(data.bounds.max[1],sourceRna.bounds.max[1]),Math.max(data.bounds.max[2],sourceRna.bounds.max[2])));
    const center=bounds.getCenter(new THREE.Vector3()), size=bounds.getSize(new THREE.Vector3());
    camera=new THREE.PerspectiveCamera(32,1,.05,5000); camera.up.set(0,1,0);
    renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
    renderer.setPixelRatio(Math.min(devicePixelRatio,2));
    renderer.outputColorSpace=THREE.SRGBColorSpace;
    canvasHost.replaceChildren(renderer.domElement);
    controls=new OrbitControls(camera,renderer.domElement); controls.enableDamping=true; controls.dampingFactor=.08;

    function setView(kind:'iso'|'front'|'side'|'top') {
      const span=Math.max(size.x,size.y,size.z), d=span*1.25;
      const c=center.clone();
      camera.up.set(0,1,0);
      if(kind==='front') camera.position.set(c.x,c.y,c.z+d);
      else if(kind==='side') camera.position.set(c.x+d,c.y,c.z);
      else if(kind==='top') { camera.up.set(0,0,-1); camera.position.set(c.x,c.y+d,c.z+.001); }
      else camera.position.set(c.x+d*.56,c.y+d*.12,c.z+d*.78);
      controls!.target.copy(c); controls!.update();
    }
    setView('iso'); resizeObserver.observe(canvasHost); resize();
    const tick=()=>{if(!alive)return; controls!.update();renderer!.render(scene,camera);frame=requestAnimationFrame(tick);}; tick();

    const select=host.querySelector<HTMLSelectElement>('#model-part')!;
    const sorted=[...visuals].sort((a,b)=>a.category.localeCompare(b.category)||a.name.localeCompare(b.name));
    select.innerHTML='<option value="">全部部件</option>'+sorted.map(v=>`<option value="${safe(v.name)}">${safe(v.name)} · ${safe(v.info.elementTypes.join('/'))}</option>`).join('');

    const catChecks=[...host.querySelectorAll<HTMLInputElement>('#model-layers input[data-cat]')];
    const meshCheck=host.querySelector<HTMLInputElement>('#model-mesh')!;
    const transparentCheck=host.querySelector<HTMLInputElement>('#model-transparent')!;
    const isolateCheck=host.querySelector<HTMLInputElement>('#model-isolate')!;
    const rnaActiveCheck=host.querySelector<HTMLInputElement>('#model-rna-active')!;
    const foundationCheck=host.querySelector<HTMLInputElement>('#model-foundation')!;
    const rebarCheck=host.querySelector<HTMLButtonElement>('#model-rebar-check')!;
    let rebarInspect=false;
    function updateVisibility() {
      const selected=select.value, isolate=isolateCheck.checked;
      const enabled=new Set(catChecks.filter(x=>x.checked).map(x=>x.dataset.cat));
      for(const v of visuals) {
        const base=enabled.has(v.category) && (!isolate || !selected || v.name===selected);
        if(v.surface) v.surface.visible=base;
        if(v.wire) v.wire.visible=base && meshCheck.checked && !(rebarInspect && v.category==='concrete');
        if(v.line) v.line.visible=base;
        if(v.material) {
          v.material.opacity=rebarInspect && v.category==='concrete' ? .14 : (transparentCheck.checked ? .28 : (v.baseOpacity ?? 1));
          v.material.emissive.set(v.name===selected ? 0x273b20 : 0x000000);
        }
      }
      rnaGroup.visible=rnaActiveCheck.checked && !rebarInspect;
      foundationGroup.visible=foundationCheck.checked;
      const v=visuals.find(x=>x.name===selected);
      host.querySelector('#part-details')!.textContent=v ? `${v.name} · ${v.info.nodes.toLocaleString()} 节点 · ${v.info.elements.toLocaleString()} 单元 · ${v.info.elementTypes.join(', ')}` : '点击模型或从下拉框选择实例；可配合“隔离选中”检查单段网格。';
    }
    select.onchange=updateVisibility; isolateCheck.onchange=updateVisibility; meshCheck.onchange=updateVisibility; transparentCheck.onchange=updateVisibility; rnaActiveCheck.onchange=updateVisibility; foundationCheck.onchange=updateVisibility;
    rebarCheck.onclick=()=>{
      rebarInspect=!rebarInspect;
      rebarCheck.classList.toggle('primary',rebarInspect);
      rebarCheck.textContent=rebarInspect?'退出钢筋检查':'钢筋检查';
      if(rebarInspect){
        for(const x of catChecks) x.checked=x.dataset.cat==='concrete'||x.dataset.cat==='rebar'||x.dataset.cat==='hoop'||x.dataset.cat==='tiebar';
        rnaActiveCheck.checked=false; isolateCheck.checked=false; select.value='';
      } else {
        for(const x of catChecks) x.checked=true;
        rnaActiveCheck.checked=true;
      }
      updateVisibility();
    };
    catChecks.forEach(x=>x.onchange=updateVisibility); updateVisibility();

    const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2();
    clickHandler=(event:PointerEvent)=>{
      const rect=renderer!.domElement.getBoundingClientRect();
      pointer.x=((event.clientX-rect.left)/rect.width)*2-1; pointer.y=-((event.clientY-rect.top)/rect.height)*2+1;
      raycaster.setFromCamera(pointer,camera);
      const hit=raycaster.intersectObjects(pickMeshes,false)[0];
      if(hit){select.value=String(hit.object.userData.visualName||'');updateVisibility();}
    };
    renderer.domElement.addEventListener('pointerdown',clickHandler);

    host.querySelector<HTMLButtonElement>('#model-reset')!.onclick=()=>setView('iso');
    host.querySelector<HTMLButtonElement>('#model-front')!.onclick=()=>setView('front');
    host.querySelector<HTMLButtonElement>('#model-side')!.onclick=()=>setView('side');
    host.querySelector<HTMLButtonElement>('#model-top')!.onclick=()=>setView('top');
    const rnaFocus=host.querySelector<HTMLButtonElement>('#model-rna-focus')!;
    rnaFocus.onclick=()=>{
      const src=catChecks.find(x=>x.dataset.cat==='rna-source'); if(src) src.checked=true;
      rnaActiveCheck.checked=false; isolateCheck.checked=false; select.value='';
      updateVisibility();
      const rb=new THREE.Box3(new THREE.Vector3().fromArray(sourceRna.bounds.min),new THREE.Vector3().fromArray(sourceRna.bounds.max));
      const g=rb.getCenter(new THREE.Vector3()), rs=rb.getSize(new THREE.Vector3()), d=Math.max(rs.x,rs.y,rs.z)*1.2;
      camera.up.set(0,1,0); camera.position.set(g.x+d*.45,g.y+d*.12,g.z+d*.78);
      controls!.target.copy(g); controls!.update();
    };
    host.querySelector<HTMLButtonElement>('#model-png')!.onclick=()=>{
      renderer!.render(scene,camera);
      const link=document.createElement('a');link.download='DTU158-FULL-TURBINE-Abaqus-FE.png';link.href=renderer!.domElement.toDataURL('image/png');link.click();
    };

    const rnaInstances=(sourceRnaReport.instances||[]) as any[];
    const bladeCount=rnaInstances.filter(x=>x.subtype==='blade').length;
    const nacelleCount=rnaInstances.filter(x=>x.subtype==='nacelle').length;
    const spinnerCount=rnaInstances.filter(x=>x.subtype==='spinner').length;
    host.querySelector('#model-report')!.innerHTML=`<p><strong>完整风机显示：</strong>158 m混塔 + 原始完整RNA外形。</p><p><strong>RNA表面网格：</strong>${sourceRnaReport.counts.instances} 个实例 · ${sourceRnaReport.counts.nodes.toLocaleString()} 节点 · ${sourceRnaReport.counts.elements.toLocaleString()} 单元；其中叶片实例 ${bladeCount} 个、机舱实例 ${nacelleCount} 个、spinner/轮毂实例 ${spinnerCount} 个。</p><p><strong>Abaqus求解主体：</strong>T070（T057 physics + diagnostics） · ${report.counts.instances} 个装配实例 · ${report.counts.solidElements.toLocaleString()} 个实体单元 · ${report.counts.lineElements.toLocaleString()} 个线单元。</p><p><strong>求解RNA：</strong>R2空间等效惯性，不使用完整外壳重复参与求解。</p><p>完整RNA高度范围：${sourceRnaReport.bounds.min[1].toFixed(3)} ～ ${sourceRnaReport.bounds.max[1].toFixed(3)} m。</p><details><summary>模型与RNA导出证据</summary><p>T070 SHA256：<code>${safe(report.sha256)}</code></p><p>RNA表面网格SHA256：<code>${safe(sourceRnaReport.sha256)}</code></p><p>${safe(sourceRnaReport.source.nodes)}</p><p>${safe(sourceRnaReport.source.elements)}</p></details>`;
    host.querySelector('#rebar-audit')!.innerHTML=`<p><b>当前T070纵筋：</b><span class="badge done">GEOMETRY PASS</span> 31/31 Embedded，钢筋几何位于筒壁内。</p><p><b>当前环筋/拉筋：</b>继承T057旧候选，仅供现阶段建模和几何检查；Task2最终规范配筋冻结后必须替换，不能把旧φ14@80/φ6直接写成最终设计。</p><p class="model-note">网页这里展示的是“当前可运行父模型”，不是Task2最终冻结配筋。最终纵筋、环筋、拉筋和保护层一旦闭合，应由同一生成脚本刷新网页与Abaqus输入，保证显示和求解模型一致。</p><p>${safe(rebarAudit.implementationOnlyNote)}</p><a href="${import.meta.env.BASE_URL}research/rebar-audit.json" target="_blank" rel="noopener">纵筋几何审计</a> · <a href="${repo}/blob/main/research/wind-tower/experiments/T070/README.md" target="_blank" rel="noopener">T070模型说明</a>`;
    host.querySelector('#pt-source')!.innerHTML=`<p><b>T070当前输入：</b>36个PT位置，每位置等效面积1120 mm²（8×140 mm²），输入中仍保留1280 MPa初始应力。</p><p><b>Task1已冻结的长期有效值：</b>σ<sub>pe</sub>=985.951363 MPa，η=0.7702745，有效总预应力Pe=39.753559 MN。</p><p class="model-note">因此T070是当前父模型，不是Task2最终长期工作模型。下一版CODE-DESIGN求解模型必须把PT长期工作应力更新为985.951363 MPa，且不得再次重复扣减预应力损失。</p><a href="${repo}/blob/main/research/wind-tower/experiments/T078/T078_PRESTRESS_DESIGN_REPORT.md" target="_blank" rel="noopener">Task1预应力闭合报告</a>`;
    const rna=data.rna;
    host.querySelector('#rna-details')!.innerHTML=`<p><b>完整外形层：</b><span class="badge done">DISPLAY</span> 原始Abaqus CAE导出的三片叶片、机舱与spinner/轮毂表面网格。</p><p><b>真正求解层：</b><span class="badge done">ACTIVE</span> R2空间等效RNA：MASS + 完整ROTARYI + 偏心CG + 塔顶6DOF耦合。</p><p><b>来源：</b>${safe(sourceRnaReport.source.nodes)} + ${safe(sourceRnaReport.source.elements)}。</p><p class="model-note">完整RNA外壳只是显示层；它不与R2等效RNA同时计质量、惯量或刚度。这样既能在线看到完整风机，又保持论文实际Abaqus求解路线严谨。</p><details open><summary>R2求解参数</summary><p>MASS ${rna ? Number(rna.mass).toLocaleString(undefined,{maximumFractionDigits:3}) : '—'} kg</p><p>CG ${rna?.rnaCg?.map((x:number)=>x.toFixed(6)).join(', ') || '—'} m</p><p>ROTARYI ${rna?.rotaryInertia?.map((x:number)=>Number(x).toExponential(6)).join(', ') || '—'}</p><p>Coupling: ${safe(rna?.coupling || '—')}</p></details>`;
  } catch(error) {
    if(alive) canvasHost.innerHTML=`<p role="alert">${safe(error)}。Pages 构建需先运行 scripts/read-abaqus.cjs；请查看 GitHub Actions 日志。</p>`;
  }
  return dispose;
}