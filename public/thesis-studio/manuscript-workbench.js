"use strict";
/* Jiayu Thesis Workbench — latest 2026-11-21 Word manuscript, seven chapters.
 * In-browser edits are local until the owner explicitly publishes with GitHub credentials.
 * The token is held only in the active in-memory dialog; never saved to storage.
 */
(()=>{
const $=id=>document.getElementById(id);
const SOURCE='./editor-data/illustrated-manuscript-v3.json';
const PDF='./downloads/10MW-thesis-illustrated-v3-20261121.pdf';
const WORD_PARTS=Array.from({length:15},(_,i)=>'./downloads/10MW-thesis-illustrated-v3-20261121.part'+String(i+1).padStart(2,'0')+'.bin');
const DRIVE_WORD='https://docs.google.com/document/d/1KbJ-KUWdEdQsmjow1yFd4Vb40icm7bWL/edit';
const REMOTE='https://api.github.com/repos/g2066203208-beep/voxel-frontier/contents/public/thesis-studio/editor-data/owner-published-draft.json';
const REMOTE_PUBLIC='./editor-data/owner-published-draft.json';
const STORE_KEY='jy-thesis-word-editor-v1';
const DB_NAME='jy-thesis-editor';
const state={source:null,chapter:'03',patches:{},versions:[],baseSha:'',lastSaved:0,dirty:false,db:null,remoteSha:null,search:'',focusBlock:null};
let saveTimer=null,toastTimer=null;
const E=(tag,className,text)=>{const el=document.createElement(tag);if(className)el.className=className;if(text!==undefined)el.textContent=String(text);return el;};
const fmt=t=>new Date(t).toLocaleString('zh-CN',{hour12:false});
const blocks=()=>state.source?.chapters.flatMap(c=>c.blocks)||[];
const originals=new Map();
function toast(message){const t=$('toast');t.textContent=message;t.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.hidden=true,3600);}
function status(message,dirty=false){const target=$('save-state');target.lastChild.textContent=message;target.querySelector('.save-dot').style.background=dirty?'#e6bb79':'#8dc7a9';}
function sourceText(b){return b.kind==='table'?b.rows:b.text;}
function valueFor(b){const patch=state.patches[b.id];return patch?patch.value:sourceText(b);}
function equal(a,b){return JSON.stringify(a)===JSON.stringify(b);}
function getChapter(id){return state.source.chapters.find(c=>c.id===id);}
function dirtyCount(){return Object.keys(state.patches).length;}
function updateCounter(){$('edit-counter').textContent=dirtyCount()+'处修改';}
function prepare(){originals.clear();state.source.chapters.forEach(c=>c.blocks.forEach(b=>originals.set(b.id,b)));}
async function openDB(){return new Promise(resolve=>{if(!('indexedDB' in window))return resolve(null);try{const req=indexedDB.open(DB_NAME,1);req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains('kv'))req.result.createObjectStore('kv');};req.onsuccess=()=>resolve(req.result);req.onerror=()=>resolve(null);}catch{resolve(null);}})}
async function readStore(key){if(state.db){try{return await new Promise((resolve,reject)=>{const q=state.db.transaction('kv','readonly').objectStore('kv').get(key);q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);});}catch{}}
 try{const x=localStorage.getItem(STORE_KEY+':'+key);return x?JSON.parse(x):null;}catch{return null;}}
async function writeStore(key,data){if(state.db){try{await new Promise((resolve,reject)=>{const txn=state.db.transaction('kv','readwrite');txn.objectStore('kv').put(data,key);txn.oncomplete=resolve;txn.onerror=()=>reject(txn.error);});return true;}catch{}}
 try{localStorage.setItem(STORE_KEY+':'+key,JSON.stringify(data));return true;}catch{return false;}}
