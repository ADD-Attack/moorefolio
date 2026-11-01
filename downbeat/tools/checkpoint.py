"""mark(ticket_dir, stage, **fields): record build progress in <ticket_dir>/state.json.

Stages: composed / rendered / mixed / qa / delivered. Keeps `stage` (latest), `updated`, and a `history`
list of {stage, time, **fields}. Written via temp file + rename so a crash never leaves it half-written.
"""
import datetime
import json
import os


def mark(ticket_dir, stage, **fields):
    p = os.path.join(ticket_dir, 'state.json')
    st = json.load(open(p)) if os.path.exists(p) else {'history': []}
    now = datetime.datetime.now().isoformat(timespec='seconds')
    st.update(stage=stage, updated=now)
    st['history'].append(dict(stage=stage, time=now, **fields))
    tmp = p + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(st, f, indent=1, default=str)
    os.replace(tmp, p)
    return st
