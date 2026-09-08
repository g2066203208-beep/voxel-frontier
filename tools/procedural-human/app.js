import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { MASTER_URL, DEFAULT_PARAMS, PRESETS, parseOBJ, canonicalize, generateHuman, toOBJ } from './human-core.js';

const state = { master:null, model:null, params:{...DEFAULT_PARAMS}, mesh:null, wire:false };
const sliderDefs = [
  ['heightCm','身高','cm',145,205,1],['sex','体型性征','女 ← → 男',-1,1,0.01],
  ['shoulderWidth','肩宽','',-1,1,0.01],['chest','胸廓宽度','',-1,1,0.01],
  ['chestDepth','胸廓厚度','',-1,1,0.01],['waist','腰部围度','',-1,1,0.01],
  ['hips','骨盆/臀宽','',-1,1,0.01],['hipDepth','骨盆厚度','',-1,1,0.01],
  ['torsoLength','躯干长度','',-1,1,0.01],['legLength','腿长比例','',-1,1,0.01],
  ['armLength','手臂长度','',-1,1,0.01],['bodyFat','软组织/体脂','',-1,1,0.01],
  ['muscle','肌肉量','',-1,1,0.01],['thigh','大腿围度','',-1,1,0.01],
  ['calf','小腿围度','',-1,1,0.01],['headScale','头部比例','',-1,1,0.01],
  ['neckWidth','颈部粗细','',-1,1,0.01]
];
const $ = q => document.querySelector(q);
const canvas = $('#viewport');
const renderer = new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.shadowMap.enabled=true;
const scene=new THREE.Scene(); scene.background=new THREE.Color(0x0c0f14);
const camera=new THREE.PerspectiveCamera(35,1,0.01,100); camera.position.set(2.6,1.25,3.5);
const controls=new OrbitControls(camera,renderer.domElement); controls.target.set(0,0.9,0); controls.enableDamping=true; controls.minDistance=1.3; controls.maxDistance=7;
scene.add(new THREE.HemisphereLight(0xdfe8ff,0x252a33,2.2));
const key=new THREE.DirectionalLight(0xffffff,3); key.position.set(3,4,4); key.castShadow=true; scene.add(key);
const rim=new THREE.DirectionalLight(0xa8c8ff,1.5); rim.position.set(-3,2,-3); scene.add(rim);
const floor=new THREE.Mesh(new THREE.CircleGeometry(1.2,64),new THREE.MeshStandardMaterial({color:0x222831,roughness:0.95})); floor.rotation.x=-Math.PI/2; floor.receiveShadow=true; scene.add(floor);
function resize(){const r=canvas.getBoundingClientRect();if(canvas.width!==Math.round(r.width*renderer.getPixelRatio())||canvas.height!==Math.round(r.height*renderer.getPixelRatio())){renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();}}
function animate(){resize();controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);} animate();
function buildUI(){const box=$('#sliders');box.innerHTML='';for(const [key,label,unit,min,max,step] of sliderDefs){const row=document.createElement('label');row.className='slider-row';row.innerHTML=`<div class="slider-head"><span>${label}</span><output id="out-${key}"></output></div><input id="in-${key}" type="range" min="${min}" max="${max}" step="${step}"><small>${unit}</small>`;box.appendChild(row);const input=row.querySelector('input');input.value=state.params[key];input.addEventListener('input',()=>{state.params[key]=Number(input.value);updateOutput(key);rebuild();});updateOutput(key);}}
function updateOutput(key){const o=$(`#out-${key}`);if(!o)return;const v=state.params[key];o.textContent=key==='heightCm'?`${Math.round(v)} cm`:Number(v).toFixed(2);}
function syncUI(){for(const [key] of sliderDefs){const i=$(`#in-${key}`);if(i)i.value=state.params[key];updateOutput(key);}}
function geometryFromModel(model){const pos=new Float32Array(model.faces.length*9);let k=0;for(const f of model.faces)for(const id of f){const v=model.vertices[id];pos[k++]=v[0];pos[k++]=v[1];pos[k++]=v[2];}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.computeVertexNormals();g.computeBoundingSphere();return g;}
function rebuild(){if(!state.master)return;state.model=generateHuman(state.master,state.params);const g=geometryFromModel(state.model);if(state.mesh){state.mesh.geometry.dispose();state.mesh.geometry=g;state.mesh.material.wireframe=state.wire;}else{const mat=new THREE.MeshPhysicalMaterial({color:0xc6a88e,roughness:0.72,metalness:0,clearcoat:0.03,side:THREE.DoubleSide});state.mesh=new THREE.Mesh(g,mat);state.mesh.castShadow=true;scene.add(state.mesh);}floor.position.y=-0.003;const m=state.model.measurements;$('#measurements').innerHTML=`<span>身高 <b>${m.heightCm.toFixed(1)} cm</b></span><span>肩宽≈ <b>${m.shoulderWidthCm.toFixed(1)} cm</b></span><span>胸围≈ <b>${m.chestCm.toFixed(1)} cm</b></span><span>腰围≈ <b>${m.waistCm.toFixed(1)} cm</b></span><span>臀围≈ <b>${m.hipCm.toFixed(1)} cm</b></span>`;$('#status').textContent=`${state.model.vertices.length.toLocaleString()} vertices · ${state.model.faces.length.toLocaleString()} triangles · fixed topology`;}
function applyPreset(name){state.params={...DEFAULT_PARAMS,...PRESETS[name]};syncUI();rebuild();}
function download(name,blob){const a=document.createElement('a');const u=URL.createObjectURL(blob);a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);}
$('#presetMale').addEventListener('click',()=>applyPreset('male'));$('#presetFemale').addEventListener('click',()=>applyPreset('female'));$('#reset').addEventListener('click',()=>{state.params={...DEFAULT_PARAMS};syncUI();rebuild();});$('#wire').addEventListener('click',()=>{state.wire=!state.wire;if(state.mesh)state.mesh.material.wireframe=state.wire;});$('#exportObj').addEventListener('click',()=>{if(state.model)download('procedural-human.obj',new Blob([toOBJ(state.model)],{type:'text/plain'}));});$('#exportGlb').addEventListener('click',()=>{if(!state.mesh)return;new GLTFExporter().parse(state.mesh,data=>download('procedural-human.glb',new Blob([data],{type:'model/gltf-binary'})),e=>console.error(e),{binary:true,onlyVisible:true});});
async function load(){try{$('#status').textContent='Loading CC0 master human mesh…';const res=await fetch(MASTER_URL,{cache:'force-cache'});if(!res.ok)throw new Error(`HTTP ${res.status}`);const parsed=parseOBJ(await res.text());state.master=canonicalize(parsed);buildUI();applyPreset('male');}catch(err){console.error(err);$('#status').textContent=`Load failed: ${err.message}`;$('#error').hidden=false;}} load();
