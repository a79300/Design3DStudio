import bpy
import math
import os

class ModalCubeOperator(bpy.types.Operator):
    bl_idname = "wm.modal_cube_operator"
    bl_label = "Add Cube on Key Press"
    
    ROOM_SIZE = 10  
    WALL_HEIGHT = 5
    WOOD_TEXTURE_PATH = "C:/Users/YangSafe/Desktop/Software Stuff/Blender/TP5/textures/planks.png"

    def modal(self, context, event):
        
        if event.type == 'ESC':
            self.report({'INFO'}, "Exiting Modal Operator")
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        
        self.create_room()
        
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Press 'ESC' to exit.")
        return {'RUNNING_MODAL'}
    
    def create_room(self):
        
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        room_size = self.ROOM_SIZE
        wall_height = self.WALL_HEIGHT
        wall_thickness = 0.2  
        floor_thickness = 0.2  
        
        bpy.ops.mesh.primitive_cube_add(size=room_size, location=(0, 0, -floor_thickness / 2))
        floor = bpy.context.object
        floor.scale.z = floor_thickness / (room_size / 2)  
        floor.name = "Floor"
        
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, room_size / 2 - wall_thickness / 2, wall_height / 2))
        back_wall = bpy.context.object
        back_wall.scale = (room_size / 2, wall_thickness / 2, wall_height / 2)
        back_wall.name = "Back Wall"
        
        bpy.ops.mesh.primitive_cube_add(size=2, location=(-room_size / 2 + wall_thickness / 2, 0, wall_height / 2))
        left_wall = bpy.context.object
        left_wall.scale = (wall_thickness / 2, room_size / 2, wall_height / 2)
        left_wall.name = "Left Wall"
        
        bpy.ops.mesh.primitive_cube_add(size=2, location=(room_size / 2 - wall_thickness / 2, 0, wall_height / 2))
        right_wall = bpy.context.object
        right_wall.scale = (wall_thickness / 2, room_size / 2, wall_height / 2)
        right_wall.name = "Right Wall"
        
        bpy.ops.object.camera_add(location=(0, -room_size, wall_height / 2))
        camera = bpy.context.object
        camera.name = "Entry Camera"
        
        camera.rotation_euler = (math.radians(90), 0, 0)  

        bpy.context.scene.camera = camera
        
        self.apply_white_wall_texture(back_wall)
        self.apply_white_wall_texture(left_wall)
        self.apply_white_wall_texture(right_wall)
        
        self.apply_wooden_floor_texture(floor)
    
    def apply_white_wall_texture(self, wall_object):
        mat = bpy.data.materials.new(name="WhiteWallMaterial")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
        
        if wall_object.data.materials:
            wall_object.data.materials[0] = mat
        else:
            wall_object.data.materials.append(mat)
    
    def apply_wooden_floor_texture(self, floor_object):
        mat = bpy.data.materials.new(name="WoodenFloorMaterial")
        mat.use_nodes = True
        
        texture_image = bpy.data.images.load(self.WOOD_TEXTURE_PATH)
        
        texture_node = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
        texture_node.image = texture_image
        
        mapping_node = mat.node_tree.nodes.new(type='ShaderNodeMapping')
        texture_coords_node = mat.node_tree.nodes.new(type='ShaderNodeTexCoord')
        
        mat.node_tree.links.new(texture_coords_node.outputs['UV'], mapping_node.inputs['Vector'])
        mat.node_tree.links.new(mapping_node.outputs['Vector'], texture_node.inputs['Vector'])
        
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        mat.node_tree.links.new(texture_node.outputs['Color'], bsdf.inputs['Base Color'])
        
        if floor_object.data.materials:
            floor_object.data.materials[0] = mat
        else:
            floor_object.data.materials.append(mat)

def register():
    bpy.utils.register_class(ModalCubeOperator)

def unregister():
    bpy.utils.unregister_class(ModalCubeOperator)

if __name__ == "__main__":
    register()
    
    bpy.ops.wm.modal_cube_operator('INVOKE_DEFAULT')
