import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from html import escape
p=Path(__file__).parent
r=json.loads((p/'results.json').read_text())
im=Image.new('RGB',(1200,1030),'#142638')
d=ImageDraw.Draw(im)
def label(x,y,text,size,bold=False,color='#f5f7fc'):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',size)
    d.text((x,y),text,font=font,fill=color,anchor='lt')
label(66,56,'AGENT OUTPUTS   /   LOCAL EXPERIMENT',25,True,'#a4dbfa')
label(62,129,'Can the wrong answer pass?',68,True)
label(66,235,'Expected ticket priority: high. Allowed values: high or low.',34)
label(66,344,'Candidate response',32,True)
label(628,344,'JSON object',29,True)
label(930,344,'Schema',29,True)
for i,row in enumerate(r['results']):
    y=415+80*i
    d.line((66,y-18,1134,y-18),fill='#536474')
    label(66,y,row['candidate'],29)
    for x,ok in zip((628,930),row['accepted']):
        label(x,y,'Allowed' if ok else 'Blocked',29,True,'#a6edcd' if ok else '#ffbea7')
label(66,938,'Six fixed inputs  ·  Byte-level replay  ·  Transformers.js constraint engine 4.3.2',25,color='#c1d4e1')
im.save(p/'chart.png')
