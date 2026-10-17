import bpy,bmesh,math,os,json,random
from mathutils import Vector,Matrix
from math import sin,cos,pi
D=os.environ.get('ASSEMBLY_WORKDIR','D:/OpenClaw/assembly-sol-op-20261017');O=os.environ.get('ASSEMBLY_OUTPUT',D+'/delivery');os.makedirs(O+'/textures',exist_ok=True);os.makedirs(O+'/captures',exist_ok=True)
random.seed(17)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.bake_type='NORMAL';sc.render.bake.margin=12

def select(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def crop(o,pred):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not pred(v.co)],context='VERTS');bm.to_mesh(o.data);bm.free();o.data.update()

def load(name):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=D+'/hunyuan-'+name+'.glb');o=next(o for o in bpy.data.objects if o not in before and o.type=='MESH');select(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);o.data.materials.clear();return o

def image(n,size,color=(.5,.5,.5,1)):
 im=bpy.data.images.new(n,width=size,height=size,alpha=False);im.generated_color=color;return im

def bake_section(kind,pred,transform,target):
 high=load(kind);crop(high,pred)
 bm=bmesh.new();bm.from_mesh(high.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(high.data);bm.free()
 for v in high.data.vertices:v.co=transform(v.co)
 # Remove isolated scraps by area-connected component where possible.
 high.name=kind+'_source_extracted';high.data.materials.clear();m=bpy.data.materials.new(kind+'_source');m.use_nodes=True;high.data.materials.append(m)
 low=high.copy();low.data=high.data.copy();bpy.context.collection.objects.link(low);low.name=kind+'_budgeted';select(low)
 if kind=='segment2':
  # Closed longitudinal/radial retopology sampled directly from the extracted source.
  high.data.update();bpy.context.view_layer.update();vs=[];fs=[];N=36;K=12
  for j in range(K+1):
   x=-.36+.66*j/K
   for i in range(N):
    a=2*pi*i/N;rad=Vector((0,cos(a),sin(a)));hit,loc,n,idx=high.ray_cast(Vector((x,0,0))+rad*1.5,-rad)
    r=max(.40,min(.57,Vector((0,loc.y,loc.z)).length)) if hit else .465
    vs.append((x,r*cos(a),r*sin(a)))
  for j in range(K):
   for i in range(N):a=j*N+i;b=j*N+(i+1)%N;c=(j+1)*N+(i+1)%N;d=(j+1)*N+i;fs.append((a,b,c,d))
  vs.extend([(-.36,0,0),(.30,0,0)]);a=len(vs)-2;b=len(vs)-1
  for i in range(N):fs.extend([(a,(i+1)%N,i),(b,K*N+i,K*N+(i+1)%N)])
  me=bpy.data.meshes.new('Source sampled closed segment');me.from_pydata(vs,[],fs);me.update();low.data=me
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 else:
  mod=low.modifiers.new('Manifold reconstruction','REMESH');mod.mode='SMOOTH';mod.octree_depth=7 if kind=='segment2' else 8;mod.scale=.9;mod.use_remove_disconnected=True;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name)
  bm=bmesh.new();bm.from_mesh(low.data);unseen=set(bm.verts);components=[]
  while unseen:
   seed=unseen.pop();group={seed};stack=[seed]
   while stack:
    u=stack.pop()
    for e in u.link_edges:
     v=e.other_vert(u)
     if v in unseen:unseen.remove(v);group.add(v);stack.append(v)
   components.append(group)
  if components:
   keep=max(components,key=len);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in keep],context='VERTS')
  bm.to_mesh(low.data);bm.free()
 mod=low.modifiers.new('pretri','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=low.modifiers.new('budget collapse','DECIMATE');mod.ratio=min(1,target/len(low.data.polygons));bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=low.modifiers.new('triangulate','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in low.data.polygons:p.use_smooth=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
 mat=bpy.data.materials.new(kind+'_Gunmetal');mat.use_nodes=True;low.data.materials.clear();low.data.materials.append(mat);nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=.82;bs.inputs['Roughness'].default_value=.43
 size=1024 if kind=='head' else 512
 normal=image(kind+'_normal',size,(.5,.5,1,1));normal.colorspace_settings.name='Non-Color';tex=nodes.new('ShaderNodeTexImage');tex.image=normal;nodes.active=tex
 select(low);high.select_set(True);sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.075;sc.render.bake.max_ray_distance=.15
 print('BAKE',kind,len(low.data.polygons),flush=True);bpy.ops.object.bake(type='NORMAL');normal.filepath_raw=O+'/textures/'+kind+'_normal.png';normal.file_format='PNG';normal.save()
 ao=image(kind+'_ao',size,(1,1,1,1));ao.colorspace_settings.name='Non-Color';tex.image=ao;nodes.active=tex;bpy.ops.object.bake(type='AO');ao.filepath_raw=O+'/textures/'+kind+'_ao.png';ao.save()
 bpy.data.objects.remove(high,do_unlink=True);select(low)
 # Deterministic procedural worn PBR atlas, AO only in packed R, not albedo.
 import numpy as np
 nr=np.array(normal.pixels[:],dtype=np.float32).reshape(size,size,4);invalid=(nr[:,:,2]<.35);nr[invalid]=(.5,.5,1,1);normal.pixels.foreach_set(nr.ravel());normal.save()
 a=np.array(ao.pixels[:],dtype=np.float32).reshape(size,size,4)[:,:,0];rng=np.random.default_rng(51);yy,xx=np.mgrid[:size,:size];grain=rng.random((size,size));scr=((np.sin(xx*.31+np.sin(yy*.015)*30)> .992)&(grain>.55));macro=(np.sin(xx*.027)*np.sin(yy*.021)+1)*.5
 edge=np.clip((a-.65)*2,0,1);value=.22+.07*macro+.025*grain+scr*.12+edge*.025
 def save_arr(name,arr,noncolor=False):
  im=image(name,size);im.colorspace_settings.name='Non-Color' if noncolor else 'sRGB';im.pixels.foreach_set(arr.astype(np.float32).ravel());im.filepath_raw=O+'/textures/'+name+'.png';im.file_format='PNG';im.save();return im
 color=np.ones((size,size,4),dtype=np.float32);color[:,:,0]=value*.94;color[:,:,1]=value*.99;color[:,:,2]=value*1.04;base=save_arr(kind+'_basecolor',color)
 orm=np.ones_like(color);orm[:,:,0]=a;orm[:,:,1]=.38+.18*grain+.1*(1-a);orm[:,:,2]=.83-.18*(1-a);packed=save_arr(kind+'_ORM',orm,True)
 tex.image=normal;nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.65;links.new(tex.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 t=nodes.new('ShaderNodeTexImage');t.image=base;links.new(t.outputs['Color'],bs.inputs['Base Color']);t=nodes.new('ShaderNodeTexImage');t.image=packed;sep=nodes.new('ShaderNodeSeparateColor');links.new(t.outputs['Color'],sep.inputs['Color']);links.new(sep.outputs['Green'],bs.inputs['Roughness']);links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 group=bpy.data.node_groups.get('glTF Material Output')
 if not group:
  group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree');group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
 gn=nodes.new('ShaderNodeGroup');gn.node_tree=group;links.new(sep.outputs['Red'],gn.inputs['Occlusion'])
 print('SECTION_READY',kind,len(low.data.polygons),flush=True);return low

# Source coordinates are Blender Z-up; head rear cut before first neck plate.
head=bake_section('head',lambda v:v.x<-.17 and v.z>.12,lambda v:Vector(((v.x+.17)*1.9,v.y*1.9,(v.z-.48)*1.9)),12000)
# Clean near-side segment; both the far melted form and right-hand appendage are discarded.
body=bake_section('segment2',lambda v:v.y<-.18 and v.x<.17 and v.z>-.53,lambda v:Vector(((v.x+.23)*.84,(v.y+.57)*1.15,v.z*.88)),1080)
# Last two tapered sections and terminal snout: discard the flat triangulated floor.
tail=bake_section('tail',lambda v:v.x>.28 and v.y<.30 and v.z>-.245,lambda v:Vector(((.30-v.y)*2.0,(v.x-.72)*2.0,(v.z+.005)*2.0)),2400)
# Save extracted standalone modules for deterministic assembly iterations.
select(head);body.select_set(True);tail.select_set(True);bpy.ops.wm.save_as_mainfile(filepath=O+'/sections.blend')
print('SECTIONS_DONE',flush=True)
