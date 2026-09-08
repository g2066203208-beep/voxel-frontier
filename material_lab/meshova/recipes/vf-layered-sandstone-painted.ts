import { C, G, M, S, TAU, hash, wrapDelta, periodicField, finalize, makeTexture, type RGB } from "./vf-painterly-core.js";

export type VfLayeredSandstoneParams = {
  seed?: number;
  bands?: number;
  minSlabs?: number;
  maxSlabs?: number;
  crackChance?: number;
  chipStrength?: number;
  relief?: number;
  normalStrength?: number;
};

type RockBlock = {
  cx:number; cy:number; hw:number; hh:number; angle:number;
  base:number; lift:number; warm:number; cool:number; macro:boolean;
  bevel:number; strata:number[]; crack:boolean; crackX:number; crackTilt:number;
  chipX:number; chipY:number; chip:number;
  planes:[number,number,number][];
};

function makeBlock(seed:number,row:number,id:number,cx:number,cy:number,hw:number,hh:number,base:number,lift:number,macro:boolean,crackChance:number):RockBlock{
  const strata:number[]=[];
  const strataCount=macro?3:2;
  for(let k=0;k<strataCount;k++) strata.push(-0.58+hash(seed,row,id,40+k)*1.16);
  const planes:[number,number,number][]=[];
  for(let k=0;k<5;k++) planes.push([
    (hash(seed,row,id,60+k*3)-.5)*1.35,
    (hash(seed,row,id,61+k*3)-.5)*1.05,
    (hash(seed,row,id,62+k*3)-.5)*.34,
  ]);
  return {
    cx:(cx+2)%1, cy:(cy+2)%1, hw, hh,
    angle:(hash(seed,row,id,5)-.5)*(macro?.22:.14),
    base, lift, warm:hash(seed,row,id,6), cool:hash(seed,row,id,7), macro,
    bevel:macro?.18:.15,
    strata,
    crack:hash(seed,row,id,8)<crackChance,
    crackX:(hash(seed,row,id,9)-.5)*.34,
    crackTilt:(hash(seed,row,id,10)-.5)*.18,
    chipX:(hash(seed,row,id,11)<.5?-1:1)*(.68+hash(seed,row,id,12)*.18),
    chipY:(hash(seed,row,id,13)-.5)*1.2,
    chip:hash(seed,row,id,14),
    planes,
  };
}

function buildBlocks(seed:number,bands:number,minSlabs:number,maxSlabs:number,crackChance:number):RockBlock[]{
  const out:RockBlock[]=[];
  const rows=Math.max(4,Math.min(6,bands));
  const rowStep=1/rows;
  for(let row=0;row<rows;row++){
    // Support mass must fill the shell, never read as one or two long horizontal planks.
    const requested=minSlabs+Math.floor(hash(seed,row,101)*(maxSlabs-minSlabs+1));
    const count=Math.max(3,Math.min(4,requested+1));
    const raw:number[]=[]; let total=0;
    for(let i=0;i<count;i++){const w=.82+hash(seed,row,i,102)*.48;raw.push(w);total+=w;}
    let cursor=-.025+(hash(seed,row,103)-.5)*.03;
    for(let i=0;i<count;i++){
      const frac=raw[i]/total;
      const cx=cursor+frac*.5; cursor+=frac;
      out.push(makeBlock(
        seed,row,i,cx,
        (row+.5)/rows+(hash(seed,row,i,104)-.5)*rowStep*.20,
        (frac+.032)*.60,
        rowStep*(.62+hash(seed,row,i,105)*.12),
        .462+(hash(seed,row,i,106)-.5)*.016,
        .065+hash(seed,row,i,107)*.025,
        false,crackChance*.24,
      ));
    }
  }

  const hero:[number,number,number,number,number,number][]=[
    [.56,.52,.235,.19,.555,.245], [.29,.47,.18,.17,.535,.205], [.81,.45,.17,.17,.525,.195],
    [.39,.70,.20,.16,.535,.205], [.70,.70,.19,.16,.525,.195], [.16,.65,.14,.17,.515,.175],
    [.57,.29,.18,.135,.525,.185], [.31,.27,.14,.12,.505,.155], [.82,.27,.135,.12,.505,.15],
    [.55,.86,.18,.12,.505,.16], [.26,.84,.13,.105,.495,.145], [.82,.84,.13,.105,.495,.145],
  ];
  for(let i=0;i<hero.length;i++){
    const [cx,cy,hw,hh,base,lift]=hero[i];
    out.push(makeBlock(seed,90,i,
      cx+(hash(seed,90,i,1)-.5)*.025,
      cy+(hash(seed,90,i,2)-.5)*.025,
      hw*(.98+hash(seed,90,i,3)*.10),
      hh*(.98+hash(seed,90,i,4)*.10),
      base+(hash(seed,90,i,15)-.5)*.018,
      lift*(.94+hash(seed,90,i,16)*.14),
      true,crackChance*(i===0?1.55:.9),
    ));
  }
  return out;
}

function blockShape(x:number,y:number){
  const ax=Math.abs(x), ay=Math.abs(y);
  const chamfer=(ax+ay)*.71;
  return Math.max(ax*.92,ay*.96,chamfer);
}

