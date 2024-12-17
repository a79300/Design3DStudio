import bpy
import math

class ModalCubeOperator(bpy.types.Operator):
    bl_idname = "wm.modal_cube_operator"
    bl_label = "Add Cube on Key Press"
    
    ROOM_SIZE = 10  
    WALL_HEIGHT = 5  
    
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

def register():
    bpy.utils.register_class(ModalCubeOperator)

def unregister():
    bpy.utils.unregister_class(ModalCubeOperator)

if __name__ == "__main__":
    register()
    
    bpy.ops.wm.modal_cube_operator('INVOKE_DEFAULT')
