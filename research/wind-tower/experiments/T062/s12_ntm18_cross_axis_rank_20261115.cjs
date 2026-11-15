// Source-level cross-axis rank falsification, historical 18 NTM cases only.
// Usage: node research/wind-tower/experiments/T062/s12_ntm18_cross_axis_rank_20261115.cjs
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path'),assert=require('node:assert/strict');
const source=path.join(__dirname,'S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv');
const bytes=fs.readFileSync(source);
const hash=crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(hash,'95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f','source SHA256 mismatch');
const lines=bytes.toString('utf8').trim().split(/\r?\n/),cols=lines.shift().split(',');
const ix=Object.fromEntries(cols.map((k,i)=>[k,i]));
const rows=lines.map(s=>s.split(','));
assert.equal(rows.length,1080);
const names=[...new Set(rows.map(r=>r[ix.case]))].sort();assert.equal(names.length,18);
function series(channel){return names.map(n=>{const match=rows.filter(r=>r[ix.case]===n&&r[ix.channel]===channel);assert.equal(match.length,1);const v=Number(match[0][ix.DEL_m4_Nref600]);assert(Number.isFinite(v)&&v>0);return v;});}
const x=series('TwrBsMxt'),y=series('TwrBsMyt');
let concordant=0,discordant=0,ties=0;
for(let i=0;i<18;i++)for(let j=i+1;j<18;j++){const d=(x[i]-x[j])*(y[i]-y[j]);if(d>0)concordant++;else if(d<0)discordant++;else ties++;}
assert.equal(concordant+discordant+ties,153);
assert.deepEqual([concordant,discordant,ties],[126,27,0]);
const rank=a=>a.map(v=>1+a.filter(w=>w>v).length);
const rx=rank(x),ry=rank(y);assert.equal(names[rx.indexOf(1)],'U19p202140_NTM_S04');assert.equal(names[ry.indexOf(1)],'U19p202140_NTM_S04');
console.log(JSON.stringify({source_sha256:hash,case_count:18,comparisons:153,concordant,discordant,ties,kendall_tau:(concordant-discordant)/153,top_case:names[rx.indexOf(1)],rankings:names.map((case_id,i)=>({case_id,Mx_rank:rx[i],My_rank:ry[i]}))},null,2));
