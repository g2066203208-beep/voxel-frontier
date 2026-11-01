"use strict";
// OpenFAST v3.5.3 source-audited S06 nine-gage TP/RP/AL child OutList.
// Never changes frozen inputs; RP angles are NOT an exact DCM.
// ElastoDyn.f90 SHA256 a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3
// ElastoDyn_IO.f90 SHA256 af1c78a15e4102668f83740c8ad1fc450f7112cdcc2ce004093278acf75d1d5a
const fs=require("fs"),crypto=require("crypto"),path=require("path");
const suffixes=["TPxi","TPyi","RPxi","RPyi","RPzi","ALxt","ALyt","ALzt"];
const parents=new Set([
"e8c1653486cc96eaa5f32a28b01701df080bd2f185f851abd4ebf54a13ef23c7",
"7cce15fcb6ef0a0e6f9138850e4c66745450655d50d1ee59a7171b1e1530ce0f",
"bd59ed51c843f1ca9e82b2d3cd1441b2055e2b222a36636becc31bd54400c060",
"4c524f1e524d049c816f5fa44dea01f9c1d8e3a2e8cf34ca13ff45487655c4c7"]);
function ck(x,m){if(!x)throw Error(m);}
function sha(b){return crypto.createHash("sha256").update(b).digest("hex");}
function patch(src){
 const lines=src.replace(/\r\n/g,"\n").split("\n");
 ck(lines.filter(x=>/^\s*9\s+NTwGages\b/i.test(x)).length===1,"N_GAGES");
 const g=lines.filter(x=>/^\s*[\d,\s]+\s+TwrGagNd\b/i.test(x));
 ck(g.length===1,"GAGE_FIELD");
 const nodes=g[0].split(/\bTwrGagNd\b/i)[0].trim().split(/[\s,]+/).map(Number);
 ck(nodes.length===9&&nodes.every(Number.isInteger)&&new Set(nodes).size===9,"GAGE_NODES");
 const marks=lines.map((x,i)=>/^\s*OutList\b/i.test(x)?i:-1).filter(i=>i>=0);
 ck(marks.length===1,"OUTLIST_MARK");
 const ends=lines.map((x,i)=>i>marks[0]&&/^\s*END\s*(?:!.*)?$/i.test(x)?i:-1).filter(i=>i>=0);
 ck(ends.length===1,"OUTLIST_END");
 const end=ends[0],body=lines.slice(marks[0]+1,end).join("\n");
 const names=new Set([...body.matchAll(/["']([A-Za-z][A-Za-z0-9]*)["']/g)].map(m=>m[1].toUpperCase()));
 for(let i=1;i<=9;i++)ck(names.has("TWHT"+i+"TPZI"),"ORIGINAL_TPZI_"+i);
 const add=[];
 for(let i=1;i<=9;i++)for(const s of suffixes){
  const n="TwHt"+i+s;if(!names.has(n.toUpperCase())){add.push('  "'+n+'"');names.add(n.toUpperCase());}
 }
 ck(names.size<=863,"MAXOUTPTS");
 return {text:[...lines.slice(0,end),...add,...lines.slice(end)].join("\n"),added:add.length,nodes};
}
function cross(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
function transport(F,M,rA,rB){
 for(const x of [F,M,rA,rB])ck(x.length===3&&x.every(Number.isFinite),"NONFINITE_WRENCH");
 const d=rA.map((v,i)=>v-rB[i]),c=cross(d,F);
 return M.map((v,i)=>v+c[i]);
}
function selftest(){
 const x='9 NTwGages\n13,39,65,91,117,142,168,194,220 TwrGagNd\nOutList\n'+
 Array.from({length:9},(_,i)=>'"TwHt'+(i+1)+'TPzi"').join("\n")+'\nEND\n';
 const a=patch(x);ck(a.added===72&&patch(a.text).added===0,"POSE_72_IDEMPOTENT");
 const bad=[s=>s.replace("END","STOP"),s=>s.replace("OutList","WRONG"),
 s=>s.replace("9 NTwGages","8 NTwGages"),s=>s.replace('"TwHt1TPzi"','"BAD"'),
 s=>s.replace("OutList","OutList\nOutList"),s=>s.replace("END","END\nEND"),
 s=>s.replace("13,39","13,13"),s=>s.replace('"TwHt9TPzi"','"TwHt10TPzi"')];
 let reject=0;for(const f of bad){try{patch(f(x))}catch(e){reject++;continue}throw Error("BAD_ACCEPTED");}
 ck(reject===8,"NEGATIVE_COUNT");
 ck(JSON.stringify(transport([2,-3,5],[7,11,13],[0,0,10],[0,0,4]))===JSON.stringify([25,23,13]),"WRENCH_SIGN");
 ck(JSON.stringify(transport([2,-3,5],[25,23,13],[0,0,4],[0,0,10]))===JSON.stringify([7,11,13]),"WRENCH_REVERSE");
 let rejectNan=false;try{transport([NaN,0,0],[0,0,0],[0,0,0],[0,0,0])}catch(e){rejectNan=true}
 ck(rejectNan,"NONFINITE_REJECT");
 return {status:"SYNTHETIC_TEST_PASS",added_per_batch:72,negative_rejections:reject,
 wrench_transport:"PASS",wrench_reverse:"PASS",nonfinite_rejection:"PASS",exact_DCM:false,physical_pass:false};
}
function main(a){
 if(a.length===1&&a[0]==="--selftest"){console.log(JSON.stringify(selftest()));return;}
 ck(a.length===3&&a[0]==="--patch","USAGE --selftest | --patch verified_parent.dat new_child.dat");
 const input=path.resolve(a[1]),output=path.resolve(a[2]);
 ck(input!==output&&!fs.existsSync(output),"NO_OVERWRITE");
 const b=fs.readFileSync(input),hash=sha(b);
 ck(parents.has(hash),"UNVERIFIED_2S_ETM_PARENT_SHA");
 const p=patch(b.toString("utf8"));ck(p.added===72,"EXPECTED_72_ADDITIONS");
 fs.writeFileSync(output,p.text,"utf8");
 console.log(JSON.stringify({parent_sha256:hash,child_sha256:sha(fs.readFileSync(output)),
 added:p.added,nodes:p.nodes,exact_DCM:false,physical_pass:false}));
}
module.exports={patch,transport,selftest,parents};
if(require.main===module)main(process.argv.slice(2));
