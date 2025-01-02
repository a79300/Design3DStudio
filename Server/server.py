import socket
import json
import threading
import time
import sys
import msvcrt
import uuid

def start_server():
    host = "127.0.0.1"
    port = 65432

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor ouvindo em {host}:{port}...")

    def handle_client(conn, addr):
        print(f"Conexão estabelecida com {addr}")
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    print(f"Conexão encerrada por {addr}")
                    break
                message = json.loads(data.decode("utf-8"))
                print(f"Recebido de {addr}: {message}")

                if message["action"] == "get_object":
                    objects_data = [
                        {
                            "uid": str(uuid.uuid4()),
                            "dimensions": [0.002, 0.002, 0.002],
                            "location": [0.0, 0.0, 0.1],
                            "rotation": [90, 0, 0],
                            "model": "C:/Users/joaossousa/Desktop/CompVisual/Design3DStudio/Objects/couch.obj",
                        }
                    ]
                    conn.sendall(json.dumps(objects_data).encode("utf-8"))
                else:
                    conn.sendall(
                        json.dumps({"message": "Ação não reconhecida"}).encode("utf-8")
                    )
            except Exception as e:
                print(f"Erro com o cliente {addr}: {e}")
                break
        try:
            conn.close()
        except OSError:
            print(f"Erro ao tentar fechar a conexão com {addr}")

    def accept_connections():
        while True:
            try:
                conn, addr = server_socket.accept()
                threading.Thread(
                    target=handle_client, args=(conn, addr), daemon=True
                ).start()
            except OSError:
                print("Erro ao aceitar novas conexões.")
                break

    threading.Thread(target=accept_connections, daemon=True).start()

    print("Servidor está rodando. Pressione 'Q' para parar.")

    while True:
        if msvcrt.kbhit():
            user_input = msvcrt.getch().decode("utf-8")
            if user_input.lower() == "q":
                print("Fechando o servidor...")
                try:
                    server_socket.close()
                except OSError:
                    print("Erro ao tentar fechar o servidor.")
                break
        time.sleep(0.1)


if __name__ == "__main__":
    start_server()
