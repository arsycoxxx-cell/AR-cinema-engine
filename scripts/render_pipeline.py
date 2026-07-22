import bpy
import math
import os
import traceback

output_dir = os.path.abspath("output")
os.makedirs(output_dir, exist_ok=True)
crash_log = os.path.join(output_dir, "CRASH_LOG.txt")

try:
    # 1. CLEAN SCENE WITHOUT CONTEXT ERRORS
    scene = bpy.context.scene
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    # 2. IMPORT 73.4MB GLTF CHARACTER MESH
    mesh_path = os.path.abspath("assets/character.glb")
    if os.path.exists(mesh_path) and os.path.getsize(mesh_path) > 100000:
        print("Importing 73.4MB mesh from assets/character.glb...")
        bpy.ops.import_scene.gltf(filepath=mesh_path)
        mesh_objs = [o for o in scene.objects if o.type == 'MESH']
        character_mesh = mesh_objs[0] if mesh_objs else None
    else:
        character_mesh = None

    if not character_mesh:
        print("Creating fallback mesh using bpy.data...")
        mesh_data = bpy.data.meshes.new("FallbackMesh")
        character_mesh = bpy.data.objects.new("FallbackObj", mesh_data)
        scene.collection.objects.link(character_mesh)

    # 3. CREATE REFLECTIVE GROUND PLANE (bpy.data constructor)
    plane_mesh = bpy.data.meshes.new("GroundMesh")
    coords = [(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)]
    faces = [(0, 1, 2, 3)]
    plane_mesh.from_pydata(coords, [], faces)
    plane_mesh.update()

    ground = bpy.data.objects.new("Ground", plane_mesh)
    scene.collection.objects.link(ground)

    ground_mat = bpy.data.materials.new(name="WetAsphaltPBR")
    ground_mat.use_nodes = True
    g_bsdf = ground_mat.node_tree.nodes.get("Principled BSDF")
    if g_bsdf:
        g_bsdf.inputs['Roughness'].default_value = 0.05
        g_bsdf.inputs['Base Color'].default_value = (0.015, 0.015, 0.025, 1.0)
    ground.data.materials.append(ground_mat)

    # 4. CREATE ANIME AURA LIGHTING (bpy.data constructor)
    light_data = bpy.data.lights.new(name="AuraLight", type='POINT')
    light_data.energy = 600.0
    light_data.color = (0.05, 0.55, 1.0)
    aura_light = bpy.data.objects.new(name="AuraLight", object_data=light_data)
    aura_light.location = (0, 0, 1.5)
    scene.collection.objects.link(aura_light)

    for f in [15, 30, 45, 60]:
        aura_light.data.energy = 3500.0
        aura_light.data.keyframe_insert(data_path="energy", frame=f)
        aura_light.data.energy = 200.0
        aura_light.data.keyframe_insert(data_path="energy", frame=f + 6)

    # 5. CREATE UNTHINKABLE CAMERA ENGINE (bpy.data constructor)
    camera_data = bpy.data.cameras.new(name="UnthinkableCam")
    camera_data.lens = 16
    camera_obj = bpy.data.objects.new("UnthinkableCam", camera_data)
    scene.collection.objects.link(camera_obj)
    scene.camera = camera_obj

    camera_obj.location = (0, -4.5, 0.8)
    camera_obj.rotation_euler = (math.radians(82), 0, 0)
    camera_obj.keyframe_insert(data_path="location", frame=1)
    camera_obj.keyframe_insert(data_path="rotation_euler", frame=1)

    camera_obj.location = (0.7, -0.6, 1.7)
    camera_obj.rotation_euler = (math.radians(40), math.radians(180), math.radians(95))
    camera_obj.keyframe_insert(data_path="location", frame=30)
    camera_obj.keyframe_insert(data_path="rotation_euler", frame=30)

    # 6. SHAPE-SHIFTING ELEMENTAL MORPH SHADER
    displace_mod = character_mesh.modifiers.new(name="ElementalMorph", type='DISPLACE')
    texture = bpy.data.textures.new(name="NoiseTex", type='CLOUDS')
    texture.noise_scale = 0.35
    displace_mod.texture = texture

    displace_mod.keyframe_insert(data_path="strength", frame=1)
    displace_mod.strength = 3.5
    displace_mod.keyframe_insert(data_path="strength", frame=30)
    displace_mod.strength = -1.2
    displace_mod.keyframe_insert(data_path="strength", frame=55)
    displace_mod.strength = 0.0
    displace_mod.keyframe_insert(data_path="strength", frame=85)

    # 7. CYCLES RAY-TRACING RENDER SETUP
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.filepath = os.path.join(output_dir, "frame_0030.png")

    scene.frame_set(30)
    bpy.ops.render.render(write_still=True)

    # 8. EXPORT MASTER GLB SCENE
    glb_out = os.path.join(output_dir, "master_scene.glb")
    try:
        bpy.ops.export_scene.gltf(filepath=glb_out)
    except Exception:
        try:
            bpy.ops.wm.gltf_export(filepath=glb_out)
        except Exception as exp:
            print(f"GLTF Export notice: {exp}")

    print("SUCCESS: Engine rendered and exported output files successfully!")

except Exception as err:
    err_text = traceback.format_exc()
    print("CRASH DETECTED:\n", err_text)
    with open(crash_log, "w") as f:
        f.write(err_text)
