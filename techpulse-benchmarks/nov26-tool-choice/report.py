import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).parent
def measure(filename):
    rows = json.loads((root/filename).read_text())
    assert len(rows) == 24
    correct = unwanted = 0
    arguments = {'set_volume':'percent','set_temperature':'degrees','set_timer':'minutes'}
    for row in rows:
        assert row['finish'] == 'stop'
        output = row['message']['content']
        name = row['expected']
        if name:
            exact = '<start_function_call>call:%s{%s:%d}<end_function_call>' % (name,arguments[name],row['value'])
            correct += output == exact
        else:
            unwanted += '<start_function_call>call:' in output
    return [correct, unwanted]

score = measure('results.json')
explicit = measure('explicit.json')
print('explicit rule:',explicit)
im = Image.new('RGB',(1200,780),'#17282d')
d = ImageDraw.Draw(im)
def label(x,y,s,size,bold=False,color='#f3f2e9'):
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',size)
    d.text((x,y),s,font=font,fill=color,anchor='lt')
label(62,57,'LOCAL AGENT EVALUATION    /    FUNCTIONGEMMA 270M',25,True,'#9dd1c0')
label(60,135,'Should the agent call a tool?',62,True)
label(62,241,'12 action requests',34,True)
label(62,292,'Correct tool and argument',27)
label(62,406,'12 related questions',34,True)
label(62,458,'Unwanted tool calls',27)
for y,n,color in zip([276,441],score,['#90d6bf','#ffad85']):
    for i in range(12):
        x=525+i*41
        d.rounded_rectangle((x,y,x+31,y+41),radius=4,fill=color if i<n else '#40565b')
    label(1033,y+4,f'{n}/12',36,True)
d.line((62,566,1135,566), fill='#52696a',width=2)
label(62,613,'Explicit rule to skip calls on questions: %d/12 still proposed one.' % explicit[1] + '',30)
label(62,684,'Handwritten prompt pairs  /  four numbers per pair  /  proposals only',26,False,'#ace0ce')
im.save(root/'chart.png')
print(score)
