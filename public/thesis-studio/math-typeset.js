"use strict";
/* T093: professional MathML+HTML KaTeX rendering, no source changes.
   Fails open to verbatim original LaTeX if asset/command unavailable. */
(function(){
function inline(root,engine){
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
 const nodes=[];
 while(walker.nextNode()){
  const n=walker.currentNode,p=n.parentElement;
  if(!p||p.closest("pre,code,script,style,textarea,.katex,.thesis-math-error"))continue;
  if(/\\\([\s\S]*?\\\)/.test(n.nodeValue))nodes.push(n);
 }
 let count=0;
 for(const node of nodes){
  const text=node.nodeValue,rx=/\\\(([\s\S]*?)\\\)/g;
  let at=0,match,fragment=document.createDocumentFragment(),changed=false;
  while((match=rx.exec(text))!==null){
   if(match.index>at)fragment.append(document.createTextNode(text.slice(at,match.index)));
   const span=document.createElement("span");span.className="thesis-math-inline";
   span.setAttribute("aria-label","数学公式 "+match[1]);
   try{engine.render(match[1],span,{displayMode:false,throwOnError:false,trust:false,strict:"ignore",output:"htmlAndMathml"});count++}
   catch(e){span.classList.add("thesis-math-error");span.textContent=match[0]}
   fragment.append(span);changed=true;at=rx.lastIndex;
  }
  if(changed){
   if(at<text.length)fragment.append(document.createTextNode(text.slice(at)));
   node.replaceWith(fragment)
  }
 }
 return count;
}
function display(root,engine){
 let count=0;
 root.querySelectorAll("pre.thesis-equation").forEach(block=>{
  if(block.dataset.typeset==="true")return;
  const latex=block.textContent.trim();
  if(!latex)return;
  const box=document.createElement("div");
  box.className="thesis-math-display";
  box.setAttribute("role","math");
  box.setAttribute("aria-label","数学公式 "+latex);
  try{
   engine.render(latex,box,{displayMode:true,throwOnError:false,trust:false,strict:"ignore",output:"htmlAndMathml"});
   block.replaceWith(box);count++
  }catch(e){
   block.classList.add("thesis-math-error");
   block.title="保留原始 LaTeX："+e.message
  }
 });
 return count;
}
function typeset(root){
 if(!root)return 0;
 const engine=window.katex;
 if(!engine?.render){root.dataset.mathStatus="vendor-unavailable";return 0}
 const result=display(root,engine)+inline(root,engine);
 root.dataset.mathStatus="katex-rendered";
 root.dataset.mathCount=String(result);
 return result;
}
window.JYMathTypeset={typeset};
})();