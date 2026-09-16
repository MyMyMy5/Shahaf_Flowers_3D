"""Shahaf's garden: locally authored Blender draft, meters / Z up.

Run stages through Blender MCP. No downloaded/generated meshes or textures.
The source website uses Y up; W() converts its coordinates to Blender.
"""
import bpy
import bmesh
import math
import random
import json
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[1]
FPS = 24
END = 112 * FPS
TAU = math.tau
PREFIX = 'SF3D_'
MATS = {}
CACHE = {}
LIGHTS = []
OPENING_AUDIT = []
COL = None


def W(x, height, depth):
    return (x, -depth, height)


def rgb(value):
    v = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x < .04045 else ((x + .055) / 1.055) ** 2.4 for x in v) + (1,)


def collection(name):
    global COL
    name = PREFIX + name
    COL = bpy.data.collections.get(name)
    if COL is None:
        COL = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(COL)
    return COL


def material(name, color, rough=.5, metal=0, transmission=0, subsurface=0, emission=0, texture=False):
    name = PREFIX + name
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = rgb(color)
    n = m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value = rgb(color)
    n.inputs['Roughness'].default_value = rough
    n.inputs['Metallic'].default_value = metal
    n.inputs['Transmission Weight'].default_value = transmission
    n.inputs['Subsurface Weight'].default_value = subsurface
    n.inputs['Subsurface Scale'].default_value = .035
    n.inputs['Coat Weight'].default_value = .12 if metal else .035
    if emission:
        n.inputs['Emission Color'].default_value = rgb(color)
        n.inputs['Emission Strength'].default_value = emission
    if texture:
        noise = m.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 85 if name.endswith('Linen') else 7
        noise.inputs['Detail'].default_value = 3
        bump = m.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .16
        bump.inputs['Distance'].default_value = .015 if 'Stone' in name else .003
        m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], n.inputs['Normal'])
    MATS[name.removeprefix(PREFIX)] = m
    return m


def mesh_data(name, vertices, faces, smooth=True):
    d = bpy.data.meshes.new(PREFIX + name)
    d.from_pydata(vertices, [], faces)
    d.update()
    for p in d.polygons:
        p.use_smooth = smooth
    return d


def obj_mesh(name, data, loc=(0, 0, 0), scale=(1, 1, 1), mat=None, parent=None):
    o = bpy.data.objects.new(PREFIX + name, data)
    COL.objects.link(o)
    o.location = loc
    o.scale = scale
    if parent:
        o.parent = parent
    if mat:
        if not data.materials:
            data.materials.append(mat)
        o.material_slots[0].link = 'OBJECT'
        o.material_slots[0].material = mat
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(PREFIX + name, None)
    COL.objects.link(o)
    o.location = loc
    o.parent = parent
    o.empty_display_size = .1
    return o


def primitive_mesh(kind):
    if kind in CACHE:
        return CACHE[kind]
    if kind == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=1)
    elif kind == 'ico':
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
    elif kind == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=1)
    else:
        bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    data = o.data
    data.name = PREFIX + 'Unit_' + kind
    for p in data.polygons:
        p.use_smooth = kind in ('sphere', 'ico') or (kind == 'cylinder' and len(p.vertices) == 4)
    bpy.data.objects.remove(o, do_unlink=True)
    CACHE[kind] = data
    return data


def ball(name, loc, scale, mat, parent=None):
    return obj_mesh(name, primitive_mesh('sphere'), loc, scale, mat, parent)


def box(name, loc, dimensions, mat, bevel=.015, parent=None):
    key = ('box', tuple(round(x, 5) for x in dimensions), round(bevel, 5))
    if key not in CACHE:
        bpy.ops.mesh.primitive_cube_add(size=1)
        temp = bpy.context.object
        temp.dimensions = dimensions
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel:
            mod = temp.modifiers.new('Soft crafted edges', 'BEVEL')
            mod.width = bevel
            mod.segments = 3
            bpy.ops.object.modifier_apply(modifier=mod.name)
            for p in temp.data.polygons:
                p.use_smooth = True
            normal = temp.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
            bpy.ops.object.modifier_apply(modifier=normal.name)
        CACHE[key] = temp.data
        bpy.data.objects.remove(temp, do_unlink=True)
    return obj_mesh(name, CACHE[key], loc, mat=mat, parent=parent)


def cylinder(name, loc, radius, depth, mat, parent=None):
    return obj_mesh(name, primitive_mesh('cylinder'), loc, (radius, radius, depth), mat, parent)


def tube(name, a, b, radius, mat, parent=None):
    a, b = Vector(a), Vector(b)
    o = cylinder(name, (a + b) * .5, radius, (b - a).length, mat, parent)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
    return o


def limb(name, a, b, radius, mat, parent=None):
    a, b = Vector(a), Vector(b)
    o = ball(name, (a + b) * .5, (radius, radius, (b - a).length * .5 + radius * .65), mat, parent)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
    return o


def curve(name, points, radius, mat, parent=None, cyclic=False):
    d = bpy.data.curves.new(PREFIX + name, 'CURVE')
    d.dimensions = '3D'
    d.resolution_u = 12
    d.bevel_depth = radius
    d.bevel_resolution = 3
    d.use_fill_caps = True
    s = d.splines.new('POLY')
    s.points.add(len(points) - 1)
    for p, co in zip(s.points, points):
        p.co = (*co, 1)
    s.use_cyclic_u = cyclic
    o = bpy.data.objects.new(PREFIX + name, d)
    COL.objects.link(o)
    d.materials.append(mat)
    o.parent = parent
    return o


def lathe(name, profile, loc, mat, segments=64, parent=None):
    vertices, faces, rings = [], [], []
    for r, z in profile:
        ids = []
        for j in range(1 if abs(r) < 1e-8 else segments):
            a = j / segments * TAU
            ids.append(len(vertices))
            vertices.append((r * math.cos(a), r * math.sin(a), z))
        rings.append(ids)
    for a, b in zip(rings, rings[1:]):
        for j in range(segments):
            k = (j + 1) % segments
            faces.append((a[0], b[k], b[j]) if len(a) == 1 else (a[j], a[k], b[0]) if len(b) == 1 else (a[j], a[k], b[k], b[j]))
    o = obj_mesh(name, mesh_data(name, vertices, faces), loc, mat=mat, parent=parent)
    return o


def light(name, kind, loc, color, energy, size=.2, target=None, parent=None):
    d = bpy.data.lights.new(PREFIX + name, kind)
    d.energy = energy
    d.color = rgb(color)[:3]
    if kind == 'AREA':
        d.shape = 'DISK'
        d.size = size
    elif kind == 'POINT':
        d.shadow_soft_size = size
    o = bpy.data.objects.new(PREFIX + name, d)
    COL.objects.link(o)
    o.location = loc
    o.parent = parent
    if target:
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    LIGHTS.append({'id': o.name, 'type': kind, 'location': list(loc), 'energy': energy, 'color': color, 'size': size})
    return o


def reveal(o, at, duration=2, final_scale=None):
    scale = tuple(final_scale or o.scale)
    o.scale = (.0001, .0001, .0001)
    o.keyframe_insert('scale', frame=max(1, round(at * FPS)))
    o.scale = scale
    o.keyframe_insert('scale', frame=round((at + duration) * FPS))
    o['reveal_seconds'] = at


