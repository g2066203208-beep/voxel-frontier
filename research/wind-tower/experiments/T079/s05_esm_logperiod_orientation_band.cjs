#!/usr/bin/env node
// S05 source-level spectrum diagnostic. No target design spectrum or physical tower response.
const fs=require('fs'),crypto=require('crypto');
const source=process.argv[2];
if(!source) throw Error('usage: node s05_esm_logperiod_orientation_band.cjs <46period.csv>');
const bytes=fs.readFileSync(source);const sha=crypto.createHash('sha256').update(bytes).digest('hex');
const expected=''; // supply --sha in provenance report; GitHub blob SHA is not SHA256
const lines=bytes.toString('utf8').trim().split(/\r?\n/);
const headers=lines.shift().split(',');
for(const k of ['period_s','RotD50_PSA_m_s2','RotD100_PSA_m_s2','f_over_reported_SNR_0p09Hz']) if(!headers.includes(k)) throw Error('missing '+k);
const rows=lines.map(l=>{const a=l.split(',');if(a.length!==headers.length)throw Error('malformed row');const o=Object.fromEntries(headers.map((k,i)=>[k,a[i]]));for(const k of ['period_s','RotD50_PSA_m_s2','RotD100_PSA_m_s2','f_over_reported_SNR_0p09Hz']){o[k]=Number(o[k]);if(!Number.isFinite(o[k])||o[k]<=0)throw Error('invalid '+k)}return o});
if(rows.length!==46)throw Error('unexpected source length');
for(let i=1;i<rows.length;i++)if(rows[i].period_s<=rows[i-1].period_s)throw Error('period order');
const integrate=(r,key)=>{if(r.length<2)throw Error('insufficient');let total=0,width=0;for(let i=1;i<r.length;i++){const d=Math.log(r[i].period_s/r[i-1].period_s);total+=d*(Math.log(r[i-1][key])+Math.log(r[i][key]))/2;width+=d}return {mean:Math.exp(total/width),width}};
const band=rows.filter(x=>x.period_s>=4&&x.period_s<=10),q=band.filter(x=>x.f_over_reported_SNR_0p09Hz>=1.5);
for(const [name,r] of [['observed_4_10',band],['snr_1p5',q]]){if(r.length<2)throw Error('empty band');const a=integrate(r,'RotD50_PSA_m_s2'),b=integrate(r,'RotD100_PSA_m_s2');process.stdout.write(JSON.stringify({name,points:r.length,min_T:r[0].period_s,max_T:r.at(-1).period_s,logwidth:a.width,geometric_RotD50_PSA_m_s2:a.mean,geometric_RotD100_PSA_m_s2:b.mean,orientation_ratio:b.mean/a.mean,source_sha256:sha})+'\n')}
