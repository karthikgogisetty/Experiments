import json
from pathlib import Path

root = Path(__file__).parent
r = json.loads((root/'results.json').read_text())
bits = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="960" viewBox="0 0 1200 960" role="img" aria-labelledby="t d"><title id="t">What reaches the reranker?</title><desc id="d">Claims with a labeled relevant paper in the BM25 shortlist, out of 300.</desc><rect width="1200" height="960" fill="#f8f6ed"/>']
def text(x,y,label,size,font="Helvetica",color="#192f2c"):
    bits.append(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{color}">{label}</text>')
text(72,77,"TECHPULSE   /   RETRIEVAL EXPERIMENTS",26)
bits.append('<path d="M72 109H1128" stroke="#213b33"/>')
text(68,223,"What reaches the reranker?",82,"Georgia")
text(72,295,"Claims with a relevant paper in the shortlist, out of 300",36)
for i,(k,count) in enumerate(r['hits'].items()):
    y=391+i*102
    text(72,y+28,"Top "+k,32)
    bits.append(f'<rect x="234" y="{y}" width="700" height="32" fill="#dce1d9"/><rect x="234" y="{y}" width="{700*count/300:.2f}" height="32" fill="#176350"/>')
    text(959,y+29,f"{count} / 300",32)
bits.append('<path d="M72 788H1128" stroke="#84978b"/>')
text(72,852,"36 claims still had no labeled match in the top 50.",37,"Georgia")
text(72,917,"BEIR SciFact test set   ·   5,183 papers   ·   BM25 on titles and abstracts",26)
(root/'chart.svg').write_text(''.join(bits)+'</svg>')