def arch_mesh(name, width, height, depth, loc, mat=None):
    radius = width * .5
    outline = [(-radius, 0), (radius, 0)]
    outline += [(math.cos(i / 40 * math.pi) * radius, height - radius + math.sin(i / 40 * math.pi) * radius) for i in range(41)]
    n = len(outline)
    verts = [(x, y, z) for y in (-depth / 2, depth / 2) for x, z in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    data = mesh_data(name, verts, faces, False)
    bm = bmesh.new(); bm.from_mesh(data); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(data); bm.free()
    return obj_mesh(name, data, loc, mat=mat)


def arch_trim(name, x, y, z, width, height, radius, mat):
    r = width * .5
    points = [(x-r, y, z), (x-r, y, z+height-r)]
    points += [(x+r*math.cos(a), y, z+height-r+r*math.sin(a)) for a in [math.pi-i/56*math.pi for i in range(57)]]
    points.append((x+r, y, z))
    return curve(name, points, radius, mat)


def stage_base():
    if bpy.context.mode != 'OBJECT' and bpy.context.object:
        bpy.ops.object.mode_set(mode='OBJECT')
    foreign = [o.name for o in bpy.context.scene.objects if not o.name.startswith(PREFIX) and o.name not in ('Cube', 'Camera', 'Light')]
    if foreign:
        raise RuntimeError('Unexpected objects, leaving them intact: ' + repr(foreign))
    for o in list(bpy.context.scene.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name.startswith(PREFIX):
            bpy.data.collections.remove(c)
    CACHE.clear(); LIGHTS.clear(); OPENING_AUDIT.clear()
    s = bpy.context.scene
    s.name = 'Shahaf_Garden_Authoring_v001'
    s.unit_settings.system = 'METRIC'
    s.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    s.cycles.device = 'GPU'
    s.cycles.samples = 128
    s.cycles.adaptive_threshold = .01
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 8
    s.cycles.transparent_max_bounces = 8
    s.render.resolution_x = 1600; s.render.resolution_y = 1000; s.render.resolution_percentage = 100
    s.render.image_settings.file_format = 'PNG'
    s.render.fps = FPS; s.frame_start = 1; s.frame_end = END
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - Medium High Contrast'
    s.view_settings.exposure = .35
    palette = [
        ('Forest', '#102d29', .36, .28), ('Brass', '#b9935f', .27, .82), ('DarkMetal', '#263a35', .32, .72),
        ('Stone', '#b7ad97', .76, 0), ('StoneDark', '#7b8076', .80, 0), ('Linen', '#eee4d3', .76, 0),
        ('Porcelain', '#fff1df', .25, 0), ('Wax', '#f4d5a0', .56, 0), ('Wood', '#483426', .50, 0),
        ('Leaf', '#427345', .50, 0), ('Stem', '#325c38', .58, 0), ('Hair', '#35241d', .54, 0),
        ('HairLight', '#604332', .54, 0), ('Skin', '#dbad8f', .56, 0), ('SkinRose', '#e8ba9e', .56, 0),
        ('Shirt', '#3c6156', .72, 0), ('Trousers', '#273b3c', .78, 0), ('Dress', '#ce8da5', .70, 0),
        ('Seat', '#bd8d91', .72, 0), ('Shoe', '#42332d', .40, 0), ('Eye', '#302018', .20, 0), ('Lips', '#ab6967', .52, 0),
    ]
    for name, color, rough, metal in palette:
        material(name, color, rough, metal, subsurface=.09 if 'Skin' in name else 0, texture=name in ('Stone', 'StoneDark', 'Linen', 'Wood', 'Dress', 'Shirt'))
    for name, color in [('PetalPink','#e7a2ba'),('PetalLilac','#b2a1d6'),('PetalIvory','#f4ddbf'),('PetalRed','#ad1839')]:
        material(name,color,.42,subsurface=.13,texture=True)
    material('Pollen','#f0bd66',.52)
    material('Glass','#e2ede9',.08,transmission=1)
    material('RoofGlass','#a0b8ba',.14,transmission=.82)
    material('Glow','#ffcb83',.32,emission=7)
    material('Spark','#ffdfaf',.40,emission=5)
    material('Heart','#fba5b7',.42,emission=3)
    material('Moon','#d9e7ff',.35,emission=3)
    collection('01_Ground')
    rng = random.Random(5714)
    verts=[(0,0,-.16)]; faces=[]
    rings, sides = 24, 144
    for j in range(1,rings+1):
        r=j/rings*15
        for i in range(sides):
            a=i/sides*TAU; x=math.cos(a)*r; y=math.sin(a)*r
            h=-.14+max(0,(r-4.4)/10)*(.13*math.sin(x*.7)+.10*math.cos(y*.6))
            verts.append((x,y,h))
    for i in range(sides):faces.append((0,1+i,1+(i+1)%sides))
    for j in range(rings-1):
        for i in range(sides):
            a=1+j*sides+i;b=1+j*sides+(i+1)%sides;faces.append((a,a+sides,b+sides,b))
    groundmat=material('Moss','#273c2b',.95,texture=True)
    ground=obj_mesh('Garden_terrain',mesh_data('Terrain',verts,faces),mat=groundmat)
    cylinder('Terrace_foundation',(0,1.2,-.05),4.1,.45,MATS['StoneDark'])
    cylinder('Terrace_stone',(0,1.2,.185),4.08,.025,MATS['Stone'])
    for i in range(16):
        for j in range(16):
            x=-3.82+i*.50;y=-2.60+j*.50
            if math.hypot(x,y-1.2)<3.82:
                box(f'Terrace_tile_{i:02}_{j:02}',(x,y,.218),(.482,.482,.05),MATS['Stone'] if (i+j)%4 else MATS['StoneDark'],.012)
    for row in range(39):
        z=11.8-row*.35
        if z<3.05:continue
        center=math.sin(z*.27)*.45
        for side in (-1,1):
            x=center+side*.39
            bpy.context.view_layer.update()
            hit,point,normal,index=ground.ray_cast(Vector((x,-z,10)),Vector((0,0,-1)))
            o=box(f'Path_stone_{row:02}_{side}',(x,-z,point.z+.056 if hit else ground_z(x,-z)+.056),(.65,.29,.12),MATS['StoneDark'] if row%3 else MATS['Stone'],.048)
            yaw=.10*math.sin(z*.27)+rng.uniform(-.045,.045)
            o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(normal if hit else Vector((0,0,1))) @ Quaternion((0,0,1),yaw)
    for i in range(3):
        top=.060+i*.055;base=-.14
        box(f'Entrance_step_{i}',(0,-3.30+i*.23,(top+base)*.5),(2.38-i*.14,.67,top-base),MATS['Stone'],.024)
    return {'stage':'base','objects':len(s.objects),'gpu':'OPTIX','duration_seconds':112}


def stage_architecture():
    collection('02_Conservatory')
    forest, brass, metal = MATS['Forest'],MATS['Brass'],MATS['DarkMetal']
    wall=arch_mesh('Facade_structure',6.8,5.1,.28,(0,4.2,.22),forest)
    openings=[('door_center',0,.24,1.72,3.25),('window_left',-2.2,.72,1.62,2.64),('window_right',2.2,.72,1.62,2.64)]
    for name,x,z,w,h in openings:
        cutter=arch_mesh('Cut_'+name,w,h,.85,(x,4.2,z))
        bpy.context.view_layer.objects.active=wall;wall.select_set(True)
        mod=wall.modifiers.new('Opening_'+name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter,do_unlink=True)
        arch_trim(name+'_brass_reveal',x,4.025,z,w+.075,h+.045,.045,brass)
        if name.startswith('window'):
            arch_mesh(name+'_glass',w-.05,h-.035,.015,(x,4.12,z+.02),MATS['Glass'])
            box(name+'_sill',(x,3.97,z),(w+.20,.34,.105),brass,.015)
            tube(name+'_mullion',(x,4.02,z+.07),(x,4.02,z+h-.08),.022,metal)
            for zz in [z+.8,z+1.65]:tube(name+'_crossbar',(x-w*.5,4.01,zz),(x+w*.5,4.01,zz),.021,metal)
        else:
            box('Door_threshold',(0,4.13,.26),(1.86,.53,.075),MATS['Stone'],.016)
        wall['opening_'+name]=True
        bpy.context.view_layer.update()
        hit=wall.ray_cast(Vector((x,3.7,z+h*.4))-wall.location,Vector((0,1,0)),distance=1.0)[0]
        OPENING_AUDIT.append({'id':name,'width':w,'height':h,'boolean_applied':True,'center_ray_clear':not hit})
    wall['role']='structural facade with three real apertures'
    arch_mesh('Rear_structure',6.8,5.1,.22,(0,5.8,.22),forest)
    for side in (-1,1):box('Service_nook_side_'+str(side),(side*3.37,5.0,1.10),(.18,1.75,1.84),forest,.02)
    box('Service_nook_floor',(0,4.9,.17),(6.72,1.92,.15),MATS['StoneDark'],.02)
    for x in (-2.2,2.2):
        for z in (1.02,1.78,2.50):
            box('Oak_display_shelf',(x,5.42,z),(1.66,.52,.075),MATS['Wood'],.025)
            for j in range(4):
                px=x-.58+j*.38
                lathe('Shelf_ceramic',[(0,0),(.09,0),(.11,.05),(.10,.21),(.075,.26),(.065,.25),(.075,.06),(0,.04)],(px,5.33,z+.038),MATS['Porcelain'],32)
    box('Rear_counter',(0,5.16,.75),(1.42,.72,1.04),MATS['Wood'],.045)
    box('Counter_top',(0,5.12,1.31),(1.56,.83,.09),MATS['Stone'],.026)
    roofverts=[];rooffaces=[];nu,nv=80,12
    for j in range(nv+1):
        y=1.72+j/nv*4.22
        for i in range(nu+1):
            a=i/nu*math.pi;roofverts.append((3.4*math.cos(a),y,1.92+3.4*math.sin(a)))
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i;rooffaces.append((a,a+1,a+nu+2,a+nu+1))
    roof=obj_mesh('Barrel_glass_roof',mesh_data('Roof',roofverts,rooffaces),mat=MATS['RoofGlass'])
    solid=roof.modifiers.new('Glass thickness','SOLIDIFY');solid.thickness=.018
    for j,y in enumerate([1.70,2.54,3.38,4.20,5.03,5.88]):
        arch_trim('Canopy_rib_'+str(j),0,y,.22,6.86,5.14,.052,brass)
    for i in range(13):
        a=i/12*math.pi;x=3.435*math.cos(a);z=1.92+3.435*math.sin(a)
        tube('Roof_longitudinal_'+str(i),(x,1.69,z),(x,5.93,z),.022,metal if i%2 else brass)
    for side in (-1,1):
        for y in [1.70,4.2,5.88]:
            box('Canopy_post',(side*3.42,y,1.07),(.13,.13,1.70),metal,.018)
            cylinder('Post_foot',(side*3.42,y,.28),.12,.10,brass)
        for y in [-1.4,.0,1.45]:
            tube('Balustrade_post',(side*3.35,y,.24),(side*3.35,y,1.06),.025,metal)
        curve('Balustrade_top',[(side*(3.35+.14*math.sin(i/24*math.pi)),-1.5+i/24*3.05,1.04) for i in range(25)],.032,brass)
        for j in range(13):tube('Balustrade_spindle',(side*3.35,-1.45+j*.245,.25),(side*3.35,-1.45+j*.245,1.02),.012,metal)
    box('Hanging_sign',(0,1.53,3.88),(1.65,.065,.48),forest,.035)
    for x in (-.65,.65):
        anchor=1.93+math.sqrt(3.43**2-x*x)
        tube('Sign_bracket',(x,1.70,anchor),(x,1.57,anchor),.014,brass)
        tube('Sign_chain',(x,1.57,anchor),(x,1.57,4.12),.011,brass)
    d=bpy.data.curves.new(PREFIX+'Sign_letters','FONT');d.body='just us.';d.align_x='CENTER';d.align_y='CENTER';d.size=.30;d.extrude=.002;d.bevel_depth=.001
    font_path=Path(r'C:\Windows\Fonts\georgiai.ttf')
    if font_path.exists():
        d.font=bpy.data.fonts.load(str(font_path));d.font.name=PREFIX+'Sign_Italic'
        if hasattr(d.font,'pack'):d.font.pack()
    o=bpy.data.objects.new(PREFIX+'Sign_text',d);COL.objects.link(o);o.location=(0,1.49,3.88);o.rotation_euler.x=math.pi/2;d.materials.append(brass)
    return {'stage':'architecture','openings':OPENING_AUDIT,'objects':len(bpy.context.scene.objects)}


def stage_furniture():
    collection('03_Table_for_two')
    deck=.245
    root=empty('Dining_group',(0,-.65,deck))
    root['role']='hero table and conversation focus'
    lathe('Table_pedestal',[(0,0),(.37,0),(.38,.045),(.12,.12),(.068,.24),(.065,.66),(.24,.71),(0,.73)],(0,0,0),MATS['DarkMetal'],64,root)
    cylinder('Table_top',(0,0,.75),.92,.07,MATS['Wood'],root)
    cylinder('Tablecloth_top',(0,0,.793),.925,.012,MATS['Linen'],root)
    verts=[];faces=[];nu,nv=128,10
    for j in range(nv+1):
        v=j/nv
        for i in range(nu):
            a=i/nu*TAU;r=.93+.019*math.sin(a*38)*v*v+.027*v
            verts.append((math.cos(a)*r,math.sin(a)*r,.797-v*(.36+.018*math.sin(a*9))))
    for j in range(nv):
        for i in range(nu):
            k=(i+1)%nu;faces.append((j*nu+i,j*nu+k,(j+1)*nu+k,(j+1)*nu+i))
    o=obj_mesh('Linen_draped_hem',mesh_data('Tablecloth',verts,faces),mat=MATS['Linen'],parent=root)
    solid=o.modifiers.new('Linen thickness','SOLIDIFY');solid.thickness=.003
    for side in (-1,1):
        x=side*.54
        lathe('Gold_charger',[(0,0),(.27,0),(.285,.012),(.26,.028),(.21,.010),(0,.010)],(x,0,.803),MATS['Brass'],64,root)
        lathe('Porcelain_plate',[(0,0),(.21,0),(.245,.018),(.25,.031),(.22,.046),(.18,.016),(0,.016)],(x,0,.815),MATS['Porcelain'],64,root)
        for sy in (-1,1):
            tube('Cutlery_handle',(x-.07,sy*.30,.82),(x+.12,sy*.30,.82),.007,MATS['Brass'],root)
            if sy<0:
                for j in range(4):tube('Fork_tine',(x+.11,sy*.30+(j-1.5)*.009,.82),(x+.19,sy*.30+(j-1.5)*.009,.825),.003,MATS['Brass'],root)
            else:box('Knife_blade',(x+.15,sy*.30,.826),(.13,.022,.007),MATS['Brass'],.003,root)
        lathe('Stemmed_glass',[(0,0),(.083,0),(.086,.01),(.019,.032),(.014,.18),(.055,.22),(.08,.29),(.071,.36),(.065,.36),(.073,.289),(.049,.224),(.009,.19),(0,.185)],(x,-side*.38,.803),MATS['Glass'],56,root)
        o=box('Folded_napkin',(x,.035,.845),(.20,.11,.022),MATS['Dress'],.012,root);o.rotation_euler.z=side*.22
    for y in (-.29,.30):
        cylinder('Candle_brass_holder',(.08,y,.815),.075,.025,MATS['Brass'],root)
        cylinder('Ivory_candle',(.08,y,.904),.048,.15,MATS['Wax'],root)
        ball('Candle_flame',(.08,y,1.016),(.012,.012,.037),MATS['Glow'],root)
        tube('Candle_wick',(.08,y,.976),(.08,y,1.002),.002,MATS['DarkMetal'],root)
        light('Candle_light','POINT',(.08,y,1.027),'#ffad58',6,.07,parent=root)
    lathe('Bud_vase',[(0,0),(.085,0),(.11,.055),(.075,.20),(.032,.25),(.026,.25),(.065,.19),(.10,.055),(0,.012)],(0,0,.802),MATS['Porcelain'],48,root)
    for side in (-1,1):
        c=empty('Chair_'+('Shahaf' if side>0 else 'Neria'),(side*1.35,-.65,deck));c.rotation_euler.z=side*math.pi/2
        cylinder('Chair_seat_frame',(0,0,.45),.35,.055,MATS['Brass'],c)
        ball('Velvet_seat',(0,0,.487),(.335,.32,.045),MATS['Seat'],c)
        for x in (-.25,.25):
            for y in (-.22,.22):tube('Chair_leg',(x*1.12,y*1.12,.003),(x,y,.45),.023,MATS['DarkMetal'],c)
        points=[(-.32,-.27,.47),(-.32,-.27,.90)]+[(math.cos(a)*.32,-.27,.90+math.sin(a)*.32) for a in [math.pi-i/32*math.pi for i in range(33)]]+[(.32,-.27,.47)]
        curve('Chair_arched_back',points,.023,MATS['Brass'],c)
        for x in (-.16,0,.16):tube('Chair_back_spindle',(x,-.27,.51),(x,-.27,1.12),.011,MATS['DarkMetal'],c)
        curve('Chair_back_medallion',[(math.cos(i/40*TAU)*.15,-.28,.94+math.sin(i/40*TAU)*.15) for i in range(40)],.009,MATS['Brass'],c,True)
    return {'stage':'furniture','objects':len(bpy.context.scene.objects)}


def shirt_front_y(x,z):
    return -.025+.135*math.sqrt(max(.001,1-(x/.215)**2-((z-.91)/.29)**2))


def shirt_collar(root):
    for side in (-1,1):
        vertices=[(side*.025,.071,1.180),(side*.115,shirt_front_y(side*.115,1.135)+.003,1.135),(side*.057,shirt_front_y(side*.057,1.070)+.003,1.070)]
        face=(0,1,2) if side>0 else (2,1,0)
        o=obj_mesh('Neria_shirt_collar',mesh_data('Shirt_collar',vertices,[face]),mat=MATS['Linen'],parent=root)
        mod=o.modifiers.new('Collar fabric thickness','SOLIDIFY');mod.thickness=.003


def hair_cap_vertex(angle,polar,female):
    x=.173*math.sin(polar)*math.cos(angle);y=.157*math.sin(polar)*math.sin(angle);z=.225*math.cos(polar)
    if not female:
        top=max(0,min(1,(z-.035)/.13));front=math.exp(-((y-.045)/.115)**2)
        z+=top*(.030*math.exp(-((x+.035)/.11)**2-((y-.065)/.09)**2)+.004*math.sin((x+.15)*70+y*5)*front)
    return (x,y,z)


def stage_characters():
    collection('04_Couple')
    for side,female in [(-1,False),(1,True)]:
        who='Shahaf' if female else 'Neria'
        root=empty(who+'_pose',(side*1.35,-.65,.245));root.rotation_euler.z=side*math.pi/2
        root['role']='stylized adult seated at the shared table'
        skin=MATS['SkinRose' if female else 'Skin'];cloth=MATS['Dress' if female else 'Shirt']
        ball(who+'_torso',(0,-.025,.91),(.215,.135,.29),cloth,root)
        ball(who+'_hip',(0,.05,.59),(.215,.19,.125),cloth if female else MATS['Trousers'],root)
        if female:
            verts=[];faces=[];n=64
            for j in range(8):
                v=j/7;r=.22+.10*v
                for i in range(n):
                    a=i/n*TAU;wave=.012*math.sin(a*14)*v
                    verts.append((math.cos(a)*(r+wave),.12+math.sin(a)*(r+wave)*1.22,.74-v*.30))
            for j in range(7):
                for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
            obj_mesh(who+'_draped_skirt',mesh_data('Dress_skirt',verts,faces),mat=cloth,parent=root)
        else:
            shirt_collar(root)
            for z in (.84,.94,1.04):ball(who+'_shirt_button',(0,shirt_front_y(0,z)+.004,z),(.009,.005,.009),MATS['Brass'],root)
        for sign in (-1,1):
            hip=(sign*.115,.045,.585);knee=(sign*.12,.36,.455);ankle=(sign*.13,.405,.09)
            limb(who+'_thigh',hip,knee,.083,skin if female else MATS['Trousers'],root)
            limb(who+'_lower_leg',knee,ankle,.043 if female else .057,skin if female else MATS['Trousers'],root)
            ball(who+'_shoe',(sign*.13,.45,.05),(.066,.12,.050),MATS['Shoe'],root)
            shoulder=(sign*.195,-.005,1.09);elbow=(sign*.25,.225,.77);wrist=(sign*.19,.51,.81)
            limb(who+'_upper_arm',shoulder,elbow,.057,skin if female else cloth,root)
            ball(who+'_elbow',elbow,(.053,.055,.054),skin if female else cloth,root)
            limb(who+'_forearm',elbow,wrist,.044,skin if female else cloth,root)
            ball(who+'_hand',(sign*.19,.55,.805),(.037,.056,.018),skin,root)
            for finger in range(4):
                x=sign*.19+(finger-1.5)*.014
                limb(who+'_finger',(x,.58,.807),(x,.61+.006*(1-abs(finger-1.5)),.802),.006,skin,root)
        limb(who+'_neck',(0,0,1.12),(0,0,1.29),.069,skin,root)
        head=empty(who+'_head',(0,-.01,1.41),root);head.rotation_euler.z=side*.16;head.rotation_euler.y=-side*.055
        ball(who+'_face',(0,0,0),(.154,.137,.208),skin,head)
        ball(who+'_chin',(0,.007,-.127),(.097,.093,.075),skin,head)
        for sign in (-1,1):
            ball(who+'_ear',(sign*.15,0,-.017),(.027,.043,.047),skin,head)
            ball(who+'_eye_white',(sign*.062,.123,.027),(.027,.014,.017),MATS['Porcelain'],head)
            ball(who+'_iris',(sign*.062,.136,.026),(.011,.005,.012),MATS['Eye'],head)
            ball(who+'_eye_glint',(sign*.057,.141,.031),(.003,.002,.003),MATS['Porcelain'],head)
            curve(who+'_eyebrow',[(sign*(.035+i*.014),.13,.068+.009*math.sin(i/4*math.pi)) for i in range(5)],.008,MATS['Hair'],head)
        ball(who+'_nose',(0,.138,-.013),(.023,.037,.032),skin,head)
        curve(who+'_smile',[(-.038+i*.0095,.124,-.077-.007*math.sin(i/8*math.pi)) for i in range(9)],.0045,MATS['Lips'],head)
        verts=[];faces=[];nu,nv=48,18
        for j in range(nv+1):
            for i in range(nu):
                a=i/nu*TAU;t=j/nv*(1.58-.31*math.sin(a))
                verts.append(hair_cap_vertex(a,t,female))
        for j in range(nv):
            for i in range(nu):faces.append((j*nu+i,j*nu+(i+1)%nu,(j+1)*nu+(i+1)%nu,(j+1)*nu+i))
        obj_mesh(who+'_hair_cap',mesh_data(who+'_hair',verts,faces),mat=MATS['Hair'],parent=head)
        if female:
            for j in range(11):
                a=math.pi+j/10*math.pi
                points=[]
                for k in range(18):
                    t=k/17
                    points.append((math.cos(a)*(.13+.035*t)+.016*math.sin(t*9+j),-.04+math.sin(a)*.085-.025*t,.10-.52*t))
                curve(who+'_wavy_hair',points,.028 if j%2 else .032,MATS['HairLight' if j%4==0 else 'Hair'],head)
            for sign in (-1,1):ball(who+'_earring',(sign*.165,.005,-.076),(.012,.012,.020),MATS['Brass'],head)
        head.rotation_euler.x=.018;head.keyframe_insert('rotation_euler',frame=1)
        for seconds in (32,44,60,74,90,112):
            head.rotation_euler.x=.018+.018*math.sin(seconds*.18+side);head.keyframe_insert('rotation_euler',frame=seconds*FPS)
        reveal(root,31.2+(female*.45),1.6)
    return {'stage':'couple','objects':len(bpy.context.scene.objects)}


def ground_z(x,y):
    r=math.hypot(x,y)
    return -.14+max(0,(r-4.4)/10)*(.13*math.sin(x*.7)+.10*math.cos(y*.6))


def flower_geometry(rose=False,detail=1):
    verts=[];opened=[];faces=[];indices=[]
    def patch(fn,closed,nu,nv,material_index):
        offset=len(verts)
        for j in range(nv+1):
            v=max(.0002,min(.9998,j/nv))
            for i in range(nu+1):
                u=i/nu;verts.append(closed(u,v));opened.append(fn(u,v))
        for j in range(nv):
            for i in range(nu):
                a=offset+j*(nu+1)+i;faces.append((a,a+1,a+nu+2,a+nu+1));indices.append(material_index)
    h=1.8 if rose else 2.65
    stem=lambda u,v:(.05*math.sin(v*4)+.025*math.cos(u*TAU),.025*math.sin(u*TAU),h*v)
    patch(stem,stem,6 if detail==0 else 8,9 if detail==0 else 12,1)
    for j in range(3 if rose else 4):
        base=.40+j*(.36 if rose else .43);side=(-1)**j;length=.48 if rose else .72-j*.06
        leaf=lambda u,v,s=side,b=base,l=length:(s*l*v,.19*math.sin(v*math.pi)*(u*2-1),b+.22*math.sin(v*2.4)+.045*(u*2-1)**2)
        closed=lambda u,v,s=side,b=base,l=length:(s*.03*v,.01*(u*2-1),b+l*.7*v)
        patch(leaf,closed,3 if detail==0 else 5,6 if detail==0 else 8,2)
    rings=[(7,.66,.38,.37),(6,.47,.32,.49),(5,.29,.25,.59),(3,.14,.18,.66)] if rose else [(11,1.03,.30,0),(9,.81,.29,.11),(7,.55,.25,.23)]
    tilt=.16 if rose else .60
    def at_head(x,y,z):
        return (x,-(y*math.cos(tilt)+z*math.sin(tilt)),h-y*math.sin(tilt)+z*math.cos(tilt))
    for ring,(count,length,width,lift) in enumerate(rings):
        for j in range(count):
            angle=j/count*TAU+ring*.73;s,c=math.sin(angle),math.cos(angle)
            def petal(u,v,s=s,c=c,length=length,width=width,lift=lift,ring=ring,angle=angle,count=count):
                q=u*2-1
                if rose:
                    a=angle+q*(TAU/count*.72)
                    radial=.035+length*math.sin(v*math.pi*.60)*(1-.10*q*q)
                    z=lift*v+.10*(1-q*q)*math.sin(v*math.pi*.5)-.06*v*v
                    return at_head(math.sin(a)*radial,math.cos(a)*radial,z)
                w=width*math.sqrt(max(0,1-(v*2-1)**2))*q
                radial=.045+length*v
                z=.06+lift+.13*math.sin(v*math.pi)+.12*q*q*math.sin(v*math.pi)-.13*v*v
                return at_head(s*radial+c*w,c*radial-s*w,z)
            def bud(u,v,s=s,c=c,length=length,width=width):
                r=.07+.14*math.sin(v*math.pi);w=width*.13*math.sin(v*math.pi)*(u*2-1)
                return at_head(s*r+c*w,c*r-s*w,(.76 if rose else length*.85)*v)
            patch(petal,bud,14 if detail==2 else 5 if detail==0 else 8,20 if detail==2 else 8 if detail==0 else 12,0)
    if not rose:
        for j in range(27 if detail==2 else 7 if detail==0 else 17):
            a=j*2.399963;r=.15*math.sqrt(j/(27 if detail==2 else 7 if detail==0 else 17))
            pos=Vector(at_head(math.cos(a)*r,math.sin(a)*r,.35))
            stamen=lambda u,v,p=pos:tuple(p+Vector((.022*math.cos(u*TAU)*math.sin(v*math.pi),.022*math.sin(u*TAU)*math.sin(v*math.pi),.030*math.cos(v*math.pi))))
            patch(stamen,stamen,4 if detail==0 else 8,2 if detail==0 else 6,3)
    return verts,opened,faces,indices


def flower(name,location,scale,mat,start,rose=False,detail=1,rotation=0,animated=True):
    key=('flower_geometry',rose,detail)
    if key not in CACHE:CACHE[key]=flower_geometry(rose,detail)
    closed,opened,faces,indices=CACHE[key]
    data=mesh_data(name,closed if animated else opened,faces)
    for m in (mat,MATS['Stem'],MATS['Leaf'],MATS['Pollen']):data.materials.append(m)
    for p,i in zip(data.polygons,indices):p.material_index=i
    o=obj_mesh(name,data,location,(scale,scale,scale));o.rotation_euler.z=rotation
    if animated:
        o.shape_key_add(name='Bud')
        key=o.shape_key_add(name='Bloom')
        key.data.foreach_set('co',[n for v in opened for n in v])
        key.value=0;key.keyframe_insert('value',frame=max(1,round((start+2.2)*FPS)))
        key.value=1;key.keyframe_insert('value',frame=round((start+5.5)*FPS))
        reveal(o,start,3.3)
    o['role']='path red rose' if rose else 'fantasy garden blossom'
    o['botanical_kind']='rose' if rose else 'peony'
    o['flower_detail']=detail
    o['growth_start_seconds']=start
    return o


def climbing_crown(name,location,scale,mat):
    closed,opened,faces,indices=flower_geometry(False,1)
    selected=[(f,i) for f,i in zip(faces,indices) if i in (0,3)]
    used=sorted({j for f,i in selected for j in f});mapping={j:k for k,j in enumerate(used)}
    vertices=[(opened[j][0],opened[j][1],opened[j][2]-2.65) for j in used]
    data=mesh_data(name,vertices,[tuple(mapping[j] for j in f) for f,i in selected])
    for m in (mat,MATS['Stem'],MATS['Leaf'],MATS['Pollen']):data.materials.append(m)
    for p,(f,i) in zip(data.polygons,selected):p.material_index=i
    o=obj_mesh(name,data,location,(scale,)*3);o['role']='climbing blossom';o['source_anchor']=list(location);o['source_scale']=scale
    mod=o.modifiers.new('Organic petal smoothing','SUBSURF');mod.levels=mod.render_levels=1
    for side in (-1,1):
        verts=[];fs=[]
        for j in range(9):
            v=max(.001,min(.999,j/8))
            for k in range(5):
                u=k/4;verts.append((side*.34*v,.10*math.sin(v*math.pi)*(u*2-1),.11*math.sin(v*math.pi)-.08*v))
        for j in range(8):
            for k in range(4):a=j*5+k;fs.append((a,a+1,a+6,a+5))
        leaf=obj_mesh(name+'_vine_leaf',mesh_data('Climbing_leaf',verts,fs),location,mat=MATS['Leaf']);leaf.rotation_euler.y=side*.5;leaf['source_anchor']=list(location)
    return o


def stage_botanicals():
    collection('05_Garden')
    rng=random.Random(20260915)
    hero=flower('Hero_first_bloom',(-2.6,-6.6,ground_z(-2.6,-6.6)),1.20,MATS['PetalPink'],1.2,detail=2)
    hero['role']='opening hero flower with animated petal shape key'
    positions=[]
    for i in range(84):
        for trial in range(200):
            x=rng.uniform(-12.5,12.5);y=rng.uniform(-11.4,10.8)
            if math.hypot(x,y)>13.7 or math.hypot(x,y-1.2)<4.7:continue
            if y<1.8 and abs(x-math.sin(-y*.27)*.45)<1.60:continue
            if math.hypot(x+2.6,y+6.6)<1.35:continue
            break
        scale=rng.uniform(.43,.81)*(1.0 if y<0 else .88)
        positions.append((x,y,scale))
    positions += [(-5.2,-5.6,1.05),(4.9,-5.5,.97),(-7.3,-3.9,.90),(6.8,-3.8,.94),(-4.8,-9.3,.80),(4.7,-9.4,.83),(-4.7,4.7,.72),(4.7,4.7,.76)]
    for i,(x,y,scale) in enumerate(positions):
        start=10.3+math.hypot(x+2.6,y+6.6)*.16+rng.uniform(0,1.8)
        flower(f'Garden_blossom_{i:03}',(x,y,ground_z(x,y)),scale,MATS[['PetalPink','PetalLilac','PetalIvory'][i%3]],start,rotation=rng.uniform(-.55,.55))
    collection('06_Rose_walkway')
    for i in range(12):
        for side in (-1,1):
            depth=3.45+i*.70+side*.08;y=-depth;x=math.sin(depth*.27)*.45+side*(1.04+.025*math.sin(i*1.7))
            o=flower(f'Path_rose_{i:02}_{"L" if side<0 else "R"}',(x,y,ground_z(x,y)),.30+rng.uniform(0,.035),MATS['PetalRed'],42+i*.20+(side>0)*.10,rose=True,rotation=side*.16)
            o['border_side']='left' if side<0 else 'right'
    collection('07_Climbing_flowers')
    for side in (-1,1):
        vine=[(side*(3.43-.10*math.sin(t*20)),1.58+.07*math.sin(t*15),.25+t*1.75) for t in [j/45 for j in range(46)]]
        curve('Climbing_stem',vine,.014,MATS['Stem'])
        for j in range(8):
            z=.40+j*.20;x=side*(3.43-.07*math.sin(j*.7))
            climbing_crown('Pillar_floret',(x,1.56,z),.115+rng.random()*.030,MATS['PetalIvory' if j%3 else 'PetalPink'])
            tube('Pillar_vine_attachment',(x,1.56,z),(side*3.42,1.65,z),.014,MATS['Stem'])
    for j in range(25):
        a=.10+j/24*(math.pi-.2);x=3.45*math.cos(a);z=1.93+3.45*math.sin(a)
        climbing_crown('Arch_floret',(x,1.55,z),.115+rng.random()*.035,MATS['PetalPink' if j%3 else 'PetalIvory'])
        if j%4==0:tube('Arch_vine_attachment',(x,1.55,z),(x,1.70,z),.013,MATS['Stem'])
    curve('Arch_vine',[(3.45*math.cos(a),1.55,1.93+3.45*math.sin(a)) for a in [i/90*math.pi for i in range(91)]],.018,MATS['Stem'])
    collection('03_Table_for_two')
    for j in range(3):
        o=flower('Vase_rose',((j-1)*.055,-.65+(j%2)*.045,1.25),.095,MATS['PetalPink' if j%2 else 'PetalIvory'],29,rose=True,animated=False)
        o['role']='table vase rose'
    collection('08_Grasses')
    verts=[];faces=[]
    for i in range(4800):
        a=rng.random()*TAU;r=math.sqrt(rng.random())*14.6;x=math.cos(a)*r;y=math.sin(a)*r
        if math.hypot(x,y-1.2)<4.18 or (y<1.8 and abs(x-math.sin(-y*.27)*.45)<.87):continue
        z=ground_z(x,y);h=rng.uniform(.08,.28);w=rng.uniform(.007,.017);lean=rng.uniform(-.08,.08);base=len(verts)
        verts.extend([(x-w,y,z),(x+w,y,z),(x+lean+w*.35,y+.025,z+h*.6),(x+lean-w*.35,y+.025,z+h*.6),(x+lean*1.5,y+.045,z+h)])
        faces.extend([(base,base+1,base+2,base+3),(base+3,base+2,base+4)])
    obj_mesh('Meadow_blades',mesh_data('Meadow',verts,faces),mat=MATS['Leaf'])
    return {'stage':'botanicals','garden_flowers':93,'path_roses':24,'objects':len(bpy.context.scene.objects)}


def lantern_fixture(name,loc,scale=1,floating=False):
    root=empty(name,loc);root.scale=(scale,)*3
    mat=MATS['PaperGlow'] if floating else MATS['Glass']
    lathe(name+'_body',[(.105,0),(.125,.08),(.135,.22),(.115,.34),(.109,.34),(.128,.22),(.119,.08),(.099,0),(.105,0)],(0,0,-.17),mat,40,root)
    for z in (-.175,.17):
        curve(name+'_rim',[(.115*math.cos(j/40*TAU),.115*math.sin(j/40*TAU),z) for j in range(40)],.011,MATS['Brass'],root,True)
    if not floating:
        lathe(name+'_cap',[(0,0),(.145,0),(.14,.025),(.035,.09),(0,.09)],(0,0,.175),MATS['DarkMetal'],40,root)
        for a in (0,math.pi/2,math.pi,math.pi*1.5):tube(name+'_cage',(.117*math.cos(a),.117*math.sin(a),-.17),(.117*math.cos(a),.117*math.sin(a),.20),.008,MATS['Brass'],root)
    ball(name+'_flame',(0,0,-.03),(.025,.025,.070),MATS['Glow'],root)
    if not floating:light(name+'_light','POINT',(0,0,-.02),'#ffc482',12*scale*scale,.09,parent=root)
    return root


def stage_atmosphere():
    collection('09_Lighting_and_lanterns')
    material('PaperGlow','#edc99b',.72,transmission=.16,subsurface=.06,emission=.45)
    world=bpy.data.worlds.new(PREFIX+'Midnight_world')
    bpy.context.scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=rgb('#253454')
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.38
    light('Moon_softbox','AREA',(4,-2,15),'#bbcaff',1900,10,(0,1,1))
    light('Portrait_soft_fill','AREA',(0,-8,8),'#ffe0c0',680,7,(0,-.65,1.0))
    light('Garden_blue_rim','AREA',(-8,6,10),'#b2b9ff',1900,8,(0,0,2))
    for x in (-2.1,2.1):light('Interior_warm_glow','AREA',(x,5.25,3.20),'#ffbd73',200,1.5,(x,2.0,1.7))
    light('Table_canopy_fill','AREA',(0,1.0,4.3),'#ffd09b',95,2.0,(0,-.65,1))
    for x in (-2.85,2.85):
        anchor=1.93+math.sqrt(3.43**2-x*x)
        tube('Lantern_bracket',(x,1.70,anchor),(x,1.57,anchor),.016,MATS['Brass'])
        tube('Lantern_suspension',(x,1.57,anchor),(x,1.57,3.012),.012,MATS['Brass'])
        lantern_fixture('Entrance_lantern',(x,1.57,2.70),1.18)
    for x in (-3.35,3.35):
        for y in (-1.45,.65):
            tube('Garden_lamp_post',(x,y,.25),(x,y,1.465),.032,MATS['DarkMetal'])
            lantern_fixture('Garden_lamp',(x,y,1.60),.73)
    for row,y in enumerate((.75,2.70)):
        z=3.40+row*.27
        points=[(-3.38+6.76*j/64,y,z-.48*math.sin(j/64*math.pi)) for j in range(65)]
        curve('String_light_cable',points,.009,MATS['DarkMetal'])
        for j in range(21):
            t=(j+.35)/21;x=-3.38+6.76*t;zz=z-.48*math.sin(t*math.pi)
            tube('Bulb_drop',(x,y,zz),(x,y,zz-.085),.006,MATS['DarkMetal'])
            ball('Warm_string_bulb',(x,y,zz-.115),(.026,.026,.044),MATS['Glow'])
    rng=random.Random(3812)
    for i in range(14):
        x=rng.uniform(-10,10);y=rng.uniform(-1,9);z=rng.uniform(5.5,12.0)
        o=lantern_fixture(f'Floating_paper_lantern_{i:02}',(x,y,z),rng.uniform(.65,1.10),True)
        scale=tuple(o.scale);o.location.z=2.0;o.keyframe_insert('location',frame=84*FPS);o.location=(x+.7*math.sin(i),y,z);o.keyframe_insert('location',frame=END)
        reveal(o,84+(i%4)*.7,5,scale)
    collection('10_Stars_and_glints')
    for i in range(165):
        o=obj_mesh('Distant_star',primitive_mesh('ico'),(rng.uniform(-38,38),rng.uniform(20,38),rng.uniform(8,34)),(rng.uniform(.022,.057),)*3,MATS['Spark'])
        o.visible_shadow=False;o.visible_diffuse=False;o.visible_glossy=False
    for i in range(115):
        x=rng.uniform(-12,12);y=rng.uniform(-10,10);z=rng.uniform(.6,5.0);r=rng.uniform(.006,.018)
        o=obj_mesh('Garden_firefly',primitive_mesh('ico'),(x,y,z),(r,)*3,MATS['Spark'])
        reveal(o,7+rng.random()*6,2)
        o.visible_shadow=False;o.visible_diffuse=False
    coil=empty('Opening_gold_spiral',(-2.6,-6.6,ground_z(-2.6,-6.6)))
    for j in range(105):
        u=j/104;a=u*TAU*2.2;r=.30+.12*math.sin(u*math.pi)
        obj_mesh('Stem_glint',primitive_mesh('ico'),(math.cos(a)*r,math.sin(a)*r,.1+u*3.15),(.012 if j%11 else .022,)*3,MATS['Spark'],coil)
    coil.scale=(.001,)*3;coil.keyframe_insert('scale',frame=1.5*FPS);coil.scale=(1,)*3;coil.keyframe_insert('scale',frame=2.8*FPS);coil.keyframe_insert('scale',frame=7*FPS);coil.scale=(.001,)*3;coil.keyframe_insert('scale',frame=11*FPS)
    coil.rotation_euler.z=0;coil.keyframe_insert('rotation_euler',frame=FPS);coil.rotation_euler.z=TAU;coil.keyframe_insert('rotation_euler',frame=11*FPS)
    heart=empty('Constellation_heart')
    for i in range(164):
        a=i/164*TAU;x=math.sin(a)**3*2.0;z=8.1+(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))*.135
        o=obj_mesh('Heart_star',primitive_mesh('ico'),(x,1.6,z),(.018 if i%5 else .025,)*3,MATS['Heart'],heart)
        o.visible_shadow=False;o.visible_diffuse=False
        o.scale=(.0001,)*3;o.keyframe_insert('scale',frame=(96+i/164*8)*FPS);o.scale=(.018 if i%5 else .025,)*3;o.keyframe_insert('scale',frame=(96.4+i/164*8)*FPS)
    # A thin crescent, oriented to the main production view, rather than a flat full disk.
    moonverts=[]
    for i in range(81):
        a=math.radians(55)+i/80*math.radians(250);moonverts.append((math.cos(a)*1.30,0,math.sin(a)*1.30))
    for i in range(61):
        a=math.radians(260)-i/60*math.radians(160);moonverts.append((.50+math.cos(a)*1.13,0,.20+math.sin(a)*1.13))
    moon=obj_mesh('Crescent_moon',mesh_data('Moon',moonverts,[tuple(range(len(moonverts)))],False),(11,20,19),mat=MATS['Moon'])
    moon.visible_shadow=False;moon.visible_diffuse=False;moon.visible_glossy=False
    collection('11_Butterflies')
    material('WingGold','#f3d193',.43,transmission=.10,subsurface=.08)
    material('WingLilac','#c9add9',.46,transmission=.10,subsurface=.08)
    for i in range(6):
        root=empty(f'Butterfly_{i:02}')
        root.scale=(.52 if i<3 else .39,)*3
        ball('Butterfly_body',(0,0,0),(.017,.025,.145),MATS['DarkMetal'],root)
        for side in (-1,1):
            hinge=empty('Butterfly_wing_hinge',parent=root)
            for lower in (False,True):
                verts=[];faces=[];nu,nv=8,12
                for j in range(nv+1):
                    v=max(.0001,min(.9999,j/nv))
                    for k in range(nu+1):
                        u=k/nu;length=.27 if lower else .36;width=.10 if lower else .145
                        verts.append((side*(.015+length*v),.022*math.sin(u*math.pi)*math.sin(v*math.pi),(-.105 if lower else .055)+(u*2-1)*width*math.sin(v*math.pi)+(.02 if lower else .08)*math.sin(v*math.pi)))
                for j in range(nv):
                    for k in range(nu):a=j*(nu+1)+k;faces.append((a,a+1,a+nu+2,a+nu+1))
                obj_mesh('Butterfly_wing',mesh_data('Wing',verts,faces),mat=MATS['WingGold' if i%2==0 else 'WingLilac'],parent=hinge)
            f=hinge.driver_add('rotation_euler',2);f.driver.expression=f'{side}*sin(frame*0.44+{i})*0.78'
            curve('Butterfly_antenna',[(side*.008,0,.12),(side*.032,-.005,.21),(side*.064,0,.25)],.004,MATS['Brass'],root)
        for sec in range(0,113,2):
            phase=i*TAU/3+(TAU/6 if i>=3 else 0);t=sec*(.48 if i<3 else .64)+phase;g=max(0,min(1,(sec-16)/11));g=g*g*(3-2*g)
            x=(-2.6+math.sin(t)*1.5)*(1-g)+math.sin(t*.6)*5.5*g;y=(-6.6+math.cos(t)*.9)*(1-g)-math.cos(t)*2.9*g;z=3.05+math.sin(t*1.2)*.45
            root.location=(x,y,z);root.keyframe_insert('location',frame=max(1,sec*FPS));root.rotation_euler.y=.12*math.sin(t);root.keyframe_insert('rotation_euler',frame=max(1,sec*FPS))
        scale=tuple(root.scale);reveal(root,7 if i<3 else 2.2+(i-3)*.35,2,scale)
        if i>=3:root.scale=scale;root.keyframe_insert('scale',frame=10.5*FPS);root.scale=(.0001,)*3;root.keyframe_insert('scale',frame=13.5*FPS)
    return {'stage':'lighting','lights':len([o for o in bpy.context.scene.objects if o.type=='LIGHT']),'objects':len(bpy.context.scene.objects)}


CAMERA_KEYS=[
    (0,[-2.6,2.8,13.9],[-2.6,2.42,6.6]),(4,[-2.2,2.95,13.9],[-2.6,2.42,6.6]),
    (10,[.4,3.9,15.0],[-2.6,2.4,6.6]),(15,[6.9,7.3,18.2],[-.7,1.6,1.8]),
    (21,[-6.6,5.9,17.0],[0,1.7,.6]),(27,[-3.4,4.8,12.8],[0,2.7,-1]),
    (33,[1.9,4.4,11.8],[0,2.6,-1]),(40,[-.3,3.65,9.4],[0,2.55,-.6]),
    (44,[-1.4,4.2,11.4],[0,2.75,-.8]),(51,[5.7,6.5,16.2],[0,3.25,-.8]),
    (60,[2.2,5.1,14.7],[0,2.9,-1]),(72,[.8,5.5,15.5],[0,2.9,-1]),
    (83,[.2,5.6,16.2],[0,3,-.8]),(94,[5.7,6.5,16.2],[0,3.25,-.8]),
    (100,[7.5,6.9,17.3],[-2.8,3.45,-.8]),(115,[7.5,6.9,17.3],[-2.8,3.45,-.8])]


def catmull(a,b,c,d,t):
    return [.5*((2*b[i])+(-a[i]+c[i])*t+(2*a[i]-5*b[i]+4*c[i]-d[i])*t*t+(-a[i]+3*b[i]-3*c[i]+d[i])*t*t*t) for i in range(3)]


def camera_at(t):
    j=0
    while j<len(CAMERA_KEYS)-2 and t>CAMERA_KEYS[j+1][0]:j+=1
    p1,p2=CAMERA_KEYS[j],CAMERA_KEYS[j+1];p0=CAMERA_KEYS[max(0,j-1)];p3=CAMERA_KEYS[min(len(CAMERA_KEYS)-1,j+2)];u=max(0,min(1,(t-p1[0])/(p2[0]-p1[0])))
    return [W(*catmull(p0[k],p1[k],p2[k],p3[k],u)) for k in (1,2)]


def stage_camera_and_save():
    collection('12_Cameras')
    s=bpy.context.scene
    d=bpy.data.cameras.new(PREFIX+'Cinematic_lens');cam=bpy.data.objects.new(PREFIX+'Production_camera',d);COL.objects.link(cam);s.camera=cam
    d.sensor_fit='VERTICAL';d.sensor_height=24;d.lens=24/(2*math.tan(math.radians(42)*.5));d.clip_end=200
    d.dof.use_dof=True;d.dof.aperture_fstop=7.1
    cam.rotation_mode='QUATERNION'
    for frame in range(1,END+1,6):
        eye,target=camera_at((frame-1)/FPS);cam.location=eye;cam.rotation_quaternion=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y');d.dof.focus_distance=(Vector(target)-Vector(eye)).length
        cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_quaternion',frame=frame);d.keyframe_insert('dof.focus_distance',frame=frame)
    eye,target=camera_at(112);cam.location=eye;cam.rotation_quaternion=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y');cam.keyframe_insert('location',frame=END);cam.keyframe_insert('rotation_quaternion',frame=END)
    for seconds,label in [(0,'01 - A little love letter'),(11,'02 - Someone likes flowers'),(22,'03 - A place for us'),(32,'04 - You and me'),(45,'05 - Choosing each other'),(69,'06 - The life we will build'),(100,'07 - Always my love')]:s.timeline_markers.new(label,frame=max(1,seconds*FPS))
    # Keep the first flower reveal uncluttered; architecture rises into the garden later.
    c=bpy.data.collections.get(PREFIX+'02_Conservatory');collection('02_Conservatory');root=empty('Conservatory_reveal');bpy.context.view_layer.update()
    for o in list(c.objects):
        if o!=root and o.parent is None:
            matrix=o.matrix_world.copy();o.parent=root;o.matrix_world=matrix
    reveal(root,22,6)
    c=bpy.data.collections.get(PREFIX+'03_Table_for_two')
    for o in c.objects:
        if o.parent is None:reveal(o,29,2)
    group=bpy.data.node_groups.new(PREFIX+'Cinematic_compositor','CompositorNodeTree');group.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    layers=group.nodes.new('CompositorNodeRLayers');layers.scene=s
    glow=group.nodes.new('CompositorNodeGlare');glow.inputs['Type'].default_value='Fog Glow';glow.inputs['Quality'].default_value='High';glow.inputs['Threshold'].default_value=1.3;glow.inputs['Strength'].default_value=.22;glow.inputs['Size'].default_value=.25
    out=group.nodes.new('NodeGroupOutput');group.links.new(layers.outputs['Image'],glow.inputs['Image']);group.links.new(glow.outputs['Image'],out.inputs['Image']);s.compositing_node_group=group
    s.frame_set(END);bpy.context.view_layer.update()
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL'
    bpy.context.view_layer.objects.active=cam
    for o in bpy.context.selected_objects:o.select_set(False)
    cam.select_set(True)
    script=bpy.data.texts.get('Shahaf_build_scene.py') or bpy.data.texts.new('Shahaf_build_scene.py');script.clear();script.write(Path(__file__).read_text(encoding='utf-8'))
    s['authoring_status']='First Blender draft; not a runtime replacement or approved export'
    s['reference']='https://mymymy5.github.io/Shahaf_Flowers_3D/'
    s['story_duration_seconds']=112
    s.render.filepath=str(ROOT/'renders'/'production_v001.png')
    path=ROOT/'Shahaf_Garden_v001.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path),check_existing=False,compress=True)
    return {'stage':'saved','file':str(path),'objects':len(s.objects),'frame':s.frame_current,'camera':cam.name,'render_engine':s.render.engine}


def stage_refine():
    # Subdivision rounds the sampled petal rims while preserving the bloom keys.
    flowers=[]
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and o.get('role') in ('path red rose','table vase rose','fantasy garden blossom','opening hero flower with animated petal shape key'):
            mod=o.modifiers.get('Organic petal smoothing') or o.modifiers.new('Organic petal smoothing','SUBSURF')
            mod.levels=1;mod.render_levels=1
            flowers.append(o)
    window=material('WindowGlass','#dae5df',.18,transmission=.94)
    plaster=material('InteriorPlaster','#ae977b',.83,texture=True)
    for o in bpy.context.scene.objects:
        if o.name.startswith(PREFIX+'window_') and o.name.endswith('_glass'):
            o.material_slots[0].material=window
        if o.name==PREFIX+'Rear_structure':o.material_slots[0].material=plaster
    collection('09_Lighting_and_lanterns')
    light('Interior_back_wall_fill','AREA',(0,4.95,4.35),'#ffd3a0',110,2.5,(0,5.8,1.8))
    for o in bpy.context.scene.objects:
        if o.type=='LIGHT' and o.name.startswith(PREFIX+'Interior_warm_glow'):o.data.energy=100
    collection('10_Stars_and_glints')
    moon=bpy.data.objects.get(PREFIX+'Crescent_moon')
    if moon:
        r=1.30;d=.55;a=math.acos(d/(2*r));verts=[]
        for i in range(101):
            t=a+i/100*(TAU-2*a);verts.append((r*math.cos(t),0,r*math.sin(t)))
        for i in range(81):
            t=math.pi+a-i/80*2*a;verts.append((d+r*math.cos(t),0,r*math.sin(t)))
        moon.data=mesh_data('Moon_crescent',verts,[tuple(range(len(verts)))],False)
        moon.data.materials.append(MATS['Moon'])
        cam=bpy.context.scene.camera;eye=cam.matrix_world.translation;rot=cam.matrix_world.to_quaternion()
        f=rot@Vector((0,0,-1));right=rot@Vector((1,0,0));up=rot@Vector((0,1,0));distance=60
        half=distance*math.tan(math.radians(42)*.5)
        moon.location=eye+f*distance+right*half*1.6*.64+up*half*.59
        moon.rotation_mode='QUATERNION';moon.rotation_quaternion=(eye-moon.location).to_track_quat('-Y','Z')
    collection('13_Atmosphere')
    m=bpy.data.materials.new(PREFIX+'Blue_hour_air');m.use_nodes=True
    nodes=m.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');vol=nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Density'].default_value=.0035;vol.inputs['Color'].default_value=(.58,.67,.84,1);vol.inputs['Anisotropy'].default_value=.25
    m.node_tree.links.new(vol.outputs['Volume'],out.inputs['Volume'])
    box('Air_volume',(0,6,12),(110,110,32),m,0)
    bpy.context.view_layer.update()
    return {'stage':'refined','rounded_flowers':len(flowers),'moon_location':list(moon.location)}


