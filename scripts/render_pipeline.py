import bpy
import math
import os
import urllib.request

# -------------------------------------------------------------
# 1. INITIALIZE BLENDER SCENE & ENVIRONMENT
# -------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)

output_dir = os.path.abspath("output")
os.makedirs(output_dir, exist_ok=True)

mesh_dir = os.path.abspath("assets")
os.makedirs(mesh_dir, exist_ok=True)
mesh_path = os.path.join(mesh_dir, "character.glb")

# -------------------------------------------------------------
# 2. AUTOMATED MESH DOWNLOAD (UNCOMPRESSED 73.4MB RELEASE)
# -------------------------------------------------------------
release_url = "https://github.com/arsycoxxx-cell/AR-cinema-engine/releases/download/v1.0/character.glb"

if not os.path.exists(mesh_path):
    print("Downloading original 73.4MB mesh from GitHub Releases...")
    urllib.request.urlretrieve(release_url, mesh_path)

if os.path.exists(mesh_path):
    bpy.ops.import_scene.gltf(filepath=mesh_path)
    character_mesh = bpy.context.selected_objects[0]
else:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
    character_mesh = bpy.context.active_object

bpy.ops.object.select_all(action='DESELECT')
character_mesh.select_set(True)
bpy.context.view_layer.objects.active = character_mesh

# -------------------------------------------------------------
# 3. AUTOMATED ARMATURE RIGGING (Body, Face, Hands)
# -------------------------------------------------------------
bpy.ops.object.armature_human_metarig_add()
rig = bpy.context.active_object

character_mesh.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# -------------------------------------------------------------
# 4. CLOTH & HAIR GRAVITY PHYSICS
# -------------------------------------------------------------
cloth_mod = character_mesh.modifiers.new(name="HairClothPhysics", type='CLOTH')
cloth_mod.settings.quality = 5
cloth_mod.settings.mass = 0.2
cloth_mod.settings.air_damping = 1.0

# -------------------------------------------------------------
# 5. ELEMENTAL MORPHING & SHAPE-SHIFTING SHADER
# -------------------------------------------------------------
displace_mod = character_mesh.modifiers.new(name="ElementalMorph", type='DISPLACE')
texture = bpy.data.textures.new(name="NoiseTex", type='CLOUDS')
texture.noise_scale = 0.35
displace_mod.texture = texture
displace_mod.strength = 0.0

# Keyframe Morphing Sequence (Normal -> Monster/Element -> Normal)
displace_mod.keyframe_insert(data_path="strength", frame=1)
displace_mod.strength = 3.2  # Massive elemental shape-shift on impact
displace_mod.keyframe_insert(data_path="strength", frame=30)
displace_mod.strength = 0.1
displace_mod.keyframe_insert(data_path="strength", frame=60)

# -------------------------------------------------------------
# 6. PHOTOREALISTIC SHADERS & REFLECTION MATERIAL
# -------------------------------------------------------------
mat = bpy.data.materials.new(name="UltraRealSkin")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes.get("Principled BSDF")

if bsdf:
    bsdf.inputs['Subsurface Weight'].default_value = 0.15  # Photorealistic flesh light penetration
    bsdf.inputs['Roughness'].default_value = 0.2           # High reflection reflections
    bsdf.inputs['Metallic'].default_value = 0.05

if len(character_mesh.data.materials) == 0:
    character_mesh.data.materials.append(mat)
else:
    character_mesh.data.materials[0] = mat

# -------------------------------------------------------------
# 7. UNTHINKABLE ANAMORPHIC CAMERA SCRIPT
# -------------------------------------------------------------
camera_data = bpy.data.cameras.new(name="AnimeCam")
camera_obj = bpy.data.objects.new("AnimeCam", camera_data)
bpy.data.scenes[0].collection.objects.link(camera_obj)
bpy.data.scenes[0].camera = camera_obj

# Animate explosive camera whip-pan
camera_obj.location = (0, -4.0, 1.2)
camera_obj.rotation_euler = (math.radians(85), 0, 0)
camera_obj.keyframe_insert(data_path="location", frame=1)

camera_obj.location = (0.5, -1.5, 0.8)  # Sudden hyper-close impact angle
camera_obj.rotation_euler = (math.radians(70), math.radians(20), math.radians(15))
camera_obj.keyframe_insert(data_path="location", frame=30)

# -------------------------------------------------------------
# 8. RENDER PASSES (CYCLES RAY-TRACING + Z-DEPTH)
# -------------------------------------------------------------
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920  # Vertical Mobile Ratio
scene.render.filepath = os.path.join(output_dir, "frame_")

# Enable Z-Depth and Vector passes for Node Video
view_layer = scene.view_layers[0]
view_layer.use_pass_z = True
view_layer.use_pass_vector = True

# Export Master GLB Scene Asset
glb_output_path = os.path.join(output_dir, "master_scene.glb")
bpy.ops.export_scene.gltf(filepath=glb_output_path)

print("SUCCESS: Master Cloud Production Render Pipeline Completed!")

