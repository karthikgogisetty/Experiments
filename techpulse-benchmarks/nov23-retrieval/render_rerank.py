"""Render the static results card and a click-to-play illustration from measured ranks."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).parent
data = json.loads((root/"rerank-results.json").read_text())
rows, summary = data["rows"], data["summary"]
ink, pale, muted, blue, orange = "#1a1934","#f4f1ff","#575571","#4936ac","#aa400d"
def label(draw,x,y,text,size,bold=False,color=ink):
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial"+(" Bold" if bold else "")+".ttf",size)
    draw.text((x,y),text,font=font,fill=color,anchor="lt")

def panel():
    im = Image.new("RGB",(1200,1020),pale)
    return im,ImageDraw.Draw(im)

im,d = panel()
label(d,64,54,"SEARCH SYSTEMS   /   SCIFACT",24,True,blue)
label(d,60,120,"How deep should I rerank?",70,True)
label(d,64,220,"300 claims  •  5,183 papers  •  one CPU experiment",32)
label(d,64,320,"RELEVANT PAPER AT RANK 1",25,True,blue)
for i,(key,title) in enumerate([("bm25","BM25 alone"),("10","Rerank 10"),("50","Rerank 50")]):
    hits=sum(row[key]["hit1"] for row in rows)
    x=64+i*380
    label(d,x,390,title,36,True)
    label(d,x,448,f"{hits} / 300",44,True,blue if i!=2 else orange)
    for n in range(300):
        col,row=n%25,n//25
        xx,yy=x+col*12,530+row*12
        d.rectangle((xx,yy,xx+8,yy+8),fill=(blue if i!=2 else orange) if n<hits else "#cfcbdd")
    label(d,x,712,f'nDCG@10  {summary[key]["ndcg10"]:.3f}',29)
    if key!="bm25":
        label(d,x,776,f'{summary[key]["median_ms"]:.1f} ms median',30,True)
        label(d,x,822,f'{summary[key]["p95_ms"]:.1f} ms p95',26,color=muted)
d.line((64,900,1136,900),fill=muted,width=2)
label(d,64,926,"Each square represents one claim. Timings cover tokenization and reranking.",25)
label(d,64,971,"TinyBERT L2  /  int8  /  CPU, two inference threads  /  batch size 10",23,color=muted)
im.save(root/"rerank-chart.png")
# Show what changed across the same claims when moving from depth 10 to 50.
gain=sum(r["10"]["hit1"]<r["50"]["hit1"] for r in rows)
loss=sum(r["10"]["hit1"]>r["50"]["hit1"] for r in rows)
frames=[]
for title,desc,phase in [("Start with 10 candidates","Purple = relevant paper ranked first.",0),("Expand to 50 candidates",f"Orange = {gain} newly correct. Outlined = {loss} lost.",1),("Count the net change",f"{gain} gained minus {loss} lost = {gain-loss:+d} first-place hits.",2)]:
    frame=Image.new("RGB",(900,640),pale);draw=ImageDraw.Draw(frame)
    label(draw,50,40,"SAME 300 CLAIMS   /   PAIRED COMPARISON",20,True,blue)
    label(draw,48,103,title,48,True);label(draw,50,185,desc,26)
    for i,r in enumerate(sorted(rows,key=lambda r:r["query"])):
        x,y=54+i%30*26,255+i//30*28
        a,b=r["10"]["hit1"],r["50"]["hit1"]
        color=blue if a else "#cfcbdd";outline=None
        if phase and a!=b:
            color=orange if b else pale;outline=orange
        draw.rounded_rectangle((x,y,x+19,y+19),radius=4,fill=color,outline=outline,width=3)
    label(draw,50,572,"Each square stays with the same claim across frames.",23,color=muted)
    frames.append(frame)
frames[0].save(root/"rerank-motion.gif",save_all=True,append_images=frames[1:],duration=[2200,2700,3200],loop=0)
