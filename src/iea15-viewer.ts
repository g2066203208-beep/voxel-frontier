import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import './iea15-viewer.css';
import aeroText from '../research/wind-tower/references/reference-models-20261008/IEA-15-240-RWT_OpenFAST/OpenFAST/IEA-15-240-RWT/IEA-15-240-RWT_AeroDyn15_blade.dat?raw';
import towerAeroText from '../research/wind-tower/references/reference-models-20261008/IEA-15-240-RWT_OpenFAST/OpenFAST/IEA-15-240-RWT-Monopile/IEA-15-240-RWT-Monopile_AeroDyn15.dat?raw';
import edText from '../research/wind-tower/references/reference-models-20261008/IEA-15-240-RWT_OpenFAST/OpenFAST/IEA-15-240-RWT-Monopile/IEA-15-240-RWT-Monopile_ElastoDyn.dat?raw';

type BladeRow = { span: number; curve: number; sweep: number; twist: number; chord: number };
type TowerRow = { elevation: number; diameter: number };
type PartId = 'tower' | 'blades' | 'nacelle' | 'hub' | 'support';
const UPSTREAM_SHA = 'e4993d63de10f165389534461dd544006750fe60';
const ARCHIVE_ROOT = 'https://github.com/g2066203208-beep/voxel-frontier/tree/main/research/wind-tower/references/reference-models-20261008/IEA-15-240-RWT_OpenFAST/OpenFAST/';
const details: Record<PartId,{title:string;from:string;note:string}> = {
  tower: { title:'塔筒 · 官方直径测点重建', from:'Monopile_AeroDyn15.dat / TwrElev, TwrDiam', note:'采用20个官方塔筒气动直径站点生成旋转表面；不等于实体钢板厚度、有限元网格或强度模型。' },
  blades: { title:'三片叶片 · 官方50站气动外形', from:'AeroDyn15_blade.dat / BlSpn, BlCrvAC, BlSwpAC, BlTwist, BlChord', note:'展向长度、弦长、扭角、曲率和后掠来自官方表格；截面厚度与翼型实体轮廓为展示近似，非原始CAD。' },
  nacelle: { title:'机舱 · 几何外壳示意', from:'ElastoDyn.dat / NacMass, NacCMxn, NacCMzn', note:'机舱位置参照塔顶和轴高度；外壳尺寸和形状仅供展示。官方质量/质心数据不代表外壳几何。' },
  hub: { title:'轮毂 · 位置和半径参考', from:'ElastoDyn.dat / OverHang, HubRad, HubMass', note:'轮毂中心、旋转轴线与叶根半径参考官方结构参数；轮毂外壳造型简化，并非机械加工模型。' },
  support: { title:'水面与下部支撑 · 仅为场景示意', from:'ElastoDyn.dat / TowerBsHt (15 m above MSL)', note:'水面及下部圆柱只用于定位和帮助观看，不代表SubDyn单桩基础几何、埋深或结构设计。' }
};
function numericField(text: string, name: string): number {
  const line = text.split(/\r?\n/).find(row => row.trim().split(/\s+/)[1] === name);
  if (!line) throw new Error('官方文件缺少字段: ' + name);
  const value = Number(line.trim().split(/\s+/)[0]);
  if (!Number.isFinite(value)) throw new Error('官方文件字段不是数值: ' + name);
  return value;
}
function stations(text: string, column: string, cols: number, n: number): number[][] {
  const lines = text.split(/\r?\n/);
  const head = lines.findIndex(line => line.trim().startsWith(column));
  if (head < 0) throw new Error('官方文件缺少表格列: ' + column);
  const out: number[][] = [];
  for (let i = head+1; i < lines.length && out.length<n; i++) {
    const parts = lines[i].trim().split(/\s+/);
    if (parts.length < cols || parts.slice(0,cols).some(v => v === '' || !Number.isFinite(Number(v)))) {
      if (out.length) break;
      continue;
    }
    out.push(parts.slice(0,cols).map(Number));
  }
  if (out.length !== n) throw new Error('官方表格测点数量不符: ' + column + ', 实际 ' + out.length + ' / ' + n);
  return out;
}
const towerRows: TowerRow[] = stations(towerAeroText,'TwrElev',5,20).map(x => ({elevation:x[0], diameter:x[1]}));
const bladeRows: BladeRow[] = stations(aeroText,'BlSpn',10,50).map(x => ({span:x[0],curve:x[1],sweep:x[2],twist:x[4],chord:x[5]}));
const towerTop = numericField(edText,'TowerHt');
const towerBase = numericField(edText,'TowerBsHt');
const shaftHeight = towerTop + numericField(edText,'Twr2Shft');
const hubRadius = numericField(edText,'HubRad');
const tipRadius = numericField(edText,'TipRad');
const overhang = numericField(edText,'OverHang');
const precone = numericField(edText,'PreCone(1)');
const bladesNumber = numericField(edText,'NumBl');
const nacMass = numericField(edText,'NacMass');
const hubMass = numericField(edText,'HubMass');
if (bladesNumber !== 3 || Math.abs(towerRows[0].elevation-towerBase)>0.01 || Math.abs(towerRows[towerRows.length-1].elevation-towerTop)>0.01 || Math.abs(bladeRows[bladeRows.length-1].span -(tipRadius-hubRadius))>0.01) {
  throw new Error('官方几何参数未通过自检，停止绘制以避免显示错误模型');
}

