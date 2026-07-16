import json
a=json.load(open('batches/b0270_dialog.json',encoding='utf-8'))['items']
b=json.load(open('translated/b0270_dialog.json',encoding='utf-8'))['items']
bad=[]
for x,y in zip(a,b):
    if x['t'].count('\n')!=y['t'].count('\n') or x['t'].count('<ESC>')!=y['t'].count('<ESC>'):
        bad.append((x['i'], x['t'].count('\n'), y['t'].count('\n'), repr(y['t'][:40])))
print(bad if bad else 'ALL OK')
