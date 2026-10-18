import bpy,sys,os,numpy as np,json
T=sys.argv[sys.argv.index("--")+1];d=os.path.join(T,"r2","captures");out={}
for f in sorted(os.listdir(d)):
    if not f.endswith(".png"):continue
    im=bpy.data.images.load(os.path.join(d,f));w,h=im.size;a=(np.array(im.pixels[:],np.float32).reshape(h,w,im.channels)[::-1,:,:3]*255+.5).astype(int)
    out[f]=dict(size=[w,h],corners=[np.median(x.reshape(-1,3),0).astype(int).tolist() for x in (a[:40,:40],a[:40,-40:],a[-40:,:40],a[-40:,-40:])])
json.dump(out,open(os.path.join(d,"backdrop-check.json"),"w"),indent=1);print("BG",out)
