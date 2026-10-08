import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import loadCsv from '../research/wind-tower/experiments/T072/T072_FORMAL_36CASE_BASE_ENVELOPE.csv?raw';
import rebarCsv from '../research/wind-tower/experiments/T077/T077_FORMAL_31SEG_REBAR_BF8.csv?raw';
import segmentCsv from '../research/wind-tower/experiments/T078/T078_BF8_SEGMENT_LOSS_AND_GRAVITY_CHECK.csv?raw';
import prestressJson from '../research/wind-tower/experiments/T078/T078_PRESTRESS_DESIGN_META.json?raw';
import './wind-twin.css';

// This is a traceable RESEARCH DATA VIEWER, not a live aerodynamic or FE solver.
// T072 is a table of case-wise extrema, not a time-series dataset.
// T077/T078 are thesis CODE-DESIGN scenarios; visual meshes are illustrations.
type Row=Record<string,string>;
type Metric='Mres_max_kNm'|'Vres_max_kN'|'T_abs_max_kNm'|'Ncomp_max_kN';
type PTMeta={adopted_BF8:{BF:number;strands_total:number;Pe_MN:number;sigma_pe_MPa:number;loss_total_MPa:number;eta:number};permanent_compression_control:{min_edge_compression_MPa:number}};
function readCsv(t:string):Row[]{
 const lines=t.replace(/^\uFEFF/,'').trim().split(/\r?\n/);
 const header=(lines.shift()||'').split(',');
 return lines.filter(Boolean).map(line=>{
  const fields=line.split(',');const obj:Row={};
  header.forEach((h,i)=>obj[h]=fields[i]||'');
  return obj;
 });
}
const cases=readCsv(loadCsv),rebars=readCsv(rebarCsv),segments=readCsv(segmentCsv);
const prestress=JSON.parse(prestressJson) as PTMeta;
if(cases.length!==36||rebars.length!==31||segments.length!==31)throw new Error('Data count failed: expected 36/31/31');
for(let i=0;i<31;i++)if(rebars[i].segment!==segments[i].segment)throw new Error('Source segment misalignment');
const n=(r:Row,k:string)=>Number(r[k]);
const fmt=(v:number,d=2)=>v.toLocaleString('zh-CN',{minimumFractionDigits:d,maximumFractionDigits:d});
const node=(name:string)=>{const element=document.getElementById(name);if(!element)throw new Error('Missing UI: '+name);return element;};
const put=(name:string,value:string)=>node(name).textContent=value;
let activeSegment=0, activeCase=Math.max(0,cases.findIndex(r=>r.case==='U09p343881_ETM_S06'));
let metric:Metric='Mres_max_kNm';
let wind=11.4,spinning=true,fault=false,cutaway=false,showPT=false,showRebar=false;
const names:Record<Metric,{title:string;unit:string;time:string}>={
 Mres_max_kNm:{title:'塔底合成弯矩极值',unit:'kN·m',time:'Mres_time_s'},
 Vres_max_kN:{title:'塔底合成剪力极值',unit:'kN',time:'Vres_time_s'},
 T_abs_max_kNm:{title:'塔底扭矩绝对极值',unit:'kN·m',time:'T_time_s'},
 Ncomp_max_kN:{title:'塔底最大轴向压力',unit:'kN',time:''}
};
const maxCase=cases.reduce((a,b)=>n(a,'Mres_max_kNm')>n(b,'Mres_max_kNm')?a:b);
put('metric-cases',String(cases.length)+' 组');
put('metric-moment',fmt(n(maxCase,'Mres_max_kNm')/1000)+' MN·m');
put('metric-control',maxCase.case);
put('metric-prestress',fmt(prestress.adopted_BF8.Pe_MN)+' MN');
put('pt-bf',String(prestress.adopted_BF8.BF));
put('pt-count',String(prestress.adopted_BF8.strands_total));
put('pt-sigma',fmt(prestress.adopted_BF8.sigma_pe_MPa,1));
put('pt-loss',fmt(prestress.adopted_BF8.loss_total_MPa,1));
put('pt-eta',fmt(prestress.adopted_BF8.eta*100)+'%');
put('pt-minstress',fmt(prestress.permanent_compression_control.min_edge_compression_MPa,3));
const picker=node('segment-select') as HTMLSelectElement;
segments.forEach((row,i)=>{const o=document.createElement('option');o.value=String(i);o.textContent=row.segment+' · 第'+(i+1)+'节';picker.append(o);});
const table=node('csv-table');
const tbl=document.createElement('table');
const head=document.createElement('thead');head.innerHTML='<tr><th>节段</th><th>等级</th><th>外径m</th><th>每层纵筋数</th><th>设计Φ/mm</th><th>利用系数</th><th>最小压应力MPa</th></tr>';tbl.append(head);
const body=document.createElement('tbody');
const tableRows:HTMLTableRowElement[]=[];
segments.forEach((s,i)=>{
 const tr=document.createElement('tr');tr.tabIndex=0;
 const values=[s.segment,s.grade,fmt(n(s,'D_m')),rebars[i].He_bars_each_layer_LOCKED,rebars[i].bar_d_mm,fmt(n(rebars[i],'max_utilization'),3),fmt(n(s,'min_edge_compression_MPa'),3)];
 values.forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.append(td);});
 tr.addEventListener('click',()=>chooseSegment(i));
 tr.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();chooseSegment(i);}});
 body.append(tr);tableRows.push(tr);
});
tbl.append(body);table.append(tbl);
const viewport=node('wind-viewport');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.setClearColor(0x0b2131);
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.45;
viewport.prepend(renderer.domElement);
const scene=new THREE.Scene();scene.fog=new THREE.Fog(0x0b2131,260,600);
scene.add(new THREE.AmbientLight(0xeaf7ff,1.4));
scene.add(new THREE.HemisphereLight(0xbfe6ff,0x1a3a4d,2.1));
const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(110,180,160);scene.add(light);
const back=new THREE.DirectionalLight(0x5ddfcb,2);back.position.set(-130,185,-115);scene.add(back);
const camera=new THREE.PerspectiveCamera(43,1,.1,2000);
const orbit=new OrbitControls(camera,renderer.domElement);
orbit.enableDamping=true;orbit.dampingFactor=.07;orbit.minDistance=25;orbit.maxDistance=640;
const concrete=new THREE.Group(),steel=new THREE.Group(),ptGroup=new THREE.Group(),rebarGroup=new THREE.Group(),rna=new THREE.Group();
scene.add(concrete,steel,ptGroup,rebarGroup,rna);
const meshes:THREE.Mesh[]=[];
const heights:number[]=[0],outer:number[]=[],inner:number[]=[];
const lengths=segments.map(s=>n(s,'segment_length_m'));
const sumLengths=lengths.reduce((a,b)=>a+b,0);
let height=0;
for(let i=0;i<31;i++){
 const current=segments[i],r=n(current,'D_m')/2;
 const next=i<30?n(segments[i+1],'D_m')/2:r*.986;
 const area=n(current,'A_m2');
 const ri=Math.sqrt(Math.max(.05,r*r-area/Math.PI));
 const riNext=Math.sqrt(Math.max(.05,next*next-area/Math.PI));
 const len=112*lengths[i]/sumLengths;
 const geom=new THREE.LatheGeometry([
  new THREE.Vector2(ri,0),new THREE.Vector2(r,0),
  new THREE.Vector2(next,len),new THREE.Vector2(riNext,len)
 ],44);
 const mat=new THREE.MeshStandardMaterial({color:i%2?0xb0c5c8:0xb9d0d4,metalness:.06,roughness:.76,side:THREE.DoubleSide,transparent:true});
 const part=new THREE.Mesh(geom,mat);part.position.y=height;part.userData.segment=i;
 meshes.push(part);concrete.add(part);outer.push(r);inner.push(ri);
 const line=new THREE.Mesh(new THREE.TorusGeometry(r,.027,5,52),new THREE.MeshBasicMaterial({color:0x658e99,transparent:true,opacity:.7}));
 line.rotation.x=Math.PI/2;line.position.y=height;concrete.add(line);
 height+=len;heights.push(height);
}
const radiusBottom=outer[30],radiusTop=Math.max(1.4,radiusBottom*.64);
const shell=new THREE.Mesh(new THREE.LatheGeometry([
 new THREE.Vector2(radiusBottom-.08,0),new THREE.Vector2(radiusBottom,0),
 new THREE.Vector2(radiusTop,46),new THREE.Vector2(radiusTop-.05,46)
],52),new THREE.MeshStandardMaterial({color:0xb3c9d8,metalness:.6,roughness:.35,side:THREE.DoubleSide}));
shell.position.y=112;steel.add(shell);
const collar=new THREE.Mesh(new THREE.CylinderGeometry(radiusBottom+.12,radiusBottom+.12,.7,52),new THREE.MeshStandardMaterial({color:0x4a8192,metalness:.7,roughness:.4}));collar.position.y=112;steel.add(collar);
for(let i=1;i<4;i++){
 const level=112+46*i/4,r=radiusBottom+(radiusTop-radiusBottom)*i/4;
 const ring=new THREE.Mesh(new THREE.TorusGeometry(r,.045,6,50),new THREE.MeshStandardMaterial({color:0x508e9c,metalness:.6,roughness:.4}));
 ring.rotation.x=Math.PI/2;ring.position.y=level;steel.add(ring);
}
const ptVerts:number[]=[];
for(let k=0;k<36;k++){
 const a=k*Math.PI*2/36,r=1.75;
 ptVerts.push(r*Math.cos(a),0,r*Math.sin(a),r*Math.cos(a),112,r*Math.sin(a));
}
const ptGeom=new THREE.BufferGeometry();ptGeom.setAttribute('position',new THREE.Float32BufferAttribute(ptVerts,3));
ptGroup.add(new THREE.LineSegments(ptGeom,new THREE.LineBasicMaterial({color:0xffc27a})));
function rebuildBars(index:number){
 rebarGroup.clear();
 const count=Math.max(0,Math.round(n(rebars[index],'He_bars_each_layer_LOCKED')));
 const vertices:number[]=[];
 const h=heights[index],len=heights[index+1]-heights[index];
 const rings=[Math.min(outer[index]-.06,inner[index]+.12),Math.max(inner[index]+.06,outer[index]-.12)];
 for(const radius of rings){
  for(let j=0;j<count;j++){
   const a=j*Math.PI*2/count,x=radius*Math.cos(a),z=radius*Math.sin(a);
   vertices.push(x,h+.04,z,x,h+len-.04,z);
  }
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
 rebarGroup.add(new THREE.LineSegments(g,new THREE.LineBasicMaterial({color:0xff9d62})));
}
function addMesh(parent:THREE.Group,shape:THREE.BufferGeometry,color:number,x:number,y:number,z:number){
 const m=new THREE.Mesh(shape,new THREE.MeshStandardMaterial({color,roughness:.46,metalness:.28,side:THREE.DoubleSide}));m.position.set(x,y,z);parent.add(m);return m;
}
addMesh(rna,new THREE.BoxGeometry(7,4.5,12),0xb9d0dd,0,161,5);
const spinner=addMesh(rna,new THREE.ConeGeometry(2.25,5,28),0x77b8c7,0,162.5,13);
spinner.rotation.x=Math.PI/2;
const rotor=new THREE.Group();rotor.position.set(0,162.5,14);rna.add(rotor);
addMesh(rotor,new THREE.SphereGeometry(2.7,24,16),0x7acbd0,0,0,0);
const bladeVerts:number[]=[];const bladeIndices:number[]=[];
for(let i=0;i<=24;i++){
 const span=i/24,radial=3.5+span*81.5;
 const chord=span<.1?1.5+span*28:Math.max(.18,4.5*Math.pow(1-span,1.22));
 bladeVerts.push(radial,-chord*.45,span*span*1.6,radial,chord*.55,span*span*1.6);
}
for(let i=0;i<24;i++){const a=i*2;bladeIndices.push(a,a+1,a+2,a+1,a+3,a+2);}
const bladeShape=new THREE.BufferGeometry();bladeShape.setAttribute('position',new THREE.Float32BufferAttribute(bladeVerts,3));bladeShape.setIndex(bladeIndices);bladeShape.computeVertexNormals();
for(let i=0;i<3;i++){const blade=addMesh(rotor,bladeShape,0xe6edf2,0,0,0);blade.rotation.z=i*2*Math.PI/3;}
const grid=new THREE.GridHelper(160,32,0x326a80,0x173747);grid.position.y=-.15;scene.add(grid);
const floor=addMesh(scene as unknown as THREE.Group,new THREE.CylinderGeometry(6.1,6.5,.9,48),0x527484,0,-.6,0);
floor.receiveShadow=false;
function chooseSegment(index:number){
 activeSegment=Math.min(30,Math.max(0,index));
 const s=segments[activeSegment],r=rebars[activeSegment];
 picker.value=String(activeSegment);
 put('seg-grade',s.grade);put('seg-diameter',fmt(n(s,'D_m')));put('seg-bars',r.He_bars_each_layer_LOCKED+' 根');
 put('seg-phi','Φ'+fmt(n(r,'bar_d_mm'),0)+' mm');
 put('seg-util',fmt(n(r,'max_utilization'),3));
 put('seg-stress',fmt(n(s,'min_edge_compression_MPa'),3));
 meshes.forEach((mesh,i)=>{
  const mat=mesh.material as THREE.MeshStandardMaterial;
  mat.emissive.setHex(i===activeSegment?0x276955:0x081a23);
  mat.emissiveIntensity=i===activeSegment?.75:.10;
 });
 tableRows.forEach((row,i)=>row.classList.toggle('current',i===activeSegment));
 rebuildBars(activeSegment);
}
function selectCase(index:number){
 activeCase=Math.min(35,Math.max(0,index));
 const r=cases[activeCase],settings=names[metric],time=settings.time;
 put('case-code',r.case);
 put('case-quantity',fmt(n(r,metric))+' '+settings.unit);
 put('case-time',time?'t = '+fmt(n(r,time))+' s':'无极值时间字段');
 document.querySelectorAll<HTMLButtonElement>('.bar[data-index]').forEach(bar=>bar.classList.toggle('selected',Number(bar.dataset.index)===activeCase));
}
function drawChart(){
 const settings=names[metric],peak=Math.max(...cases.map(r=>n(r,metric)));
 put('chart-title',settings.title);
 put('chart-max','MAX '+fmt(peak)+' '+settings.unit);
 const chart=node('load-chart');chart.replaceChildren();
 cases.forEach((r,i)=>{
  const value=n(r,metric);
  const bar=document.createElement('button');
  bar.className='bar'+(r.case.includes('_ETM_')?' etm':'')+(i===activeCase?' selected':'');
  bar.setAttribute('data-index',String(i));
  bar.style.setProperty('--h',Math.max(2,value/peak*100).toFixed(4)+'%');
  bar.title=r.case+' | '+fmt(value)+' '+settings.unit;
  bar.setAttribute('aria-label',bar.title);
  bar.addEventListener('click',()=>selectCase(i));chart.append(bar);
 });
 selectCase(activeCase);
}
function cameraView(name:string){
 orbit.target.set(0,86,0);camera.up.set(0,1,0);
 if(name==='front')camera.position.set(0,89,286);
 else if(name==='side')camera.position.set(286,89,.01);
 else camera.position.set(194,142,226);
 camera.lookAt(orbit.target);orbit.update();
 document.querySelectorAll<HTMLButtonElement>('[data-camera]').forEach(b=>b.classList.toggle('active',b.dataset.camera===name));
}
function resize(){
 const w=Math.max(250,viewport.clientWidth),h=Math.max(260,viewport.clientHeight);
 camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);
}
new ResizeObserver(resize).observe(viewport);resize();cameraView('iso');
function refreshVisibility(){
 concrete.visible=(node('show-concrete') as HTMLInputElement).checked;
 steel.visible=(node('show-steel') as HTMLInputElement).checked;
 showPT=(node('show-pt') as HTMLInputElement).checked;
 showRebar=(node('show-rebar') as HTMLInputElement).checked;
 ptGroup.visible=showPT;rebarGroup.visible=showRebar;
 meshes.forEach(mesh=>{const m=mesh.material as THREE.MeshStandardMaterial;m.opacity=cutaway?.25:1;m.depthWrite=!cutaway;});
 node('tower-section').classList.toggle('active',cutaway);
 node('tower-pt').classList.toggle('active',showPT);
 node('tower-rebar').classList.toggle('active',showRebar);
}
function rpm(){
 if(!spinning||fault||wind<3||wind>=25)return 0;
 return Math.min(13.5,Math.max(4,5+wind*.68));
}
function refreshControls(){
 const speed=rpm();
 put('hud-rpm',fmt(speed,1)+' rpm');
 put('hud-state',fault?'模拟故障停机（不是实测）':!spinning?'动画暂停':speed===0?'演示风速超出运行区间':'教学演示：叶轮旋转');
 put('wind-label',fmt(wind,1)+' m/s');
 put('run-btn',spinning?'Ⅱ 暂停动画':'▶ 继续动画');
 put('fault-btn',fault?'✓ 演示维修恢复':'⚠ 演示故障停机');
 node('fault-btn').classList.toggle('active',fault);
}
chooseSegment(0);drawChart();refreshVisibility();refreshControls();
picker.addEventListener('change',()=>chooseSegment(Number(picker.value)));
(node('metric-select') as HTMLSelectElement).addEventListener('change',e=>{metric=(e.target as HTMLSelectElement).value as Metric;drawChart();});
(node('wind-slider') as HTMLInputElement).addEventListener('input',e=>{wind=Number((e.target as HTMLInputElement).value);refreshControls();});
node('run-btn').addEventListener('click',()=>{spinning=!spinning;refreshControls();});
node('fault-btn').addEventListener('click',()=>{fault=!fault;refreshControls();});
node('reset-btn').addEventListener('click',()=>{
 wind=11.4;spinning=true;fault=false;cutaway=false;
 (node('wind-slider') as HTMLInputElement).value='11.4';
 for(const key of ['show-concrete','show-steel'])(node(key) as HTMLInputElement).checked=true;
 for(const key of ['show-pt','show-rebar'])(node(key) as HTMLInputElement).checked=false;
 refreshControls();refreshVisibility();chooseSegment(0);cameraView('iso');
});
document.querySelectorAll<HTMLButtonElement>('[data-camera]').forEach(b=>b.addEventListener('click',()=>cameraView(b.dataset.camera||'iso')));
node('tower-section').addEventListener('click',()=>{cutaway=!cutaway;refreshVisibility();});
node('tower-pt').addEventListener('click',()=>{(node('show-pt') as HTMLInputElement).checked=!showPT;refreshVisibility();});
node('tower-rebar').addEventListener('click',()=>{(node('show-rebar') as HTMLInputElement).checked=!showRebar;refreshVisibility();});
for(const key of ['show-concrete','show-steel','show-pt','show-rebar'])node(key).addEventListener('change',refreshVisibility);
node('capture-btn').addEventListener('click',()=>{
 try{renderer.render(scene,camera);const a=document.createElement('a');
 a.download='10MW-158m-hybrid-tower-visualization.png';a.href=renderer.domElement.toDataURL('image/png');a.click();
 }catch(err){window.alert('图片导出失败: '+String(err));}
});
const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();
let down:{x:number;y:number}|null=null;
renderer.domElement.addEventListener('pointerdown',e=>down={x:e.clientX,y:e.clientY});
renderer.domElement.addEventListener('pointerup',e=>{
 if(!down||Math.hypot(e.clientX-down.x,e.clientY-down.y)>5){down=null;return;}down=null;
 const b=renderer.domElement.getBoundingClientRect();
 pointer.set((e.clientX-b.left)/b.width*2-1,-(e.clientY-b.top)/b.height*2+1);
 ray.setFromCamera(pointer,camera);const hit=ray.intersectObjects(meshes,false)[0];
 if(hit&&typeof hit.object.userData.segment==='number')chooseSegment(hit.object.userData.segment as number);
});
let previous=performance.now();
function tick(now:number){
 const dt=Math.min(.05,Math.max(0,(now-previous)/1000));previous=now;
 const speed=rpm();if(speed)rotor.rotation.z-=speed*2*Math.PI*dt/60;
 orbit.update();renderer.render(scene,camera);requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