async function persist(){clearTimeout(saveTimer);saveTimer=null;state.lastSaved=Date.now();const data={schema:1,base_sha256:state.baseSha,patches:state.patches,chapter:state.chapter,saved_at:state.lastSaved};const ok=await writeStore('draft',data);if(ok){state.dirty=false;status('已自动保存 · 本机');$('autosave-time').textContent='本地保存 '+fmt(state.lastSaved);}else{status('浏览器存储失败，请立即导出',true);toast('自动保存失败：请使用「导出修改备份」');}}
function scheduleSave(){state.dirty=true;status('正在保存草稿…',true);updateCounter();clearTimeout(saveTimer);saveTimer=setTimeout(persist,480);}
function changeBlock(id,value){const orig=originals.get(id);if(!orig)return;if(equal(sourceText(orig),value))delete state.patches[id];else state.patches[id]={value};scheduleSave();}
function renderNav(){const nav=$('chapter-list');nav.replaceChildren();for(const ch of state.source.chapters){const b=E('button','chapter-btn'+(ch.id===state.chapter?' selected':''));b.type='button';b.dataset.chapter=ch.id;const num=E('span','chapter-no',ch.id==='front'?'序':ch.id);const title=E('span','chapter-name',ch.id==='front'?'前置内容':ch.title.replace(/^第.{1,3}章\s*/,''));const meta=E('span','chapter-meta',ch.blocks.length+'段');b.append(num,title,meta);b.addEventListener('click',()=>navigate(ch.id));nav.append(b);} $('nav-count').textContent=state.source.chapters.length+'部分';}
function pasteText(e){e.preventDefault();const txt=(e.clipboardData||window.clipboardData).getData('text/plain');document.execCommand('insertText',false,txt);}
function makeEditable(block,value,className,onInput){const el=E('div',className,value);el.contentEditable='true';el.setAttribute('role','textbox');el.setAttribute('aria-label','可编辑论文正文');el.setAttribute('spellcheck','false');el.dataset.block=block.id;el.addEventListener('paste',pasteText);el.addEventListener('input',()=>onInput(el.innerText.replace(/\r/g,'')));el.addEventListener('focus',()=>{state.focusBlock=block.id;});return el;}
function blockNode(b){const value=valueFor(b),changed=!!state.patches[b.id];if(b.kind==='table'){
  const wrap=E('div','table-wrap'+(changed?' edited':''));wrap.dataset.block=b.id;const table=E('table');(value||[]).forEach((row,ri)=>{const tr=E('tr');row.forEach((v,ci)=>{const cell=E('td','',v);cell.contentEditable='true';cell.setAttribute('role','textbox');cell.setAttribute('aria-label',`第${ri+1}行第${ci+1}列表格单元格`);cell.addEventListener('paste',pasteText);cell.addEventListener('input',()=>{const source=valueFor(b);const edited=source.map(a=>a.slice());edited[ri][ci]=cell.innerText;changeBlock(b.id,edited);wrap.classList.toggle('edited',!!state.patches[b.id]);});tr.append(cell);});table.append(tr);});wrap.append(table);return wrap;
 }
 const wrap=E('div','paper-block kind-'+b.kind+(changed?' edited':''));wrap.dataset.block=b.id;
 if(b.figure_asset){const fig=E('figure','thesis-inline-figure');const img=E('img');img.src=b.figure_asset;img.alt=b.figure_caption_match||String(value);img.loading='lazy';img.dataset.figure=(String(value).match(/^图\d+-\d+/)||[b.id])[0];fig.append(img);wrap.append(fig);}
 const edit=makeEditable(b,value,'editable',next=>{changeBlock(b.id,next);wrap.classList.toggle('edited',!!state.patches[b.id]);});wrap.append(edit);
 if(b.has_math||b.has_media)wrap.append(E('div','media-note','本段含特殊对象，请对照右侧原稿核对。'));
 return wrap;
}
function navigate(id,focus=null){const c=getChapter(id);if(!c)return;state.chapter=id;$('current-chapter').textContent=c.title;const headBlock=c.blocks.find(b=>b.kind==='h1');const visibleHead=headBlock?valueFor(headBlock):c.title;const chapterHeading=$('chapter-heading');chapterHeading.textContent=visibleHead;chapterHeading.contentEditable=headBlock?'true':'false';chapterHeading.setAttribute('spellcheck','false');chapterHeading.onpaste=headBlock?pasteText:null;chapterHeading.oninput=headBlock?()=>changeBlock(headBlock.id,chapterHeading.innerText):null;$('chapter-foot').textContent=id==='front'?'前置内容':'第'+id+'章';$('chapter-subtitle').textContent=`本部分共${c.blocks.length}个可核对文本/表格区块。点击任何段落即可在线修改；修改实时保存在本浏览器。`;
 const host=$('document-body'),frag=document.createDocumentFragment();for(const b of c.blocks){if(headBlock&&b.id===headBlock.id)continue;frag.append(blockNode(b));}host.replaceChildren(frag);renderNav();$('editing-scroll').scrollTop=0;
 history.replaceState(null,'',location.pathname+(id==='front'?'#front':'#chapter-'+id));
 if(focus){requestAnimationFrame(()=>{const target=Array.from(host.querySelectorAll('[data-block]')).find(el=>el.dataset.block===focus);if(target){target.scrollIntoView({behavior:'smooth',block:'center'});target.classList.add('selected-search');setTimeout(()=>target.classList.remove('selected-search'),2400);}});}
 scheduleChapterOnly();}
