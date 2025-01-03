import socket
import json
import threading
import time
import msvcrt
import os
import cv2
import numpy as np
import mediapipe as mp

FILE_PATH = "data.json"
FRAME_WIDTH, FRAME_HEIGHT = 640, 480


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

    def hand_detection():

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        if not cap.isOpened():
            print("Erro ao acessar a câmera.")
            return

        try:
            background = cv2.imread("assets/background.png")
            if background is None:
                background = (
                    np.ones((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8) * 255
                )
            else:
                background = cv2.resize(background, (FRAME_WIDTH, FRAME_HEIGHT))
        except Exception as e:
            background = np.ones((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8) * 255

        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            min_detection_confidence=0.7, min_tracking_confidence=0.7
        )

        while True:

            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = hands.process(rgb_frame)

            frame_with_background = background.copy()

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    for connection in mp_hands.HAND_CONNECTIONS:
                        start_idx, end_idx = connection
                        start = hand_landmarks.landmark[start_idx]
                        end = hand_landmarks.landmark[end_idx]

                        start_x, start_y = int(start.x * FRAME_WIDTH), int(
                            start.y * FRAME_HEIGHT
                        )
                        end_x, end_y = int(end.x * FRAME_WIDTH), int(
                            end.y * FRAME_HEIGHT
                        )

                        cv2.line(
                            frame_with_background,
                            (start_x, start_y),
                            (end_x, end_y),
                            (0, 255, 0),
                            2,
                        )

                    for landmark in hand_landmarks.landmark:
                        x = int(landmark.x * FRAME_WIDTH)
                        y = int(landmark.y * FRAME_HEIGHT)
                        cv2.circle(frame_with_background, (x, y), 5, (0, 0, 255), -1)

            cv2.imshow("Object Selector", frame_with_background)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Fechando o servidor...")
                try:
                    server_socket.close()
                except OSError:
                    print("Erro ao tentar fechar o servidor.")
                save_objects_data(objects_data)
                break

        cap.release()
        cv2.destroyAllWindows()

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
    hand_detection()
    print("Servidor está rodando. Pressione 'Q' para parar.")


if __name__ == "__main__":
    start_server()
