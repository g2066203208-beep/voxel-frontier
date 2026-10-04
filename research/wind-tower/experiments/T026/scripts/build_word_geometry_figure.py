"""Same true INP projections, with 7pt minimum text at 5.5in Word width."""
from pathlib import Path
from io import BytesIO
import argparse,hashlib,json,subprocess,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--input',type=Path,help='Actual reconstructed M2 INP; uses the recorded local source if omitted.')
cli.add_argument('--output-dir',type=Path,default=Path('D:/Codex-research-validation/T026/figures'))
cli.add_argument('--pdftoppm',type=Path,help='Poppler pdftoppm executable; otherwise bundled runtime or PATH.')
args=cli.parse_args()
source=HERE/'build_input_geometry_figure.py'
code=source.read_text(encoding='utf-8').split('qa={')[0]
replacements={
 "c=canvas.Canvas(str(PDF),pagesize=(W,H),pageCompression=1)":"pdf_memory=BytesIO();c=canvas.Canvas(pdf_memory,pagesize=(W,H),pageCompression=1)",
 "c.setFillColor(color);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,t)":"c.setFillColor(color);c.setFont('Helvetica-Bold' if bold else 'Helvetica',max(size,18));c.drawString(x,y,t)",
 "text(x+13,y+h-21,title,12,bold=True)":"text(x+13,y+h-24,title,21,bold=True)",
 "text(x-4,y-17,'X / Y / Z (m)',8)":"text(x-4,y-20,'X / Y / Z (m)',18)",
 "text(end[0]+3,end[1]-3,label,9,bold=True)":"text(end[0]+3,end[1]+(7 if label=='Z' else -5),label,18,bold=True)",
 "Actual nodes and connectivity from DTU158_RECONSTRUCTED_M2.inp; undeformed input, no result contour.":"Actual M2 input coordinates and connectivity; undeformed geometry. Axes in metres.",
 "'Y = 0 m; base'":"'Y = 0 m'",
 "'Y = 112 m; C / S'":"'Y = 112 m'",
 "'Y = 158 m; tower top'":"'Y = 158 m'",
 "triad(72,155,P_MAIN,24)":"triad(72,165,P_MAIN,34)",
 "text(50,129,'Tower: 31 concrete + 4 steel segments',9)":"text(215,129,'31 C + 4 S',18)",
 "triad(450,427,P_MAIN,20)":"triad(450,535,P_MAIN,32)",
 " '32 nodes; 28 B31 elements',\n 'Rigid body at RNA_RP',\n 'RP = (0, 160, 0) m',\n 'Tower top = (0, 158, 0) m',\n 'Source-restored mass carrier',\n 'Not physical blade surfaces',\n 'Not a rotating aeroelastic model'":" '32 nodes / 28 B31',\n 'Rigid RNA skeleton',\n 'RP (0, 160, 0) m',\n 'Tower top Y = 158 m',\n 'No blade surfaces'",
 "text(760,608-21*i,t,9,bold=i==0)":"text(760,608-26*i,t,18,bold=i==0)",
 "text(760,441,'Mass / inertia acceptance:',9,bold=True)":"text(760,443,'Mass / inertia:',18,bold=True)",
 "text(760,426,'see separate discrete FE audit.',9)":"text(760,420,'see chapter text.',18)",
 " 'CSEG_01  |  C3D8R / C70',\n '72 circumferential divisions',\n '3 axial divisions',\n '2 divisions through thickness',\n '432 hexahedral elements',\n 'Height: 3.64 m',\n 'Wall thickness: 0.28 m',\n 'Outer diameter: 8.33 -> 8.17 m'":" 'CSEG_01 / C3D8R',\n '72 x 3 x 2 divisions',\n '432 solid elements',\n 'h = 3.64 m',\n 't = 0.28 m',\n 'D = 8.33 -> 8.17 m'",
 "text(760,312-18*i,t,9,bold=i==0)":"text(760,312-27*i,t,18,bold=i==0)",
 "text(415,126,'Projection uses actual X/Y/Z coordinates; uniform scale within each panel.',8)":"# Projection basis and lineage remain in the unchanged full source PDF / QA.",
 "M2 tower: 15,120 elements / 29,808 nodes.  RNA skeleton is shown at true relative scale in (a).":"M2: 15,120 tower elements / 29,808 nodes. Panel (a) uses true relative scale.",
 "Projected coordinate basis: (a,b) u = X + 0.45 Z; v = Y + 0.18 Z.  (c) stated orthographic basis in QA metadata.":"Basis (a,b): u = X + 0.45 Z; v = Y + 0.18 Z. Panel (c): orthographic projection.",
 "Scope: traceable reconstructed reference branch; geometry/topology figure only.  No stress, mode shape or validation result is implied.":"Geometry / topology only. No stress, vibration amplitude or result contour."
}
for old,new in replacements.items():
 assert old in code,old
 code=code.replace(old,new,1)
if args.input is not None:
 old="INPUT=Path('D:/Codex-research-validation/T026/tower/DTU158_RECONSTRUCTED_M2/DTU158_RECONSTRUCTED_M2.inp')"
 assert old in code
 code=code.replace(old,'INPUT=provided_input',1)
code=code.replace("OUTDIR=Path('D:/Codex-research-validation/T026/figures')",'OUTDIR=provided_output_dir',1)
ns={'BytesIO':BytesIO,'__file__':str(source),'provided_input':args.input,'provided_output_dir':args.output_dir};exec(compile(code,str(source),'exec'),ns)
memory=ns['pdf_memory'].getvalue()
out=args.output_dir/'figure2-1-word.png'
render_input=out.with_name('.figure2-1-word-render-tmp.pdf')
originals=[out.with_name('figure2-1-input-geometry.pdf'),out.with_name('figure2-1-input-geometry.png'),out.with_name('figure2-1-input-geometry-300dpi.png')]
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in originals if p.exists()}
bundled_poppler=Path('C:/Users/REME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
poppler=args.pdftoppm or (bundled_poppler if bundled_poppler.exists() else Path(shutil.which('pdftoppm') or 'pdftoppm'))
render_input.write_bytes(memory)
try:
 subprocess.run([str(poppler),'-png','-r','216','-singlefile',str(render_input),str(out.with_suffix(''))],check=True,capture_output=True)
finally:
 render_input.unlink(missing_ok=True)
size=Image.open(out).size
unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
assert unchanged,'Original figure changed'
qa={'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_builder':str(source),'source_INP':str(ns['INPUT']),'source_INP_sha256':ns['s']['sha256'],'minimum_text_font_source_points':18,'minimum_text_at_5_5_in_word_points':18*5.5*72/1000,'dimensions_px':list(size),'same_actual_nodes_elements_and_projections':True,'original_PDF_and_PNG_unmodified':unchanged,'original_sha256':before,'temporary_PDF_removed':not render_input.exists(),'visual_QA':'pending view_image'}
out.with_name('figure2-1-word-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(qa,ensure_ascii=False))