def stage_finish_animation():
    s=bpy.context.scene
    for group_name,root_name,start,duration,selector in [
        ('01_Ground','Terrace_reveal',22,3,lambda o:o.name.startswith((PREFIX+'Terrace_',PREFIX+'Entrance_step_'))),
        ('07_Climbing_flowers','Climbing_flowers_reveal',28,3,lambda o:True),
    ]:
        c=bpy.data.collections.get(PREFIX+group_name);collection(group_name);root=empty(root_name);bpy.context.view_layer.update()
        for o in list(c.objects):
            if o!=root and o.parent is None and selector(o):
                matrix=o.matrix_world.copy();o.parent=root;o.matrix_world=matrix
        reveal(root,start,duration)
    for o in s.objects:
        if o.name.startswith(PREFIX+'Path_stone_'):
            row=int(o.name.split('_')[3]);reveal(o,17+row*.045,.85)
        if o.parent is None and o.name.startswith(tuple(PREFIX+n for n in ('Entrance_lantern','Garden_lamp','Lantern_suspension','Lantern_bracket','String_light_cable','Bulb_drop','Warm_string_bulb'))):
            reveal(o,27,2.5)
        if o.type=='LIGHT' and not o.name.startswith(tuple(PREFIX+n for n in ('Moon_softbox','Portrait_soft_fill','Garden_blue_rim'))):
            energy=o.data.energy;o.data.energy=0;o.data.keyframe_insert('energy',frame=25*FPS);o.data.energy=energy;o.data.keyframe_insert('energy',frame=29*FPS)
    bg=s.world.node_tree.nodes['Background'].inputs['Color']
    moon=bpy.data.objects[PREFIX+'Moon_softbox'].data
    for sec,sky,tint in [(0,'#282137','#dfc4fa'),(10,'#39304c','#f3c8d6'),(23,'#4e3a48','#ffc496'),(38,'#25324b','#d3c5ea'),(50,'#253454','#bbcaff'),(112,'#253454','#bbcaff')]:
        bg.default_value=rgb(sky);bg.keyframe_insert('default_value',frame=max(1,sec*FPS));moon.color=rgb(tint)[:3];moon.keyframe_insert('color',frame=max(1,sec*FPS))
    sound_path=ROOT.parents[1]/'assets'/'song.mp3'
    seq=s.sequence_editor_create()
    strips=seq.strips if hasattr(seq,'strips') else seq.sequences
    track=strips.new_sound('Shahaf soundtrack',str(sound_path),channel=1,frame_start=1)
    track.sound.pack();track.volume=.72;s.render.use_sequencer=False
    s.sync_mode='AUDIO_SYNC'
    story=ROOT.parents[1]/'output'/'relationship-message.md'
    if story.exists():
        text=bpy.data.texts.get('Relationship_message.md') or bpy.data.texts.new('Relationship_message.md');text.clear();text.write(story.read_text(encoding='utf-8'))
    s.frame_set(END);bpy.context.view_layer.update()
    return {'stage':'animation_finished','packed_sound':bool(track.sound.packed_file),'frame_end':END}


def build_all():
    reports=[f() for f in (stage_base,stage_architecture,stage_furniture,stage_characters,stage_botanicals,stage_atmosphere,stage_camera_and_save,stage_refine,stage_finish_animation)]
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Shahaf_Garden_v001.blend'),check_existing=False,compress=True)
    return reports


if __name__=='__main__':
    bpy.app.driver_namespace['SF3D_BUILD']=globals()
    print(json.dumps(build_all()))
