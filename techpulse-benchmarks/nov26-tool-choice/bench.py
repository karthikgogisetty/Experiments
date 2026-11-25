"""Run against llama.cpp b12668, FunctionGemma 270M IT Q8_0, CPU, context 2048."""
import json
import argparse
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler

http = build_opener(ProxyHandler({}))
tools = []
for name, arg, desc in [('set_timer','minutes','Start a countdown for the given number of minutes.'),('set_volume','percent','Change speaker volume to the given percentage.'),('set_temperature','degrees','Set the thermostat to the given temperature in Celsius.')]:
    schema = dict(type='object', properties={arg:{'type':'integer'}}, required=[arg])
    tools.append(dict(type='function',function=dict(name=name,description=desc,parameters=schema)))
cases = []
for value in (15,20,25,30):
    for tool, action, question in [
        ('set_timer',f'Start a {value}-minute timer.',f'How many seconds are in a {value}-minute timer?'),
        ('set_volume',f'Set the speaker volume to {value} percent.',f'What does {value} percent speaker volume mean?'),
        ('set_temperature',f'Set the thermostat to {value} degrees Celsius.',f'What is {value} degrees Celsius in Fahrenheit?')]:
        cases.extend([(action,tool,value),(question,None,value)])

parser = argparse.ArgumentParser()
parser.add_argument('--explicit',action='store_true')
args = parser.parse_args()
instruction = 'You are a model that can do function calling with the following functions'
if args.explicit:
    instruction += '. Call a tool only if the user explicitly asks to change a device or start a timer. For informational questions, reply in text without calling any tool.'
rows=[]
for prompt, expected, value in cases:
    payload=dict(messages=[dict(role='developer',content=instruction),dict(role='user',content=prompt)],tools=tools,temperature=0,seed=42,max_tokens=96,stop=['<start_function_response>'])
    req=Request('http://127.0.0.1:18973/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with http.open(req,timeout=45) as response:
        choice=json.load(response)['choices'][0]
    msg=choice['message']
    rows.append(dict(prompt=prompt,expected=expected,value=value,message=msg,finish=choice['finish_reason']))
Path(__file__).with_name('explicit.json' if args.explicit else 'results.json').write_text(json.dumps(rows,indent=2))