function scheduleChapterOnly(){const last=state.lastSaved;if(last&&!state.dirty){clearTimeout(saveTimer);saveTimer=setTimeout(persist,1000);}}
function fullText(b){const v=valueFor(b);return b.kind==='table'?v.flat().join(' '):String(v);}
function search(query){const q=query.trim().toLowerCase(),wrap=$('results-wrap'),out=$('search-results');out.replaceChildren();wrap.hidden=!q;if(!q)return;const matches=[];for(const ch of state.source.chapters){for(const b of ch.blocks){const text=fullText(b);if(text.toLowerCase().includes(q))matches.push({ch,b,text});}}$('search-count').textContent=matches.length+'处';matches.slice(0,80).forEach(({ch,b,text})=>{const btn=E('button','result');const where=E('b','',ch.id==='front'?'前置内容':ch.id+'章');const excerpt=E('small','',text.length>96?text.slice(0,96)+'…':text);btn.append(where,excerpt);btn.onclick=()=>navigate(ch.id,b.id);out.append(btn);});if(matches.length>80)out.append(E('p','foot-title','仅显示前80项结果'));}
function modal(title){$('modal-title').textContent=title;$('modal-body').replaceChildren();$('modal').hidden=false;return $('modal-body');}
function closeModal(){$('modal').hidden=true;}
function paragraph(parent,text,cls=''){parent.append(E('p',cls,text));}
function link(parent,label,url,download=false){const a=E('a','dialog-link',label);a.href=url;if(download)a.download='';else{a.target='_blank';a.rel='noopener noreferrer';}parent.append(a);return a;}
function button(parent,label,callback,cls=''){const b=E('button',cls,label);b.type='button';b.addEventListener('click',callback);parent.append(b);return b;}
function saveBlob(fileName,blob){const url=URL.createObjectURL(blob),a=E('a');a.href=url;a.download=fileName;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);}
function exportJSON(){saveBlob('10MW混塔论文_在线修订备份_'+new Date().toISOString().slice(0,10)+'.json',new Blob([JSON.stringify({schema:1,base_sha256:state.baseSha,source:state.source.source,patches:state.patches,exported_at:new Date().toISOString()},null,2)],{type:'application/json'}));toast('已导出可恢复的修改备份');}
function asMarkdown(ch){const lines=[];lines.push('# '+ch.title,'');for(const b of ch.blocks){const v=valueFor(b);if(b.kind==='table'){if(!v.length)continue;const esc=c=>String(c).replace(/\|/g,'\\|').replace(/\n/g,' ');lines.push('| '+v[0].map(esc).join(' | ')+' |','| '+v[0].map(()=>'---').join(' | ')+' |');v.slice(1).forEach(row=>lines.push('| '+row.map(esc).join(' | ')+' |'));lines.push('');}else{const mark=b.kind==='h1'?'# ':b.kind==='h2'?'## ':b.kind==='h3'?'### ':'';lines.push(mark+v,'');if(b.has_math||b.has_media)lines.push('<!-- 该段原Word包含非文字对象：须参照原稿 -->','');}}return lines.join('\n');}
function exportMarkdown(all=false){const cs=all?state.source.chapters:[getChapter(state.chapter)];saveBlob('10MW混塔论文_'+(all?'全部七章':'章节'+state.chapter)+'_编辑稿.md',new Blob([cs.map(asMarkdown).join('\n\n---\n\n')],{type:'text/markdown;charset=utf-8'}));toast('已下载Markdown编辑稿');}
function exportHTML(){const css='<style>body{max-width:800px;margin:auto;padding:35px;color:#222;line-height:1.9;font-family:"SimSun",serif}h1,h2,h3{font-family:"SimHei",sans-serif}table{border-collapse:collapse;width:100%;font-size:12px}td{border:1px solid #999;padding:5px}</style>';
 const esc=v=>String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');let contents='';for(const ch of state.source.chapters){contents+='<h1>'+esc(ch.title)+'</h1>';for(const b of ch.blocks){const v=valueFor(b);if(b.kind==='table'){contents+='<table>';for(const row of v){contents+='<tr>'+row.map(cell=>'<td>'+esc(cell).replaceAll('\n','<br>')+'</td>').join('')+'</tr>';}contents+='</table>';}else{let t=b.kind==='h2'?'h2':b.kind==='h3'?'h3':b.kind==='h1'?'h1':'p';contents+='<'+t+'>'+esc(v).replaceAll('\n','<br>')+'</'+t+'>';}}}
 saveBlob('10MW混塔论文_全文章节编辑稿.html',new Blob(['<!doctype html><html lang="zh-CN"><meta charset="utf-8">'+css+'<body>'+contents+'</body></html>'],{type:'text/html;charset=utf-8'}));toast('已导出可供浏览器与Word打开的HTML');}
