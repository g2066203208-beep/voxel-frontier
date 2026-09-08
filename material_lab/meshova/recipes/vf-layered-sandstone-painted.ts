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
  strata:number[]; crack:boolean; crackX:number; crackTilt:number;
  chipX:number; chipY:number; chip:number;
  planes:[number,number,number][];
};

function makeBlock(seed:number,row:number,id:number,cx:number,cy:number,hw:number,hh:number,base:number,lift:number,macro:boolean,crackChance:number):RockBlock{
  const strata:number[]=[];
  for(let k=0;k<(macro?4:2);k++) strata.push(-.66+hash(seed,row,id,40+k)*1.32);
  const planes:[number,number,number][]=[];
  for(let k=0;k<6;k++) planes.push([
    (hash(seed,row,id,60+k*3)-.5)*1.62,
    (hash(seed,row,id,61+k*3)-.5)*1.30,
    (hash(seed,row,id,62+k*3)-.5)*.34,
  ]);
  return {
    cx:(cx+2)%1,cy:(cy+2)%1,hw,hh,
    angle:(hash(seed,row,id,5)-.5)*(macro?.32:.16),
    base,lift,warm:hash(seed,row,id,6),cool:hash(seed,row,id,7),macro,
    strata,
    crack:hash(seed,row,id,8)<crackChance,
    crackX:(hash(seed,row,id,9)-.5)*.30,
    crackTilt:(hash(seed,row,id,10)-.5)*.22,
    chipX:(hash(seed,row,id,11)<.5?-1:1)*(.62+hash(seed,row,id,12)*.22),
    chipY:(hash(seed,row,id,13)-.5)*1.25,
    chip:hash(seed,row,id,14),
    planes,
  };
}

function buildBlocks(seed:number,bands:number,minSlabs:number,maxSlabs:number,crackChance:number):RockBlock[]{
  const out:RockBlock[]=[];
  const rows=Math.max(4,Math.min(6,bands)),rowStep=1/rows;

  // Low interlocking support stone: closes gaps but stays visibly below the hero slabs.
  for(let row=0;row<rows;row++){
    const requested=minSlabs+Math.floor(hash(seed,row,101)*(maxSlabs-minSlabs+1));
    const count=Math.max(3,Math.min(4,requested+1));
    const raw:number[]=[];let total=0;
    for(let i=0;i<count;i++){const w=.78+hash(seed,row,i,102)*.56;raw.push(w);total+=w;}
    let cursor=-.025+(hash(seed,row,103)-.5)*.03;
    for(let i=0;i<count;i++){
      const frac=raw[i]/total,cx=cursor+frac*.5;cursor+=frac;
      out.push(makeBlock(seed,row,i,cx,
        (row+.5)/rows+(hash(seed,row,i,104)-.5)*rowStep*.22,
        (frac+.025)*.60,rowStep*(.58+hash(seed,row,i,105)*.10),
        .408+(hash(seed,row,i,106)-.5)*.008,
        .032+hash(seed,row,i,107)*.014,false,crackChance*.12));
    }
  }

  // Signature hero slabs. Fewer, larger and deliberately asymmetric: cliff shelves, not cobbles.
  const hero:[number,number,number,number,number,number][]=[
    [.56,.53,.235,.180,.475,.355],
    [.255,.455,.170,.145,.458,.300],
    [.825,.425,.165,.150,.462,.285],
    [.385,.735,.188,.150,.468,.315],
    [.735,.715,.176,.142,.462,.292],
    [.565,.265,.180,.122,.462,.278],
    [.035,.565,.195,.208,.472,.340],
    [.945,.825,.145,.118,.456,.250],
  ];
  for(let i=0;i<hero.length;i++){
    const [cx,cy,hw,hh,base,lift]=hero[i];
    out.push(makeBlock(seed,90,i,
      cx+(hash(seed,90,i,1)-.5)*.014,cy+(hash(seed,90,i,2)-.5)*.014,
      hw*(.97+hash(seed,90,i,3)*.07),hh*(.97+hash(seed,90,i,4)*.07),
      base+(hash(seed,90,i,15)-.5)*.010,lift*(.97+hash(seed,90,i,16)*.08),
      true,crackChance*(i===0?1.18:.58)));
  }
  return out;
}

