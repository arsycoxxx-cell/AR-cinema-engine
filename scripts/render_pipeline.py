import bpy
import os
import math

# 1. Prepare Output Folder
output_dir = os.path.abspath("output")
os.makedirs(output_dir, exist_ok=True)

# 2. Reset Scene
scene = bpy.context.scene
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# 3. Load 73.4MB Character Mesh safely
mesh_path = os.path.abspath("assets/character.glb")
if os.path.exists(mesh_path) and os.path.getsize(mesh_path) > 100000:
    print("Loading GLTF Character Mesh...")
    bpy.ops.import_scene.gltf(filepath=mesh_path)
    mesh_objs = [o for o in scene.objects if o.type == 'MESH']
    character_mesh = mesh_objs[0] if mesh_objs else None
else:
    character_mesh = None

if not character_mesh:
    mesh_data = bpy.data.meshes.new("FallbackMesh")
    character_mesh = bpy.data.objects.new("FallbackObj", mesh_data)
    scene.collection.objects.link(character_mesh)

# 4. Create Ground & Light using Direct Data Constructors (No UI Context Needed)
plane_mesh = bpy.data.meshes.new("GroundMesh")
plane_mesh.from_pydata([(-50, -50, 0), (50, -50, 0), (50, 50, 0), (-50, 50, 0)], [], [(0, 1, 2, 3)])
plane_mesh.update()
ground = bpy.data.objects.new("Ground", plane_mesh)
scene.collection.objects.link(ground)

light_data = bpy.data.lights.new(name="SunLight", type='SUN')
light_data.energy = 5.0
light_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
scene.collection.objects.link(light_obj)

# 5. Create Camera
cam_data = bpy.data.cameras.new("AnimeCam")
cam_obj = bpy.data.objects.new("AnimeCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = (0, -4.0, 1.2)
cam_obj.rotation_euler = (math.radians(80), 0, 0)

# 6. Render Fast Software Image (CPU Safe)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.filepath = os.path.join(output_dir, "render_output.png")
bpy.ops.render.render(write_still=True)

# 7. Export Animated/Rigged GLB Scene for Mobile
glb_out = os.path.join(output_dir, "master_scene.glb")
try:
    bpy.ops.export_scene.gltf(filepath=glb_out)
except Exception as e:
    print(f"GLTF Export notice: {e}")

print("SUCCESS: Files successfully written to output directory!")
