import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const repo = 'https://github.com/g2066203208-beep/voxel-frontier';
const safe = (x: unknown) => String(x ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
export function researchPage() {
  return `<div class="page-heading"><div><div class="eyebrow">GITHUB RESEARCH</div><h1>从题目开始，建立证据链</h1><p>正式研究流程、问题与工程文件均由 GitHub 管理。论文正文和老师讨论原文不公开。</p></div><a class="button primary" href="${repo}/tree/main/research/wind-tower/workflow" target="_blank" rel="noopener">打开完整流程</a></div><section class="panel research-intro"><h2>本轮已开始逐章核查</h2><p>七章第一轮审查形成25项台账；127条文献已登记，书目身份与论断支持分别核查。优先处理摘要与第三章的36组重算状态矛盾、材料引用不完整、模型身份和载荷映射证据。</p><div class="research-links"><a class="button primary" href="${repo}/blob/main/research/wind-tower/audit/01-first-review.md" target="_blank" rel="noopener">逐章问题与文献对照</a><a class="button" href="${repo}/blob/main/research/wind-tower/audit/reference-records.json" target="_blank" rel="noopener">127条书目核查记录</a><a class="button" href="${import.meta.env.BASE_URL}research/reported-checks.json" target="_blank" rel="noopener">基础算术复核报告</a></div></section><section class="panel research-intro"><h2>10 MW级陆上风机预应力混凝土—钢混合塔架抗风性能与结构优化研究</h2><p>这是待证据支持的工作题目。先确认塔架身份、预应力建模、风环境、RNA 简化及约束，再决定是否保留“优化”等承诺。现有数值属于文稿报告值，不能作为独立验证结果。</p><div class="research-links">${[['00-title.md','01 · 逐词审查题目与研究问题'],['01-process.md','02 · 从立项到结论的完整流程'],['02-evidence.md','03 · 参数、证据与验收规则'],['03-cloud.md','04 · GitHub 云端执行与模型读取'],['04-literature.md','05 · 文献检索与核查记录']].map(([file,label])=>`<a class="button" href="${repo}/blob/main/research/wind-tower/workflow/${file}" target="_blank" rel="noopener">${label}</a>`).join('')}</div></section><section class="panel research-intro"><h2>当前阻塞与研究顺序</h2><ol><li>确认 158 m 与 SHOWTIME185 模型各自的用途，建立同一基准。</li><li>审查模型材料、预应力、连接、边界条件与 RNA 表征；修复缺失的 jobs 记录。</li><li>补齐气象原始数据、风场、载荷时程及求解结果，复核 36 组工况。</li><li>统一阻尼后重新判断控制工况；随后开展响应、疲劳及优化。</li></ol><p>每项完成必须关联输入哈希、脚本版本、运行记录及输出；缺少证据时保持待核查。</p><a href="${repo}/blob/main/research/wind-tower/discussion-issues.md" target="_blank" rel="noopener">查看老师指出的问题与工程排查清单</a></section><section class="panel research-intro"><h2>全程 GitHub 的工作入口</h2><p>修改正式流程请使用 GitHub 文件编辑器；运行模型读取使用 Actions；成果由 Pages 展示。左侧原有笔记模块仍是浏览器草稿，不会自动写入仓库。</p><div class="research-links"><a class="button" href="${repo}/edit/main/research/wind-tower/workflow/01-process.md" target="_blank" rel="noopener">在 GitHub 编辑流程</a><a class="button" href="${repo}/actions" target="_blank" rel="noopener">查看云端运行与检查</a><a class="button" href="${repo}/tree/main/research/wind-tower" target="_blank" rel="noopener">工程文件与版本</a></div></section>`;
}
export function engineeringPage() {
  return `<div class="page-heading"><div><div class="eyebrow">ENGINEERING / SOURCE GEOMETRY</div><h1>工程模型读取与检查</h1><p>从仓库 STEP 实际读取生成，单位为米。可选择部件、检查网格并导出视图。</p></div><a class="button" href="${repo}/actions" target="_blank" rel="noopener">云端读取记录</a></div><div class="engineering-layout"><section class="panel viewer-panel"><div class="viewer-controls"><button class="button" id="model-reset">恢复视角</button><label><input type="checkbox" id="model-wire"/> 线框</label><label><input type="checkbox" id="model-isolate"/> 隔离选中部件</label><button class="button" id="model-png">导出 PNG</button></div><div id="model-canvas"><p id="model-loading" role="status">正在读取云端几何成果…</p></div><p class="viewer-caption">拖动旋转 · 滚轮缩放 · 右键平移。该视图表示 CAD 几何，不表示应力或有限元验证结果。</p></section><aside class="panel model-details"><h2>原始文件与读取结果</h2><div id="model-report" role="status">加载中…</div><label>部件 <select id="model-part"><option value="">全部部件</option></select></label><div id="part-details"></div><h3>CAE 元数据检查</h3><p>读取先前提取的审计文件；未实现专有 CAE 二进制的完整解码。</p><button class="button" id="audit-showtime">SHOWTIME185</button><pre id="audit-result">选择模型查看材料、步骤与网格数量。</pre></aside></div>`;
}
export async function mountEngineering(host: HTMLElement): Promise<()=>void> {
  let alive = true, frame = 0; const controller = new AbortController();
  let renderer: THREE.WebGLRenderer | undefined, controls: OrbitControls | undefined;
  const geometries: THREE.BufferGeometry[] = [], materials: THREE.MeshStandardMaterial[] = [];
  const dispose = () => { alive=false; controller.abort(); cancelAnimationFrame(frame); controls?.dispose(); geometries.forEach(g=>g.dispose()); materials.forEach(m=>m.dispose()); renderer?.dispose(); resizeObserver.disconnect(); };
  const canvasHost = host.querySelector<HTMLElement>('#model-canvas')!;
  const resizeObserver = new ResizeObserver(()=>resize());
  let camera: THREE.PerspectiveCamera;
  function resize() { if(!renderer || !camera) return; const w=canvasHost.clientWidth,h=canvasHost.clientHeight; camera.aspect=w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h); }
  async function json(file:string,gzip=false) {
    const response = await fetch(`${import.meta.env.BASE_URL}research/${file}`,{signal:controller.signal});
    if(!response.ok) throw Error(`读取失败 HTTP ${response.status}`);
    // Fetch already decodes HTTP Content-Encoding; Pages may instead serve a raw gzip file.
    if(gzip && !response.headers.get('Content-Encoding')?.includes('gzip')) return JSON.parse(await new Response(response.body!.pipeThrough(new DecompressionStream('gzip'))).text());
    return response.json();
  }
  try {
    const [data, report] = await Promise.all([json('geometry.json.gz',true),json('geometry-report.json')]);
    if(!alive || !canvasHost.isConnected) { dispose(); return dispose; }
    const scene=new THREE.Scene(); scene.background=new THREE.Color('#e9eeea'); scene.add(new THREE.HemisphereLight(0xffffff,0x596d64,2.7));
    const light=new THREE.DirectionalLight(0xffffff,3); light.position.set(80,100,100); scene.add(light);
    const group=new THREE.Group(); scene.add(group);
    const meshes:THREE.Mesh[]=[];
    for(const part of data.meshes) {
      const geometry=new THREE.BufferGeometry(); geometry.setAttribute('position',new THREE.Float32BufferAttribute(part.attributes.position.array,3)); geometry.setIndex(part.index.array);
      if(part.attributes.normal) geometry.setAttribute('normal',new THREE.Float32BufferAttribute(part.attributes.normal.array,3)); else geometry.computeVertexNormals();
      const color=part.color ? new THREE.Color(...part.color as [number,number,number]) : new THREE.Color('#b5c8c1');
      const material=new THREE.MeshStandardMaterial({color,roughness:.65,metalness:.15,side:THREE.DoubleSide});
      const mesh=new THREE.Mesh(geometry,material); group.add(mesh); meshes.push(mesh); geometries.push(geometry); materials.push(material);
    }
    const bounds=new THREE.Box3().setFromObject(group),center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3());
    camera=new THREE.PerspectiveCamera(35,1,.000001,10000); camera.up.set(0,1,0);
    renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); canvasHost.replaceChildren(renderer.domElement);
    controls=new OrbitControls(camera,renderer.domElement); controls.enableDamping=true;
    function reset(){ const distance=Math.max(size.x,size.y,size.z)*1.6; camera.position.copy(center).add(new THREE.Vector3(distance*.6,distance*.18,distance)); controls!.target.copy(center); controls!.update(); }
    reset(); resizeObserver.observe(canvasHost); resize();
    const tick=()=>{if(!alive)return; controls!.update(); renderer!.render(scene,camera); frame=requestAnimationFrame(tick);}; tick();
    const select=host.querySelector<HTMLSelectElement>('#model-part')!;
    select.innerHTML='<option value="">全部部件</option>'+report.parts.map((p:any)=>`<option value="${p.id}">${safe(p.name)}</option>`).join('');
    host.querySelector('#model-report')!.innerHTML=`<p><strong>${report.parts.length}</strong> 部件 · <strong>${report.triangles.toLocaleString()}</strong> 三角面</p><p>包围盒尺寸：${report.dimensions.map((v:number)=>v.toFixed(3)).join(' × ')} m</p><p>非有限数：${report.checks.nonfinite} · 越界索引：${report.checks.invalidIndices} · 退化面：${report.checks.degenerate}</p><details><summary>来源与 SHA-256</summary><code>${safe(report.sha256)}</code><p>${safe(report.source)}</p><p>弦偏差 ${report.parameters.linearDeflection} m；读取器 ${safe(report.reader)} ${safe(report.readerVersion)}</p></details>`;
    if(report.warnings?.length) { const warning=document.createElement('p');warning.className='model-warning';warning.textContent='单位冲突待核查：STEP声明毫米，读取后装配最大尺寸不足1 m，与百米级塔架不符。尚未自动修正比例。';host.querySelector('#model-report')!.prepend(warning); }
    const download=document.createElement('a');download.href=`${import.meta.env.BASE_URL}research/geometry-report.json`;download.target='_blank';download.rel='noopener';download.textContent='打开完整读取与检查报告';host.querySelector('#model-report')!.append(download);
    function selection(){const id=select.value===''?-1:Number(select.value),isolate=host.querySelector<HTMLInputElement>('#model-isolate')!.checked; meshes.forEach((mesh,i)=>{mesh.visible=!isolate||id===-1||i===id; materials[i].emissive.set(i===id?0x334f25:0);}); const part=report.parts[id]; host.querySelector('#part-details')!.textContent=part?`${part.name} · ${part.vertices} 顶点 · ${part.triangles} 三角面`:'';}
    select.onchange=selection; host.querySelector<HTMLInputElement>('#model-isolate')!.onchange=selection;
    host.querySelector<HTMLInputElement>('#model-wire')!.onchange=e=>materials.forEach(m=>m.wireframe=(e.target as HTMLInputElement).checked);
    host.querySelector<HTMLButtonElement>('#model-reset')!.onclick=reset;
    host.querySelector<HTMLButtonElement>('#model-png')!.onclick=()=>{renderer!.render(scene,camera); const link=document.createElement('a'); link.download='DTU158-CAD-geometry.png';link.href=renderer!.domElement.toDataURL('image/png');link.click();};
    const audit=async(name:string)=>{const target=host.querySelector('#audit-result')!; target.textContent='读取审计元数据…';try{const audit=await json(`${name}.cae.audit.json.gz`,true); if(!alive)return;target.textContent=JSON.stringify(audit.models ? Object.fromEntries(Object.entries(audit.models).map(([key,value])=>{const m=value as any;return[key,{parts:Object.keys(m.parts??{}).length,instances:Object.keys(m.instances??{}).length,nodes:Object.values(m.parts??{}).reduce((n:number,p:any)=>n+(p.nodes??0),0),elements:Object.values(m.parts??{}).reduce((n:number,p:any)=>n+(p.elements??0),0),materials:m.materials,steps:m.steps}];})) : audit,null,2)+(audit.error?`\n读取错误：${audit.error}`:'');}catch(e){if(alive)target.textContent=String(e);}};
    host.querySelector<HTMLButtonElement>('#audit-showtime')!.onclick=()=>void audit('SHOWTIME185_V167_MAINLEG_CALIBRATED_VALIDATED');
  } catch(error) { if(alive) canvasHost.innerHTML=`<p role="alert">${safe(error)}。请查看 GitHub Actions 的模型读取日志。</p>`; }
  return dispose;
}
