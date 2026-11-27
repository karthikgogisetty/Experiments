import json
from pathlib import Path
from statistics import median
from math import ceil
from PIL import Image,ImageDraw,ImageFont
from xml.etree import ElementTree as ET

root=Path(__file__).parent
rows=json.loads((root/'hybrid-results.json').read_text())
svg=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',width='1200',height='820',viewBox='0 0 1200 820')
ET.SubElement(svg,'title').text='Keyword, embedding and hybrid search on the same 200 tool requests'
im=Image.new('RGB',(1200,820),'#faf8f4')
draw=ImageDraw.Draw(im)
def rect(x,y,w,h,color):
    ET.SubElement(svg,'rect',x=str(x),y=str(y),width=str(w),height=str(h),fill=color)
    draw.rectangle((x,y,x+w,y+h),fill=color)
def label(x,y,s,size,bold=False,color='#272b35'):
    ET.SubElement(svg,'text',x=str(x),y=str(y),fill=color,**{'font-size':str(size),'font-weight':'700' if bold else '400','font-family':'Arial,sans-serif'}).text=s
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',size)
    draw.text((x,y),s,fill=color,font=font,anchor='ls')
rect(0,0,1200,820,'#faf8f4')
label(54,62,'AGENT TOOL SEARCH   /   LOCAL CPU',23,True,'#4e6174')
label(54,142,'Can hybrid search keep the keyword hits?',52,True)
label(54,204,'480 tools  ·  200 questions  ·  five candidates per question',29)
for x,s in [(55,'Search'),(402,'Target in top 5'),(716,'Median'),(975,'p95')]:
    label(x,307,s,29,True)
for i,(key,title) in enumerate([('keyword','BM25'),('semantic','MiniLM'),('hybrid','Hybrid')]):
    y=374+i*76
    times=sorted(t for r in rows.values() for t in r[key+'_ms'])
    hits=sum(r[key+'_rank'] is not None for r in rows.values())
    for x,s in [(55,title),(402,f'{hits} / 200'),(716,f'{median(times):.2f} ms'),(975,f'{times[ceil(.95*len(times))-1]:.2f} ms')]:
        label(x,y,s,35,True,'#175d63' if i else '#474459')
    rect(55,y+24,1080,2,'#d6d6ce')
gain=sum(not r['keyword_rank'] and bool(r['hybrid_rank']) for r in rows.values())
loss=sum(bool(r['keyword_rank']) and not r['hybrid_rank'] for r in rows.values())
label(55,620,f'Hybrid recovered {gain} keyword misses and lost {loss} keyword hits.',32,True)
label(55,689,f'Currency converter: keyword miss, embedding #2, hybrid #{rows["multiple_52"]["hybrid_rank"]}.',26)
label(55,764,'Warm indexes. One query at a time. Embedding latency includes encoding the question.',23)
im.save(root/'hybrid-chart.png')
ET.ElementTree(svg).write(root/'hybrid-chart.svg',encoding='utf-8')
