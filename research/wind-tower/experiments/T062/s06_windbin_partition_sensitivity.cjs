'use strict';
// Source-level S06 bin-partition sensitivity, not a wind-load simulation.
// node s06_windbin_partition_sensitivity.cjs --self-test
// node s06_windbin_partition_sensitivity.cjs --write
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const names=['S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv','S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv'];
const locks=['e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102','d57ff9e71b58b531b1aaa357ad7a57a86daf529e061f9d8996cf2453b04a7da5'];
const sha=s=>crypto.createHash('sha256').update(s,'utf8').digest('hex');
function parse(s){const l=s.trim().split(/\r?\n/),h=l.shift().split(',');return l.map(line=>{const v=line.split(',');assert.equal(v.length,h.length);return Object.fromEntries(h.map((k,i)=>[k,v[i]]))})}
function load(i){const s=fs.readFileSync(path.join(__dirname,names[i]),'utf8');assert.equal(sha(s),locks[i],'source hash');return parse(s)}
function compute(bins,cases){
 const total=bins.reduce((s,x)=>s+ +x.hours,0),oper=bins.filter(x=>+x.bin_lower_mps>=4&&+x.bin_lower_mps<25).reduce((s,x)=>s+ +x.hours,0);
 assert.equal(bins.length,31);assert.equal(total,184080);assert.equal(oper,106900);assert.equal(cases.length,18);
 assert.equal(new Set(cases.map(x=>x.fst_sha256)).size,1);assert.equal(new Set(cases.map(x=>x.tower_sha256)).size,1);assert.equal(new Set(cases.map(x=>x.outb_sha256)).size,18);
 const bySpeed=new Map();
 for(const x of cases){const m=/^U(\d+)p(\d+)_NTM_S(\d\d)$/.exec(x.case);assert(m);const u=+(m[1]+'.'+m[2]);if(!bySpeed.has(u))bySpeed.set(u,new Set());bySpeed.get(u).add(m[3])}
 assert.deepEqual([...bySpeed.keys()].sort((a,b)=>a-b),[9.343881,11.4,19.20214]);
 for(const seeds of bySpeed.values())assert.equal(seeds.size,6);
 const rows=[];
 for(let w=1;w<=4;w++)for(let p=0;p<w;p++){
  const ed=[4];if(p)ed.push(4+p);while(ed.at(-1)<25)ed.push(Math.min(25,ed.at(-1)+w));
  const cells=new Set();
  for(const u of bySpeed.keys()){const i=ed.findIndex((v,j)=>j<ed.length-1&&u>=v&&u<ed[j+1]);assert(i>=0);cells.add(ed[i]+'-'+ed[i+1])}
  const n=bins.filter(x=>[...cells].some(c=>{const [lo,hi]=c.split('-').map(Number);return +x.bin_lower_mps>=lo&&+x.bin_lower_mps<hi})).reduce((s,x)=>s+ +x.hours,0);
  let oracle=0;for(const cell of cells){const [lo,hi]=cell.split('-').map(Number);oracle+=bins.filter(x=>+x.bin_lower_mps>=lo&&+x.bin_upper_mps_exclusive<=hi).reduce((s,x)=>s+ +x.hours,0)}
  assert.equal(n,oracle);assert(n<=oper);rows.push({w,p,n,k:cells.size,c:[...cells],all:100*n/total,cond:100*n/oper});
 }
 assert.equal(rows.length,10);assert.equal(rows[0].n,7164);assert.equal(rows[8].n,54977);assert.equal(rows[7].n,11002);return rows
}
function csv(rows){return 'bin_width_mps,first_partial_width_mps,distinct_occupied_bins,retrospective_era5_hours,share_all_hours_pct,share_diagnostic_4_25_hours_pct,occupied_intervals,formal_DLC12_validated_slots\n'+rows.map(x=>[x.w,x.p,x.k,x.n,x.all.toFixed(9),x.cond.toFixed(9),x.c.join('|'),0].join(',')).join('\n')+'\n'}
function svg(rows){const l=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="555" viewBox="0 0 1080 555">','<rect width="1080" height="555" fill="white"/>','<text x="45" y="39" font-family="Arial" font-size="22" font-weight="bold">Wind-bin occupancy depends on arbitrary partition</text>','<text x="45" y="63" font-family="Arial" font-size="14">Same 18 NTM sources / 184,080 ERA5 hours / zero validated DLC1.2 slots</text>'];for(let i=0;i<rows.length;i++){const x=rows[i],y=94+i*39,color=i===8?'#c16b39':i===0?'#295c80':'#8298a7';l.push('<text x="45" y="'+(y+19)+'" font-family="Arial" font-size="15">'+x.w+' m width / '+x.p+' m phase</text>','<rect x="305" y="'+y+'" width="'+(x.all*18).toFixed(2)+'" height="24" fill="'+color+'"/>','<text x="'+(316+x.all*18).toFixed(2)+'" y="'+(y+19)+'" font-family="Arial" font-size="14">'+x.all.toFixed(3)+'% ('+x.n+' h)</text>')}l.push('<text x="45" y="513" font-family="Arial" font-size="14">Integer boundaries only, diagnostic [4,25) m/s. Three actual speeds: 9.343881, 11.4, 19.202140 m/s.</text>','<text x="45" y="538" font-family="Arial" font-size="14">Bin occupancy is not physical load validation, interpolation or an IEC sampling plan.</text>','</svg>');return l.join('\n')+'\n'}
if(require.main===module){const bins=load(0),cases=load(1),rows=compute(bins,cases);if(process.argv.includes('--self-test')){assert.throws(()=>assert.equal(sha('X'+fs.readFileSync(path.join(__dirname,names[0]),'utf8')),locks[0]));assert.throws(()=>compute(bins.slice(1),cases));assert.throws(()=>compute(bins,cases.slice(1)));console.log('SELF_TEST_PASS 10 partitions / 18 identities / 3 negative tests')}else if(process.argv.includes('--write')){const c=csv(rows),s=svg(rows);fs.writeFileSync(path.join(__dirname,'S06_NTM18_BIN_PARTITION_SENSITIVITY_10ROW_20261112.csv'),c);fs.writeFileSync(path.join(__dirname,'../../manuscript/final-thesis/figures/FIG3_S06_BIN_PARTITION_SENSITIVITY_20261112.svg'),s);console.log('WROTE',sha(c),sha(s))}else process.stdout.write(csv(rows))}
module.exports={compute,csv,svg};
