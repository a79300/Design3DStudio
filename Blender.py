import bpy
import os
import math
import socket
import json
import threading
import time


class SocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            self.connected = True
        except Exception as e:
            self.connected = False

    def listen_and_request(self):
        while self.running:
            if not self.connected:
                self.reconnect()
                time.sleep(2)
                continue

            try:
                request = {"action": "get_object"}
                self.sock.sendall(json.dumps(request).encode("utf-8"))

                data = self.sock.recv(4096)
                if not data:
                    break

                message = data.decode("utf-8")

                objects = json.loads(message)
                if isinstance(objects, list):
                    self.handle_message(objects)

                time.sleep(0.1)

            except Exception as e:
                self.connected = False

    def reconnect(self):
        self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def handle_message(self, objects):
        for obj_data in objects:
            uid = obj_data.get("uid")

            if uid == "rotate":
                side = obj_data.get("side", 0)
                obj = bpy.data.objects.get("camera")

                if side == 0:
                    location = (0, -28.5, 3.65)
                    rotation = (
                        math.radians(4409.9),
                        math.radians(-0.219),
                        math.radians(359.54),
                    )

                    wall_1 = bpy.data.objects.get("Wall_1")
                    wall_1.location = (7.7, 0.112159, 3.65)
                    wall_1.scale = (0.250, 15, 7.5)
                    wall_1.rotation_euler = (0, 0, 0)
                    wall_2 = bpy.data.objects.get("Wall_2")
                    wall_2.location = (-7.1947, 0.112159, 3.65)
                    wall_2.scale = (0.250, 15, 7.5)
                    wall_2.rotation_euler = (0, 0, 0)
                    wall_3 = bpy.data.objects.get("Wall_3")
                    wall_3.location = (0.30, 7.5, 3.65)
                    wall_3.scale = (0.250, 15, 7.5)
                    wall_3.rotation_euler = (0, 0, math.radians(90))

                elif side == 2:
                    location = (0, 28.787, 3.65)
                    rotation = (
                        math.radians(-4409.5),
                        math.radians(-179.92),
                        math.radians(360.74),
                    )

                    wall_1 = bpy.data.objects.get("Wall_1")
                    wall_1.location = (7.7, 0.112159, 3.65)
                    wall_1.scale = (0.250, 15, 7.5)
                    wall_1.rotation_euler = (0, 0, 0)
                    wall_2 = bpy.data.objects.get("Wall_2")
                    wall_2.location = (-7.1947, 0.112159, 3.65)
                    wall_2.scale = (0.250, 15, 7.5)
                    wall_2.rotation_euler = (0, 0, 0)
                    wall_3 = bpy.data.objects.get("Wall_3")
                    wall_3.location = (0.30, -7.5, 3.65)
                    wall_3.scale = (0.250, 15, 7.5)
                    wall_3.rotation_euler = (0, 0, math.radians(90))

                elif side == 1:
                    location = (-28.582, 0, 3.65)
                    rotation = (
                        math.radians(4230.5),
                        math.radians(539.74),
                        math.radians(-269.58),
                    )

                    wall_1 = bpy.data.objects.get("Wall_1")
                    wall_1.location = (0.30, 7.5, 3.65)
                    wall_1.scale = (0.250, 15, 7.5)
                    wall_1.rotation_euler = (0, 0, math.radians(90))
                    wall_2 = bpy.data.objects.get("Wall_2")
                    wall_2.location = (7.7, 0.112159, 3.65)
                    wall_2.scale = (0.250, 15, 7.5)
                    wall_2.rotation_euler = (0, 0, 0)
                    wall_3 = bpy.data.objects.get("Wall_3")
                    wall_3.location = (0.30, -7.5, 3.65)
                    wall_3.scale = (0.250, 15, 7.5)
                    wall_3.rotation_euler = (0, 0, math.radians(90))

                elif side == 3:
                    location = (29.257, 0, 3.65)
                    rotation = (
                        math.radians(-4230.1),
                        math.radians(359.56),
                        math.radians(-270.25),
                    )

                    wall_1 = bpy.data.objects.get("Wall_1")
                    wall_1.location = (0.3, 7.5, 3.65)
                    wall_1.scale = (0.250, 15, 7.5)
                    wall_1.rotation_euler = (0, 0, math.radians(90))
                    wall_2 = bpy.data.objects.get("Wall_2")
                    wall_2.location = (0.3, -7.5, 3.65)
                    wall_2.scale = (0.250, 15, 7.5)
                    wall_2.rotation_euler = (0, 0, math.radians(90))
                    wall_3 = bpy.data.objects.get("Wall_3")
                    wall_3.location = (-7.1918, 0.112159, 3.65)
                    wall_3.scale = (0.250, 15, 7.5)
                    wall_3.rotation_euler = (0, 0, 0)
                else:
                    continue

                obj.location = location
                obj.rotation_euler = rotation

            else:
                dimensions = obj_data.get("dimensions", {})
                location = obj_data.get("location", {})
                rotation = obj_data.get("rotation", {})
                obj_file = (
                    "C:/Users/joaossousa/Desktop/CompVisual/Design3DStudio/Objects/"
                    + obj_data.get("model", "")
                )

                if not obj_file:
                    continue

                bpy.app.timers.register(
                    lambda obj_uid=uid, obj_dimensions=dimensions, obj_location=location, obj_rotation=rotation, obj_file=obj_file: self.update_or_create_object(
                        str(obj_uid),
                        obj_dimensions,
                        obj_location,
                        obj_rotation,
                        obj_file,
                    )
                )

    def update_or_create_object(self, uid, dimensions, location, rotation, obj_file):

        obj = bpy.data.objects.get(str(uid))
        if obj is None:
            if os.path.exists(obj_file):
                bpy.ops.wm.obj_import(filepath=obj_file)

                imported_objects = bpy.context.selected_objects
                for imported_obj in imported_objects:
                    imported_obj.name = uid

                    imported_obj.location = (location[0], location[1], location[2])
                    imported_obj.rotation_euler = (
                        math.radians(rotation[0]),
                        math.radians(rotation[1]),
                        math.radians(rotation[2]),
                    )
                    imported_obj.scale = (dimensions[0], dimensions[1], dimensions[2])
        else:

            obj.location = (location[0], location[1], location[2])
            obj.rotation_euler = (
                math.radians(rotation[0]),
                math.radians(rotation[1]),
                math.radians(rotation[2]),
            )
            obj.scale = (dimensions[0], dimensions[1], dimensions[2])

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()


