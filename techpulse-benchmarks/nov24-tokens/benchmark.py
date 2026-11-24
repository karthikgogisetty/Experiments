"""Run with tokenizers 0.22.1; pass directory of tokenizer.json files named after models.json keys."""
import csv,json,sys,hashlib
from pathlib import Path
from tokenizers import Tokenizer
p=Path(__file__).parent
messages=list(csv.DictReader((p/'messages.tsv').open(),delimiter='\t'))
out={}
for name,meta in json.loads((p/'models.json').read_text()).items():
    file=Path(sys.argv[1])/(name+'.json')
    tok=Tokenizer.from_file(str(file))
    counts=[{lang:len(tok.encode(text,add_special_tokens=False).ids) for lang,text in row.items()} for row in messages]
    out[name]={**meta,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'counts':counts,'totals':{lang:sum(r[lang] for r in counts) for lang in messages[0]}}
(p/'results.json').write_text(json.dumps(out,indent=2))
print({k:(v['counts'][0],v['totals']) for k,v in out.items()})
