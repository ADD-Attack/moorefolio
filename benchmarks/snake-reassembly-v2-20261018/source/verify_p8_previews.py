import json,hashlib,struct,zlib
from pathlib import Path
base=json.load(open('fix/captures/fix-p7-render-settings.json'));cur=json.load(open('fix/previews/fix-p8d-render-settings.json'))
keys=['frames','lights','catcher','backdrop','glare','materials'];checks={k:base[k]==cur[k] for k in keys};assert all(checks.values()),checks
r={'staging_matches_p7':checks,'preview_only':True,'samples':cur['samples'],'images':{}}
for p in sorted(Path('fix/previews').glob('fix-p8d-*.png')):
 data=p.read_bytes();pos=8;chunks=[]
 while pos<len(data):
  n=struct.unpack('>I',data[pos:pos+4])[0];typ=data[pos+4:pos+8];d=data[pos+8:pos+8+n];pos+=12+n
  if typ==b'IHDR':w,h,depth,color=struct.unpack('>IIBB',d[:10])
  if typ==b'IDAT':chunks.append(d)
 assert depth==8 and color in (2,6),(depth,color)
 raw=zlib.decompress(b''.join(chunks));corner=list(raw[1:4]);assert (w,h)==(960,540)
 plain=p.name.endswith(('full-body.png','head-closeup.png'))
 if plain:assert max(abs(a-b) for a,b in zip(corner,[193,193,191]))<=1,(p.name,corner)
 r['images'][p.name]={'size':[w,h],'top_left_pixel':corner,'background_sample':plain,'sha256':hashlib.sha256(data).hexdigest()}
assert len(r['images'])==5
Path('fix/p8-preview-checks.json').write_text(json.dumps(r,indent=2));print('Five preview PNGs and frozen staging verified; full/head background sampled')
