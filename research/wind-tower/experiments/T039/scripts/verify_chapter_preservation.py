"""Verify a format-only DOCX edit without disclosing thesis text.

python verify_chapter_preservation.py --draft DRAFT.docx --output RESULT.docx
       --reference TEMPLATE.docx --report preservation.json
Requires lxml. Reads all inputs without modifying them. Visual QA is separate.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile
from lxml import etree as E

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
NS={'w':W,'wp':WP}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def package(path):
    with zipfile.ZipFile(path) as archive:
        return {n:archive.read(n) for n in archive.namelist()}

def body_and_text(parts):
    root=E.fromstring(parts['word/document.xml'])
    body=root.find('{'+W+'}body')
    return body,body.xpath('.//w:t/text()',namespaces=NS)

def citations(body):
    signatures=[]
    sizes=Counter()
    for run in body.xpath('.//w:r[w:rPr/w:vertAlign[@w:val="superscript"]]',namespaces=NS):
        text=''.join(run.xpath('.//w:t/text()',namespaces=NS))
        size=run.find('{'+W+'}rPr/{'+W+'}sz')
        point=float(size.get('{'+W+'}val'))/2 if size is not None else None
        where='table' if any(a.tag=='{'+W+'}tbl' for a in run.iterancestors()) else 'body'
        signatures.append([digest(text.encode('utf-8')),point,where])
        sizes[(where,point)]+=1
    return signatures,[{'region':r,'size_pt':p,'count':n} for (r,p),n in sorted(sizes.items())]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['draft','output','reference','report']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    paths=[args.draft,args.output,args.reference]
    if args.report.resolve() in {p.resolve() for p in paths}:
        raise ValueError('Report must not overwrite an input document')
    before={p.name:digest(p.read_bytes()) for p in paths}
    old,new,reference=map(package,paths)
    old_body,old_text=body_and_text(old)
    body,new_text=body_and_text(new)
    old_cites,old_sizes=citations(old_body)
    new_cites,new_sizes=citations(body)
    media_old={n:digest(b) for n,b in old.items() if n.startswith('word/media/') and b}
    media_new={digest(b) for n,b in new.items() if n.startswith('word/media/') and b}
    section=body.find('{'+W+'}sectPr')
    reference_section=E.fromstring(reference['word/document.xml']).xpath('.//w:sectPr',namespaces=NS)[6]
    def page_geometry(section_node):
        return {
            'size':[section_node.find('{'+W+'}pgSz').get('{'+W+'}'+k) for k in ['w','h']],
            'margins':{k:section_node.find('{'+W+'}pgMar').get('{'+W+'}'+k) for k in ['top','bottom','left','right','header','footer']}
        }
    geometry=page_geometry(section)
    image_extents=[{'width_cm':int(x.get('cx'))/360000,'height_cm':int(x.get('cy'))/360000}
                   for x in body.xpath('.//wp:inline/wp:extent',namespaces=NS)]
    table_borders_old=[E.tostring(x) for x in old_body.xpath('.//w:tblBorders|.//w:tcBorders',namespaces=NS)]
    table_borders_new=[E.tostring(x) for x in body.xpath('.//w:tblBorders|.//w:tcBorders',namespaces=NS)]
    # Prefix declarations may differ after template import; compare expanded-tag trees.
    def normalized(xml_bytes):
        node=E.fromstring(xml_bytes)
        return [(e.tag,sorted(e.attrib.items()),e.text or '') for e in node.iter()]
    border_match=[normalized(x) for x in table_borders_old]==[normalized(x) for x in table_borders_new]
    record={'scope':'Structural preservation only; no visual or scientific approval',
            'source_hashes':before,
            'visible_w_t_sequence_unchanged':old_text==new_text,
            'visible_w_t_sequence_sha256':digest('\n'.join(new_text).encode('utf-8')),
            'superscript_text_hashes_sizes_and_regions_unchanged':old_cites==new_cites,
            'superscript_groups':new_sizes,
            'all_source_image_bytes_preserved':all(x in media_new for x in media_old.values()),
            'source_image_hashes':media_old,
            'source_table_borders_preserved':border_match,
            'image_extents_cm':image_extents,
            'template_default_header5_bytes_preserved':new['word/header5.xml']==reference['word/header5.xml'],
            'template_default_footer5_bytes_preserved':new['word/footer5.xml']==reference['word/footer5.xml'],
            'page_width_height_twips':geometry['size'],
            'margins_twips':geometry['margins'],
            'page_geometry_matches_template_body_section':geometry==page_geometry(reference_section),
            'inputs_unchanged':before=={p.name:digest(p.read_bytes()) for p in paths},
            'private_text_excluded':True}
    mandatory=['visible_w_t_sequence_unchanged','superscript_text_hashes_sizes_and_regions_unchanged',
               'all_source_image_bytes_preserved','source_table_borders_preserved',
               'template_default_header5_bytes_preserved','template_default_footer5_bytes_preserved',
               'page_geometry_matches_template_body_section','inputs_unchanged']
    record['structural_checks_pass']=all(record[k] for k in mandatory)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not record['structural_checks_pass']:
        raise RuntimeError('Structural preservation check failed; inspect the JSON report')
    print(json.dumps({'structural_checks_pass':True,'superscript_groups':new_sizes,'image_extents_cm':image_extents},ensure_ascii=False))

if __name__=='__main__':
    main()
