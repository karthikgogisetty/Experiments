from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).parent
r=json.loads((p/'results.json').read_text())
im=Image.new('RGB',(1200,970),'#fff9ed');d=ImageDraw.Draw(im)
def text(x,y,s,n,b=False,c='#312a36'):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',n)
    d.text((x,y),s,font=font,fill=c,anchor='lt')
text(62,52,'MULTILINGUAL AI    /    LOCAL TOKENIZER TEST',25,True)
text(60,123,'Eight messages, four languages',66,True)
text(62,228,'Total input tokens across eight app messages in each language',31)
for x,c,t in [(64,'#73438a','Sarvam-30B'),(405,'#026e76','Qwen3-30B-A3B')]:
    d.rectangle((x,305,x+30,332),fill=c);text(x+45,305,t,27)
for i,lang in enumerate(['English','Hindi','Tamil','Telugu']):
    y=392+i*124;text(62,y+12,lang,35,True)
    for j,(name,color) in enumerate([('Sarvam','#73438a'),('Qwen','#026e76')]):
        n=r[name]['totals'][lang];end=265+n*2.5;top=y+j*42
        d.rectangle((265,top,end,top+25),fill=color);text(end+14,top,str(n),27,True)
d.line((62,898,1138,898),fill='#b4a9ad');text(62,922,'Same strings for both tokenizers. No chat template or special tokens.',24)
im.save(p/'chart.png')
