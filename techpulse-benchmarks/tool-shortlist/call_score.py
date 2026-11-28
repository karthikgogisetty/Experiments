"""Parse a single FunctionGemma call and compare to BFCL's listed argument alternatives."""
import json
import re
def parse(text):
    match=re.fullmatch(r'\s*<start_function_call>call:([\w.]+)(\{.*\})<end_function_call>\s*',text,re.S)
    if not match: raise ValueError('not one complete call')
    # Quote bare object keys outside escaped strings; defer nesting and scalar types to JSON.
    parts=re.split(r'(<escape>.*?<escape>)',match[2],flags=re.S)
    for i,s in enumerate(parts):
        parts[i]=json.dumps(s[8:-8]) if i%2 else re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:',r'\1"\2":',s)
    def unique(items):
        out=dict(items)
        if len(out)!=len(items): raise ValueError('duplicate key')
        return out
    return match[1],json.loads(''.join(parts),object_pairs_hook=unique)

def matches(args,expected):
    if not isinstance(args,dict) or args.keys()-expected.keys(): return False
    def equal(a,b):
        if isinstance(a,bool)!=isinstance(b,bool): return False
        if isinstance(a,list) and isinstance(b,list): return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
        if isinstance(a,dict) and isinstance(b,dict): return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
        return a==b
    return all(any(equal(args[k],option) for option in options) if k in args else '' in options for k,options in expected.items())
