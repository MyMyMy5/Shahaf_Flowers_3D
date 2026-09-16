"""Measure consecutive offline frames without changing the saved authoring file."""
import bpy
import time
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
s=bpy.context.scene;s.camera=bpy.data.objects['SF3D_Production_camera']
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=48
s.cycles.use_denoising=True;s.render.use_persistent_data=True
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
s.render.resolution_x=1280;s.render.resolution_y=800;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.use_sequencer=False
folder=root/'renders'/'benchmark';folder.mkdir(exist_ok=True)
records=[]
for frame in (156,157,936,937,2687,2688):
    s.frame_set(frame);s.render.filepath=str(folder/f'{frame:04}.png');start=time.perf_counter()
    bpy.ops.render.render(write_still=True)
    record={'frame':frame,'seconds':round(time.perf_counter()-start,3)};records.append(record)
    (root/'render-benchmark.json').write_text(json.dumps({'engine':'CYCLES','device':'OPTIX','resolution':[1280,800],'samples':48,'frames':records},indent=2),encoding='utf-8')
    print('SHAHAF_FRAME '+json.dumps(record),flush=True)