function blockShape(x:number,y:number,warm:number,cool:number){
  // Sheared/tapered octagonal footprint with unequal diagonal cuts. This makes each slab a wedge,
  // not a rounded rectangle and not a radial blob.
  const shear=(warm-.5)*.34;
  const taper=(cool-.5)*.24;
  const xx=x+y*shear;
  const yy=y*(1+taper*x*.72);
  const ax=Math.abs(xx),ay=Math.abs(yy);
  const d1=Math.abs(xx*.78+yy*.63)*(1.00+(warm-.5)*.10);
  const d2=Math.abs(xx*.67-yy*.76)*(1.00+(cool-.5)*.10);
  return Math.max(ax*.91,ay*.97,d1*.99,d2*.96);
}

export function bakeVfLayeredSandstonePainted(size:number,p:VfLayeredSandstoneParams={}){
  const seed=Math.floor(p.seed??771231);
  const bands=Math.max(4,Math.min(6,Math.floor(p.bands??5)));
  const minSlabs=Math.max(2,Math.floor(p.minSlabs??2));
  const maxSlabs=Math.max(minSlabs,Math.min(4,Math.floor(p.maxSlabs??3)));
  const crackChance=C(p.crackChance??.12),chipStrength=C(p.chipStrength??.82);
  const relief=Math.max(.8,Math.min(1.8,p.relief??1.34));
  const normalStrength=Math.max(3,Math.min(20,p.normalStrength??14.2));
  const blocks=buildBlocks(seed,bands,minSlabs,maxSlabs,crackChance);

  const baseColor=makeTexture(size,size,3),roughness=makeTexture(size,size,1),height=makeTexture(size,size,1),ao=makeTexture(size,size,1);
  const ink:RGB=[.024,.013,.025],deep:RGB=[.060,.035,.052],cool:RGB=[.110,.120,.185],mid:RGB=[.315,.120,.060],light:RGB=[.625,.315,.135],ochre:RGB=[.885,.555,.235],cream:RGB=[.965,.735,.365];

  for(let py=0;py<size;py++){
    const v=1-(py+.5)/size;
    for(let px=0;px<size;px++){
      const u=(px+.5)/size,i=py*size+px,j=i*3;
      const shell=.395+periodicField(u,v,seed+700,2)*.006;
      let best=shell,second=best-.010,bestId=-1,bestEdge=0,bestCrack=0,bestChip=0,bestFacet=0,bestStrata=0,bx=0,by=0;

      for(let id=0;id<blocks.length;id++){
        const q=blocks[id],dx=wrapDelta(u-q.cx),dy=wrapDelta(v-q.cy);
        const ca=Math.cos(q.angle),sa=Math.sin(q.angle),rx=dx*ca+dy*sa,ry=-dx*sa+dy*ca;
        if(Math.abs(rx)>q.hw*1.22||Math.abs(ry)>q.hh*1.22)continue;
        const x=rx/Math.max(q.hw,1e-6),y=ry/Math.max(q.hh,1e-6);
        const shape=blockShape(x,y,q.warm,q.cool)+periodicField(x*.19+id*.13,y*.19-id*.07,seed+id*29,2)*.009;
        if(shape>1.08)continue;

        // Four stacked planar zones: broad outer shoulder -> shelf -> table -> crown.
        // The sum stays continuous at the outside but creates unmistakable terraced rock thickness.
        const shoulder=C((1.08-shape)/(q.macro?.34:.27));
        const shelf=C((.86-shape)/(q.macro?.13:.12));
        const table=C((.66-shape)/(q.macro?.12:.11));
        const crown=C((.43-shape)/(q.macro?.13:.11));
        const profile=.27*shoulder+.30*shelf+.28*table+.15*crown;
        const edge=C((1.08-shape)/(q.macro?.13:.10));

        let top=-99,secondPlane=-99;
        for(const [a,b,c] of q.planes){const plane=a*x+b*y+c;if(plane>top){secondPlane=top;top=plane;}else if(plane>secondPlane)secondPlane=plane;}
        const rawFacet=top*(q.macro?.047:.021)+(top-secondPlane)*(q.macro?.028:.011);
        const hardFacet=Math.round(rawFacet/(q.macro?.020:.010))*(q.macro?.020:.010)*(shelf*.45+table*.55);

        let strata=0;
        for(let k=0;k<q.strata.length;k++){
          const s=q.strata[k]+Math.sin((x*.47+q.warm+k*.17)*TAU)*.010;
          const lip=G((y-s)/(.019+k*.002))*shelf;
          strata+=lip*(y>s?(q.macro?.014:.006):(q.macro?-.006:-.003));
        }
        const upperLedge=G((y-.58)/.095)*table*(q.macro?.024:.008);
        const lowerLedge=G((y+.64)/.090)*shelf*(q.macro?.018:.006);

        let crack=0;
        if(q.crack){
          const line=q.crackX+q.crackTilt*y+periodicField(u,v,seed+id*41,2)*.006;
          crack=G((x-line)/(q.macro?.0075:.012))*S((y+.74)/.10)*S((.76-y)/.10)*table;
        }
        const chip=q.chip>.62?G((x-q.chipX)/(q.macro?.085:.12))*G((y-q.chipY)/(q.macro?.105:.15))*chipStrength*shelf:0;

        const anchor=q.macro?.402:.396;
        let surf=anchor+q.lift*profile+hardFacet+strata+upperLedge-lowerLedge;
        surf+=(q.macro?periodicField(x*.27+q.cx,y*.27+q.cy,seed+id*53,2)*.005*table:0);
        surf-=crack*(q.macro?.070:.032);
        surf-=chip*(q.macro?.034:.016);
        surf=.5+(surf-.5)*relief;

        if(surf>best){second=best;best=surf;bestId=id;bestEdge=edge;bestCrack=crack;bestChip=chip;bestFacet=hardFacet;bestStrata=Math.abs(strata);bx=x;by=y;}
        else if(surf>second)second=surf;
      }

      const overlap=C((best-second)/.072),seam=C((1-overlap)*.28+(bestId<0?.08:0));
      const cavity=C(seam*.20+(1-bestEdge)*.065+bestCrack*.96+bestChip*.22);
      let col:RGB=[.21,.082,.060],rr=.85,aa=.87;
      if(bestId>=0){
        const q=blocks[bestId];
        const planeLight=C(.47+bestFacet*7.0-by*.10+bx*.035);
        col=M(mid,light,C(.18+(best-.40)*1.72));
        col=M(col,ochre,C(planeLight*.29+q.warm*.080+(q.macro?.055:0)));
        col=M(col,cool,C((.55-planeLight)*.34+q.cool*.070));
        col=M(col,cream,C(bestStrata*4.2+Math.max(0,bestFacet)*.32));
        col=M(col,deep,C(cavity*.44));
        col=M(col,ink,C(bestCrack*.995+seam*.075));
        const wash=periodicField(u,v,seed+920+bestId*17,2);
        col=M(col,wash>0?ochre:cool,Math.abs(wash)*.080*bestEdge);
        rr=C(.66+(1-bestEdge)*.14+bestCrack*.24+bestChip*.06+seam*.03-bestStrata*.07);
        aa=C(1-cavity*.40-bestCrack*.17);
      }else{col=M(deep,cool,.25);rr=.92;aa=.81;}

      baseColor.data[j]=C(col[0]);baseColor.data[j+1]=C(col[1]);baseColor.data[j+2]=C(col[2]);
      height.data[i]=C(best);roughness.data[i]=rr;ao.data[i]=aa;
    }
  }
  return finalize(size,baseColor,roughness,height,ao,normalStrength);
}
