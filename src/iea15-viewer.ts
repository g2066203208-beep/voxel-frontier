import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import './iea15-viewer.css';

/**
 * This viewer displays UNCHANGED official IEA Wind Task 37 STL geometry,
 * extracted in-memory from the exact upstream ZIP binaries.
 * No wind turbine mesh is generated, estimated, redrawn or assembled here.
 */
type MeshRecord={key:string;label:string;file:string;description:string};
const MODELS:MeshRecord[]=[
 {key:'fixed',label:'官方整机 · 单桩式',file:'IEA-15-240-RWT.stl.zip',description:'官方 OpenSCAD 原始整机STL（固定式）'},
 {key:'floating',label:'官方整机 · 半潜式',file:'IEA-15-240-RWT_VolturnUS-S.stl.zip',description:'官方 OpenSCAD 原始整机STL（UMaine浮式）'},
 {key:'blade',label:'官方叶片',file:'IEA-15-240-RWT_blade.stl.zip',description:'官方叶片STL原网格'},
 {key:'tower',label:'官方塔筒',file:'IEA-15-240-RWT_tower.stl.zip',description:'官方塔筒STL原网格'},
 {key:'monopile',label:'官方单桩',file:'IEA-15-240-RWT_monopile.stl.zip',description:'官方单桩STL原网格'},
 {key:'floater',label:'官方浮式基础',file:'IEA-15-240-RWT_VolturnUS-S_floater.stl.zip',description:'官方浮式基础STL原网格'},
];
const OFFICIAL_CAD='https://github.com/IEAWindSystems/IEA-15-240-RWT/tree/master/CAD';
const SELF_CAD='https://github.com/g2066203208-beep/voxel-frontier/tree/main/research/wind-tower/references/reference-models-20261008/IEA15_original_CAD';
const MANIFEST='https://github.com/g2066203208-beep/voxel-frontier/blob/main/research/wind-tower/references/reference-models-20261008/IEA15_ORIGINAL_CAD_ARCHIVE_MANIFEST.tsv';
const root=document.querySelector<HTMLElement>('#iea15-app');
if(!root)throw new Error('页面容器缺失');
root.innerHTML=
 '<header class="topbar"><a href="./" class="return">← 返回论文工作室</a><div class="identity"><div class="identity-kicker">IEA WIND TASK 37 · ORIGINAL CAD FILES</div><h1>IEA 15 MW <span>官方原始模型</span></h1></div><a class="source-head" href="'+OFFICIAL_CAD+'" target="_blank" rel="noopener">查看官方CAD原始仓库 ↗</a></header>'+
 '<main class="viewer-layout"><section class="stage"><div class="stage-top"><div class="stage-label"><span class="live-dot"></span> 官方STL原网格 · 在线查看</div><span class="stage-pill">非重新建模 · 非有限元验证</span></div><div class="viewport" id="viewport"><div class="viewport-hint">拖动旋转 · 滚轮缩放 · 右键平移<br>手机单指旋转、双指缩放</div></div><div class="stage-bottom"><div class="view-buttons"><button data-view="iso">三维</button><button data-view="front">正面</button><button data-view="side">侧面</button><button data-view="top">俯视</button><button id="snapshot">导出模型截图</button></div><div id="viewer-status" role="status">准备载入官方STL文件…</div></div></section>'+
 '<aside class="panel"><div class="panel-head"><span class="eyebrow">SOURCE FILE VIEWER</span><h2>官方原始几何</h2><p>网页直接读取官方仓库发布的 STL ZIP。没有根据OpenFAST参数重新绘制叶片、塔筒或机舱。</p></div>'+
 '<div class="section-title">选择官方模型文件</div><div class="model-picker"><select id="model-kind" aria-label="选择官方原始模型">'+MODELS.map(m=>'<option value="'+m.key+'">'+m.label+'</option>').join('')+'</select><button id="load-model">载入原始网格</button></div>'+
 '<div class="selection" id="file-meta"><div class="selection-tag">FILE IDENTITY</div><h3>正在准备官方整机</h3><p>官方原始网格会被逐三角面读取，不生成替代模型。</p></div>'+
 '<div class="section-title">显示选项</div><div class="switch-row"><label><input type="checkbox" id="wire"> 显示原网格线</label><label><input type="checkbox" id="turntable"> 自动旋转视角</label></div>'+
 '<div class="source-box"><b>官方原始模型下载</b><p>原仓库标为 deprecated 的 SolidWorks 和叶片STEP是旧版原始CAD，需留意发布说明。OpenSCAD发布的是几何外表面STL，不是Abaqus CAE、实体结构网格或材料正确性证明。</p><div class="refs"><a href="'+SELF_CAD+'" target="_blank" rel="noopener">本仓库SolidWorks/STEP ↗</a><a href="'+OFFICIAL_CAD+'" target="_blank" rel="noopener">官方CAD目录 ↗</a><a href="'+MANIFEST+'" target="_blank" rel="noopener">原文件校验清单 ↗</a></div></div>'+
 '<div class="source-box"><b>论文使用边界</b><p>本网页只用于查看 IEA 15 MW 官方原始几何。不能将其误称为158 m混合塔架，也不能作为Abaqus精细模型已经通过验证的证据。</p></div></aside></main>'+
 '<footer class="page-footer">IEA Wind Task 37 原始几何版权及开源许可见官方仓库 LICENSE。页面代码只负责文件解压、三维渲染和交互；从不自行生成风机部件。</footer>';

