import bpy, sys, os, numpy as np
T=sys.argv[sys.argv.index("--")+1]
for f,(cx,cy) in [("REFERENCE.png",(351,329)),("head-closeup.png",(330,292))]:
    im=bpy.data.images.load(os.path.join(T,"pack",f)); w,h=im.size
    a=(np.array(im.pixels[:],dtype=np.float32).reshape(h,w,im.channels)[::-1,:,:3]*255+.5).astype(int)
    # refine centre = brightest-lum centroid near guess
    sub=a[cy-40:cy+40,cx-40:cx+40].mean(2); ys,xs=np.where(sub>=np.percentile(sub,97)); cx2=int(cx-40+xs.mean()); cy2=int(cy-40+ys.mean())
    yy,xx=np.mgrid[:h,:w]; r=np.hypot(xx-cx2,yy-cy2)
    print(f,"centre",cx2,cy2)
    for r0 in range(0,70,5):
        m=(r>=r0)&(r<r0+5); print(f" r{r0:02d}-{r0+5:02d}", np.median(a[m],0).astype(int).tolist())
print("EYEDONE")
