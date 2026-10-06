import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const repo = 'https://github.com/g2066203208-beep/voxel-frontier';
const safe = (x: unknown) => String(x ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
export function researchPage() {
  return `<div class="page-heading"><div><div class="eyebrow">GITHUB RESEARCH</div><h1>从题目开始，建立证据链</h1><p>正式研究流程、问题与工程文件均由 GitHub 管理。论文正文和老师讨论原文不公开。</p></div><a class="button primary" href="${repo}/tree/main/research/wind-tower/workflow" target="_blank" rel="noopener">打开完整流程</a></div><section class="panel research-intro"><h2>本轮已开始逐章核查</h2><p>七章第一轮审查形成25项台账；127条文献已登记，书目身份与论断支持分别核查。优先处理摘要与第三章的36组重算状态矛盾、材料引用不完整、模型身份和载荷映射证据。</p><div class="research-links"><a class="button primary" href="${repo}/blob/main/research/wind-tower/audit/01-first-review.md" target="_blank" rel="noopener">逐章问题与文献对照</a><a class="button" href="${repo}/blob/main/research/wind-tower/audit/reference-records.json" target="_blank" rel="noopener">127条书目核查记录</a><a class="button" href="${import.meta.env.BASE_URL}research/reported-checks.json" target="_blank" rel="noopener">基础算术复核报告</a></div></section><section class="panel research-intro"><h2>10 MW级陆上风机预应力混凝土—钢混合塔架抗风性能与结构优化研究</h2><p>这是待证据支持的工作题目。先确认塔架身份、预应力建模、风环境、RNA 简化及约束，再决定是否保留“优化”等承诺。现有数值属于文稿报告值，不能作为独立验证结果。</p><div class="research-links">${[['00-title.md','01 · 逐词审查题目与研究问题'],['01-process.md','02 · 从立项到结论的完整流程'],['02-evidence.md','03 · 参数、证据与验收规则'],['03-cloud.md','04 · GitHub 云端执行与模型读取'],['04-literature.md','05 · 文献检索与核查记录']].map(([file,label])=>`<a class="button" href="${repo}/blob/main/research/wind-tower/workflow/${file}" target="_blank" rel="noopener">${label}</a>`).join('')}</div></section><section class="panel research-intro"><h2>当前阻塞与研究顺序</h2><ol><li>确认 158 m 与 SHOWTIME185 模型各自的用途，建立同一基准。</li><li>审查模型材料、预应力、连接、边界条件与 RNA 表征；修复缺失的 jobs 记录。</li><li>补齐气象原始数据、风场、载荷时程及求解结果，复核 36 组工况。</li><li>统一阻尼后重新判断控制工况；随后开展响应、疲劳及优化。</li></ol><p>每项完成必须关联输入哈希、脚本版本、运行记录及输出；缺少证据时保持待核查。</p><a href="${repo}/blob/main/research/wind-tower/discussion-issues.md" target="_blank" rel="noopener">查看老师指出的问题与工程排查清单</a></section><section class="panel research-intro"><h2>全程 GitHub 的工作入口</h2><p>修改正式流程请使用 GitHub 文件编辑器；运行模型读取使用 Actions；成果由 Pages 展示。左侧原有笔记模块仍是浏览器草稿，不会自动写入仓库。</p><div class="research-links"><a class="button" href="${repo}/edit/main/research/wind-tower/workflow/01-process.md" target="_blank" rel="noopener">在 GitHub 编辑流程</a><a class="button" href="${repo}/actions" target="_blank" rel="noopener">查看云端运行与检查</a><a class="button" href="${repo}/tree/main/research/wind-tower" target="_blank" rel="noopener">工程文件与版本</a></div></section>`;
}
export function engineeringPage() {
  const inp = repo + '/blob/main/research/wind-tower/experiments/T046/inputs/BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp';
  return `<div class="page-heading"><div><div class="eyebrow">ABAQUS / FINITE ELEMENT MODEL</div><h1>完整风机 Abaqus 模型在线查看</h1><p>默认展示此前保存的完整风机装配：158 m 混塔 + 三片完整叶片 + 机舱 + spinner/轮毂。RNA 几何直接来自原始 Abaqus CAE 导出的节点与表面单元；不再加载 T048 示意/候选 RNA。</p></div><a class="button primary" href="${repo}/blob/main/research/wind-tower/geometry/DTU158_TOWER_RNA_FULL_ASSEMBLY.step" target="_blank" rel="noopener">完整风机 STEP</a></div><div class="engineering-layout"><section class="panel viewer-panel"><div class="viewer-controls"><button class="button" id="model-reset">轴测</button><button class="button" id="model-front">正视</button><button class="button" id="model-side">侧视</button><button class="button" id="model-top">俯视</button><label><input type="checkbox" id="model-mesh" checked/> 外表面网格</label><label><input type="checkbox" id="model-transparent"/> 半透明</label><button class="button" id="model-rebar-check">钢筋检查</button><button class="button" id="model-rna-focus">聚焦完整 RNA</button><label><input type="checkbox" id="model-rna-legacy"/> 单CG简化对照</label><label><input type="checkbox" id="model-foundation" checked/> 等效基础固定面</label><label><input type="checkbox" id="model-isolate"/> 隔离选中</label><button class="button" id="model-png">导出 PNG</button></div><div id="model-canvas"><p id="model-loading" role="status">正在读取完整风机 Abaqus 网格…</p></div><p class="viewer-caption">拖动旋转 · 滚轮缩放 · 右键平移 · 点击实体可选中部件。叶片、机舱和 spinner/轮毂来自原始 Abaqus CAE 导出的实际表面网格；塔架来自当前混塔有限元输入。</p></section><aside class="panel model-details"><h2>完整风机装配</h2><div id="model-report" role="status">加载中…</div><h3>显示层</h3><div class="layer-grid" id="model-layers"><label><input type="checkbox" data-cat="concrete" checked/> 混凝土塔段</label><label><input type="checkbox" data-cat="steel" checked/> 钢塔段</label><label><input type="checkbox" data-cat="rebar" checked/> 普通纵向钢筋</label><label><input type="checkbox" data-cat="hoop" checked/> T046 环向钢筋候选</label><label><input type="checkbox" data-cat="tiebar"/> T046 拉筋候选</label><label><input type="checkbox" data-cat="prestress" checked/> 预应力筋</label><label><input type="checkbox" data-cat="joint" checked/> 接头弹簧</label><label><input type="checkbox" data-cat="rna-source" checked/> 完整 RNA（三叶片/机舱/spinner）</label></div><label>部件 / 实例 <select id="model-part"><option value="">全部部件</option></select></label><div id="part-details"></div><h3>完整 RNA 来源</h3><div id="rna-details" class="rna-details">加载中…</div><h3>纵筋几何审计</h3><div id="rebar-audit" class="rna-details">加载中…</div><h3>预应力PT来源状态</h3><div id="pt-source" class="rna-details">加载中…</div><h3>模型文件</h3><div class="research-links model-links"><a href="${repo}/blob/main/research/wind-tower/geometry/DTU158_TOWER_RNA_FULL_ASSEMBLY.step" target="_blank" rel="noopener">完整风机 STEP</a><a href="${repo}/blob/main/research/wind-tower/archive/local-large-assets-20261004/abaqus-dtu-models/DTU158_HybridTower_v29_RNA_DISTRIBUTED_OFFICIAL.cae" target="_blank" rel="noopener">完整 RNA CAE v29</a><a href="${repo}/blob/main/research/wind-tower/archive/local-large-assets-20261004/abaqus-dtu-models/DTU158_HybridTower_v28_RNA_DISTRIBUTED_OFFICIAL.cae" target="_blank" rel="noopener">完整 RNA CAE v28</a><a href="${inp}" target="_blank" rel="noopener">当前混塔 INP</a><a href="${import.meta.env.BASE_URL}research/source-rna-model-report.json" target="_blank" rel="noopener">RNA 网格报告</a></div></aside></div>`;
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
      visuals.push({name:g.name,category:'rna-source',kind:'surface',surface,wire,material:mat,info:{...g,displayRole:'原始 Abaqus RNA 表面网格（仅展示，不参与 T045 求解）'},baseOpacity:.82});
    }

    const t046Groups=[{name:'T046_CODE_HOOP',category:'hoop',positions:t046Overlay.hoop.positions,info:{nodes:0,elements:t046Overlay.hoop.elements,elementTypes:['T3D2'],displayRole:'规范推导的环向钢筋候选；不参与当前 T045 求解'}},{name:'T046_CODE_TIE',category:'tiebar',positions:t046Overlay.tie.positions,info:{nodes:0,elements:t046Overlay.tie.elements,elementTypes:['T3D2'],displayRole:'规范推导的拉筋候选；不参与当前 T045 求解'}}];
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
    const rnaLegacyCheck=host.querySelector<HTMLInputElement>('#model-rna-legacy')!;
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
      rnaGroup.visible=rnaLegacyCheck.checked && !rebarInspect;
      foundationGroup.visible=foundationCheck.checked;
      const v=visuals.find(x=>x.name===selected);
      host.querySelector('#part-details')!.textContent=v ? `${v.name} · ${v.info.nodes.toLocaleString()} 节点 · ${v.info.elements.toLocaleString()} 单元 · ${v.info.elementTypes.join(', ')}` : '点击模型或从下拉框选择实例；可配合“隔离选中”检查单段网格。';
    }
    select.onchange=updateVisibility; isolateCheck.onchange=updateVisibility; meshCheck.onchange=updateVisibility; transparentCheck.onchange=updateVisibility; rnaLegacyCheck.onchange=updateVisibility; foundationCheck.onchange=updateVisibility;
    rebarCheck.onclick=()=>{
      rebarInspect=!rebarInspect;
      rebarCheck.classList.toggle('primary',rebarInspect);
      rebarCheck.textContent=rebarInspect?'退出钢筋检查':'钢筋检查';
      if(rebarInspect){
        for(const x of catChecks) x.checked=x.dataset.cat==='concrete'||x.dataset.cat==='rebar'||x.dataset.cat==='hoop'||x.dataset.cat==='tiebar';
        rnaLegacyCheck.checked=false; isolateCheck.checked=false; select.value='';
      } else {
        for(const x of catChecks) x.checked=true;
        rnaLegacyCheck.checked=false;
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
      rnaLegacyCheck.checked=false; isolateCheck.checked=false; select.value='';
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
    host.querySelector('#model-report')!.innerHTML=`<p><strong>完整风机：</strong>158 m 混塔 + 原始完整 RNA。</p><p><strong>RNA 表面网格：</strong>${sourceRnaReport.counts.instances} 个实例 · ${sourceRnaReport.counts.nodes.toLocaleString()} 节点 · ${sourceRnaReport.counts.elements.toLocaleString()} 单元；其中叶片实例 ${bladeCount} 个、机舱实例 ${nacelleCount} 个、spinner/轮毂实例 ${spinnerCount} 个。</p><p><strong>塔架主体：</strong>${report.counts.instances} 个装配实例 · ${report.counts.solidElements.toLocaleString()} 个实体单元 · ${report.counts.lineElements.toLocaleString()} 个线单元。</p><p>完整 RNA 高度范围：${sourceRnaReport.bounds.min[1].toFixed(3)} ～ ${sourceRnaReport.bounds.max[1].toFixed(3)} m。</p><details><summary>RNA 导出证据</summary><code>${safe(sourceRnaReport.sha256)}</code><p>${safe(sourceRnaReport.source.nodes)}</p><p>${safe(sourceRnaReport.source.elements)}</p></details>`;
    host.querySelector('#rebar-audit')!.innerHTML=`<p><b>T045纵筋：</b><span class="badge done">PASS</span> 5440 根，31/31 Embedded，位置在筒壁内部。</p><p><b>T045环向筋/拉筋：</b><span class="badge">MISSING</span> 当前正式输入为 0；因此不能称完整钢筋网。</p><p><b>T046-E1候选：</b>φ14@80 mm 双层环向筋 + φ6 拉筋；新增质量约 <b>${(t046Report.candidate.totalAddedRebarMassKg/1000).toFixed(1)} t</b>，最不利配筋率 ${t046Report.candidate.providedWorstHoopRatioPercent.toFixed(3)}% ≥ ${t046Report.candidate.requiredWorstHoopRatioPercent.toFixed(3)}%。</p><p class="model-note">T046 是 GB50135/T/CEC5008/GB50010 推导候选，不冒充何泽瑜未公开的箍筋参数；尚未完成 Abaqus 求解，网页红色环筋/棕色拉筋是候选叠加层。</p><p>${safe(rebarAudit.implementationOnlyNote)}</p><a href="${import.meta.env.BASE_URL}research/rebar-audit.json" target="_blank" rel="noopener">纵筋逐段审计</a> · <a href="${import.meta.env.BASE_URL}research/t046-rebar-report.json" target="_blank" rel="noopener">T046配筋补全报告</a>`;
    const ptCurrent=ptTrace.variants.find((v:any)=>v.factor===1), ptB8=ptTrace.variants.find((v:any)=>v.factor===8);
    host.querySelector('#pt-source')!.innerHTML=`<p><b>CURRENT PT = 36 × 单股140 mm²</b><br/>T045名义总预应力：${(ptCurrent.totalNominalForceN/1e6).toFixed(4)} MN。</p><p><b>REF139同类工程：</b>36束×8股15.2 mm；据此生成B8敏感性候选，保持1280 MPa时名义总预应力 ${(ptB8.totalNominalForceN/1e6).toFixed(4)} MN。</p><p class="model-note">REF139不是本文158 m原型，不能直接把B8设为最终值；但它证明“36”很可能需要区分单股与多股束。r=1.75 m仍是重建参数，最终冻结前必须继续来源追溯/敏感性。</p><a href="${import.meta.env.BASE_URL}research/t047-pt-bundle-sensitivity.json" target="_blank" rel="noopener">打开PT来源与束系数报告</a>`;
    const rna=data.rna;
    host.querySelector('#rna-details')!.innerHTML=`<p><b>当前默认显示：</b><span class="badge done">FULL RNA</span> 原始 Abaqus CAE 导出的三片叶片、机舱与 spinner/轮毂表面网格。</p><p><b>来源：</b>${safe(sourceRnaReport.source.nodes)} + ${safe(sourceRnaReport.source.elements)}。</p><p><b>实例：</b>${rnaInstances.map((x:any)=>safe(x.name)).join('<br/>')}</p><p class="model-note">这里显示的是此前完整 RNA 的真实导出网格，不是我后加的 B31/T048 示意模型。单CG MASS+ROTARYI 仅保留为可选对照，默认关闭。</p><details><summary>单CG简化对照参数</summary><p>MASS ${rna ? Number(rna.mass).toLocaleString(undefined,{maximumFractionDigits:3}) : '—'} kg</p><p>CG ${rna?.rnaCg?.map((x:number)=>x.toFixed(6)).join(', ') || '—'} m</p></details>`;
  } catch(error) {
    if(alive) canvasHost.innerHTML=`<p role="alert">${safe(error)}。Pages 构建需先运行 scripts/read-abaqus.cjs；请查看 GitHub Actions 日志。</p>`;
  }
  return dispose;
}