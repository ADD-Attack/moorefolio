# usage: hy_send.py <crop.png> <seed> <tag> <outdir>  (runs on Windows python)
import sys,json,shutil,time,urllib.request,glob,os
crop,seed,tag,out=sys.argv[1],int(sys.argv[2]),sys.argv[3],sys.argv[4]
inp=r'D:\Hunyuan3D\ComfyUI\ComfyUI\input'; shutil.copy(crop,os.path.join(inp,tag+'.png'))
g=json.load(open(os.path.join(os.path.dirname(__file__),'graph-template.json')))
p=g['prompt']; p['2']['inputs']['image']=tag+'.png'; p['7']['inputs']['seed']=seed; p['10']['inputs']['filename_prefix']='eden-'+tag
if len(sys.argv)>5: p['9']['inputs']['algorithm']=sys.argv[5]
r=json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8188/prompt',json.dumps(g).encode(),{'Content-Type':'application/json'})))
pid=r['prompt_id']; print('PROMPT-ID',pid,flush=True)
for _ in range(80):
    time.sleep(10)
    h=json.load(urllib.request.urlopen('http://127.0.0.1:8188/history/'+pid)).get(pid)
    if h and h.get('status',{}).get('status_str')=='success': break
    if h and h.get('status',{}).get('status_str')=='error': print('FAILED',json.dumps(h['status'])[:800]); sys.exit(1)
else: print('TIMEOUT'); sys.exit(1)
f=sorted(glob.glob(r'D:\Hunyuan3D\ComfyUI\ComfyUI\output\eden-'+tag+'*.glb'),key=os.path.getmtime)[-1]
shutil.copy(f,os.path.join(out,tag+'.glb')); print('DONE',tag,pid,os.path.getsize(f))
