"use strict";
const fs=require("node:fs");
const path=require("node:path");
const {chromium}=require("playwright");
const BASE="https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/";
const OUT="artifacts/visual-audit";
const views=[
 ["00-overview","overview"],["01-figures","figures"],["02-evidence","evidence"],
 ["03-thesis","thesis"],["04-library","library"],["05-notes","notes"],
 ["06-proposal","proposal"],["07-field","field"],["08-windResource","windResource"],
 ["09-windLoad","windLoad"],["10-seismic","seismic"],["11-structure","structure"],
 ["12-foundation","foundation"],["13-coupling","coupling"],["14-fatigue","fatigue"],
 ["15-optimization","optimization"],["16-literature","literature"],
 ["17-manuscript","manuscript"],["18-reports","reports"],["19-governance","governance"]
];
async function run(){
 fs.mkdirSync(OUT,{recursive:true});
 const browser=await chromium.launch({headless:true,args:["--disable-dev-shm-usage"]});
 const report={base:BASE,utc:new Date().toISOString(),pages:[],errors:[]};
 const sizes=[{name:"desktop",width:1440,height:900},{name:"mobile",width:390,height:844}];
 for(const size of sizes){
  const page=await browser.newPage({viewport:{width:size.width,height:size.height},deviceScaleFactor:1});
  page.setDefaultTimeout(15000);
  const consoleErrors=[];
  page.on("pageerror",error=>consoleErrors.push(String(error.message).slice(0,300)));
  for(const [slug,id] of views){
   const record={size:size.name,id,url:BASE+"#"+id};
   try{
    const response=await page.goto(record.url,{waitUntil:"domcontentloaded",timeout:30000});
    record.http=response?.status();
    await page.waitForFunction(id=>{
      const el=document.getElementById(id==="overview"?"overview-view":
       ["figures","evidence","thesis","library","notes"].includes(id)?id+"-view":"module-view");
      return el&&!el.hidden;
    },id,{timeout:16000});
    await page.waitForTimeout(id==="figures"||id==="literature"?2200:850);
    record.title=await page.locator("#page-title").innerText().catch(()=>"(missing)");
    record.visibleHeadings=await page.locator("h1:visible,h2:visible").allTextContents();
    record.sourceItems=await page.locator("#module-view:not([hidden]) .source-item").count();
    record.bodyLength=await page.locator("body").innerText().then(t=>t.length);
    record.imgBad=await page.locator("img:visible").evaluateAll(nodes=>nodes.filter(i=>i.complete&&i.naturalWidth===0).length);
    record.pageErrors=consoleErrors.splice(0);
    const target=path.join(OUT,size.name+"-"+slug+".png");
    await page.screenshot({path:target,animations:"disabled",timeout:20000});
    record.screenshot=target;
    console.log("SCREENSHOT",record.screenshot,record.title,record.sourceItems,"sources");
    if(["overview","figures","literature","thesis","evidence"].includes(id)){
     await page.evaluate(()=>window.scrollTo(0,Math.min(1100,document.documentElement.scrollHeight-window.innerHeight)));
     await page.waitForTimeout(500);
     const deep=path.join(OUT,size.name+"-"+slug+"-scrolled.png");
     await page.screenshot({path:deep,animations:"disabled",timeout:20000});
     record.scrolledScreenshot=deep;
    }
   }catch(e){record.error=String(e.stack||e).slice(0,950);report.errors.push({size:size.name,id,error:record.error});console.log("FAIL",size.name,id,record.error);}
   report.pages.push(record);
  }
  await page.close();
 }
 await browser.close();
 fs.writeFileSync(path.join(OUT,"report.json"),JSON.stringify(report,null,2));
 fs.writeFileSync(path.join(OUT,"summary.md"),"# Live studio Chromium screenshots\n\n"+"Source: "+BASE+"\n\n"+report.pages.map(r=>"- "+r.size+" / "+r.id+" / "+(r.title||"no view")+" / "+(r.screenshot||"NO SCREENSHOT")+(r.error?" / ERROR "+r.error.slice(0,130):"")).join("\n")+"\n");
 console.log("AUDIT",JSON.stringify({total:report.pages.length,screenshots:report.pages.filter(x=>x.screenshot).length,errors:report.errors}));
 if(report.errors.length)process.exitCode=1;
}
run().catch(err=>{console.error(err);process.exitCode=1});
