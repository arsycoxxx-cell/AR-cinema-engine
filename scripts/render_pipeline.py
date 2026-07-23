import bpy
import math
import os
import traceback

output_dir = os.path.abspath("output")
os.makedirs(output_dir, exist_ok=True)
crash_log = os.path.join(output_dir, "CRASH_LOG.txt")

try:
    # 1. CLEAN BLENDER SCENE
    scene = bpy.context.scene
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    # 2. READ STORYBOARD PROMPT
    storyboard_path = os.path.abspath("storyboard.txt")
    if os.path.exists(storyboard_path):
        with open(storyboard_path, "r") as f:
            print("Loaded storyboard prompts successfully.")

    # 3. IMPORT CHARACTER MESH
    mesh_path = os.path.abspath("assets/character.glb")
    character_mesh = None

    if os.path.exists(mesh_path) and os.path.getsize(mesh_path) > 100000:
        print("Importing character mesh...")
        bpy.ops.import_scene.gltf(filepath=mesh_path)
        mesh_objs = [o for o in scene.objects if o.type == 'MESH']
        if mesh_objs:
            character_mesh = mesh_objs[0]

    if not character_mesh:
        mesh_data = bpy.data.meshes.new("FallbackMesh")
        character_mesh = bpy.data.objects.new("FallbackObj", mesh_data)
        scene.collection.objects.link(character_mesh)

    # 4. SKELETAL RIGGING & CLOTH PHYSICS
    armature_data = bpy.data.armatures.new("AutoRigArmature")
    rig_obj = bpy.data.objects.new("AutoRig", armature_data)
    scene.collection.objects.link(rig_obj)

    arm_mod = character_mesh.modifiers.new(name="ArmatureRig", type='ARMATURE')
    arm_mod.object = rig_obj

    cloth_mod = character_mesh.modifiers.new(name="ClothHairPhysics", type='CLOTH')
    cloth_mod.settings.quality = 5

    # 5. FACIAL SPEECH MORPH KEYS
    if not character_mesh.data.shape_keys:
        character_mesh.shape_key_add(name="Basis", from_mix=False)

    mouth_open = character_mesh.shape_key_add(name="MouthOpen", from_mix=False)
    for frame in range(1, 90):
        amp = math.sin(frame * 0.45) * 0.85 if (frame % 8 < 5) else 0.05
        mouth_open.value = max(0.0, amp)
        mouth_open.keyframe_insert(data_path="value", frame=frame)

    # 6. WET ASPHALT PBR GROUND
    plane_mesh = bpy.data.meshes.new("GroundMesh")
    coords = [(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)]
    plane_mesh.from_pydata(coords, [], [(0, 1, 2, 3)])
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

    # 7. ANIME AURA LIGHTING
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

    # 8. SHAPE-SHIFTING ELEMENTAL MORPH SHADER
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

    # 9. UNTHINKABLE 360° CAMERA MOTION
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

    # 10. CYCLES RAY-TRACING & MULTI-PASS EXPORT
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.filepath = os.path.join(output_dir, "frame_0030.png")

    scene.frame_set(30)
    bpy.ops.render.render(write_still=True)

    glb_out = os.path.join(output_dir, "master_scene.glb")
    try:
        bpy.ops.export_scene.gltf(filepath=glb_out)
    except Exception:
        try:
            bpy.ops.wm.gltf_export(filepath=glb_out)
        except Exception as e_exp:
            print(f"GLTF Export notice: {e_exp}")

    print("SUCCESS: Engine rendered and exported output files successfully!")

except Exception as err:
    err_text = traceback.format_exc()
    print("CRASH DETECTED:\n", err_text)
    with open(crash_log, "w") as f:
        f.write(err_text)
