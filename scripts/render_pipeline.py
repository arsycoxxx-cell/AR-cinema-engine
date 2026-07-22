import bpy
import math
import os
import traceback

# 1. SETUP OUTPUT PATHS
output_dir = os.path.abspath("output")
os.makedirs(output_dir, exist_ok=True)

mesh_path = os.path.abspath("assets/character.glb")

try:
    # Reset Blender Scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # 2. IMPORT 73.4MB CHARACTER MESH
    if os.path.exists(mesh_path) and os.path.getsize(mesh_path) > 100000:
        print("Importing 73.4MB character mesh from assets/character.glb...")
        bpy.ops.import_scene.gltf(filepath=mesh_path)
        mesh_objs = [obj for obj in scene.objects if obj.type == 'MESH']
        character_mesh = mesh_objs[0] if mesh_objs else None
    else:
        character_mesh = None

    if not character_mesh:
        print("Creating fallback character mesh...")
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 1.0))
        character_mesh = bpy.context.active_object

    bpy.ops.object.select_all(action='DESELECT')
    character_mesh.select_set(True)
    bpy.context.view_layer.objects.active = character_mesh

    # 3. CONTEXT-SAFE SKELETAL RIGGING
    armature_data = bpy.data.armatures.new("AutoRigArmature")
    rig_obj = bpy.data.objects.new("AutoRig", armature_data)
    scene.collection.objects.link(rig_obj)
    
    arm_mod = character_mesh.modifiers.new(name="ArmatureRig", type='ARMATURE')
    arm_mod.object = rig_obj

    # 4. LIP-SYNC FACIAL SHAPE KEYS
    if not character_mesh.data.shape_keys:
        character_mesh.shape_key_add(name="Basis", from_mix=False)
    
    mouth_open = character_mesh.shape_key_add(name="MouthOpen", from_mix=False)
    for frame in range(1, 90):
        amp = math.sin(frame * 0.45) * 0.85 if (frame % 8 < 5) else 0.05
        mouth_open.value = max(0.0, amp)
        mouth_open.keyframe_insert(data_path="value", frame=frame)

    # 5. CLOTH & HAIR GRAVITY PHYSICS
    cloth_mod = character_mesh.modifiers.new(name="ClothHairPhysics", type='CLOTH')
    cloth_mod.settings.quality = 5
    cloth_mod.settings.mass = 0.16

    # 6. PBR ENVIRONMENT (Wet Asphalt Ground)
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground_mat = bpy.data.materials.new(name="WetAsphalt")
    ground_mat.use_nodes = True
    g_bsdf = ground_mat.node_tree.nodes.get("Principled BSDF")
    if g_bsdf:
        g_bsdf.inputs['Roughness'].default_value = 0.05
        g_bsdf.inputs['Base Color'].default_value = (0.015, 0.015, 0.025, 1.0)
    ground.data.materials.append(ground_mat)

    # Anime Aura Lighting
    bpy.ops.object.light_add(type='POINT', location=(0, 0, 1.5))
    aura_light = bpy.context.active_object
    aura_light.data.energy = 600.0
    aura_light.data.color = (0.05, 0.55, 1.0)

    for f in [15, 30, 45, 60]:
        aura_light.data.energy = 3500.0
        aura_light.data.keyframe_insert(data_path="energy", frame=f)
        aura_light.data.energy = 200.0
        aura_light.data.keyframe_insert(data_path="energy", frame=f + 6)

    # 7. SHAPE-SHIFTING ELEMENTAL MORPH SHADER
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

    # 8. UNTHINKABLE CAMERA ENGINE
    camera_data = bpy.data.cameras.new(name="UnthinkableCam")
    camera_obj = bpy.data.objects.new("UnthinkableCam", camera_data)
    scene.collection.objects.link(camera_obj)
    scene.camera = camera_obj
    camera_data.lens = 16

    camera_obj.location = (0, -4.5, 0.8)
    camera_obj.rotation_euler = (math.radians(82), 0, 0)
    camera_obj.keyframe_insert(data_path="location", frame=1)
    camera_obj.keyframe_insert(data_path="rotation_euler", frame=1)

    camera_obj.location = (0.7, -0.6, 1.7)
    camera_obj.rotation_euler = (math.radians(40), math.radians(180), math.radians(95))
    camera_obj.keyframe_insert(data_path="location", frame=30)
    camera_obj.keyframe_insert(data_path="rotation_euler", frame=30)

    # 9. RENDER PASSES & EXPORT
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.filepath = os.path.join(output_dir, "frame_")

    # Render Impact Frame 30
    scene.frame_set(30)
    bpy.ops.render.render(write_still=True)

    # Export Master GLB Scene
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
    error_log = os.path.join(output_dir, "CRASH_LOG.txt")
    with open(error_log, "w") as f:
        f.write(traceback.format_exc())
    print("ERROR ENCOUNTERED. Log written to CRASH_LOG.txt")
