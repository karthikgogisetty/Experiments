import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).parent
runs=json.loads((p/'results.json').read_text())['traces']['toolagent']['runs']
im=Image.new('RGB',(1200,960),'#faf8f3');d=ImageDraw.Draw(im)
def label(x,y,s,n,b=False,color='#1d2b3b'):
    d.text((x,y),s,font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',n),fill=color,anchor='lt')
label(65,54,'INFERENCE SYSTEMS   /   TRACE REPLAY',26,True)
label(62,132,'A fleet average can hide a hot replica',55,True)
label(65,225,'Change in uncached input tokens versus round robin',32)
zero=790
d.line((zero,331,zero,756),fill='#5b6770',width=2)
for i,cap in enumerate((256,1024,4096)):
    pair=runs[f'{cap}/1000'];a,b=pair['round_robin']['uncached'],pair['prefix']['uncached']
    y=340+148*i
    label(65,y,f'{cap:,} blocks / replica',28,True)
    for j,(key,fun) in enumerate([('Fleet total',sum),('Largest replica total',max)]):
        delta=100*(fun(b)/fun(a)-1);end=zero+delta*20;top=y+43*j
        label(65,top+40,key,22) if False else None
        color='#216e68' if j==0 else '#a34b21'
        d.rectangle((min(zero,end),top,max(zero,end),top+23),fill=color)
        label(end+10 if delta>0 else end-109,top-2,f'{delta:+.1f}%',24,True,color)
d.rectangle((65,802,96,826),fill='#216e68');label(110,799,'Fleet total',26)
d.rectangle((400,802,431,826),fill='#a34b21');label(445,799,'Largest per-replica total',26)
label(65,890,'Mooncake tool-agent trace  /  23,608 requests  /  four independent LRU caches',24)
im.save(p/'chart.png')
