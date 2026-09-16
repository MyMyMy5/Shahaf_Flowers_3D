"""Add the cinematic lighting cue and floating petals to the authored garden.

Run in the live authoring session after build_scene.py. This adds a named detail
collection; it does not rebuild or replace the existing scene.
"""
import bpy
import math
import random
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def polish():
    ns=bpy.app.driver_namespace['SF3D_BUILD']
    if bpy.data.objects.get('SF3D_Seed_of_light'):
        return {'status':'already_applied'}
    ns['collection']('14_Cinematic_details')
    rng=random.Random(15092026)
    mats=ns['MATS'];fps=24
    seed=ns['ball']('Seed_of_light',(-2.6,-6.6,5.8),(.045,)*3,mats['Spark'])
    for sec,z,scale in [(0,5.8,.001),(.35,5.8,1),(.8,5.15,1),(1.6,.15,1),(1.9,.14,1.5),(2.6,.14,.001)]:
        seed.location.z=z;seed.scale=(.045*scale,)*3
        seed.keyframe_insert('location',frame=max(1,round(sec*fps)));seed.keyframe_insert('scale',frame=max(1,round(sec*fps)))
    seed.visible_shadow=False
    # A few softly curved petals rise from the flower; timing is staggered.
    petalmat=ns['material']('Drifting_rose_petal','#ecb0bd',.39,subsurface=.16)
    verts=[];faces=[];nu,nv=10,14
    for j in range(nv+1):
        v=j/nv
        for i in range(nu+1):
            u=i/nu*2-1;w=math.sin(v*math.pi)**.65
            verts.append((u*w*.095,.23*v,.036*math.sin(v*math.pi)+u*u*.025*w))
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i;faces.append((a,a+1,a+nu+2,a+nu+1))
    data=ns['mesh_data']('Drifting_petal',verts,faces)
    petals=[]
    for i in range(22):
        a=i*2.399963;t0=3.9+rng.random()*2.5;life=4.1+rng.random()*2.0
        o=ns['obj_mesh'](f'Opening_petal_{i:02}',data.copy(),mat=petalmat)
        scale=rng.uniform(.65,1.18);turn=rng.uniform(-1,1)
        for step in range(7):
            u=step/6;t=t0+life*u;radius=.35+u*(.8+rng.random()*.14)
            o.location=(-2.6+math.cos(a+u*.9)*radius,-6.6+math.sin(a+u*.9)*radius,2.7+u*.8+math.sin(u*math.pi)*.28)
            o.rotation_euler=(.4+turn*u*1.2,a+u*.7,u*1.8+turn)
            fade=math.sin(u*math.pi)**.65;o.scale=(max(.001,scale*fade),)*3
            for prop in ('location','rotation_euler','scale'):o.keyframe_insert(prop,frame=round(t*fps))
        o.scale=(.0001,)*3;o.keyframe_insert('scale',frame=1)
        o.visible_shadow=False;petals.append(o)
    # Smaller grains make the gold spiral feel like living light, not a wire.
    dust=[]
    for i in range(64):
        a=rng.random()*math.tau;t0=2+rng.random()*4.6;life=2+rng.random()*2.3
        r=rng.uniform(.17,.85);z=rng.uniform(.2,3.35)
        o=ns['obj_mesh'](f'Opening_dust_{i:02}',ns['primitive_mesh']('ico'),mat=mats['Spark'])
        size=rng.uniform(.003,.010)
        for u,factor in [(0,.001),(.15,1),(.7,.55),(1,.001)]:
            o.location=(-2.6+math.cos(a+u)*r,-6.6+math.sin(a+u)*r,z+u*.65)
            o.scale=(max(.00001,size*factor),)*3
            o.keyframe_insert('location',frame=round((t0+u*life)*fps));o.keyframe_insert('scale',frame=round((t0+u*life)*fps))
        o.scale=(.00001,)*3;o.keyframe_insert('scale',frame=1)
        o.visible_shadow=False;o.visible_diffuse=False;dust.append(o)
    camera=bpy.data.objects['SF3D_Production_camera'].data
    for sec,fstop in [(0,2.8),(10,2.8),(19,5.6),(28,5.6),(35,4.0),(43,4.0),(51,6.3),(112,6.3)]:
        camera.dof.aperture_fstop=fstop;camera.keyframe_insert('dof.aperture_fstop',frame=max(1,round(sec*fps)))
    air=bpy.data.materials.get('SF3D_Blue_hour_air')
    if air:
        density=next(n for n in air.node_tree.nodes if n.type=='PRINCIPLED_VOLUME').inputs['Density']
        for sec,value in [(0,.020),(8,.020),(17,.0045),(32,.0035),(112,.0035)]:
            density.default_value=value;density.keyframe_insert('default_value',frame=max(1,round(sec*fps)))
    s=bpy.context.scene
    glare=next(n for n in s.compositing_node_group.nodes if n.type=='GLARE')
    glare.inputs['Strength'].default_value=.30;glare.inputs['Threshold'].default_value=1.15
    s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=128
    s.render.resolution_x=1600;s.render.resolution_y=1000;s.frame_set(2688)
    report={'stage':'cinematic_polish_1','added_petals':len(petals),'added_dust':len(dust),'opening_fstop':2.8,'opening_volume_density':.020,'intent':'a seed of light, a bloom, then rose petals drifting into the garden'}
    (ROOT/'cinematic-polish.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    text=bpy.data.texts.get('Shahaf_polish_scene.py') or bpy.data.texts.new('Shahaf_polish_scene.py');text.clear();text.write(Path(__file__).read_text(encoding='utf-8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Shahaf_Garden_v001.blend'),check_existing=False,compress=True)
    return report


if __name__=='__main__':
    print(json.dumps(polish()))