class ModalSocketOperator(bpy.types.Operator):
    bl_idname = "wm.modal_socket_operator"
    bl_label = "Socket Client Operator"

    def __init__(self):
        self.client = None

    def create_room(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

        bpy.ops.object.camera_add()
        camera = bpy.context.active_object
        camera.name = "camera"

        bpy.ops.mesh.primitive_cube_add(size=0)
        ceiling = bpy.context.active_object
        ceiling.name = "ceiling"
        ceiling.location = (0.29127, 0.0111, 7.3)
        ceiling.rotation_euler = (math.radians(90), math.radians(-90), 0)
        ceiling.scale = (0.250, 15, 15)
        bpy.ops.mesh.primitive_cube_add(size=0)
        wall_1 = bpy.context.active_object
        wall_1.name = "Wall_1"
        bpy.ops.mesh.primitive_cube_add(size=0)
        wall_2 = bpy.context.active_object
        wall_2.name = "Wall_2"
        bpy.ops.mesh.primitive_cube_add(size=0)
        wall_3 = bpy.context.active_object
        wall_3.name = "Wall_3"

    def modal(self, context, event):
        if event.type == "ESC":
            self.client.stop()
            return {"CANCELLED"}
        return {"PASS_THROUGH"}

    def execute(self, context):
        self.create_room()

        self.client = SocketClient("127.0.0.1", 65432)
        self.client.connect()

        threading.Thread(target=self.client.listen_and_request, daemon=True).start()

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


def register():
    bpy.utils.register_class(ModalSocketOperator)


def unregister():
    bpy.utils.unregister_class(ModalSocketOperator)


if __name__ == "__main__":
    register()
    bpy.ops.wm.modal_socket_operator("INVOKE_DEFAULT")
