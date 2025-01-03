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
            print(obj_data)
            uid = obj_data.get("uid")
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
                    str(obj_uid), obj_dimensions, obj_location, obj_rotation, obj_file
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
