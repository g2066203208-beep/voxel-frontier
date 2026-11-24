
/* REV17: output/step optimization; input model unchanged. */
(function(root){
"use strict";
const eq="** REV13 E-only direct integration; gravity and equilibrated prestress propagate from last general step.\n*Step, name=EQ_2H_RAYLEIGH_REL, nlgeom=YES, inc=2000000, unsymm=YES\nUnscaled ESM horizontal record, fixed-base relative coordinates; provisional Rayleigh 1%.\n*Dynamic, application=TRANSIENT FIDELITY\n0.005, 160.195, 1.e-7, 0.005\n*Contact Controls, reset\n** Uniform support translation: -M r a_g; no simultaneous prescribed support motion.\n*Boundary, op=NEW, type=DISPLACEMENT\nCSEG_01-1.FACE_BOTTOM, 1, 3, 0.\nPT_36x15p2-1.SET_PT_BOTTOM_GEOM, 1, 3, 0.\n** Reassert self-weight when replacing distributed loads. All directions use the same whole-model mass selection.\n*Dload, op=NEW\n, GRAV, 9.81, 0., -1., 0.\n*Dload, op=NEW, amplitude=EQ_X_EAST_SI\n, GRAV, 1., -1., 0., 0.\n*Dload, op=NEW, amplitude=EQ_Z_MINUS_NORTH_SI\n, GRAV, 1., 0., 0., -1.\n*Restart, write, frequency=1000, overlay\n*Output, field, number interval=80, time marks=NO\n*Node Output\nU\n*Node Output, nset=SET_RNA_RP\nU, V, A, RF\n*Element Output, elset=SET_CSEG_ALL_ACTIVE\nS, LE, DAMAGEC, DAMAGET, PEEQ, PEEQT\n*Element Output, elset=SET_SSEG_ALL_ACTIVE\nS, LE, PEEQ\n*Element Output, elset=FLANGE_SOLID-1.SET_ALL\nS, LE, PEEQ\n*Element Output, elset=PT_36x15p2-1.SET_PT_ALL_ELEMS\nS, LE\n*Element Output, elset=REV04_ALL_REBAR\nS, LE, PEEQ\n*Contact Output\nCSTRESS, CDISP, CSTATUS\n*Output, history, frequency=1\n*Energy Output\nALLAE, ALLIE, ALLKE, ALLVD, ALLWK, ETOTAL, ALLSE, ALLSD, ALLFD, ALLPD, ALLDMD\n*Node Output, nset=SET_RNA_RP\nU1, U2, U3, UR1, UR2, UR3, A1, A2, A3\n*Node Output, nset=CSEG_01-1.FACE_BOTTOM\nRF1, RF2, RF3\n*Node Output, nset=PT_36x15p2-1.SET_PT_BOTTOM_GEOM\nRF1, RF2, RF3\n*Node Output, nset=REV13_C_BASE_PROBE\nU1, U2, U3, A1, A2, A3\n*Node Output, nset=REV13_PT_BASE_PROBE\nU1, U2, U3, A1, A2, A3\n*Element Output, elset=AUDIT_C_BASE\nS22, LE22, DAMAGEC, DAMAGET, PEEQ, PEEQT\n*Element Output, elset=AUDIT_C_TOP\nS22, LE22, DAMAGEC, DAMAGET, PEEQ, PEEQT\n*Element Output, elset=AUDIT_S_TRANS\nS22, LE22, PEEQ\n*Element Output, elset=PT_36x15p2-1.SET_PT_ALL_ELEMS\nS11\n*Contact Output, secondary=CSEG_02-1.SURF_BOTTOM, main=CSEG_01-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_03-1.SURF_BOTTOM, main=CSEG_02-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_04-1.SURF_BOTTOM, main=CSEG_03-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_05-1.SURF_BOTTOM, main=CSEG_04-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_06-1.SURF_BOTTOM, main=CSEG_05-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_07-1.SURF_BOTTOM, main=CSEG_06-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_08-1.SURF_BOTTOM, main=CSEG_07-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_09-1.SURF_BOTTOM, main=CSEG_08-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_10-1.SURF_BOTTOM, main=CSEG_09-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_11-1.SURF_BOTTOM, main=CSEG_10-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_12-1.SURF_BOTTOM, main=CSEG_11-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_13-1.SURF_BOTTOM, main=CSEG_12-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_14-1.SURF_BOTTOM, main=CSEG_13-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_15-1.SURF_BOTTOM, main=CSEG_14-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_16-1.SURF_BOTTOM, main=CSEG_15-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_17-1.SURF_BOTTOM, main=CSEG_16-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_18-1.SURF_BOTTOM, main=CSEG_17-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_19-1.SURF_BOTTOM, main=CSEG_18-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_20-1.SURF_BOTTOM, main=CSEG_19-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_21-1.SURF_BOTTOM, main=CSEG_20-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_22-1.SURF_BOTTOM, main=CSEG_21-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_23-1.SURF_BOTTOM, main=CSEG_22-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_24-1.SURF_BOTTOM, main=CSEG_23-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_25-1.SURF_BOTTOM, main=CSEG_24-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_26-1.SURF_BOTTOM, main=CSEG_25-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_27-1.SURF_BOTTOM, main=CSEG_26-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_28-1.SURF_BOTTOM, main=CSEG_27-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_29-1.SURF_BOTTOM, main=CSEG_28-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_30-1.SURF_BOTTOM, main=CSEG_29-1.SURF_TOP\nCFN, CFS, CAREA\n*Contact Output, secondary=CSEG_31-1.SURF_BOTTOM, main=CSEG_30-1.SURF_TOP\nCFN, CFS, CAREA\n*End Step\n";
const initial="0.005, 160.195, 1.e-7, 0.005\n";
const rebar="*Element Output, elset=REV04_ALL_REBAR\nS, LE, PEEQ\n";
const history="*Output, history, frequency=1\n";
const modes={
 precheck:{name:"HE_REV17_PRECHECK.inp",precheck:true},
 lean005:{name:"HE_REV17_EQ_LEAN005.inp",max:0.005},
 lean010:{name:"HE_REV17_EQ_LEAN010.inp",max:0.01},
 lean020:{name:"HE_REV17_EQ_LEAN020.inp",max:0.02},
 trial40:{name:"HE_REV17_EQ_TRIAL40.inp",max:0.01,period:40}
};
function one(s,a,b){if(s.indexOf(a)<0||s.indexOf(a)!==s.lastIndexOf(a))throw Error("Expected one source block: "+a.slice(0,70));return s.replace(a,b)}
function inspect(text){
 const counts={},parts=new Map(),instances=new Map(),materials=new Set(),materialRefs=[],steps=[],errors=[];
 const count=(k)=>counts[k]=(counts[k]||0)+1;
 let part=null,mode="",etype="",currentStep=null;
 const args=(line)=>Object.fromEntries(line.split(",").slice(1).map(x=>x.trim().split(/\s*=\s*/,2)).filter(x=>x.length===2).map(([a,b])=>[a.toUpperCase(),b.toUpperCase()]));
 const integer=x=>/^\d+$/.test(x)&&Number.isSafeInteger(Number(x))&&Number(x)>0;
 for(const raw of text.split(/\r?\n/)){
  const line=raw.trim();if(!line||line.startsWith("**"))continue;
  if(line.startsWith("*")){
   const k=line.slice(1).split(",")[0].trim().toUpperCase(),p=args(line);count(k);mode="";
   if(k==="PART"){if(part)errors.push("Nested part "+p.NAME);part={name:p.NAME,nodes:new Set(),elements:new Set(),connect:[]};if(!p.NAME||parts.has(p.NAME))errors.push("Duplicate or missing part "+p.NAME);parts.set(p.NAME,part);}
   else if(k==="END PART"){if(!part)errors.push("Unmatched END PART");else for(const [id,...n] of part.connect){if(n.some(x=>!part.nodes.has(x)))errors.push("Missing node "+part.name+":"+id)}part=null;}
   else if(k==="INSTANCE"){if(!p.NAME||!p.PART||instances.has(p.NAME))errors.push("Invalid instance "+p.NAME);instances.set(p.NAME,p.PART);}
   else if(k==="NODE"&&part)mode="node";
   else if(k==="ELEMENT"&&part){mode="element";etype=p.TYPE;if(!["C3D8R","C3D8I","T3D2","B31","MASS","ROTARYI"].includes(etype))errors.push("Unsupported audit element type "+etype);}
   else if(k==="MATERIAL"){if(!p.NAME||materials.has(p.NAME))errors.push("Invalid material "+p.NAME);materials.add(p.NAME);}
   else if(p.MATERIAL&&/SECTION$/.test(k))materialRefs.push(p.MATERIAL);
   else if(k==="STEP"){if(currentStep)errors.push("Nested step");currentStep=p.NAME||"(unnamed)";steps.push(currentStep);}
   else if(k==="END STEP"){if(!currentStep)errors.push("Unmatched END STEP");currentStep=null;}
   continue;
  }
  if(!part||!mode)continue;
  const f=line.split(",").map(x=>x.trim()).filter(Boolean);
  if(!integer(f[0])){errors.push("Invalid label "+part.name+":"+line.slice(0,60));continue}
  const id=Number(f[0]);
  if(mode==="node"){if(part.nodes.has(id))errors.push("Duplicate node "+part.name+":"+id);part.nodes.add(id);if(f.slice(1).some(x=>!Number.isFinite(Number(x.replace(/[dD]/g,"e")))))errors.push("Invalid coordinate "+part.name+":"+id);count("PART_NODES");}
  else{const n={C3D8R:8,C3D8I:8,T3D2:2,B31:2,MASS:1,ROTARYI:1}[etype];if(f.length!==n+1||f.slice(1).some(x=>!integer(x)))errors.push("Invalid connectivity "+part.name+":"+id);if(part.elements.has(id))errors.push("Duplicate element "+part.name+":"+id);part.elements.add(id);part.connect.push(f.map(Number));count("ELEMENT_"+etype);}
  if(errors.length>50)throw Error(errors.slice(0,10).join("; "));
 }
 if(part||currentStep)errors.push("Unclosed part or step");
 for(const [n,p] of instances)if(!parts.has(p))errors.push("Instance "+n+" references missing part "+p);
 for(const n of materialRefs)if(!materials.has(n))errors.push("Missing material "+n);
 const expect={PART:100,"END PART":100,INSTANCE:100,"END INSTANCE":100,ASSEMBLY:1,"END ASSEMBLY":1,"CONTACT PAIR":30,"EMBEDDED ELEMENT":62,TIE:5,"RIGID BODY":1,ELEMENT_C3D8R:2976,ELEMENT_C3D8I:7296,ELEMENT_T3D2:203812,ELEMENT_B31:150,ELEMENT_MASS:155,ELEMENT_ROTARYI:155};
 for(const [k,v] of Object.entries(expect))if(counts[k]!==v)errors.push(k+": expected "+v+", got "+counts[k]);
 if(steps.join("|")!=="PT_BALANCE|GRAVITY|GRAVITY_CHECK|MODAL_30|EQ_2H_RAYLEIGH_REL")errors.push("Unexpected analysis sequence "+steps.join("|"));
 if(errors.length)throw Error(errors.slice(0,20).join("; "));
 return {counts,steps,materialNames:[...materials],scope:"Part-level connectivity/material references, keyword counts and step sequence; not Abaqus data check."};
}
function reviseEQ(mode){
 const m=modes[mode];if(!m)throw Error("Unknown REV17 option");if(m.precheck)return "";
 let s=eq;
 s=one(s,initial,"0.005, "+(m.period||160.195)+", 1.e-7, "+m.max+"\n");
 // Keep full structural/contact field output 80 intervals; rebar fields at 10 intervals only.
 s=one(s,rebar,"");
 s=one(s,history,"*Output, field, op=ADD, number interval=10, time marks=NO\n"+rebar+history);
 // Preserve all per-increment history and restart settings for comparison.
 if((s.match(/\*Contact Output, secondary=/g)||[]).length!==30)throw Error("Contact history count changed");
 if(s.slice(s.indexOf(history))!==eq.slice(eq.indexOf(history)))throw Error("History changed");
 return s;
}
function apply(text,mode){
 const m=modes[mode];if(!m)throw Error("Unknown option");
 const report=inspect(text);
 if(!text.endsWith(eq))throw Error("REV16 earthquake block is not exact; refusing change");
 const prefix=text.slice(0,-eq.length);
 let out=prefix+reviseEQ(mode);
 const old="** Job name: HE_REV16_EQ_FLEX_RNA Model name: CONTACT_REV16_FLEX_RNA\n";
 const job=m.name.replace(/\.inp$/,"");
 out=one(out,old,"** Job name: "+job+" Model name: "+job+"\n");
 if(!m.precheck&&out.slice(out.lastIndexOf(history))!==text.slice(text.lastIndexOf(history)))throw Error("History preservation failed");
 return {text:out,file:m.name,report,period:m.precheck?0:m.period||160.195,maximumIncrement:m.max||null};
}
root.Rev17={inspect,reviseEQ,apply,modes,eq};
})(typeof window!=="undefined"?window:globalThis);
