import json
from pathlib import Path
from statistics import median

root=Path(__file__).parent
data=json.loads((root/'results.json').read_text())
rows=data['rows']
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 760" width="1120" height="760"><title>Tool retrieval coverage and median JSON size</title><rect width="1120" height="760" fill="#faf7ef"/>']
def text(x,y,s,n,b=False,color='#242e35'):
    svg.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{n}" font-weight="{700 if b else 400}" fill="{color}">{s}</text>')
text(60,68,'AGENT TOOL SEARCH   /   200 REQUESTS',24,True,'#246357')
text(60,154,'How many tools should an agent see?',51,True)
text(60,213,'Exact target schema retrieved from a catalog of 480',29)
for x,s in [(60,'Tools shown'),(330,'Questions covered'),(834,'Schema size¹')]:text(x,316,s,24,True)
for i,k in enumerate([1,3,5,10,20]):
    y=375+60*i
    hits=sum(r['rank'] is not None and r['rank']<=k for r in rows)
    text(65,y,str(k),30,True)
    svg.append(f'<rect x="330" y="{y-21}" width="330" height="18" fill="#d9ded7"/><rect x="330" y="{y-21}" width="{330*hits/len(rows)}" height="18" fill="#287761"/>')
    text(675,y,f'{hits}/200',25)
    text(840,y,f"{median(r['bytes'][str(k)] for r in rows)/1000:.1f} kB",28)
text(60,685,'¹ Median compact JSON per request. Full catalog: 230.5 kB.',24)
text(60,730,'BFCL v4 multiple subset  ·  pooled catalog  ·  SQLite FTS5 / BM25',22,False,'#41595a')
svg.append('</svg>')
raw=''.join(svg).encode()
(root/'chart.svg').write_bytes(raw)
# Rasterize the chart's two SVG primitives for the LinkedIn attachment.
from xml.etree import ElementTree
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1120,760))
draw=ImageDraw.Draw(im)
for el in ElementTree.fromstring(raw):
    a=el.attrib
    x,y=float(a.get('x',0)),float(a.get('y',0))
    if el.tag.endswith('rect'):
        draw.rectangle((x,y,x+float(a['width']),y+float(a['height'])),fill=a['fill'])
    elif el.tag.endswith('text'):
        family='Arial Bold.ttf' if a['font-weight']=='700' else 'Arial.ttf'
        font=ImageFont.truetype('/System/Library/Fonts/Supplemental/'+family,int(a['font-size']))
        draw.text((x,y),el.text,font=font,fill=a['fill'],anchor='ls')
im.save(root/'chart.png')