const element=<T extends HTMLElement>(selector:string):T=>{
 const node=document.querySelector<T>(selector);if(!node)throw new Error('UI element missing: '+selector);return node;
};
const viewport=element<HTMLDivElement>('#viewport');
const status=element<HTMLElement>('#viewer-status');
const meta=element<HTMLElement>('#file-meta');
const selector=element<HTMLSelectElement>('#model-kind');
const loadButton=element<HTMLButtonElement>('#load-model');
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x152330);
scene.add(new THREE.HemisphereLight(0xf4f7ff,0x526679,2.8));
const key=new THREE.DirectionalLight(0xffffff,2.9);key.position.set(1.5,4,6);scene.add(key);
const back=new THREE.DirectionalLight(0xb3d9e8,1.5);back.position.set(-5,2,-3);scene.add(back);
const camera=new THREE.PerspectiveCamera(42,1,.01,1e7);
camera.position.set(200,140,260);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.5;
viewport.prepend(renderer.domElement);
const control=new OrbitControls(camera,renderer.domElement);
control.enableDamping=true;
control.dampingFactor=.07;
control.minDistance=.01;
control.maxDistance=1e7;
const STL_MATERIAL=new THREE.MeshStandardMaterial({color:0xd5e4e9,metalness:.43,roughness:.49,side:THREE.DoubleSide});
let mesh:THREE.Mesh|undefined;
let bounds=new THREE.Box3();
let radius=200;
let center=new THREE.Vector3();
let lastType='';
function resize(){
 const w=Math.max(viewport.clientWidth,200),h=Math.max(viewport.clientHeight,250);
 camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);
}
new ResizeObserver(resize).observe(viewport);resize();
renderer.setAnimationLoop(()=>{
 control.update();renderer.render(scene,camera);
});
function positionCamera(kind:string){
 if(!mesh)return;
 control.target.copy(center);
 const length=radius*2.9;
 camera.up.set(0,1,0);
 if(kind==='front')camera.position.copy(center).add(new THREE.Vector3(0,0,length));
 else if(kind==='side')camera.position.copy(center).add(new THREE.Vector3(length,0,0));
 else if(kind==='top')camera.position.copy(center).add(new THREE.Vector3(.001,length,.001));
 else camera.position.copy(center).add(new THREE.Vector3(length*.88,length*.48,length*.86));
 camera.near=Math.max(radius*.00008,.01);
 camera.far=Math.max(radius*75,1000);
 camera.updateProjectionMatrix();
 camera.lookAt(center);control.minDistance=radius*.03;control.maxDistance=radius*30;control.update();
}
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(el=>el.addEventListener('click',()=>positionCamera(el.dataset.view||'iso')));
element<HTMLInputElement>('#wire').addEventListener('change',e=>{STL_MATERIAL.wireframe=(e.currentTarget as HTMLInputElement).checked;STL_MATERIAL.needsUpdate=true;});
element<HTMLInputElement>('#turntable').addEventListener('change',e=>{control.autoRotate=(e.currentTarget as HTMLInputElement).checked;control.autoRotateSpeed=.65;});
element<HTMLButtonElement>('#snapshot').addEventListener('click',()=>{
 if(!mesh)return;
 renderer.render(scene,camera);const link=document.createElement('a');link.href=renderer.domElement.toDataURL('image/png');
 link.download='IEA15_original_official_STL_'+lastType+'.png';link.click();
});
function findEOCD(data:DataView):number{
 const last=data.byteLength-22,min=Math.max(0,data.byteLength-65557);
 for(let pos=last;pos>=min;pos--)if(data.getUint32(pos,true)===0x06054b50)return pos;
 throw Error('官方 ZIP 缺少中央目录结束记录');
}
async function extractOfficialSTL(archive:ArrayBuffer):Promise<{name:string;data:ArrayBuffer}>{
 const view=new DataView(archive),bytes=new Uint8Array(archive);
 const end=findEOCD(view);
 const files=view.getUint16(end+10,true),centralOffset=view.getUint32(end+16,true);
 let ptr=centralOffset;
 for(let i=0;i<files;i++){
  if(view.getUint32(ptr,true)!==0x02014b50)throw Error('官方 ZIP 中央目录损坏');
  const method=view.getUint16(ptr+10,true);
  const compressed=view.getUint32(ptr+20,true),uncompressed=view.getUint32(ptr+24,true);
  const fn=view.getUint16(ptr+28,true),extra=view.getUint16(ptr+30,true),comment=view.getUint16(ptr+32,true);
  const local=view.getUint32(ptr+42,true);
  const name=new TextDecoder().decode(bytes.subarray(ptr+46,ptr+46+fn));
  if(name.toLowerCase().endsWith('.stl')){
   if(uncompressed>450_000_000)throw Error('原始STL超过450MB，当前设备内存不适合直接预览；请使用本仓库下载原文件');
   if(view.getUint32(local,true)!==0x04034b50)throw Error('原始STL ZIP局部文件头异常');
   const dataStart=local+30+view.getUint16(local+26,true)+view.getUint16(local+28,true);
   const packed=archive.slice(dataStart,dataStart+compressed);
   let expanded:ArrayBuffer;
   if(method===0)expanded=packed;
   else if(method===8){
    if(typeof DecompressionStream==='undefined')throw Error('浏览器不支持ZIP解压，建议使用最新版Chrome或Edge');
    const stream=new Blob([packed]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    expanded=await new Response(stream).arrayBuffer();
   }else throw Error('未知ZIP压缩格式 '+method);
   if(expanded.byteLength!==uncompressed)throw Error('STL解压长度与官方ZIP索引不一致');
   return {name,data:expanded};
  }
  ptr+=46+fn+extra+comment;
 }
 throw Error('官方 ZIP 没有 STL 文件');
}
function failure(error:unknown,m:MeshRecord){
 const message=error instanceof Error?error.message:String(error);
 status.textContent='无法载入该原始文件';
 meta.innerHTML='<div class="selection-tag">SOURCE FILE NOT LOADED</div><h3>未展示任何替代模型</h3><p>'+message.replace(/[&<>]/g,'')+'</p>'+
 '<p><a target="_blank" rel="noopener" href="'+OFFICIAL_CAD+'">直接打开IEA官方原始CAD目录 ↗</a></p>';
 loadButton.disabled=false;
 console.warn('Original STL loading failed:',m.file,error);
}
async function loadModel(){
 const record=MODELS.find(m=>m.key===selector.value)||MODELS[0];
 loadButton.disabled=true;status.textContent='正在读取官方原始文件：'+record.file;
 try{
  const url=import.meta.env.BASE_URL+'iea15-official/'+record.file;
  const response=await fetch(url,{cache:'no-store'});
  if(!response.ok)throw Error('官方原始文件未完成GitHub Pages归档，HTTP '+response.status);
  const zip=await response.arrayBuffer();
  const entry=await extractOfficialSTL(zip);
  const geometry=new STLLoader().parse(entry.data);
  geometry.computeBoundingBox();
  if(!geometry.boundingBox || geometry.boundingBox.isEmpty())throw Error('原始STL几何为空');
  if(mesh){scene.remove(mesh);mesh.geometry.dispose();}
  mesh=new THREE.Mesh(geometry,STL_MATERIAL);mesh.frustumCulled=false;mesh.name=record.file;scene.add(mesh);
  bounds.copy(geometry.boundingBox);center=bounds.getCenter(new THREE.Vector3());
  radius=Math.max(bounds.getBoundingSphere(new THREE.Sphere()).radius,1);
  lastType=record.key;
  positionCamera('iso');
  const size=bounds.getSize(new THREE.Vector3());
  const triangles=geometry.getAttribute('position').count/3;
  meta.innerHTML='<div class="selection-tag">VERIFIED UPSTREAM FILE · ORIGINAL GEOMETRY</div><h3>'+record.label+'</h3>'+
   '<p>'+record.description+'。网页仅从ZIP解压 STL 并绘制其原始三角面，不创建几何替代件。</p>'+
   '<div class="selected-source">'+record.file+'</div>'+
   '<p>ZIP '+(zip.byteLength/1048576).toFixed(2)+' MB · 原网格 '+Math.round(triangles).toLocaleString('zh-CN')+' 个三角面 · 原始坐标包络 '+
   [size.x,size.y,size.z].map(v=>v.toFixed(1)).join(' × ')+'（STL坐标单位见官方模型说明）</p>';
  status.textContent='已加载官方源模型 · '+record.file;
 }catch(error){failure(error,record);}
 finally{loadButton.disabled=false;}
}
loadButton.addEventListener('click',()=>{void loadModel();});
selector.addEventListener('change',()=>{void loadModel();});
void loadModel();
