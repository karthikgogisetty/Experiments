import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

p=Path(__file__).parent
r=json.loads((p/"results.json").read_text())
im=Image.new("RGB",(1200,900),"#fff8ed")
d=ImageDraw.Draw(im)
def text(x,y,s,size,bold=False,color="#33281e"):
    f=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial"+(" Bold" if bold else "")+".ttf",size)
    d.text((x,y),s,font=f,fill=color,anchor="lt")
text(68,55,"MODEL EVALUATION   /   SPAM FILTER",25,True,"#8b3823")
text(64,126,"Which mistake costs more?",72,True)
text(68,230,"Same model, same 842 test examples. Only the cutoff changed.",32)
text(660,344,"Cutoff 0.50",31,True)
text(925,344,"Cutoff 0.75",31,True)
for i,(label,key) in enumerate([("Real emails sent to spam","false_alarms"),("Spam left in the inbox","missed_spam"),("Weighted cost","weighted_cost")]):
    y=424+i*115
    d.line((68,y-24,1130,y-24),fill="#cfbcaa",width=2)
    text(68,y,label,37)
    text(675,y,str(r["default"][key]),49,True)
    text(946,y,str(r["tuned"][key]),49,True,"#8b3823")
text(68,790,"Cost rule: 5 points per false alarm, 1 per missed spam email.",30)
text(68,851,"UCI Spambase   ·   Logistic regression   ·   Cutoff selected on validation data",24)
im.save(p/"chart.png")
