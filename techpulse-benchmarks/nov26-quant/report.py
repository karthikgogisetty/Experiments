import json
from pathlib import Path
from statistics import median
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).parent
runs=json.loads((root/'results.json').read_text())
assert len(runs)==4
im=Image.new('RGB',(1200,810),'#fcf8ef')
d=ImageDraw.Draw(im)
def label(x,y,s,size,bold=False,color='#272640'):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',size)
    d.text((x,y),s,font=font,fill=color,anchor='lt')
label(60,55,'QWEN2.5-CODER 0.5B   /   APPLE METAL',25,True,'#75528b')
label(60,127,'Which SQL tests survived 4-bit?',58,True)
label(60,219,'Ten prompts. Twelve test databases per query.',32)
label(590,316,'Q4_K_M',35,True)
label(875,316,'Q8_0',35,True)
metrics=['Tasks passed¹','Response time²','Peak process RSS³']
for y,name in zip([407,500,593],metrics):
    label(62,y,name,33,True)
for x,k in zip([590,875],['q4_k_m','q8_0']):
    pair=[r for r in runs if r['format']==k]
    scores=[{a['task'] for a in r['results'] if all(a['passed'])} for r in pair]
    assert scores[0]==scores[1],scores
    latency=median(a['ms'] for r in pair for a in r['results'])/1000
    rss=max(r['peak_process_bytes'] for r in pair)/2**20
    vals=[f'{len(scores[0])} / 10',f'{latency:.2f} s',f'{rss:.0f} MiB']
    for y,val in zip([407,500,593],vals):label(x,y,val,33,True,'#75528b')
    print(k,vals,sorted(scores[0]))
label(60,705,'¹ All 12 fixtures passed.   ² Median full response, two runs per format.',24)
label(60,751,'³ Maximum server resident memory across runs on a unified-memory Mac.',24)
im.save(root/'chart.png')
