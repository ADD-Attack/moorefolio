"""PNG integrity and non-warped reference/baseline comparison plates (Pillow/numpy)."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageOps,ImageDraw
T=Path(sys.argv[1]);O=T/'material';ref=Image.open(sys.argv[2]).convert('RGB');C=O/'comparisons';C.mkdir(exist_ok=True)
report={}
for view in ['full-body','head-closeup','seg-detail','tail-detail','tail_top-detail']:
 p=O/'captures'/('m4-'+view+'.png');im=Image.open(p).convert('RGB');assert im.size==(1920,1080)
 a=np.array(im);bg=np.median(a[:50,:50],axis=(0,1)).astype(int).tolist();assert max(abs(np.array(bg)-[193,193,191]))<=1
 report[view]={'size':im.size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'background_corner_median':bg}
 before=Image.open(O/'captures'/('m3-'+view+'.png')).convert('RGB')
 # Identical cameras, no warps/retouching. Reference comparison is explicitly not a solved camera match.
 canvas=Image.new('RGB',(1920,580),(35,35,35));draw=ImageDraw.Draw(canvas);draw.text((12,10),'M3 - identical frozen staging',fill='white');draw.text((972,10),'M4 - identical frozen staging',fill='white');canvas.paste(before.resize((960,540)),(0,40));canvas.paste(im.resize((960,540)),(960,40));canvas.save(C/('m3-m4-'+view+'.png'))
 if view in ['full-body','head-closeup','seg-detail','tail-detail']:
  crop={'full-body':(0,0,1920,1280),'head-closeup':(65,20,710,510),'seg-detail':(270,820,820,1150),'tail-detail':(1260,1040,1850,1260)}[view]
  target=ref.crop(crop);canvas=Image.new('RGB',(1920,660),(35,35,35));draw=ImageDraw.Draw(canvas);draw.text((12,10),'REFERENCE crop - not camera-warped',fill='white');draw.text((972,10),'M4 frozen review camera',fill='white');left=ImageOps.contain(target,(960,620));right=ImageOps.contain(im,(960,620));canvas.paste(left,((960-left.width)//2,40+(620-left.height)//2));canvas.paste(right,(960+(960-right.width)//2,40+(620-right.height)//2));canvas.save(C/('reference-m4-'+view+'.png'))
(O/'m4-capture-checks.json').write_text(json.dumps(report,indent=2));print('FIVE_PNGS_DIMENSIONS_BACKGROUND_HASHES_PASS')