const app = document.querySelector<HTMLDivElement>('#iea15-app');
if (!app) throw new Error('找不到三维页面根元素');
app.innerHTML =
'<header class="topbar"><a class="return" href="./">← 返回论文工作室</a><div class="identity"><div class="identity-kicker">OFFICIAL OPENFAST DATA · 3D RECONSTRUCTION</div><h1>IEA 15 MW <span>参考风机模型</span></h1></div><a class="source-head" target="_blank" rel="noopener" href="'+ARCHIVE_ROOT+'">查看原始模型文件 ↗</a></header>' +
'<main class="viewer-layout"><section class="stage"><div class="stage-top"><div class="stage-label"><span class="live-dot"></span> 三维交互视图 <span class="separator">/</span> Monopile configuration</div><span class="stage-pill">参数驱动可视化 · 非原始CAD</span></div><div id="viewport" class="viewport"><div class="viewport-hint">鼠标拖动旋转 · 滚轮缩放 · 右键平移<br />手机单指旋转 · 双指缩放</div></div><div class="stage-bottom"><div class="view-buttons"><button type="button" data-cam="iso">三维视角</button><button type="button" data-cam="front">正视</button><button type="button" data-cam="side">侧视</button><button type="button" data-cam="top">俯视</button><button type="button" id="capture">保存截图</button></div><div id="viewer-status" aria-live="polite">已载入官方参数</div></div></section>' +
'<aside class="panel"><div class="panel-head"><span class="eyebrow">REFERENCE TURBINE</span><h2>模型组成</h2><p>基于 GitHub 已归档的 IEA 官方 OpenFAST 输入文件实时生成三维外形。</p></div>' +
'<div class="stats"><div><b>15 <small>MW</small></b><span>额定功率</span></div><div><b>240 <small>m</small></b><span>名义叶轮直径</span></div><div><b>'+towerTop.toFixed(3)+' <small>m</small></b><span>塔顶高程</span></div><div><b>'+shaftHeight.toFixed(3)+' <small>m</small></b><span>主轴中心高程</span></div></div>' +
'<div class="section-title">结构部件 <small>点击风机也可选择</small></div><div class="parts">'+
'<label class="part"><input type="checkbox" data-part="tower" checked><span class="swatch sw-tower"></span><span>钢制锥形塔筒 <small>20个原始直径测点</small></span></label>'+
'<label class="part"><input type="checkbox" data-part="blades" checked><span class="swatch sw-blades"></span><span>3片气动叶片 <small>每片50个官方气动站点</small></span></label>'+
'<label class="part"><input type="checkbox" data-part="hub" checked><span class="swatch sw-hub"></span><span>轮毂 <small>位置/质量官方 · 外壳示意</small></span></label>'+
'<label class="part"><input type="checkbox" data-part="nacelle" checked><span class="swatch sw-nacelle"></span><span>机舱 <small>位置/质量官方 · 外壳示意</small></span></label>'+
'<label class="part"><input type="checkbox" data-part="support"><span class="swatch sw-support"></span><span>海面 / 支撑示意 <small>非SubDyn单桩模型</small></span></label></div>'+
'<div class="section-title">视图选项</div><div class="switch-row"><label><input type="checkbox" id="wire"> 显示网格线</label><label><input type="checkbox" id="spin"> 旋转叶轮（演示）</label></div><div class="switch-row"><label><input type="checkbox" id="turntable"> 自动环绕观察</label><label><input type="checkbox" id="stations"> 显示塔筒测点</label></div>'+
'<div class="selection" id="selection"><div class="selection-tag">当前选择</div><h3>整机参考视图</h3><p>点击三维部件，查看数据来源及几何简化边界。</p></div>'+
'<div class="source-box"><b>来源身份与局限</b><p>官方 IEA-15-240-RWT / OpenFAST，commit <code>'+UPSTREAM_SHA.slice(0,12)+'</code>。本页面不是原作者CAD、Abaqus模型或动力学求解结果。</p><div class="refs"><a target="_blank" rel="noopener" href="'+ARCHIVE_ROOT+'">GitHub原始输入 ↗</a><a target="_blank" rel="noopener" href="https://github.com/g2066203208-beep/voxel-frontier/blob/main/research/wind-tower/references/open-access/Gaertner_2020_IEA_15MW_Reference_Report_75698.pdf">官方技术报告 ↗</a></div></div></aside></main>' +
'<footer class="page-footer">数据直接读取本仓库的 <code>ElastoDyn.dat</code>、<code>AeroDyn15.dat</code>、<code>AeroDyn15_blade.dat</code>。力学真实性需以官方输入及单独验证为准。</footer>';