async function snapshot(){await persist();const versions=await readStore('versions:'+state.baseSha)||[];versions.unshift({id:Date.now(),saved_at:new Date().toISOString(),patches:JSON.parse(JSON.stringify(state.patches)),count:dirtyCount()});state.versions=versions.slice(0,15);await writeStore('versions:'+state.baseSha,state.versions);toast('版本快照已保存，可从历史记录恢复');}
function viewHistory(){const body=modal('本地修订历史');paragraph(body,'修改自动保存；手动快照保存独立历史版本，最多保留15个。全部历史只在当前浏览器中。');if(!state.versions.length)paragraph(body,'暂无历史快照。');state.versions.forEach((v,i)=>{const d=E('div','version-item');d.append(E('b','',fmt(v.id)+' · '+v.count+'处修改'));button(d,'恢复此版本',async()=>{if(!confirm('恢复将替换当前编辑草稿。建议先导出JSON备份。确定继续？'))return;state.patches=JSON.parse(JSON.stringify(v.patches));closeModal();navigate(state.chapter);await persist();toast('已恢复历史版本');});body.append(d);});button(body,'立即保存当前快照',async()=>{await snapshot();viewHistory();},'primary');readStore('legacy-draft').then(old=>{if(old&&old.base_sha256!==state.baseSha){paragraph(body,'检测到旧版论文母本的草稿，已与新版隔离保留，不会被自动覆盖。');button(body,'下载旧版草稿备份JSON',()=>{const data={...old,legacy_backup:true,exported_at:new Date().toISOString()};saveBlob('10MW混塔论文_旧版草稿_升级前备份.json',new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));});}});}
function viewExport(){const body=modal('导出与下载');paragraph(body,'全文修改保存在当前浏览器；一键导出修订Word将从本站下载原稿的15个分片，校验完整原稿SHA-256后只替换修改文字，图件、复杂公式和排版仍以原版Word为准。');link(body,'下载图文修复版排版PDF · 136页',PDF,true);button(body,'一键导出修改后的 Word（自动读取母本）',()=>{closeModal();exportHostedDOCX();},'primary');button(body,'使用本地原版Word导出（备用）',()=>{$('word-file').click();closeModal();});link(body,'2026-11-21历史Word备份（Google Drive；需访问权限）',DRIVE_WORD);button(body,'导出全部七章 Markdown',()=>exportMarkdown(true));button(body,'导出当前章节 Markdown',()=>exportMarkdown(false));button(body,'导出全文 HTML（可在 Word 中打开）',exportHTML);button(body,'导出修改备份 JSON（可恢复）',exportJSON);}
function viewSource(){const b=modal('原始论文与版本信息'),s=state.source.source;paragraph(b,'当前编辑母本：'+s.name+'。包含前置内容与七章正文；第二章恢复4张原有计算图（推覆、人工能、模态和质量参与率），并保留31节混凝土及4节钢塔参数表。浏览器可修改正文和表格；图片本身按来源锁定，只在Word中定位。其余图片仍按科研证据逐张核验。');paragraph(b,'Word原件 SHA256：');b.append(E('code','',s.sha256));paragraph(b,'编辑区是论文文本层，不等价于Word原位分页；复杂公式与插图在原文中未被重建为浏览器可编辑对象。');link(b,'查看完整PDF原页',PDF,true);}
async function publishDialog(){const body=modal('GitHub 授权发布与读取');paragraph(body,'普通编辑只保存在本机。此功能可将当前修改同步至网站公开GitHub仓库，跨设备读取，但内容对所有人可见。需要你自己的细粒度GitHub访问令牌（仅授予该仓库 Contents 写权限）。');paragraph(body,'令牌不写入浏览器本地存储，也不会上传到论文文件中。网页为静态页面，没有自动登录或后台协作服务。','fineprint');const label=E('label','','GitHub访问令牌（仅本次操作）');body.append(label);const field=E('input');field.type='password';field.placeholder='github_pat_…';field.autocomplete='off';body.append(field);const notice=E('p','fineprint','公开发布会把当前论文修改内容作为JSON提交到公共仓库的main分支；提交后任何人都可以阅读。');body.append(notice);const confirmWrap=E('label');confirmWrap.style.display='flex';confirmWrap.style.gap='8px';confirmWrap.style.alignItems='center';const check=E('input');check.type='checkbox';check.style.width='auto';check.style.margin='0';confirmWrap.append(check,E('span','','我同意将当前草稿修改公开发布至GitHub'));body.append(confirmWrap);button(body,'发布当前草稿到GitHub（公开）',async()=>{const token=field.value.trim();if(!token||!check.checked){toast('请提供GitHub令牌并明确确认公开发布');return;}await persist();const backup={schema:1,base_sha256:state.baseSha,patches:state.patches,exported_at:new Date().toISOString(),warning:'PUBLIC DRAFT: latest manuscript edits; not independently verified scientific results'};const btn=body.querySelector('.primary');btn.disabled=true;btn.textContent='正在核验远端版本并提交…';try{const headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'};
 let sha=state.remoteSha;
 if(sha===null){const rr=await fetch(REMOTE+'?ref=main',{headers,cache:'no-store'});if(rr.status===200){const existing=await rr.json();sha=existing.sha;}else if(rr.status!==404)throw Error('读取远端失败 HTTP '+rr.status);}
 const payload={message:'docs(thesis): publish browser-edited manuscript snapshot '+new Date().toISOString().slice(0,19),content:base64Unicode(JSON.stringify(backup)),branch:'main'};if(sha)payload.sha=sha;
 const res=await fetch(REMOTE,{method:'PUT',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await res.json();if(!res.ok)throw Error('GitHub拒绝发布 '+res.status+': '+(result.message||'未知错误'));
 state.remoteSha=result.content.sha;closeModal();status('已提交GitHub公开草稿');toast('GitHub提交成功；网站部署仍须等待Pages完成');}
 catch(e){toast(e.message);btn.disabled=false;btn.textContent='重试发布（先核对权限与冲突）';}
 },'primary');button(body,'读取网站现有公开草稿',async()=>{try{const r=await fetch(REMOTE_PUBLIC+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('当前网站尚无已发布草稿');const data=await r.json();if(data.base_sha256!==state.baseSha)throw Error('公开稿与本编辑器Word母本版本不同，已拒绝覆盖');if(!confirm('读取公开稿会覆盖本机当前未发布的编辑，请先导出备份。继续？'))return;state.patches=data.patches||{};await persist();closeModal();navigate(state.chapter);toast('已读取网站已发布版本');}catch(e){toast(e.message);}});}
function base64Unicode(s){const bytes=new TextEncoder().encode(s);let result='';const step=4096;for(let i=0;i<bytes.length;i+=step){result+=String.fromCharCode(...bytes.subarray(i,i+step));}return btoa(result);}
async function loadZip(){if(window.JSZip)return window.JSZip;await new Promise((resolve,reject)=>{const scr=E('script');scr.src='./vendor/jszip.min.js';scr.onload=resolve;scr.onerror=()=>reject(Error('Word导出组件无法加载，请使用JSON备份导出'));document.head.append(scr);});return window.JSZip;}
const W_NS='http://schemas.openxmlformats.org/wordprocessingml/2006/main';
function replaceXmlText(parent,newText,doc){let nodes=Array.from(parent.getElementsByTagNameNS(W_NS,'t'));
 if(!nodes.length){let target=parent;if(parent.localName==='tc'){target=Array.from(parent.children).find(n=>n.localName==='p');if(!target){target=doc.createElementNS(W_NS,'w:p');parent.append(target);}}
 const run=doc.createElementNS(W_NS,'w:r');const t=doc.createElementNS(W_NS,'w:t');t.setAttribute('xml:space','preserve');t.textContent=newText;run.append(t);target.append(run);return;}
 const parts=nodes.map(n=>n.textContent),old=parts.join('');if(old===newText)return;
 let prefix=0;while(prefix<old.length&&prefix<newText.length&&old[prefix]===newText[prefix])prefix++;
 let suffix=0;while(suffix<old.length-prefix&&suffix<newText.length-prefix&&old[old.length-1-suffix]===newText[newText.length-1-suffix])suffix++;
 const middle=newText.slice(prefix,newText.length-suffix);let offset=0,inserted=false;
 for(let i=0;i<nodes.length;i++){const text=parts[i],end=offset+text.length;
 const left=text.slice(0,Math.max(0,Math.min(text.length,prefix-offset)));
 const suffixStart=old.length-suffix;
 const right=text.slice(Math.max(0,Math.min(text.length,suffixStart-offset)));
 let content=left;
 if(!inserted&&(end>prefix||i===nodes.length-1)){content+=middle;inserted=true;}
 content+=right;nodes[i].textContent=content;nodes[i].setAttribute('xml:space','preserve');offset=end;}
}
function patchDocxXml(xml){const parser=new DOMParser(),doc=parser.parseFromString(xml,'application/xml');if(doc.getElementsByTagName('parsererror').length)throw Error('Word原稿XML无法解析');const body=doc.getElementsByTagNameNS(W_NS,'body')[0];if(!body)throw Error('缺少Word正文XML');const children=Array.from(body.children);let applied=0,warnings=[];
 for(const [id,change] of Object.entries(state.patches)){const orig=originals.get(id);if(!orig){warnings.push('缺失区块 '+id);continue;}const el=children[orig.word_body_index];if(!el){warnings.push('定位区块失败 '+id);continue;}if(orig.kind==='table'){
 if(el.localName!=='tbl'){warnings.push('表格顺序不匹配 '+id);continue;}
 const rows=Array.from(el.children).filter(x=>x.localName==='tr');change.value.forEach((row,ri)=>{if(!rows[ri])return;const cells=Array.from(rows[ri].children).filter(x=>x.localName==='tc');row.forEach((text,ci)=>{if(!cells[ci])return;const old=(orig.rows?.[ri]||[])[ci];if(text!==old)replaceXmlText(cells[ci],text,doc);});});applied++;
 }else{if(el.localName!=='p'){warnings.push('段落顺序不匹配 '+id);continue;}if(orig.has_math||orig.has_media){warnings.push('含复杂图件或公式的段落需人工核查 '+id);}replaceXmlText(el,change.value,doc);applied++;}}
 return {xml:new XMLSerializer().serializeToString(doc),applied,warnings};}
async function exportHostedDOCX(){
  status('正在下载工作室原版Word（约40 MB）…',true);
  try{
    const chunks=new Array(WORD_PARTS.length);
    let completed=0;
    await Promise.all(Array.from({length:4},(_,worker)=>(async()=>{
      for(let i=worker;i<WORD_PARTS.length;i+=4){
        const response=await fetch(WORD_PARTS[i],{cache:'force-cache'});
        if(!response.ok)throw Error('下载原版Word分片'+String(i+1)+'失败，HTTP '+response.status);
        chunks[i]=await response.arrayBuffer();
        completed++;
        status('正在读取Word原稿 '+completed+'/'+WORD_PARTS.length+'…',true);
      }
    })()));
    const blob=new Blob(chunks,{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'});
    if(blob.size!==state.source.source.bytes)throw Error('下载文件不完整：预期'+state.source.source.bytes+'字节，实际'+blob.size+'字节');
    const original=new File([blob],'原版完整论文.docx',{type:blob.type});
    await exportDOCX(original);
  }catch(error){
    status('原版Word下载失败 · 草稿未丢失',true);
    toast(error.message+'；可使用本地原版Word导出');
  }
}
async function exportDOCX(file){if(!file)return;const name=file.name.toLowerCase();if(!name.endsWith('.docx'))return toast('请选择.docx原格式文件');status('正在生成修订版Word…',true);try{const JSZip=await loadZip();const buffer=await file.arrayBuffer();const digest=await crypto.subtle.digest('SHA-256',buffer);const sha=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');if(sha!==state.baseSha)throw Error('选取的Word不是本编辑器的原始母本，已拒绝写入以防段落错位。请使用2026-11-21精修版Word。');const zip=await JSZip.loadAsync(buffer);const source=zip.file('word/document.xml');if(!source)throw Error('所选文件不是有效Word DOCX');const xml=await source.async('string');const result=patchDocxXml(xml);zip.file('word/document.xml',result.xml);const output=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:5}});saveBlob('10MW混塔论文_在线修改版_'+new Date().toISOString().slice(0,10)+'.docx',output);status('Word已生成 · 请复核排版');toast(`Word已导出，已写入${result.applied}处修改${result.warnings.length?'；部分复杂对象请核验':''}`);}catch(e){status('Word导出失败 · 草稿仍在本机');toast(e.message);}finally{$('word-file').value='';}}
async function init(){try{const response=await fetch(SOURCE,{cache:'no-store'});if(!response.ok)throw Error('论文Word文本数据不可读取，HTTP '+response.status);state.source=await response.json();if(!state.source.chapters||state.source.chapters.length!==8)throw Error('论文章节源不完整，应为前置内容+七章');state.baseSha=state.source.source.sha256;prepare();state.db=await openDB();const saved=await readStore('draft');if(saved&&saved.base_sha256===state.baseSha){state.patches=saved.patches||{};state.chapter=saved.chapter||'03';state.lastSaved=saved.saved_at||0;}else if(saved&&saved.base_sha256&&saved.base_sha256!==state.baseSha){await writeStore('legacy-draft',saved);const oldVersions=await readStore('versions');if(oldVersions?.length)await writeStore('legacy-versions',oldVersions);toast('已保留旧版论文修改，请到「历史版本」下载升级前备份。');}state.versions=await readStore('versions:'+state.baseSha)||(saved?.base_sha256===state.baseSha?await readStore('versions'):null)||[];const m=location.hash.match(/^#chapter-(\d\d)$/);if(m&&getChapter(m[1]))state.chapter=m[1];if(location.hash==='#front')state.chapter='front';renderNav();navigate(state.chapter);$('source-status').textContent='Word来源SHA256 '+state.baseSha.slice(0,16)+'… · '+state.source.chapters.length+'部分';status('已载入 · 草稿自动保存');$('autosave-time').textContent=state.lastSaved?'上次保存 '+fmt(state.lastSaved):'尚未修改';updateCounter();}
 catch(e){$('chapter-heading').textContent='加载失败';$('chapter-subtitle').textContent=e.message;status('文稿导入失败',true);console.error(e);}}
$('search').addEventListener('input',e=>search(e.target.value));
$('search').addEventListener('keydown',e=>{if(e.key==='Escape'){e.currentTarget.value='';search('');}});
$('history-button').addEventListener('click',viewHistory);
$('cloud-button').addEventListener('click',publishDialog);
$('export-menu').addEventListener('click',viewExport);
$('snapshot-button').addEventListener('click',snapshot);
$('source-button').addEventListener('click',viewSource);
$('pdf-toggle').addEventListener('click',()=>{document.body.classList.toggle('hide-preview');$('pdf-toggle').setAttribute('aria-pressed',String(!document.body.classList.contains('hide-preview')));});
$('focus-button').addEventListener('click',()=>{document.body.classList.toggle('focus');$('focus-button').textContent=document.body.classList.contains('focus')?'退出专注':'专注模式';});
$('word-file').addEventListener('change',e=>exportDOCX(e.target.files[0]));
$('modal-close').addEventListener('click',closeModal);
$('modal').addEventListener('click',e=>{if(e.target===$('modal'))closeModal();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeModal();return;}if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='s'){e.preventDefault();persist();toast('草稿已保存在当前浏览器');}else if(e.key==='/'&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)&&!document.activeElement.isContentEditable){e.preventDefault();$('search').focus();}});
window.addEventListener('beforeunload',()=>{if(state.dirty){try{localStorage.setItem(STORE_KEY+':draft',JSON.stringify({schema:1,base_sha256:state.baseSha,patches:state.patches,chapter:state.chapter,saved_at:Date.now()}));}catch{}}});
init();
})();