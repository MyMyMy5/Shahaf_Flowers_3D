"""Restore MCP helper namespaces after reopening the saved scene; no rebuild."""
import bpy
from pathlib import Path

HERE=Path(__file__).resolve().parent
builder={'__file__':str(HERE/'build_scene.py'),'__name__':'shahaf_helpers'}
exec(compile((HERE/'build_scene.py').read_text(encoding='utf-8'),builder['__file__'],'exec'),builder)
builder['MATS']={m.name.removeprefix('SF3D_'):m for m in bpy.data.materials if m.name.startswith('SF3D_')}
bpy.app.driver_namespace['SF3D_BUILD']=builder
audit={'__file__':str(HERE/'audit_scene.py'),'__name__':'shahaf_audit'}
exec(compile((HERE/'audit_scene.py').read_text(encoding='utf-8'),audit['__file__'],'exec'),audit)
bpy.app.driver_namespace['SF3D_AUDIT']=audit
print('Restored authoring helpers without changing scene objects.')
