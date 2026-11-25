import json
from pathlib import Path
from statistics import median
from PIL import Image, ImageDraw, ImageFont
root = Path(__file__).parent
rows = list(map(json.loads, (root/'measured.jsonl').read_text().splitlines()))
assert len(rows) == 8 and len({r['ids_sha'] for r in rows}) == 1
im = Image.new('RGB',(1200,780),'#f8f6ee')
d = ImageDraw.Draw(im)
def label(x,y,s,size,bold=False,color='#172739'):
    file = 'Arial Bold.ttf' if bold else 'Arial.ttf'
    d.text((x,y),s,font=ImageFont.truetype('/System/Library/Fonts/Supplemental/'+file,size),fill=color,anchor='lt')
label(60,48,'HUGGING FACE TOKENIZERS   /   LOCAL CPU TEST',23,True,'#526377')
label(60,106,'Same code. Same 116,537 token IDs.',55,True)
label(60,197,'Median time to encode 256 chunks of Python code',31)
for i,stage in enumerate(['First batch','Repeated batch']):
    y=280+168*i
    label(60,y,stage,33,True)
    for j,v in enumerate(['0.23.2','1.0.0-rc.5']):
        g=[r for r in rows if r['version']==v]
        n=median(r['first_ms'] for r in g) if i==0 else median(t for r in g for t in r['elapsed_ms'])
        yy=y+53+45*j
        label(64,yy,v,23)
        end=282+int(n*13)
        d.rectangle((282,yy,end,yy+24),fill=['#53667d','#007767'][j])
        label(end+14,yy,f'{n:.1f} ms',25,True)
d.line((60,636,1140,636),fill='#bcc4c4',width=2)
label(60,666,'4 fresh processes per version  ·  15 repeat batches per process',25)
label(60,714,'Includes creating Python ID lists. Excludes loading, compilation and model inference.',23)
im.save(root/'chart.png')
