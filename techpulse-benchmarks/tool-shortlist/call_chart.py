import json
from pathlib import Path
from math import ceil
from statistics import median
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw,ImageFont

root=Path(__file__).parent
rows=json.loads((root/'call-results.json').read_text())
assert len(rows)==400
im=Image.new('RGB',(1280,930),'#faf7f0')
draw=ImageDraw.Draw(im)
svg=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',viewBox='0 0 1280 930')
ET.SubElement(svg,'rect',width='1280',height='930',fill='#faf7f0')
ET.SubElement(svg,'title').text='Where the correct tool calls survived'
def text(x,y,s,n,b=False,color='#212d39'):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',n)
    draw.text((x,y),s,font=font,fill=color,anchor='ls')
    ET.SubElement(svg,'text',x=str(x),y=str(y),fill=color,**{'font-family':'Arial,sans-serif','font-size':str(n),'font-weight':'700' if b else '400'}).text=s
text(55,62,'LOCAL TOOL-CALLING TEST    /    200 QUESTIONS PER ROUTE',23,True,'#506866')
text(55,147,'Where did the correct calls survive?',59,True)
text(55,212,'Question → retrieve tools → generate one call → check arguments',31)
text(55,323,'Outcome',31,True)
text(730,323,'Keyword',31,True)
text(989,323,'Hybrid',31,True)
for i,label in enumerate(['Target in shortlist','Correct tool in parsed call','Correct tool + arguments','Median end-to-end','p95 end-to-end']):
    text(55,409+i*76,label,34,i==2)
for x,key in [(730,'keyword'),(989,'hybrid')]:
    rr=[r for r in rows if r['method']==key]
    times=sorted(r['e2e_ms'] for r in rr)
    vals=[sum(bool(r['rank']) for r in rr),sum(r['tool_ok'] for r in rr),sum(r['call_ok'] for r in rr),median(times),times[ceil(len(times)*.95)-1]]
    for i,v in enumerate(vals): text(x,409+i*76,f'{v}/200' if i<3 else f'{v:.0f} ms',36,i==2,'#216758')
    print(key,vals)
text(55,821,'FunctionGemma 270M Q8_0  ·  one request at a time  ·  warm local catalog and model',26)
text(55,872,'End-to-end spans retrieval through the model response. No external tools were executed.',24)
im.save(root/'call-chart.png')
ET.ElementTree(svg).write(root/'call-chart.svg',encoding='utf-8')
