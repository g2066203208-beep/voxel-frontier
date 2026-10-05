import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const repo = 'https://github.com/g2066203208-beep/voxel-frontier';
const safe = (x: unknown) => String(x ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
export function researchPage() {
  return `<div class="page-heading"><div><div class="eyebrow">GITHUB RESEARCH</div><h1>从题目开始，建立证据链</h1><p>正式研究流程、问题与工程文件均由 GitHub 管理。论文正文和老师讨论原文不公开。</p></div><a class="button primary" href="${repo}/tree/main/research/wind-tower/workflow" target="_blank" rel="noopener">打开完整流程</a></div><section class="panel research-intro"><h2>本轮已开始逐章核查</h2><p>七章第一轮审查形成25项台账；127条文献已登记，书目身份与论断支持分别核查。优先处理摘要与第三章的36组重算状态矛盾、材料引用不完整、模型身份和载荷映射证据。</p><div class="research-links"><a class="button primary" href="${repo}/blob/main/research/wind-tower/audit/01-first-review.md" target="_blank" rel="noopener">逐章问题与文献对照</a><a class="button" href="${repo}/blob/main/research/wind-tower/audit/reference-records.json" target="_blank" rel="noopener">127条书目核查记录</a><a class="button" href="${import.meta.env.BASE_URL}research/reported-checks.json" target="_blank" rel="noopener">基础算术复核报告</a></div></section><section class="panel research-intro"><h2>10 MW级陆上风机预应力混凝土—钢混合塔架抗风性能与结构优化研究</h2><p>这是待证据支持的工作题目。先确认塔架身份、预应力建模、风环境、RNA 简化及约束，再决定是否保留“优化”等承诺。现有数值属于文稿报告值，不能作为独立验证结果。</p><div class="research-links">${[['00-title.md','01 · 逐词审查题目与研究问题'],['01-process.md','02 · 从立项到结论的完整流程'],['02-evidence.md','03 · 参数、证据与验收规则'],['03-cloud.md','04 · GitHub 云端执行与模型读取'],['04-literature.md','05 · 文献检索与核查记录']].map(([file,label])=>`<a class="button" href="${repo}/blob/main/research/wind-tower/workflow/${file}" target="_blank" rel="noopener">${label}</a>`).join('')}</div></section><section class="panel research-intro"><h2>当前阻塞与研究顺序</h2><ol><li>确认 158 m 与 SHOWTIME185 模型各自的用途，建立同一基准。</li><li>审查模型材料、预应力、连接、边界条件与 RNA 表征；修复缺失的 jobs 记录。</li><li>补齐气象原始数据、风场、载荷时程及求解结果，复核 36 组工况。</li><li>统一阻尼后重新判断控制工况；随后开展响应、疲劳及优化。</li></ol><p>每项完成必须关联输入哈希、脚本版本、运行记录及输出；缺少证据时保持待核查。</p><a href="${repo}/blob/main/research/wind-tower/discussion-issues.md" target="_blank" rel="noopener">查看老师指出的问题与工程排查清单</a></section><section class="panel research-intro"><h2>全程 GitHub 的工作入口</h2><p>修改正式流程请使用 GitHub 文件编辑器；运行模型读取使用 Actions；成果由 Pages 展示。左侧原有笔记模块仍是浏览器草稿，不会自动写入仓库。</p><div class="research-links"><a class="button" href="${repo}/edit/main/research/wind-tower/workflow/01-process.md" target="_blank" rel="noopener">在 GitHub 编辑流程</a><a class="button" href="${repo}/actions" target="_blank" rel="noopener">查看云端运行与检查</a><a class="button" href="${repo}/tree/main/research/wind-tower" target="_blank" rel="noopener">工程文件与版本</a></div></section>`;
}
export function engineeringPage() {
  const inp = repo + '/blob/main/research/wind-tower/experiments/T045/inputs/BASE001_CANDIDATE_M2_R2RNA_O158_CLEAN.inp';
  return `<div class="page-heading"><div><div class="eyebrow">ABAQUS / FINITE ELEMENT MODEL</div><h1>Abaqus 有限元模型在线查看</h1><p>直接从当前 T045 首选 .inp 输入文件生成。显示的是未变形有限元网格、钢筋/预应力筋、接头以及 RNA 等效质量—转动惯量位置，不是 CAD 外观替代图。</p></div><a class="button primary" href="${inp}" target="_blank" rel="noopener">打开当前 Abaqus INP</a></div><div class="engineering-layout"><section class="panel viewer-panel"><div class="viewer-controls"><button class="button" id="model-reset">轴测</button><button class="button" id="model-front">正视</button><button class="button" id="model-side">侧视</button><button class="button" id="model-top">俯视</button><label><input type="checkbox" id="model-mesh" checked/> 外表面网格</label><label><input type="checkbox" id="model-transparent"/> 半透明</label><label><input type="checkbox" id="model-rna" checked/> RNA 等效点</label><label><input type="checkbox" id="model-isolate"/> 隔离选中</label><button class="button" id="model-png">导出 PNG</button></div><div id="model-canvas"><p id="model-loading" role="status">正在从 GitHub 构建的 Abaqus 网格成果读取模型…</p></div><p class="viewer-caption">拖动旋转 · 滚轮缩放 · 右键平移 · 点击实体可选中部件。该视图由 Abaqus 输入文件的节点与单元直接生成；当前仅显示未变形网格，不代表 ODB 应力/位移结果。</p></section><aside class="panel model-details"><h2>当前计算模型</h2><div id="model-report" role="status">加载中…</div><h3>显示层</h3><div class="layer-grid" id="model-layers"><label><input type="checkbox" data-cat="concrete" checked/> 混凝土塔段</label><label><input type="checkbox" data-cat="steel" checked/> 钢塔段</label><label><input type="checkbox" data-cat="rebar" checked/> 普通钢筋</label><label><input type="checkbox" data-cat="prestress" checked/> 预应力筋</label><label><input type="checkbox" data-cat="joint" checked/> 接头弹簧</label><label><input type="checkbox" data-cat="rna-source" checked/> 原始 RNA 表面网格（展示）</label></div><label>部件 / 实例 <select id="model-part"><option value="">全部部件</option></select></label><div id="part-details"></div><h3>RNA 等效算子</h3><div id="rna-details" class="rna-details">加载中…</div><h3>模型身份</h3><div class="research-links model-links"><a href="${inp}" target="_blank" rel="noopener">T045 首选 INP</a><a href="${repo}/blob/main/research/wind-tower/experiments/T045/RESEARCH_CARD.md" target="_blank" rel="noopener">T045 研究卡</a><a href="${import.meta.env.BASE_URL}research/abaqus-model-report.json" target="_blank" rel="noopener">解析报告 JSON</a></div></aside></div>`;
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
    const [data, report, sourceRna, sourceRnaReport] = await Promise.all([json('abaqus-model.json.gz',true),json('abaqus-model-report.json'),json('source-rna-model.json.gz',true),json('source-rna-model-report.json')]);
    if(!alive || !canvasHost.isConnected) { dispose(); return dispose; }

    const scene=new THREE.Scene();
    scene.background=new THREE.Color('#edf1ef');
    scene.add(new THREE.HemisphereLight(0xffffff,0x5b6660,2.5));
    const light=new THREE.DirectionalLight(0xffffff,3.2); light.position.set(80,180,120); scene.add(light);
    const root=new THREE.Group(); scene.add(root);

    const categoryColor:Record<string,string>={concrete:'#b9b7ae',steel:'#5f7896',rebar:'#725747',prestress:'#d69a3b',joint:'#8b63a5','rna-source':'#4f9688',other:'#7b8881'};
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

    const rnaGroup=new THREE.Group(); scene.add(rnaGroup);
    const markerMaterialTop=new THREE.MeshStandardMaterial({color:'#355d7a',roughness:.35}); materials.push(markerMaterialTop);
    const markerMaterialCg=new THREE.MeshStandardMaterial({color:'#b56d2a',roughness:.35}); materials.push(markerMaterialCg);
    const markerGeometryTop=new THREE.SphereGeometry(.55,24,16), markerGeometryCg=new THREE.SphereGeometry(.75,24,16); geometries.push(markerGeometryTop,markerGeometryCg);
    if(data.rna?.towerTop) {
      const m=new THREE.Mesh(markerGeometryTop,markerMaterialTop); m.position.fromArray(data.rna.towerTop); rnaGroup.add(m);
    }
    if(data.rna?.rnaCg) {
      const m=new THREE.Mesh(markerGeometryCg,markerMaterialCg); m.position.fromArray(data.rna.rnaCg); rnaGroup.add(m);
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
    const rnaCheck=host.querySelector<HTMLInputElement>('#model-rna')!;
    function updateVisibility() {
      const selected=select.value, isolate=isolateCheck.checked;
      const enabled=new Set(catChecks.filter(x=>x.checked).map(x=>x.dataset.cat));
      for(const v of visuals) {
        const base=enabled.has(v.category) && (!isolate || !selected || v.name===selected);
        if(v.surface) v.surface.visible=base;
        if(v.wire) v.wire.visible=base && meshCheck.checked;
        if(v.line) v.line.visible=base;
        if(v.material) {
          v.material.opacity=transparentCheck.checked ? .28 : (v.baseOpacity ?? 1);
          v.material.emissive.set(v.name===selected ? 0x273b20 : 0x000000);
        }
      }
      rnaGroup.visible=rnaCheck.checked;
      const v=visuals.find(x=>x.name===selected);
      host.querySelector('#part-details')!.textContent=v ? `${v.name} · ${v.info.nodes.toLocaleString()} 节点 · ${v.info.elements.toLocaleString()} 单元 · ${v.info.elementTypes.join(', ')}` : '点击模型或从下拉框选择实例；可配合“隔离选中”检查单段网格。';
    }
    select.onchange=updateVisibility; isolateCheck.onchange=updateVisibility; meshCheck.onchange=updateVisibility; transparentCheck.onchange=updateVisibility; rnaCheck.onchange=updateVisibility;
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
    host.querySelector<HTMLButtonElement>('#model-png')!.onclick=()=>{
      renderer!.render(scene,camera);
      const link=document.createElement('a');link.download='DTU158-T045-Abaqus-FE.png';link.href=renderer!.domElement.toDataURL('image/png');link.click();
    };

    host.querySelector('#model-report')!.innerHTML=`<p><strong>T045 当前计算模型：</strong>${report.counts.instances} 个装配实例 · ${report.counts.solidElements.toLocaleString()} 个实体单元 · ${report.counts.lineElements.toLocaleString()} 个线单元</p><p><strong>整机 RNA 展示层：</strong>${sourceRnaReport.counts.instances} 个原始 Abaqus 表面网格实例 · ${sourceRnaReport.counts.nodes.toLocaleString()} 节点 · ${sourceRnaReport.counts.elements.toLocaleString()} 单元</p><p>当前计算塔架高度范围：${report.bounds.min[1].toFixed(3)} ～ ${report.bounds.max[1].toFixed(3)} m；源 RNA 展示范围：${sourceRnaReport.bounds.min[1].toFixed(3)} ～ ${sourceRnaReport.bounds.max[1].toFixed(3)} m</p><p>计算模型元素类型：${report.elementTypes.join(' / ')}</p><details><summary>当前 INP 与 SHA-256</summary><code>${safe(report.sha256)}</code><p>${safe(report.source)}</p></details><details><summary>源 RNA 网格证据</summary><code>${safe(sourceRnaReport.sha256)}</code><p>${safe(sourceRnaReport.source.nodes)}</p><p>${safe(sourceRnaReport.source.elements)}</p></details>`;
    const rna=data.rna;
    host.querySelector('#rna-details')!.innerHTML=rna ? `<p><b>塔顶公共点 O</b><br/>${rna.towerTop?.map((x:number)=>x.toFixed(6)).join(', ') || '—'} m</p><p><b>RNA 质心 G</b><br/>${rna.rnaCg?.map((x:number)=>x.toFixed(6)).join(', ') || '—'} m</p><p><b>MASS</b> ${Number(rna.mass).toLocaleString(undefined,{maximumFractionDigits:3})} kg</p><p><b>ROTARYI</b><br/>${rna.rotaryInertia?.map((x:number)=>Number(x).toExponential(5)).join('<br/>') || '—'}</p><p class="model-note">网页中的两个球仅是 O 与 G 的符号标记；真实计算仍由 INP 中 MASS + ROTARYI + 6DOF 偏心耦合承担。页面同时叠加原始 Abaqus RNA 表面网格，以便整机查看，但该 RNA 表面网格不参与当前 T045 求解。</p>` : '<p>未找到 RNA 等效算子。</p>';
  } catch(error) {
    if(alive) canvasHost.innerHTML=`<p role="alert">${safe(error)}。Pages 构建需先运行 scripts/read-abaqus.cjs；请查看 GitHub Actions 日志。</p>`;
  }
  return dispose;
}
