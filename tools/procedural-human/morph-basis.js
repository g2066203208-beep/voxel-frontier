const ROOT = 'https://raw.githubusercontent.com/naver/anny/main/src/anny/data/mpfb2/targets';
const MACRO = `${ROOT}/macrodetails`;

const clamp = (v,a,b)=>Math.min(b,Math.max(a,v));

function weights3(t){
  t=clamp(t,0,1);
  if(t<=0.5) return [1-2*t,2*t,0];
  return [0,2-2*t,2*t-1];
}

async function gunzipText(url){
  const res=await fetch(url,{cache:'force-cache'});
  if(!res.ok) throw new Error(`Morph HTTP ${res.status}: ${url.split('/').pop()}`);
  if(!('DecompressionStream' in globalThis)) throw new Error('This browser needs DecompressionStream(gzip).');
  const stream=res.body.pipeThrough(new DecompressionStream('gzip'));
  return await new Response(stream).text();
}

function parseTarget(text,master){
  const out=new Float32Array(master.vertices.length*3);
  const {sourceFrame}=master;
  const H=sourceFrame.ranges[sourceFrame.up];
  for(const raw of text.split(/\r?\n/)){
    const line=raw.trim();
    if(!line||line[0]==='#') continue;
    const p=line.split(/\s+/);
    if(p.length<4) continue;
    const sourceId=Number(p[0]);
    const compactId=master.sourceToCompact.get(sourceId);
    if(compactId===undefined) continue;
    const d=[Number(p[1]),Number(p[2]),Number(p[3])];
    const i=compactId*3;
    out[i]=d[sourceFrame.width]/H;
    out[i+1]=d[sourceFrame.up]/H;
    out[i+2]=d[sourceFrame.depth]/H;
  }
  return out;
}

async function loadTarget(master,path){
  return parseTarget(await gunzipText(`${ROOT}/${path}`),master);
}

function addScaled(dst,src,w){
  if(Math.abs(w)<1e-8) return;
  for(let i=0;i<dst.length;i++) dst[i]+=src[i]*w;
}

/**
 * A compact browser rewrite of Anny/MakeHuman's adult phenotype interpolation.
 * We deliberately start with the adult `young` macro surface only:
 * gender x muscle x weight plus normalized ancestry components.
 * Local anthropometric controls are layered afterwards by human-core.js.
 */
export async function loadAdultPhenotypeBasis(master,onProgress=()=>{}){
  const genders=['male','female'];
  const muscles=['minmuscle','averagemuscle','maxmuscle'];
  const weights=['minweight','averageweight','maxweight'];
  const races=['african','asian','caucasian'];
  const universal=new Map();
  const race=new Map();

  const tasks=[];
  for(const gender of genders) for(const muscle of muscles) for(const weight of weights){
    const name=`universal-${gender}-young-${muscle}-${weight}.target.gz`;
    tasks.push((async()=>{
      universal.set(`${gender}|${muscle}|${weight}`,await loadTarget(master,`macrodetails/${name}`));
      onProgress();
    })());
  }
  for(const gender of genders) for(const r of races){
    const name=`${r}-${gender}-young.target.gz`;
    tasks.push((async()=>{
      race.set(`${r}|${gender}`,await loadTarget(master,`macrodetails/${name}`));
      onProgress();
    })());
  }
  await Promise.all(tasks);

  return {
    source:'Anny/MPFB2 CC0 sparse target displacement fields',
    targetCount:tasks.length,
    evaluate(params){
      const out=new Float32Array(master.vertices.length*3);
      // Existing UI: sex=-1 means feminine, +1 means masculine.
      const female=clamp((1-params.sex)/2,0,1);
      const gw={male:1-female,female};
      const mw=weights3((clamp(params.muscle,-1,1)+1)/2);
      const ww=weights3((clamp(params.bodyFat,-1,1)+1)/2);

      for(const gender of genders){
        const g=gw[gender];
        for(let mi=0;mi<muscles.length;mi++) for(let wi=0;wi<weights.length;wi++){
          addScaled(out,universal.get(`${gender}|${muscles[mi]}|${weights[wi]}`),g*mw[mi]*ww[wi]);
        }
      }

      // Equal ancestry mixture is the neutral default. This is exactly the
      // normalized race block semantics used by Anny when all three are equal.
      for(const gender of genders) for(const r of races){
        addScaled(out,race.get(`${r}|${gender}`),gw[gender]/3);
      }
      return out;
    }
  };
}
