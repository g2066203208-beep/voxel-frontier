"""Apply the user's retained school template to an existing chapter, without rewriting.

python format_chapter1_public.py --reference TEMPLATE.docx --draft CHAPTER.docx
       --output FORMATTED.docx --report format-verification.json
       --layout-overrides layout-overrides.json
Requires lxml. Uses the retained template package as base; neither input changes.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import posixpath
import re
import zipfile
from lxml import etree as E

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
NS={'w':W,'r':R,'wp':WP,'a':A}
def w(x): return '{'+W+'}'+x
def digest(b): return hashlib.sha256(b).hexdigest()
def xml(b): return E.fromstring(b)
def data(x): return E.tostring(x,xml_declaration=True,encoding='UTF-8',standalone=True)
def text(p): return ''.join(p.itertext()) if False else ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def el(parent, name, attrs=None):
    x=parent.find(w(name))
    if x is None: x=E.SubElement(parent,w(name))
    for k,v in (attrs or {}).items(): x.set(w(k),str(v))
    return x
def remove(parent,name):
    for x in parent.findall(w(name)): parent.remove(x)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['reference','draft','output','report']: ap.add_argument('--'+key,type=Path,required=True)
    ap.add_argument('--max-image-width-cm',type=float,default=13.2,
                    help='Layout choice for this chapter, not a school rule; preserve image aspect ratio')
    ap.add_argument('--layout-overrides',type=Path,required=True,
                    help='JSON with paragraph SHA256 to tracking-point values; contains no paragraph text')
    args=ap.parse_args()
    tracking_by_hash=json.loads(args.layout_overrides.read_text(encoding='utf-8'))['tracking_overrides_pt']
    if args.output.resolve() in {args.reference.resolve(),args.draft.resolve()}: raise ValueError('Never overwrite an input')
    template_bytes=args.reference.read_bytes(); draft_bytes=args.draft.read_bytes()
    with zipfile.ZipFile(args.reference) as z: base={n:z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(args.draft) as z: old={n:z.read(n) for n in z.namelist()}
    parts=dict(base)
    root=xml(parts['word/document.xml']); body=root.find(w('body'))
    ref_ps=body.findall(w('p'))
    old_root=xml(old['word/document.xml']); old_body=old_root.find(w('body'))
    original_text=old_body.xpath('.//w:t/text()',namespaces=NS)
    samples={'chapter':88,'body':89,'section':90,'subsection':92,'third':94,'reference_title':110,'reference':112}
    # Validate structural locators instead of assuming any similarly named file fits.
    for role,idx in samples.items():
        if idx>=len(ref_ps): raise ValueError('Template does not match audited structure')
    if not text(ref_ps[88]).startswith('第一章') or not text(ref_ps[110]).startswith('参考文献'):
        raise ValueError('Template role anchors changed')
    specs={}
    for role,idx in samples.items():
        p=ref_ps[idx]; props=deepcopy(p.find(w('pPr')))
        if props is None: props=E.Element(w('pPr'))
        for name in ['pStyle','rPr','sectPr']: remove(props,name)
        specs[role]=props
    sects=root.xpath('.//w:sectPr',namespaces=NS)
    section=deepcopy(sects[6])
    for x in list(section):
        if x.tag in [w('headerReference'),w('footerReference')] and x.get(w('type'))!='default': section.remove(x)
    # One supplied chapter, with Arabic page numbering beginning at 1.
    remove(section,'titlePg'); el(section,'pgNumType',{'start':1,'fmt':'decimal'})
    margin=section.find(w('pgMar')); page=section.find(w('pgSz'))
    if [int(margin.get(w(k))) for k in ['top','bottom','left','right','header','footer']] != [1984,1984,1814,1814,1474,1361]:
        raise ValueError('Unexpected school page geometry')
    width_twips=int(page.get(w('w')))-int(margin.get(w('left')))-int(margin.get(w('right')))
    width_emu=width_twips*635
    image_width_emu=min(width_emu,round(args.max_image_width_cm*360000))
    for child in list(body): body.remove(child)
    for child in old_body:
        if child.tag!=w('sectPr'): body.append(deepcopy(child))
    body.append(section)
    # Import only relationship targets actually used by the existing chapter body.
    rels=xml(parts['word/_rels/document.xml.rels']); old_rels=xml(old['word/_rels/document.xml.rels'])
    old_map={x.get('Id'):x for x in old_rels}
    used_ids={a for child in body if child is not section for x in child.iter()
              for k,a in x.attrib.items() if k.startswith('{'+R+'}')}
    imports=[]
    for number,rid in enumerate(sorted(used_ids),1):
        relation=old_map[rid]; new=deepcopy(relation); nrid='rIdChapterImported'+str(number); new.set('Id',nrid)
        if relation.get('TargetMode')!='External':
            original_target=posixpath.normpath(posixpath.join('word',relation.get('Target')))
            if '/media/' not in original_target: raise ValueError('Unsupported body dependency '+original_target)
            target='word/media/chapter1_imported_'+str(number)+Path(original_target).suffix
            parts[target]=old[original_target];new.set('Target',posixpath.relpath(target,'word'))
            imports.append({'original':original_target,'target':target,'sha256':digest(parts[target])})
        rels.append(new)
        for x in body.iter():
            # Section references belong to the retained template, never rewrite them.
            if x in section or x is section: continue
            for key,value in list(x.attrib.items()):
                if key.startswith('{'+R+'}') and value==rid: x.set(key,nrid)
    # Template commentary is source guidance, not a review comment in the output.
    removed_parts=[]
    for r in list(rels):
        if any(k in r.get('Type','') for k in ['comments','people']):
            target=posixpath.normpath(posixpath.join('word',r.get('Target')))
            if target in parts: del parts[target];removed_parts.append(target)
            rels.remove(r)
    for name in ['commentRangeStart','commentRangeEnd','commentReference','bookmarkStart','bookmarkEnd']:
        for x in list(body.iter(w(name))): x.getparent().remove(x)
    sizes={'chapter':18,'body':12,'section':16,'subsection':14,'third':12,'reference_title':15,'reference':10.5,'caption':10.5,'table':10.5,'image':12}
    counts={k:0 for k in sizes}
    def format_p(p,role):
        counts[role]+=1
        original_props=p.find(w('pPr'))
        old_break=original_props.find(w('pageBreakBefore')) if original_props is not None else None
        if original_props is not None: p.remove(original_props)
        if role in specs: pp=deepcopy(specs[role])
        else: pp=E.Element(w('pPr'))
        p.insert(0,pp)
        el(pp,'pStyle',{'val':'School_'+role})
        # Explicit settings prevent latent theme/normal-style properties leaking in.
        el(pp,'snapToGrid',{'val':0});el(pp,'widowControl',{'val':1})
        if role in ['chapter','section','subsection','third','reference_title']:
            el(pp,'keepNext',{'val':1});el(pp,'keepLines',{'val':1});el(pp,'ind',{'left':0,'right':0,'firstLine':0})
            el(pp,'jc',{'val':'center' if role in ['chapter','reference_title'] else 'left'})
        if role=='body':
            el(pp,'jc',{'val':'both'});el(pp,'spacing',{'before':0,'after':0,'line':400,'lineRule':'exact'})
            el(pp,'ind',{'left':0,'right':0,'firstLine':539})
        elif role=='reference':
            el(pp,'keepLines',{'val':1});el(pp,'keepNext',{'val':0});el(pp,'jc',{'val':'both'})
            el(pp,'spacing',{'before':60,'after':0,'line':340,'lineRule':'exact'})
        elif role=='reference_title':
            el(pp,'pageBreakBefore',{'val':1})
        elif role in ['caption','table']:
            caption_gap=60 if text(p).startswith('表') else 120
            el(pp,'spacing',{'before':caption_gap if role=='caption' else 0,'after':caption_gap if role=='caption' else 0,'line':340,'lineRule':'exact'})
            el(pp,'ind',{'left':0,'right':0,'firstLine':0});el(pp,'jc',{'val':'center' if role=='caption' else 'left'})
            if role=='caption' and text(p).startswith('表'): el(pp,'keepNext',{'val':1})
        elif role=='image':
            el(pp,'spacing',{'before':120,'after':0,'line':240,'lineRule':'auto'})
            el(pp,'ind',{'left':0,'right':0,'firstLine':0});el(pp,'jc',{'val':'center'});el(pp,'keepNext',{'val':1})
            if old_break is not None: pp.append(deepcopy(old_break))
        for run in p.findall('.//'+w('r')):
            previous=run.find(w('rPr'))
            superscript=previous.find(w('vertAlign')) if previous is not None else None
            preserved_sizes={name:deepcopy(previous.find(w(name))) for name in ['sz','szCs']
                             if superscript is not None and superscript.get(w('val'))=='superscript'
                             and previous.find(w(name)) is not None}
            if previous is not None: run.remove(previous)
            rp=E.Element(w('rPr'));run.insert(0,rp)
            family='黑体' if role in ['chapter','section','subsection','third','reference_title'] else '宋体'
            el(rp,'rFonts',{'ascii':'Times New Roman','hAnsi':'Times New Roman','eastAsia':family,'cs':'Times New Roman'})
            el(rp,'color',{'val':'000000'});el(rp,'sz',{'val':round(sizes[role]*2)});el(rp,'szCs',{'val':round(sizes[role]*2)})
            for name,value in preserved_sizes.items():
                remove(rp,name);rp.append(value)
            if superscript is not None: rp.append(deepcopy(superscript))
            # Prevent this source paragraph ending in a citation-only line.
            # Local tracking is a layout choice, not a change to school font/leading.
            tracking=tracking_by_hash.get(digest(text(p).encode('utf-8'))) if role=='body' else None
            if tracking is not None: el(rp,'spacing',{'val':round(float(tracking)*20)})
    in_refs=False
    for child in body:
        if child.tag==w('p'):
            t=text(child)
            if t.startswith('第一章'): role='chapter'
            elif t in ['本章参考文献','参考文献']: role='reference_title'; in_refs=True
            elif child.find('.//{'+WP+'}inline') is not None: role='image'
            elif re.match(r'^\d+\.\d+\.\d+\.\d+\s',t): role='third'
            elif re.match(r'^\d+\.\d+\.\d+\s',t): role='subsection'
            elif re.match(r'^\d+\.\d+\s',t): role='section'
            elif child.find('./'+w('pPr')+'/'+w('pStyle')) is not None and child.find('./'+w('pPr')+'/'+w('pStyle')).get(w('val'))=='Caption': role='caption'
            elif in_refs and re.match(r'^\[\d+\]',t): role='reference'
            else: role='body'
            format_p(child,role)
        elif child.tag==w('tbl'):
            for p in child.iter(w('p')): format_p(p,'table')
            pr=child.find(w('tblPr'))
            if pr is None: pr=E.Element(w('tblPr'));child.insert(0,pr)
            el(pr,'tblW',{'w':width_twips,'type':'dxa'});el(pr,'jc',{'val':'center'});el(pr,'tblLayout',{'type':'fixed'})
            cell_margins=el(pr,'tblCellMar')
            for edge in ['top','bottom']: el(cell_margins,edge,{'w':50,'type':'dxa'})
            grid=child.find(w('tblGrid')); cols=list(grid); old_width=sum(int(c.get(w('w'))) for c in cols)
            sizes_cols=[round(int(c.get(w('w')))*width_twips/old_width) for c in cols];sizes_cols[-1]+=width_twips-sum(sizes_cols)
            for c,v in zip(cols,sizes_cols):c.set(w('w'),str(v))
            for i,row in enumerate(child.findall(w('tr'))):
                rowpr=row.find(w('trPr'))
                if rowpr is None:rowpr=E.Element(w('trPr'));row.insert(0,rowpr)
                remove(rowpr,'trHeight');el(rowpr,'cantSplit',{'val':1})
                if i==0:el(rowpr,'tblHeader',{'val':1})
                # This short seven-row table fits on one page; keep its rows together.
                for para in row.iter(w('p')):
                    el(para.find(w('pPr')),'keepNext',{'val':1 if i<len(child.findall(w('tr')))-1 else 0})
                grid_index=0
                for cell in row.findall(w('tc')):
                    cp=cell.find(w('tcPr'))
                    if cp is None:cp=E.Element(w('tcPr'));cell.insert(0,cp)
                    span=cp.find(w('gridSpan'));span_count=int(span.get(w('val'))) if span is not None else 1
                    el(cp,'tcW',{'w':sum(sizes_cols[grid_index:grid_index+span_count]),'type':'dxa'})
                    grid_index+=span_count
    image_changes=[]
    for inline in body.iter('{'+WP+'}inline'):
        extent=inline.find('{'+WP+'}extent');cx=int(extent.get('cx'));cy=int(extent.get('cy'))
        if cx>image_width_emu:
            ncx=image_width_emu;ncy=round(cy*ncx/cx)
            extent.set('cx',str(ncx));extent.set('cy',str(ncy))
            for ext in inline.findall('.//{'+A+'}xfrm/{'+A+'}ext'):ext.set('cx',str(ncx));ext.set('cy',str(ncy))
            image_changes.append({'old_emu':[cx,cy],'new_emu':[ncx,ncy],'aspect_ratio_preserved':True})
    styles=xml(parts['word/styles.xml'])
    for role,size in sizes.items():
        s=E.SubElement(styles,w('style'),{w('type'):'paragraph',w('styleId'):'School_'+role})
        el(s,'name',{'val':'学校模板 '+role});el(s,'basedOn',{'val':'Normal'})
        pp=E.SubElement(s,w('pPr'));el(pp,'contextualSpacing',{'val':0})
        rp=E.SubElement(s,w('rPr'));el(rp,'rFonts',{'ascii':'Times New Roman','hAnsi':'Times New Roman','eastAsia':'黑体' if role in ['chapter','section','subsection','third','reference_title'] else '宋体'})
        el(rp,'color',{'val':'000000'});el(rp,'sz',{'val':round(size*2)})
    settings=xml(parts['word/settings.xml']);el(settings,'updateFields',{'val':1});remove(settings,'evenAndOddHeaders')
    types=xml(parts['[Content_Types].xml'])
    for x in list(types):
        if x.get('PartName','').lstrip('/') in removed_parts:types.remove(x)
    extensions={x.get('Extension') for x in types if x.tag=='{'+CT+'}Default'}
    for imported in imports:
        ext=Path(imported['target']).suffix.lstrip('.')
        if ext not in extensions:
            E.SubElement(types,'{'+CT+'}Default',Extension=ext,ContentType={'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg'}[ext]);extensions.add(ext)
    parts['word/document.xml']=data(root);parts['word/styles.xml']=data(styles);parts['word/settings.xml']=data(settings)
    parts['word/_rels/document.xml.rels']=data(rels);parts['[Content_Types].xml']=data(types)
    # Core metadata is adjusted only to describe the supplied chapter artifact.
    core=xml(parts['docProps/core.xml']);dc='http://purl.org/dc/elements/1.1/'
    title=core.find('{'+dc+'}title')
    if title is None:title=E.SubElement(core,'{'+dc+'}title')
    title.text='第一章 绪论'
    parts['docProps/core.xml']=data(core)
    final_text=body.xpath('.//w:t/text()',namespaces=NS)
    assert final_text==original_text,'Visible chapter text changed'
    assert args.reference.read_bytes()==template_bytes and args.draft.read_bytes()==draft_bytes
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for n,b in parts.items():z.writestr(n,b)
    changed=[n for n in base if n in parts and base[n]!=parts[n]]
    unchanged=[{'part':n,'sha256':digest(b)} for n,b in base.items() if n in parts and b==parts[n]]
    report={'operation':'chapter1 formatting only; not approved chapter content','reference_sha256':digest(template_bytes),'draft_sha256':digest(draft_bytes),
            'output_file':args.output.name,'output_sha256':digest(args.output.read_bytes()),'role_counts':counts,
            'visible_text_tokens_unchanged':True,'visible_text_sha256':digest('\n'.join(original_text).encode()),
            'reference_and_draft_unchanged':True,'section_count':1,'template_section_index':6,
            'page_width_twips':int(page.get(w('w'))),'page_height_twips':int(page.get(w('h'))),'margins_twips':{k:int(margin.get(w(k))) for k in ['top','bottom','left','right','header','footer']},
            'usable_width_twips':width_twips,'source_image_bytes_preserved':imports,'image_resizing':image_changes,
            'layout_choices_not_school_rules':{'image_max_width_cm':args.max_image_width_cm,'table_cell_top_bottom_pt':2.5,'table_caption_before_after_pt':3,'image_caption_before_after_pt':6,'paragraph_tracking_pt':list(tracking_by_hash.values())},
            'modified_template_parts':changed,'removed_guidance_parts':removed_parts,'preserved_template_parts':unchanged,
            'field_refresh':'updateFields=true; native read-only render checks PAGE fields; editable document retains fields',
            'unresolved_content':['chapter content has not been reviewed section by section','reference numbering and GB/T7714 entries remain pending substantive review','technical route text remains existing draft'],
            'render_review_required':True}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['output_file','output_sha256','role_counts','visible_text_tokens_unchanged','image_resizing']},ensure_ascii=False))


if __name__=='__main__':main()
