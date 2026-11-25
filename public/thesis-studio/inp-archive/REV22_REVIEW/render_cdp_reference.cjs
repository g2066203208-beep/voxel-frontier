// node render_cdp_reference.cjs; adjacent CSV from REV22; no solver outputs
const fs=require('node:fs'),path=require('node:path');
function render(csv,kind){
const rows=csv.trim().split(/\r?\n/).slice(1).map(l=>l.split(",")).map(([m,b,i,s,e,t,d])=>({m,b,i:+i,s:+s,e:+e,t:+t,d:+d}));const P={C65:{E:36500,compression:[41.5,.001808,2.021],tension:[2.93,.00011646,2.6896]},C70:{E:37000,compression:[44.5,.001844,2.183],tension:[2.99,.00011778,2.7928]}};
const S=[],add=s=>S.push(s),num=n=>Number(n.toFixed(3)),tx=(x,y,t,attr="")=>`<text x="${num(x)}" y="${num(y)}" ${attr}>${t}</text>`,ln=(x,y,a,b,attr="")=>`<path d="M${num(x)},${num(y)} L${num(a)},${num(b)}" ${attr}/>`;
const styles={C65:{color:"#245aa5",dash:"",mk:"triangle"},C70:{color:"#db292b",dash:"6 3",mk:"circle"}};
function mark(m,x,y,r=2.4){const c=styles[m].color;return m==="C65"?`<path d="M${num(x-r)},${num(y-r)} L${num(x+r)},${num(y-r)} L${num(x)},${num(y+r)} Z" fill="white" stroke="${c}" stroke-width="1"/>`:`<circle cx="${num(x)}" cy="${num(y)}" r="${r-0.2}" fill="white" stroke="${c}" stroke-width="1"/>`}
add(`<svg xmlns="http://www.w3.org/2000/svg" width="520" height="740" viewBox="0 0 520 740"><title>${kind==="stress"?"C65、C70单轴应力—应变曲线":"C65、C70单轴损伤演化曲线"}</title><rect width="520" height="740" fill="#fff"/><style>text{font-family:'Times New Roman','Noto Serif CJK SC',SimSun,serif;font-size:16px;fill:#111}.tick{font-size:15px}.zh{font-family:'Noto Serif CJK SC',SimSun,serif;font-size:16px}</style>`);
for(const [i,b] of ["compression","tension"].entries()){
const X=70,Y=20+i*365,W=420,H=272,stress=kind==="stress",xmax=b==="compression"?.006:.0012,ymax=stress?(b==="compression"?50:3.5):1,x=v=>X+W*v/xmax,y=v=>Y+H-H*v/ymax;
add(`<defs><clipPath id="p${i}"><rect x="${X}" y="${Y}" width="${W}" height="${H}"/></clipPath></defs>`);add(ln(X,Y,X,Y+H,`stroke="#111" stroke-width="1.1" fill="none"`));add(ln(X,Y+H,X+W,Y+H,`stroke="#111" stroke-width="1.1" fill="none"`));
for(let q=0;q<=6;q++){const a=xmax*q/6;add(ln(x(a),Y+H,x(a),Y+H-5,'stroke="#111"'));add(tx(x(a),Y+H+20,a.toFixed(b==="compression"?3:4),'text-anchor="middle" class="tick"'))}
const ticks=stress?(b==="compression"?[0,10,20,30,40,50]:[0,1,2,3]):[0,.2,.4,.6,.8,1];for(const a of ticks){add(ln(X,y(a),X+5,y(a),'stroke="#111"'));add(tx(X-9,y(a)+5,`${a}`,'text-anchor="end" class="tick"'))}
add(tx(X+W/2,Y+H+45,stress?"应变":(b==="compression"?"非弹性应变":"开裂应变"),'class="zh" text-anchor="middle"'));add(`<text transform="translate(19 ${Y+H/2}) rotate(-90)" text-anchor="middle" class="zh">${stress?"应力/MPa":(b==="compression"?"压缩损伤 d\u209c":"拉伸损伤 d\u209c".replace("d\u209c","dₜ"))}</text>`);if(!stress&&b==="compression"){S[S.length-1]=S[S.length-1].replace("dₜ","d<tspan baseline-shift=\"sub\" font-size=\"12\">c</tspan>")}
add(`<g clip-path="url(#p${i})">`);
for(const m of ["C65","C70"]){const a=rows.filter(v=>v.m===m&&v.b===b),st=styles[m],p=stress?Array.from({length:501},(_,q)=>{const z=xmax*q/500,[f,ep,al]=P[m][b],u=z/ep,n=1/(1-f/(P[m].E*ep));return[z,f*(u<=1?(b==="tension"?u*(1.2-.2*u**5):n*u/(n-1+u**n)):u/(al*(u-1)**(b==="tension"?1.7:2)+u))]}):a.map(v=>[v.e,v.d]);add(`<polyline points="${p.map(([u,v])=>num(x(u))+","+num(y(v))).join(" ")}" stroke="${st.color}" ${st.dash?`stroke-dasharray="${st.dash}"`:""} stroke-width="1.45" fill="none"/>`);for(const v of a)add(mark(m,x(stress?v.t:v.e),y(stress?v.s:v.d)))}add("</g>");
const lx=330,ly=Y+(stress?35:H-49);for(const [j,m] of ["C65","C70"].entries()){const st=styles[m],yy=ly+22*j;add(ln(lx,yy,lx+38,yy,`stroke="${st.color}" stroke-width="1.45" ${st.dash?`stroke-dasharray="${st.dash}"`:""}`));add(mark(m,lx+19,yy));add(tx(lx+44,yy+5,m))}
add(tx(X+W/2,Y+H+69,`(${i?"b":"a"}) ${stress?(i?"单轴拉伸":"单轴压缩"):(i?"拉伸损伤":"压缩损伤")}`,'text-anchor="middle" class="zh"'));
}add("</svg>");return S.join("\n")
}
const csv=fs.readFileSync(path.join(__dirname,'rev22-cdp-curves.csv'),'utf8');for(const kind of ['stress','damage'])fs.writeFileSync(path.join(__dirname,'cdp-reference-'+kind+'.svg'),render(csv,kind));