export function bakeVfLayeredSandstonePainted(size:number,p:VfLayeredSandstoneParams={}){
  const seed=Math.floor(p.seed??771231);
  const bands=Math.max(4,Math.min(6,Math.floor(p.bands??5)));
  const minSlabs=Math.max(2,Math.floor(p.minSlabs??2));
  const maxSlabs=Math.max(minSlabs,Math.min(4,Math.floor(p.maxSlabs??3)));
  const crackChance=C(p.crackChance??.17);
  const chipStrength=C(p.chipStrength??.92);
  const relief=Math.max(.75,Math.min(1.8,p.relief??1.20));
  const normalStrength=Math.max(2,Math.min(20,p.normalStrength??12.8));
  const blocks=buildBlocks(seed,bands,minSlabs,maxSlabs,crackChance);

  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.030,.018,.026], deep:RGB=[.075,.045,.052], cool:RGB=[.105,.125,.175], mid:RGB=[.34,.145,.075], light:RGB=[.625,.34,.17], ochre:RGB=[.86,.56,.27], cream:RGB=[.94,.72,.40];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      let best=.462+periodicField(u,v,seed+700,2)*.010;
      let second=best-.018,bestId=-1,bestEdge=0,bestCrack=0,bestChip=0,bestFacet=0,bestStrata=0,bx=0,by=0;

      for(let id=0;id<blocks.length;id++){
        const q=blocks[id];
        const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy);
        const ca=Math.cos(q.angle),sa=Math.sin(q.angle);
        const rx=dx*ca+dy*sa, ry=-dx*sa+dy*ca;
        if(Math.abs(rx)>q.hw*1.14||Math.abs(ry)>q.hh*1.14)continue;
        const x=rx/Math.max(q.hw,1e-6), y=ry/Math.max(q.hh,1e-6);
        const shape=blockShape(x,y)+periodicField(x*.23+id*.11,y*.23-id*.09,seed+id*29,2)*.016;
        if(shape>1.04)continue;
        const edge=S((1-shape)/q.bevel);
        const body=S((1-shape)/(q.bevel*1.35));

        let top=-99,secondPlane=-99;
        for(const [a,b,c] of q.planes){
          const plane=a*x+b*y+c;
          if(plane>top){secondPlane=top;top=plane;}else if(plane>secondPlane)secondPlane=plane;
        }
        const facet=(top*.045)+(top-secondPlane)*.020;
        const hardFacet=Math.round(facet/.015)*.015*body;

        let strata=0;
        for(let k=0;k<q.strata.length;k++){
          const s=q.strata[k]+Math.sin((x*.55+q.warm+k*.17)*TAU)*.014;
          const lip=G((y-s)/(.028+k*.002))*body;
          strata+=lip*(y>s?.010:-.005);
        }
        const topShelf=G((y-.62)/.13)*body*(q.macro?.020:.010);
        const lowerCut=G((y+.72)/.12)*body*(q.macro?.016:.008);

        let crack=0;
        if(q.crack){
          const line=q.crackX+q.crackTilt*y+periodicField(u,v,seed+id*41,2)*.010;
          crack=G((x-line)/(q.macro?.014:.018))*S((y+.76)/.13)*S((.78-y)/.13)*body;
        }
        const chip=q.chip>.52?G((x-q.chipX)/(q.macro?.105:.13))*G((y-q.chipY)/(q.macro?.13:.16))*chipStrength*body:0;

        let surf=q.base+q.lift*(.12+.88*body)+hardFacet+strata+topShelf-lowerCut;
        surf+=q.macro?periodicField(x*.31+q.cx,y*.31+q.cy,seed+id*53,2)*.008*body:0;
        surf-=crack*(q.macro?.115:.072);
        surf-=chip*(q.macro?.060:.036);
        surf-=(1-edge)*(q.macro?.018:.012);
        surf=.5+(surf-.5)*relief;

        if(surf>best){
          second=best;best=surf;bestId=id;bestEdge=edge;bestCrack=crack;bestChip=chip;bestFacet=hardFacet;bestStrata=Math.abs(strata);bx=x;by=y;
        }else if(surf>second)second=surf;
      }

      const overlap=C((best-second)/.050);
      const seam=C((1-overlap)*.65+(bestId<0?.30:0));
      const cavity=C(seam*.45+(1-bestEdge)*.18+bestCrack*.92+bestChip*.42);
      let col:RGB=[.25,.105,.067];
      let rr=.82,aa=.84;
      if(bestId>=0){
        const q=blocks[bestId];
        const planeLight=C(.48+bestFacet*5.0-by*.08+bx*.025);
        col=M(mid,light,C(.30+(best-.48)*1.75));
        col=M(col,ochre,C(planeLight*.20+q.warm*.07));
        col=M(col,cool,C((.52-planeLight)*.26+q.cool*.055));
        col=M(col,cream,C(bestStrata*3.0+Math.max(0,bestFacet)*.20));
        col=M(col,deep,C(cavity*.46));
        col=M(col,ink,C(bestCrack*.96+seam*.18));
        const wash=periodicField(u,v,seed+920+bestId*17,2);
        col=M(col,wash>0?ochre:cool,Math.abs(wash)*.060*bestEdge);
        rr=C(.70+(1-bestEdge)*.12+bestCrack*.20+bestChip*.08+seam*.05-bestStrata*.05);
        aa=C(1-cavity*.40-bestCrack*.14);
      }else{
        col=M(mid,cool,.18);col=M(col,deep,seam*.34);rr=.88;aa=.82;
      }

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=C(best);roughness.data[i]=rr;ao.data[i]=aa;
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
