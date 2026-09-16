"""Subtle secondary animation for the separate Blender cinematic."""
import bpy
import math
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def drive(obj,path,index,expression):
    f=obj.driver_add(path,index);f.driver.type='SCRIPTED';f.driver.expression=expression


def animate():
    s=bpy.context.scene;counts={'breathing_figures':0,'blinking_eyes':0,'swaying_flowers':0,'drifting_fireflies':0,'floating_lanterns':0}
    for side,name in [(-1,'Neria'),(1,'Shahaf')]:
        head=bpy.data.objects['SF3D_'+name+'_head']
        drive(head,'delta_location',2,f'.006*sin(frame/24*1.45+{side})')
        drive(head,'delta_rotation_euler',2,f'.045*sin(frame/24*.53+{side})')
        drive(head,'delta_rotation_euler',1,f'.025*sin(frame/24*.67+{side*.7})')
        torso=bpy.data.objects['SF3D_'+name+'_torso']
        drive(torso,'delta_scale',2,f'1+.006*sin(frame/24*1.45+{side})')
        counts['breathing_figures']+=1
        for o in head.children:
            if o.name.startswith(tuple('SF3D_'+name+'_'+part for part in ('eye_white','iris','eye_glint'))):
                # Fast eyelid closure with a longer open interval. Geometry is
                # compressed only vertically, so the eyes remain on the face.
                drive(o,'delta_scale',2,f'1-.94*exp(-pow(((frame/24+{2.3 if side==1 else .7})%4.8-2.4)/.065,2))')
                counts['blinking_eyes']+=1
    for index,o in enumerate(s.objects):
        if o.type=='MESH' and o.get('role') in ('path red rose','fantasy garden blossom','opening hero flower with animated petal shape key'):
            phase=(index*.618)%math.tau
            drive(o,'delta_rotation_euler',0,f'.009*sin(frame/24*.78+{phase})')
            drive(o,'delta_rotation_euler',1,f'.007*sin(frame/24*1.03+{phase*1.3})')
            counts['swaying_flowers']+=1
        elif o.name.startswith('SF3D_Garden_firefly'):
            phase=(index*.7548)%math.tau
            drive(o,'delta_location',0,f'.14*sin(frame/24*.6+{phase})')
            drive(o,'delta_location',1,f'.10*cos(frame/24*.47+{phase})')
            drive(o,'delta_location',2,f'.13*sin(frame/24*.71+{phase*.4})')
            counts['drifting_fireflies']+=1
        elif o.type=='EMPTY' and o.name.startswith('SF3D_Floating_paper_lantern_'):
            phase=(index*.318)%math.tau
            drive(o,'delta_location',0,f'.12*sin(frame/24*.43+{phase})')
            drive(o,'delta_rotation_euler',1,f'.055*sin(frame/24*.8+{phase})')
            counts['floating_lanterns']+=1
    s.frame_set(2688);s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=128
    s.render.resolution_x=1600;s.render.resolution_y=1000
    (ROOT/'secondary-animation.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
    t=bpy.data.texts.get('Shahaf_secondary_animation.py') or bpy.data.texts.new('Shahaf_secondary_animation.py');t.clear();t.write(Path(__file__).read_text(encoding='utf-8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Shahaf_Garden_v001.blend'),check_existing=False,compress=True)
    return counts


if __name__=='__main__':
    print(json.dumps(animate()))
