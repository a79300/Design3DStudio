import socket
import json
import threading
import time
import msvcrt
import os

FILE_PATH = "data.json"


def load_objects_data():
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, "r") as file:
                return json.load(file)
        except Exception as e:
            print(f"Erro ao carregar o ficheiro {FILE_PATH}: {e}")
            return []
    return []


def save_objects_data(data):
    try:
        with open(FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Erro ao salvar o ficheiro {FILE_PATH}: {e}")


def start_server():
    host = "127.0.0.1"
    port = 65432

    objects_data = load_objects_data()

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
                    conn.sendall(json.dumps(objects_data).encode("utf-8"))
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
                save_objects_data(objects_data)
                break
        time.sleep(0.1)


if __name__ == "__main__":
    start_server()