function el<T extends HTMLElement = HTMLElement>(selector: string): T {
  const found = document.querySelector<T>(selector);
  if (!found) throw new Error('UI元素缺失: '+selector);
  return found;
}

const stage = el<HTMLDivElement>('#viewport');
const scene = new THREE.Scene();
scene.background = new THREE.Color('#14202c');
scene.fog = new THREE.FogExp2('#14202c',0.0011);
const camera = new THREE.PerspectiveCamera(37,1,0.1,3000);
const defaultLook = new THREE.Vector3(0,120,0);
camera.position.set(-275,204,345);
const renderer = new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.35;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
stage.prepend(renderer.domElement);
renderer.domElement.setAttribute('aria-label','交互式IEA 15 MW风机三维模型');
const controls = new OrbitControls(camera,renderer.domElement);
controls.target.copy(defaultLook);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.minDistance = 45;
controls.maxDistance = 1000;
controls.maxPolarAngle = Math.PI*0.98;
controls.update();

scene.add(new THREE.HemisphereLight(0xe7f5ff,0x334254,2.15));
const light = new THREE.DirectionalLight(0xffffff,3.1);
light.position.set(-115,290,145);
light.castShadow = true;
light.shadow.mapSize.set(2048,2048);
light.shadow.camera.left = -180;
light.shadow.camera.right = 180;
light.shadow.camera.top = 280;
light.shadow.camera.bottom = -80;
scene.add(light);
const rim = new THREE.DirectionalLight(0xa0dafa,1.2);
rim.position.set(180,70,-130);
scene.add(rim);
const floorGrid = new THREE.GridHelper(420,28,0x46617b,0x2d4358);
floorGrid.position.y = -0.05;
scene.add(floorGrid);

