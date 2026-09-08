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
    angle:(hash(seed,row,id,5)-.5)*(macro?.24:.15),
    base, lift, warm:hash(seed,row,id,6), cool:hash(seed,row,id,7), macro,
    bevel:macro?.24:.17,
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

  // Continuous but deliberately LOW support mass. It closes holes and nothing more.
  for(let row=0;row<rows;row++){
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
        (frac+.030)*.58,
        rowStep*(.60+hash(seed,row,i,105)*.10),
        .420+(hash(seed,row,i,106)-.5)*.010,
        .030+hash(seed,row,i,107)*.018,
        false,crackChance*.16,
      ));
    }
  }

  // Sparse hero outcrops: broad footprint, huge elevation delta, thick shoulders.
  // Two of them deliberately straddle periodic seams so real displacement breaks the sphere silhouette.
  const hero:[number,number,number,number,number,number][]=[
    [.57,.53,.215,.175,.505,.310],
    [.27,.46,.155,.145,.485,.255],
    [.82,.43,.150,.150,.480,.245],
    [.39,.73,.175,.145,.490,.265],
    [.73,.72,.165,.145,.485,.250],
    [.56,.27,.165,.120,.480,.235],
    [.035,.56,.145,.185,.510,.345],
    [.58,.035,.185,.115,.500,.305],
  ];
  for(let i=0;i<hero.length;i++){
    const [cx,cy,hw,hh,base,lift]=hero[i];
    out.push(makeBlock(seed,90,i,
      cx+(hash(seed,90,i,1)-.5)*.020,
      cy+(hash(seed,90,i,2)-.5)*.020,
      hw*(.98+hash(seed,90,i,3)*.08),
      hh*(.98+hash(seed,90,i,4)*.08),
      base+(hash(seed,90,i,15)-.5)*.012,
      lift*(.96+hash(seed,90,i,16)*.10),
      true,crackChance*(i===0?1.35:.72),
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
  const crackChance=C(p.crackChance??.14);
  const chipStrength=C(p.chipStrength??.84);
  const relief=Math.max(.75,Math.min(1.8,p.relief??1.18));
  const normalStrength=Math.max(2,Math.min(20,p.normalStrength??13.2));
  const blocks=buildBlocks(seed,bands,minSlabs,maxSlabs,crackChance);

  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.026,.015,.024], deep:RGB=[.065,.040,.052], cool:RGB=[.105,.125,.180], mid:RGB=[.33,.135,.070], light:RGB=[.64,.35,.175], ochre:RGB=[.88,.57,.27], cream:RGB=[.95,.74,.41];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      let best=.404+periodicField(u,v,seed+700,2)*.007;
      let second=best-.012,bestId=-1,bestEdge=0,bestCrack=0,bestChip=0,bestFacet=0,bestStrata=0,bx=0,by=0;

      for(let id=0;id<blocks.length;id++){
        const q=blocks[id];
        const dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy);
        const ca=Math.cos(q.angle),sa=Math.sin(q.angle);
        const rx=dx*ca+dy*sa, ry=-dx*sa+dy*ca;
        if(Math.abs(rx)>q.hw*1.18||Math.abs(ry)>q.hh*1.18)continue;
        const x=rx/Math.max(q.hw,1e-6), y=ry/Math.max(q.hh,1e-6);
        const shape=blockShape(x,y)+periodicField(x*.23+id*.11,y*.23-id*.09,seed+id*29,2)*.013;
        if(shape>1.045)continue;

        const edge=S((1-shape)/q.bevel);
        const body=S((1-shape)/(q.bevel*(q.macro?1.62:1.18)));

        let top=-99,secondPlane=-99;
        for(const [a,b,c] of q.planes){
          const plane=a*x+b*y+c;
          if(plane>top){secondPlane=top;top=plane;}else if(plane>secondPlane)secondPlane=plane;
        }
        const facet=(top*(q.macro?.050:.024))+(top-secondPlane)*(q.macro?.022:.010);
        const hardFacet=Math.round(facet/(q.macro?.017:.010))*(q.macro?.017:.010)*body;

        let strata=0;
        for(let k=0;k<q.strata.length;k++){
          const s=q.strata[k]+Math.sin((x*.55+q.warm+k*.17)*TAU)*.012;
          const lip=G((y-s)/(.027+k*.002))*body;
          strata+=lip*(y>s?(q.macro?.012:.006):(q.macro?-.006:-.003));
        }
        const topShelf=G((y-.60)/.14)*body*(q.macro?.025:.008);
        const lowerCut=G((y+.70)/.13)*body*(q.macro?.018:.006);

        let crack=0;
        if(q.crack){
          const line=q.crackX+q.crackTilt*y+periodicField(u,v,seed+id*41,2)*.008;
          crack=G((x-line)/(q.macro?.011:.017))*S((y+.76)/.13)*S((.78-y)/.13)*body;
        }
        const chip=q.chip>.58?G((x-q.chipX)/(q.macro?.11:.14))*G((y-q.chipY)/(q.macro?.14:.17))*chipStrength*body:0;

        let surf=q.base+q.lift*(.035+.965*body)+hardFacet+strata+topShelf-lowerCut;
        surf+=q.macro?periodicField(x*.31+q.cx,y*.31+q.cy,seed+id*53,2)*.008*body:0;
        surf-=crack*(q.macro?.125:.045);
        surf-=chip*(q.macro?.055:.022);
        surf-=(1-edge)*(q.macro?.008:.006);
        surf=.5+(surf-.5)*relief;

        if(surf>best){
          second=best;best=surf;bestId=id;bestEdge=edge;bestCrack=crack;bestChip=chip;bestFacet=hardFacet;bestStrata=Math.abs(strata);bx=x;by=y;
        }else if(surf>second)second=surf;
      }

      const overlap=C((best-second)/.070);
      const seam=C((1-overlap)*.45+(bestId<0?.16:0));
      const cavity=C(seam*.32+(1-bestEdge)*.11+bestCrack*.95+bestChip*.32);
      let col:RGB=[.22,.090,.065];
      let rr=.84,aa=.86;
      if(bestId>=0){
        const q=blocks[bestId];
        const planeLight=C(.48+bestFacet*6.0-by*.09+bx*.030);
        col=M(mid,light,C(.24+(best-.42)*1.62));
        col=M(col,ochre,C(planeLight*.23+q.warm*.075+(q.macro?.045:0)));
        col=M(col,cool,C((.54-planeLight)*.31+q.cool*.060));
        col=M(col,cream,C(bestStrata*3.6+Math.max(0,bestFacet)*.26));
        col=M(col,deep,C(cavity*.48));
        col=M(col,ink,C(bestCrack*.98+seam*.12));
        const wash=periodicField(u,v,seed+920+bestId*17,2);
        col=M(col,wash>0?ochre:cool,Math.abs(wash)*.072*bestEdge);
        rr=C(.68+(1-bestEdge)*.12+bestCrack*.22+bestChip*.07+seam*.04-bestStrata*.06);
        aa=C(1-cavity*.44-bestCrack*.16);
      }else{
        col=M(deep,cool,.28);rr=.91;aa=.80;
      }

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=C(best);roughness.data[i]=rr;ao.data[i]=aa;
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
