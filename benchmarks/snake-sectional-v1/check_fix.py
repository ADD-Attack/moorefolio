"""Fresh-cache Godot 4.7.2 gate for the delivered fix pass.

python3 check_fix.py --capture
GODOT overrides the executable; capture reuses the original neutral fixture.
"""
import argparse, json, os, shutil, struct, subprocess, sys, tempfile
from pathlib import Path

D=Path(__file__).resolve().parent
args=argparse.ArgumentParser()
args.add_argument('--capture',action='store_true')
capture=args.parse_args().capture
env=dict(os.environ,ASSEMBLY_OUTPUT=str(D))
godot=os.environ.get('GODOT','godot')
version=subprocess.check_output([godot,'--version'],text=True).strip()
assert version.startswith('4.7.2.'),version
subprocess.run([sys.executable,str(D/'validate_glb.py')],env=env,check=True)
for name in ['head.glb','snake-sectional.glb']:
    shutil.copy2(D/name,D/'godot'/name)
subprocess.run([sys.executable,str(D/'validate_fix.py')],check=True)

def command(cmd,log,environment=env):
    with (D/'godot'/log).open('w') as out:
        result=subprocess.run(cmd,env=environment,stdout=out,stderr=subprocess.STDOUT,timeout=240)
    text=(D/'godot'/log).read_text()
    assert result.returncode==0,(cmd,result.returncode,text[-4000:])
    assert not any(s in text for s in ['SCRIPT ERROR:','ERROR:','Parse Error:']),text
    print(log+': PASS',flush=True)

with tempfile.TemporaryDirectory(prefix='assembly-fix-godot-') as temporary:
    target=Path(temporary)/'project'
    shutil.copytree(D/'godot',target,ignore=shutil.ignore_patterns('.godot','*.log','selftest-result.json'))
    assert not (target/'.godot').exists()
    command([godot,'--headless','--editor','--path',str(target),'--import','--quit'],'import.log')
    command([godot,'--headless','--path',str(target),'--script','res://selftest.gd'],'selftest.log')
    report=json.loads((target/'selftest-result.json').read_text())
    assert report['pass'] and report['poses_tested']==120 and not report['failures']
    assert report['triangles']==json.loads((D/'counts.json').read_text())['total']
    shutil.copy2(target/'selftest-result.json',D/'godot'/'selftest-result.json')
    if capture:
        cmd=[godot,'--path',str(target),'--rendering-method','gl_compatibility',
             '--audio-driver','Dummy','--resolution','1920x1080','--script','res://capture.gd']
        capture_env=env.copy()
        if not env.get('DISPLAY'):
            cmd=['xvfb-run','-a','-s','-screen 0 1920x1080x24']+cmd
            capture_env['LIBGL_ALWAYS_SOFTWARE']='1'
        command(cmd,'capture.log',capture_env)
        for name in ['godot-full-body.png','godot-head-closeup.png']:
            data=(target/name).read_bytes()
            assert struct.unpack('>II',data[16:24])==(1920,1080)
            shutil.copy2(target/name,D/'captures'/name)
for name in ['full-body.png','head-closeup.png']:
    data=(D/'captures'/name).read_bytes()
    assert struct.unpack('>II',data[16:24])==(1920,1080)
print('FIX_GATE_EVIDENCE_PASS: fresh import; 120/120 poses;',report['triangles'],'triangles; native capture=',capture)
