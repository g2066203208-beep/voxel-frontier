"""从相同真实 INP 坐标生成图2-1的中文 Word 版，保留英文图及全部数值。"""
from pathlib import Path
from io import BytesIO
import ast,hashlib,json,subprocess,shutil
from PIL import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE=Path(__file__).resolve().parent
english=HERE/'build_word_geometry_figure.py'
prefix=english.read_text(encoding='utf-8').split("ns={'BytesIO'")[0]
env={'__file__':str(english)}
exec(compile(prefix,str(english),'exec'),env)
code=env['code'];args=env['args'];source=env['source']
translations={
 'Figure 2-1  |  Tower and fixed RNA input geometry':'图2-1 塔架与刚体RNA输入几何',
 'Actual M2 input coordinates and connectivity; undeformed geometry. Axes in metres.':'依据M2实际节点与单元连接绘制；未变形几何，坐标单位m。',
 '(a) Complete assembly':'(a) 整体装配',
 '(b) RNA: 28 B31 mass-carrier elements':'(b) RNA：28个B31质量载体',
 '(c) CSEG_01: actual refined solid mesh':'(c) CSEG_01：实际细化实体网格',
 '31 C + 4 S':'31混凝土段＋4钢段',
 '32 nodes / 28 B31':'32节点／28个B31',
 'Rigid RNA skeleton':'刚体RNA质量骨架',
 'RP (0, 160, 0) m':'RP坐标(0,160,0)m',
 'Tower top Y = 158 m':'塔顶Y = 158 m',
 'No blade surfaces':'不表示叶片实体表面',
 'Mass / inertia:':'质量与惯量：',
 'see chapter text.':'见正文的离散核验。',
 '72 x 3 x 2 divisions':'周向72／轴向3／厚向2',
 '432 solid elements':'432个实体单元',
 'h = 3.64 m':'段高h = 3.64 m',
 't = 0.28 m':'壁厚t = 0.28 m',
 'D = 8.33 -> 8.17 m':'外径D = 8.33→8.17 m',
 'M2: 15,120 tower elements / 29,808 nodes. Panel (a) uses true relative scale.':'M2塔筒：15,120单元／29,808节点；整体图(a)保持真实相对尺度。',
 'Basis (a,b): u = X + 0.45 Z; v = Y + 0.18 Z. Panel (c): orthographic projection.':'投影(a,b)：u = X + 0.45 Z，v = Y + 0.18 Z；局部图(c)为正投影。',
 'Source SHA256: ':'输入SHA256：',
 'Geometry / topology only. No stress, vibration amplitude or result contour.':'仅表示几何与拓扑，不表示应力、振动幅值或结果云图。',
 'Figure 2-1: tower and fixed RNA input geometry, reconstructed M2':'图2-1 重建M2塔架与刚体RNA输入几何',
 'Independent coordinate and connectivity extraction; T026':'T026 依据实际节点坐标与单元连接独立绘制',
}
for old,new in translations.items():
 assert old in code,old
 code=code.replace(old,new)
code=code.replace("'Helvetica-Bold' if bold else 'Helvetica'","'TowerCN'")
code=code.replace("text(215,129,'31混凝土段＋4钢段',18)","text(177,129,'31混凝土段＋4钢段',18)")
# Local installed Windows font, used under the device's license. No font file
# is copied to the repository; the generated PDF only embeds its used subset.
font_path=Path('C:/Windows/Fonts/simhei.ttf')
font=TTFont('TowerCN',str(font_path));pdfmetrics.registerFont(font)
literal_chars=set()
for node in ast.walk(ast.parse(code)):
 if isinstance(node,ast.Constant) and isinstance(node.value,str):literal_chars.update(node.value)
display_chars={c for c in literal_chars if ord(c)>=32 and (ord(c)<127 or '\u3000'<=c<='\u9fff' or c in '→×·−')}
missing=sorted(c for c in display_chars if ord(c) not in font.face.charToGlyph)
assert not missing,'中文字体缺字：'+''.join(missing)
env2={'BytesIO':BytesIO,'__file__':str(source),'provided_input':args.input,'provided_output_dir':args.output_dir}
exec(compile(code,str(source),'exec'),env2)
out=args.output_dir/'figure2-1-word-zh.png';pdf=out.with_suffix('.pdf')
originals=[args.output_dir/n for n in ['figure2-1-input-geometry.pdf','figure2-1-input-geometry.png','figure2-1-input-geometry-300dpi.png','figure2-1-word.png']]
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in originals if p.exists()}
pdf.write_bytes(env2['pdf_memory'].getvalue())
bundled=Path('C:/Users/REME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
poppler=args.pdftoppm or (bundled if bundled.exists() else Path(shutil.which('pdftoppm') or 'pdftoppm'))
subprocess.run([str(poppler),'-png','-r','216','-singlefile',str(pdf),str(out.with_suffix(''))],check=True,capture_output=True)
unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
assert unchanged
qa={'outputs':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [out,pdf]],'source_INP':{'path':str(env2['INPUT']),'sha256':env2['s']['sha256']},'language':'zh-CN; XYZ, units and element codes retained','font':{'name':font.face.name.decode(),'local_path':str(font_path),'glyph_coverage_checked':True,'checked_character_count':len(display_chars),'missing_glyphs':missing,'font_file_not_redistributed':True},'minimum_text_at_5_5_in_word_points':7.128,'dimensions_px':list(Image.open(out).size),'same_actual_nodes_elements_and_projection_matrices':True,'original_English_figures_unchanged':unchanged,'original_SHA256':before,'visual_QA':'pending view_image','no_new_solver':True}
out.with_name('figure2-1-word-zh-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(qa,ensure_ascii=False))