const groups: Record<PartId,THREE.Group> = {
  tower: new THREE.Group(), blades: new THREE.Group(), hub: new THREE.Group(), nacelle: new THREE.Group(), support: new THREE.Group()
};
(Object.keys(groups) as PartId[]).forEach(key=>scene.add(groups[key]));

const towerMat = new THREE.MeshStandardMaterial({color:'#b6c8d5',metalness:0.7,roughness:0.33,side:THREE.DoubleSide});
const bladeMat = new THREE.MeshStandardMaterial({color:'#f1f5f8',metalness:0.19,roughness:0.45,side:THREE.DoubleSide});
const hubMat = new THREE.MeshStandardMaterial({color:'#dde8ef',metalness:0.65,roughness:0.3});
const nacMat = new THREE.MeshStandardMaterial({color:'#a2b4c0',metalness:0.58,roughness:0.38});
const seamMat = new THREE.MeshStandardMaterial({color:'#648399',metalness:0.8,roughness:0.26});
const partMaterials = [towerMat,bladeMat,hubMat,nacMat,seamMat];
const towerProfile = towerRows.map(r=>new THREE.Vector2(r.diameter/2,r.elevation));
const tower = new THREE.Mesh(new THREE.LatheGeometry(towerProfile,72),towerMat);
tower.castShadow = true; tower.receiveShadow = true; tower.userData.part='tower';
groups.tower.add(tower);
const baseCap = new THREE.Mesh(new THREE.CylinderGeometry(towerRows[0].diameter/2,towerRows[0].diameter/2,0.45,64),seamMat);
baseCap.position.y = towerBase; baseCap.userData.part='tower'; groups.tower.add(baseCap);
const topCap = new THREE.Mesh(new THREE.CylinderGeometry(towerRows[towerRows.length-1].diameter/2,towerRows[towerRows.length-1].diameter/2,0.5,64),seamMat);
topCap.position.y = towerTop; topCap.userData.part='tower'; groups.tower.add(topCap);
const ringStations = new THREE.Group();
for (const row of towerRows) {
  const ring = new THREE.Mesh(new THREE.TorusGeometry(row.diameter/2+0.08,0.055,5,66),new THREE.MeshBasicMaterial({color:'#68d0cf',transparent:true,opacity:0.83}));
  ring.rotation.x = Math.PI/2;
  ring.position.y = row.elevation;
  ring.userData.part = 'tower';
  ringStations.add(ring);
}
ringStations.visible = false;
scene.add(ringStations);

