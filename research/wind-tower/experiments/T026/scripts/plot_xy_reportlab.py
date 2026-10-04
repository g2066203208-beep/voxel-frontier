"""Small standard ReportLab XY chart helper; no matplotlib dependency."""
from pathlib import Path
import subprocess
from reportlab.graphics.shapes import Drawing,String,Line
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics import renderSVG,renderPDF
from reportlab.lib import colors

POPP=Path('C:/Users/REME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
PALETTE=['#246393','#d05a27','#65723c','#777777','#7a4b8e']


def panel(drawing,x,y,width,height,title,xlabel,ylabel,series,xlim=None,ylim=None,legend=True):
    chart=LinePlot()
    chart.x,chart.y,chart.width,chart.height=x,y,width,height
    chart.data=[s['points'] for s in series]
    chart.xValueAxis.labels.fontSize=chart.yValueAxis.labels.fontSize=9
    if xlim:chart.xValueAxis.valueMin,chart.xValueAxis.valueMax=xlim
    if ylim:chart.yValueAxis.valueMin,chart.yValueAxis.valueMax=ylim
    for i,s in enumerate(series):
        col=colors.HexColor(s.get('color',PALETTE[i%len(PALETTE)]))
        chart.lines[i].strokeColor=col if s.get('connect',True) else None
        chart.lines[i].strokeWidth=s.get('width',1.4)
        if s.get('dash'):chart.lines[i].strokeDashArray=s['dash']
        if s.get('markers'):
            marker=makeMarker('FilledCircle');marker.size=s.get('marker_size',3);marker.fillColor=col
            chart.lines[i].symbol=marker
    drawing.add(chart)
    drawing.add(String(x,y+height+28,title,fontSize=13))
    drawing.add(String(x,y+height+7,ylabel,fontSize=9))
    drawing.add(String(x+width*.18,y-32,xlabel,fontSize=10))
    if legend:
        for i,s in enumerate(series):
            yy=y-54-i*14
            drawing.add(Line(x,yy,x+18,yy,strokeColor=colors.HexColor(s.get('color',PALETTE[i%len(PALETTE)])),strokeWidth=1.4))
            drawing.add(String(x+25,yy-3,s['label'],fontSize=9))


def save_drawing(drawing,output_prefix,png=True):
    p=Path(output_prefix);p.parent.mkdir(parents=True,exist_ok=True)
    svg,pdf=str(p)+'.svg',str(p)+'.pdf'
    renderSVG.drawToFile(drawing,svg);renderPDF.drawToFile(drawing,pdf)
    files={'svg':svg,'pdf':pdf}
    if png:
        r=subprocess.run([str(POPP),'-singlefile','-r','110','-png',pdf,str(p)],capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stderr[-1000:])
        files['png']=str(p)+'.png'
    return files


def plot_xy(title,xlabel,ylabel,series,output_prefix,subtitle='',xlim=None,ylim=None,png=True):
    drawing=Drawing(760,530)
    panel(drawing,80,150,620,280,title,xlabel,ylabel,series,xlim,ylim)
    if subtitle:drawing.add(String(80,35,subtitle,fontSize=9))
    return save_drawing(drawing,output_prefix,png)
