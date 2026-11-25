"""Build the revised chart from client-side serving measurements."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).parent
stats=json.loads((root/'local-serving.json').read_text())['summary']
im=Image.new('RGB',(1200,850),'#f7f6f1')
d=ImageDraw.Draw(im)
def text(x,y,s,n,b=False,c='#182f37'):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',n)
    d.text((x,y),s,font=font,fill=c,anchor='lt')
text(65,58,'LOCAL LLM SERVING TEST',26,True,'#44656a')
text(62,131,'When nine requests want one server',58,True)
text(65,225,'95th-percentile time to first text · lower is better',31)
maxval=max(v['ttft_ms']['p95'] for v in stats.values())
for i,(key,title,color) in enumerate([('round_robin','Round robin','#437e87'),('affinity','Warm cache','#ae512d')]):
    y=340+130*i
    value=stats[key]['ttft_ms']['p95']
    text(65,y,title,32,True)
    end=396+560*value/maxval
    d.rectangle((396,y-6,end,y+38),fill=color)
    text(end+16,y,f'{value:.1f} ms',32,True)
text(65,565,f"p95 queue wait: {stats['round_robin']['queue_ms']['p95']:.1f} ms round robin  /  {stats['affinity']['queue_ms']['p95']:.1f} ms warm cache",29,True)
text(65,625,'12 requests per burst. Nine share the same opening text.',32)
text(65,695,'Four warmed CPU servers  /  one active request per server',27)
text(65,745,'288 timed requests per policy  /  Stories15M  /  first nonempty streamed text',24)
im.save(root/'local-serving.png')