const rotorCenter = new THREE.Vector3(overhang,shaftHeight,0);
const rotor = new THREE.Group();
rotor.position.copy(rotorCenter);
groups.blades.add(rotor);
const pitchCone = THREE.MathUtils.degToRad(precone);
const sectionCount = 14;
function makeBladeGeometry(rows: BladeRow[]): THREE.BufferGeometry {
  const positions:number[] = [];
  const indices:number[] = [];
  const normals:number[] = [];
  // Airfoil thickness *shape* is representative only; chord/sweep/twist/stations are official.
  for (let i=0;i<rows.length;i++) {
    const row=rows[i];
    const angle=THREE.MathUtils.degToRad(row.twist);
    const halfChord=row.chord/2;
    const halfThickness=row.chord*(0.13 - 0.04*(row.span/(tipRadius-hubRadius)));
    for (let j=0;j<sectionCount;j++) {
      const phi=2*Math.PI*j/sectionCount;
      const chordPosition=halfChord*Math.cos(phi);
      const thicknessPosition=halfThickness*Math.sin(phi);
      const x=row.curve + Math.sin(pitchCone)*row.span + chordPosition*Math.sin(angle)+thicknessPosition*Math.cos(angle);
      const y=hubRadius+row.span*Math.cos(pitchCone);
      const z=row.sweep + chordPosition*Math.cos(angle)-thicknessPosition*Math.sin(angle);
      positions.push(x,y,z);
      normals.push(0,0,0);
    }
  }
  for (let i=0;i<rows.length-1;i++) for (let j=0;j<sectionCount;j++) {
    const a=i*sectionCount+j, b=i*sectionCount+(j+1)%sectionCount, c=(i+1)*sectionCount+j, d=(i+1)*sectionCount+(j+1)%sectionCount;
    indices.push(a,c,b,b,c,d);
  }
  for(let j=1;j<sectionCount-1;j++) {
    indices.push(0,j+1,j);
    const s=(rows.length-1)*sectionCount;
    indices.push(s,s+j,s+j+1);
  }
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  g.setIndex(indices); g.computeVertexNormals(); g.computeBoundingSphere();
  return g;
}
const bladeGeometry=makeBladeGeometry(bladeRows);
for(let i=0;i<bladesNumber;i++){
  const blade = new THREE.Mesh(bladeGeometry,bladeMat);
  blade.rotation.x = 2*Math.PI*i/bladesNumber;
  blade.castShadow = true; blade.receiveShadow = true;
  blade.userData.part='blades';
  rotor.add(blade);
}
const hubBody = new THREE.Mesh(new THREE.SphereGeometry(hubRadius*1.03,38,26),hubMat);
hubBody.position.copy(rotorCenter);hubBody.castShadow=true;hubBody.userData.part='hub';
groups.hub.add(hubBody);
const spinner = new THREE.Mesh(new THREE.ConeGeometry(2.6,4.8,32),hubMat);
spinner.rotation.z=Math.PI/2;
spinner.position.set(overhang-3.5,shaftHeight,0);
spinner.userData.part='hub';groups.hub.add(spinner);
const nacelleBody = new THREE.Mesh(new THREE.BoxGeometry(16.5,6.1,7.6),nacMat);
nacelleBody.position.set(4.0,towerTop+4.1,0);
nacelleBody.userData.part='nacelle';nacelleBody.castShadow=true;groups.nacelle.add(nacelleBody);
const nacelleRoof = new THREE.Mesh(new THREE.BoxGeometry(12.5,1.2,6.2),hubMat);
nacelleRoof.position.set(4,towerTop+7.8,0);
nacelleRoof.userData.part='nacelle';groups.nacelle.add(nacelleRoof);
const shaft = new THREE.Mesh(new THREE.CylinderGeometry(1.45,1.45,7.0,32),seamMat);
shaft.rotation.z=Math.PI/2;shaft.position.set(-7.4,shaftHeight,0);
shaft.userData.part='hub';groups.hub.add(shaft);
const support = new THREE.Mesh(new THREE.CylinderGeometry(5,5,45,60),new THREE.MeshStandardMaterial({color:'#536e7f',metalness:.5,roughness:.54,transparent:true,opacity:.65}));
support.position.y=-7.5;support.userData.part='support'; groups.support.add(support);
const water = new THREE.Mesh(new THREE.CircleGeometry(145,100),new THREE.MeshStandardMaterial({color:'#316b82',metalness:.28,roughness:.3,transparent:true,opacity:.28,side:THREE.DoubleSide}));
water.rotation.x=-Math.PI/2;water.position.y=0.02; water.userData.part='support';groups.support.add(water);
groups.support.visible=false;

