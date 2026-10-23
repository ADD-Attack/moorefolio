import json, os

UNC = r'\\wsl$\OpenClawGateway\home\openclaw'
cfg_path = UNC + r'\.openclaw\openclaw.json'
print('OCPROBE cfg exists:', os.path.exists(cfg_path))
cfg = json.load(open(cfg_path))

def walk_agents(o, path=''):
    hits = []
    if isinstance(o, dict):
        if 'list' in o and isinstance(o['list'], list) and o['list'] and isinstance(o['list'][0], dict) and 'id' in o['list'][0]:
            hits.append((path, o['list']))
        for k, v in o.items():
            hits += walk_agents(v, path + '/' + k)
    return hits

for path, lst in walk_agents(cfg):
    print('AGENT LIST at', path, 'count', len(lst))
    for a in lst:
        red = {k: a.get(k) for k in ('id', 'name', 'workspace', 'agentDir', 'model', 'thinkingDefault', 'runtime') if k in a}
        print(' AGENT', json.dumps(red))
print('OCPROBE .openclaw dir:', sorted(os.listdir(UNC + r'\.openclaw')))
print('OCPROBE home dir:', sorted(d for d in os.listdir(UNC) if not d.startswith('.')))
