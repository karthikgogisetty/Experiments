"""Render a release comparison directly from all four measured runs."""
import json
import math
import statistics
from pathlib import Path

here = Path(__file__).parent
runs = [json.loads((here/f"run-{i}.json").read_text()) for i in range(1,5)]
versions = ["1.20.1","1.20.2"]
stats = {}
for case in ["shared","different"]:
    stats[case] = {}
    for version in versions:
        samples = sorted(t for r in runs if r["version"]==version for t in r["samples_ms"][case])
        assert len(samples)==200
        stats[case][version] = [statistics.median(samples), samples[189]]
(here/"comparison.json").write_text(json.dumps(stats,indent=2))
pieces = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1000" viewBox="0 0 1200 1000" role="img" aria-labelledby="bench-title bench-desc"><title id="bench-title">Qdrant release comparison</title><desc id="bench-desc">Median round-trip time per six-query batch, in milliseconds. Each version and condition includes 200 measured batches.</desc><rect width="1200" height="1000" fill="#faf7ef"/>']
def label(x,y,text,size,fill="#212e2a",font="Helvetica",weight="normal",anchor="start"):
    pieces.append(f'<text x="{x}" y="{y}" fill="{fill}" font-family="{font}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{text}</text>')
label(76,80,"TECHPULSE   /   BENCHMARK NOTES",24,weight="bold")
label(1124,80,"22 NOV 2026",24,anchor="end")
pieces.append('<path d="M76 106H1124" stroke="#263b32" stroke-width="2"/>')
label(72,215,"What changed in Qdrant 1.20.2?",69,font="Georgia")
label(76,278,"Median latency per six-query batch   ·   Lower is better",32)
limit=math.ceil(max(values[0] for group in stats.values() for values in group.values())*5)/5
for row,(case,title) in enumerate([("shared","One shared seller filter"),("different","Six different seller filters")]):
    y=375+row*227
    label(76,y,title,34,weight="bold")
    for j,v in enumerate(versions):
        baseline=y+51+j*62
        value=stats[case][v][0]
        width=660*value/limit
        label(76,baseline+10,v,30)
        color=["#86958e","#16604a"][j]
        pieces.append(f'<rect x="220" y="{baseline-20}" width="{width:.2f}" height="36" fill="{color}"/>')
        label(235+width,baseline+9,f"{value:.3f} ms",29,weight="bold")
pieces.append('<path d="M76 796H1124" stroke="#81938a"/>')
label(76,851,"24,000 synthetic products   /   64 dimensions   /   Apple Silicon",29)
label(76,904,"200 warm batches per version and filter condition.",29)
label(76,949,"Four fresh index builds. Release order: old, new, new, old.",26)
nested = [json.loads((here/f"nested-{i}.json").read_text()) for i in range(1,5)]
nested_stats = {}
for version in versions:
    timings = sorted(t for run in nested if run["version"]==version for t in run["samples_ms"])
    assert len(timings)==60
    nested_stats[version] = [statistics.median(timings),timings[56]]
stats["nested"]=nested_stats
(here/"comparison.json").write_text(json.dumps(stats,indent=2))
# Use a separate labelled scale for the much larger 768-dimensional workload.
pieces[0] = pieces[0].replace('height="1000"', 'height="1370"').replace('1200 1000','1200 1370')
label(76,1042,"Nested offers filter",48,font="Georgia")
label(76,1098,"30,000 products   /   768 dimensions   /   Independent bar scale",29)
limit=math.ceil(max(v[0] for v in nested_stats.values()))
for i,v in enumerate(versions):
    baseline=1170+i*70
    value=nested_stats[v][0]
    width=660*value/limit
    label(76,baseline+10,v,30)
    pieces.append(f'<rect x="220" y="{baseline-20}" width="{width:.2f}" height="36" fill="{["#86958e","#16604a"][i]}"/>')
    label(235+width,baseline+9,f"{value:.2f} ms",29,weight="bold")
label(76,1320,"60 timed batches per version across two fresh index builds.",28)
(here/"qdrant.svg").write_text("".join(pieces)+"</svg>")