let selected:PartId | null=null;
const pickList=[tower,baseCap,topCap,hubBody,spinner,nacelleBody,nacelleRoof,shaft,support,water,...rotor.children] as THREE.Object3D[];
function selectPart(part:PartId | null) {
  selected=part;
  const area=el('#selection');
  if(!part){ area.innerHTML='<div class="selection-tag">当前选择</div><h3>整机参考视图</h3><p>点击部件查看原始数据和建模边界。</p>'; return; }
  const info=details[part];
  area.innerHTML='<div class="selection-tag">当前选择 · '+part+'</div><h3>'+info.title+'</h3><div class="selected-source">'+info.from+'</div><p>'+info.note+'</p>';
  el('#viewer-status').textContent=info.title;
}
const picker=new THREE.Raycaster();
const ndc=new THREE.Vector2();
let downX=0,downY=0;
renderer.domElement.addEventListener('pointerdown',event=>{downX=event.clientX;downY=event.clientY;});
renderer.domElement.addEventListener('pointerup',event=>{
  if(Math.hypot(event.clientX-downX,event.clientY-downY)>7)return;
  const rect=renderer.domElement.getBoundingClientRect();
  ndc.set(((event.clientX-rect.left)/rect.width)*2-1,-((event.clientY-rect.top)/rect.height)*2+1);
  picker.setFromCamera(ndc,camera);
  const found=picker.intersectObjects(pickList.filter(o=>o.visible&&(!o.parent||o.parent.visible)),true);
  const hit=found.find(i => {
    let obj:THREE.Object3D|null=i.object;
    while(obj){if(obj.userData.part && groups[obj.userData.part as PartId].visible)return true;obj=obj.parent;}
    return false;
  });
  if(!hit){selectPart(null);return;}
  let parent:THREE.Object3D|null=hit.object;
  while(parent&&!parent.userData.part)parent=parent.parent;
  if(parent)selectPart(parent.userData.part as PartId);
});
el<HTMLInputElement>('#wire').addEventListener('change',e=>{
  const wire=(e.currentTarget as HTMLInputElement).checked;
  partMaterials.forEach(m=>{m.wireframe=wire;m.needsUpdate=true;});
});
el<HTMLInputElement>('#stations').addEventListener('change',e=>{ringStations.visible=(e.currentTarget as HTMLInputElement).checked&&groups.tower.visible;});
document.querySelectorAll<HTMLInputElement>('[data-part]').forEach(box=>box.addEventListener('change',()=>{
  const part=box.dataset.part as PartId;
  groups[part].visible=box.checked;
  if(part==='tower')ringStations.visible=box.checked&&el<HTMLInputElement>('#stations').checked;
  if(selected===part&&!box.checked)selectPart(null);
}));
function cameraPreset(view:string){
  controls.autoRotate=false;el<HTMLInputElement>('#turntable').checked=false;
  controls.target.copy(defaultLook);
  if(view==='front')camera.position.set(-420,132,0);
  else if(view==='side')camera.position.set(0,150,435);
  else if(view==='top')camera.position.set(-3,600,0.1);
  else camera.position.set(-275,204,345);
  camera.up.set(0,1,0);camera.lookAt(controls.target);controls.update();
}
document.querySelectorAll<HTMLButtonElement>('[data-cam]').forEach(button=>button.addEventListener('click',()=>cameraPreset(button.dataset.cam||'iso')));
el<HTMLInputElement>('#turntable').addEventListener('change',e=>{controls.autoRotate=(e.currentTarget as HTMLInputElement).checked;controls.autoRotateSpeed=0.6;});
el<HTMLButtonElement>('#capture').addEventListener('click',()=>{
  renderer.render(scene,camera);
  const link=document.createElement('a');
  link.download='IEA-15MW_OpenFAST_parameter-driven_3D-preview.png';
  link.href=renderer.domElement.toDataURL('image/png');
  link.click();
});
const resize=()=>{
  const width=Math.max(stage.clientWidth,200),height=Math.max(stage.clientHeight,260);
  camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height,false);
};
new ResizeObserver(resize).observe(stage);
resize();
let lastFrame=0;
renderer.setAnimationLoop(now=>{
  const seconds=Math.min((now-lastFrame)/1000,.06);
  lastFrame=now;
  if(el<HTMLInputElement>('#spin').checked)rotor.rotation.x+=seconds*0.21; // demo speed, not OpenFAST solver
  controls.update();
  renderer.render(scene,camera);
});
selectPart(null);
el('#viewer-status').textContent='官方参数已加载 · '+towerRows.length+'个塔筒测点 · '+bladeRows.length+'个叶片测点/片';
