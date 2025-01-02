import bpy
import os
import math
import socket
import json
import threading
import time


class SocketClient:
    def __init__(self, host, port, max_retries=10):
        self.host = host
        self.port = port
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.retry_count = 0
        self.max_retries = max_retries
        self.connected = False

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            print("Conectado ao servidor")
            self.retry_count = 0
            self.connected = True
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            self.connected = False

    def listen_and_request(self):
        while self.running:
            if not self.connected:
                self.retry_count += 1
                print(
                    f"Tentativa de conexão falhada {self.retry_count}/{self.max_retries}"
                )

                if self.retry_count >= self.max_retries:
                    print(
                        f"Máximo de tentativas falhadas alcançado ({self.max_retries}). Desconectando."
                    )
                    self.running = False
                    break
                else:
                    print("Tentando reconectar...")
                    self.reconnect()
                    time.sleep(2)  # Espera antes de tentar novamente
                    continue

            try:
                request = {"action": "get_object"}
                self.sock.sendall(json.dumps(request).encode("utf-8"))
                print("Pedido enviado ao servidor.")

                data = self.sock.recv(1024)
                if not data:
                    print("Conexão encerrada pelo servidor.")
                    break

                message = data.decode("utf-8")
                print(f"Resposta recebida: {message}")

                # Aqui, tratamos a resposta como um array de dicionários
                objects = json.loads(
                    message
                )  # Assumindo que o servidor envia um array de objetos
                if isinstance(objects, list):
                    self.handle_message(
                        objects
                    )  # Passa a lista inteira para o handle_message
                else:
                    print("Erro: Resposta recebida não é uma lista.")

                time.sleep(1)  # Tempo entre os pedidos

            except Exception as e:
                print(f"Erro ao se comunicar com o servidor: {e}")
                self.connected = False

    def reconnect(self):
        self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def handle_message(self, objects):
        for obj_data in objects:
            uid = obj_data.get("uid")
            dimensions = obj_data.get("dimensions", {})
            location = obj_data.get("location", {})
            rotation = obj_data.get("rotation", {})
            obj_file = obj_data.get("model", "")

            if not obj_file:
                print("Erro: Nenhum arquivo OBJ foi enviado pelo servidor.")
                continue

            bpy.app.timers.register(
                lambda: self.update_or_create_object(
                    uid, dimensions, location, rotation, obj_file
                )
            )

    def update_or_create_object(self, uid, dimensions, location, rotation, obj_file):
        obj = bpy.data.objects.get(uid)

        if obj is None:
            if os.path.exists(obj_file):
                bpy.ops.wm.obj_import(filepath=obj_file)

                imported_objects = bpy.context.selected_objects
                if imported_objects:
                    obj = imported_objects[0]
                    obj.name = uid
            else:
                return

        if obj:
            obj.location = (
                location[0],
                location[1],
                location[2],
            )
            obj.rotation_euler = (
                math.radians(rotation[0]),
                math.radians(rotation[1]),
                math.radians(rotation[2]),
            )
            obj.scale = (
                dimensions[0],
                dimensions[1],
                dimensions[2],
            )
            print(f"Objeto {uid} atualizado com sucesso.")
        else:
            print(f"Falha ao importar ou encontrar o objeto com UID: {uid}")

    def stop(self):
        self.running = False
        self.sock.close()


class ModalSocketOperator(bpy.types.Operator):
    bl_idname = "wm.modal_socket_operator"
    bl_label = "Socket Client Operator"

    ROOM_SIZE = 10
    FLOOR_THICKNESS = 0.2
    WOOD_TEXTURE_PATH = "C:/Users/joaossousa/Desktop/CompVisual/Design3DStudio/Client/textures/planks.png"

    def __init__(self):
        self.client = None

    def create_room(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

        room_size = self.ROOM_SIZE
        floor_thickness = self.FLOOR_THICKNESS

        bpy.ops.mesh.primitive_cube_add(
            size=room_size, location=(0, 0, -floor_thickness / 2)
        )
        floor = bpy.context.object
        floor.scale.z = floor_thickness / (room_size / 2)
        floor.name = "Floor"

        self.apply_wooden_floor_texture(floor)

    def apply_wooden_floor_texture(self, floor_object):
        mat = bpy.data.materials.new(name="WoodenFloorMaterial")
        mat.use_nodes = True

        texture_image = bpy.data.images.load(self.WOOD_TEXTURE_PATH)

        texture_node = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
        texture_node.image = texture_image

        mapping_node = mat.node_tree.nodes.new(type="ShaderNodeMapping")
        texture_coords_node = mat.node_tree.nodes.new(type="ShaderNodeTexCoord")

        mat.node_tree.links.new(
            texture_coords_node.outputs["UV"], mapping_node.inputs["Vector"]
        )
        mat.node_tree.links.new(
            mapping_node.outputs["Vector"], texture_node.inputs["Vector"]
        )

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        mat.node_tree.links.new(
            texture_node.outputs["Color"], bsdf.inputs["Base Color"]
        )

        if floor_object.data.materials:
            floor_object.data.materials[0] = mat
        else:
            floor_object.data.materials.append(mat)

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
