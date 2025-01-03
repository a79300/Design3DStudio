import time
import socket
import json
import threading
import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

FILE_PATH = "data.json"
FRAME_WIDTH, FRAME_HEIGHT = 640, 480
MODEL_PATH = "assets/models/efficientdet_lite16.tflite"
COCO_NAMES_PATH = "assets/coco.names"


def load_coco_classes():
    try:
        with open(COCO_NAMES_PATH, "r") as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        print(f"Erro ao carregar o arquivo {COCO_NAMES_PATH}: {e}")
        return []


coco_classes = load_coco_classes()
excluded_classes = ["person"]
allowed_classes = [cls for cls in coco_classes if cls not in excluded_classes]


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


def get_next_uid(objects_data, base_uid):
    uids = [obj["uid"] for obj in objects_data if obj["uid"].startswith(base_uid)]
    max_index = 0
    for uid in uids:
        try:
            index = int(uid.split("_")[1])
            if index > max_index:
                max_index = index
        except ValueError:
            continue
    return f"{base_uid}_{max_index + 1}"


def display_objects_grid(frame_with_background, objects_data):
    square_width = 50
    square_height = 43
    margin_x = 0
    margin_y = 11
    for i, obj in enumerate(objects_data):
        if obj["uid"] != "floor":
            img_path = "assets/images/" + obj.get("uid", "").split("_")[0] + ".png"
            if os.path.exists(img_path):
                if "couch" in obj["uid"]:
                    margin_x += 11
                elif "coffee-table" in obj["uid"]:
                    margin_x += 20
                y_offset = FRAME_HEIGHT - square_height - margin_y
                x_offset = square_width * (i - 1) + margin_x
                try:
                    obj_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

                    if obj_img.shape[2] == 4:
                        obj_img = cv2.resize(obj_img, (square_width, square_height))
                        alpha_channel = obj_img[:, :, 3] / 255.0

                        for c in range(3):
                            frame_with_background[
                                y_offset : y_offset + square_height,
                                x_offset : x_offset + square_width,
                                c,
                            ] = (1.0 - alpha_channel) * frame_with_background[
                                y_offset : y_offset + square_height,
                                x_offset : x_offset + square_width,
                                c,
                            ] + alpha_channel * obj_img[
                                :, :, c
                            ]
                    else:
                        obj_img = cv2.resize(obj_img, (square_width, square_height))
                        frame_with_background[
                            y_offset : y_offset + square_height,
                            x_offset : x_offset + square_width,
                        ] = obj_img
                except Exception as e:
                    print(f"Erro ao carregar a imagem do objeto {obj['uid']}: {e}")

                x_offset += square_width + margin_x
                if x_offset + square_width > FRAME_WIDTH:
                    x_offset = 0
                    y_offset -= square_height + margin_y

    return frame_with_background


def start_server():
    host = "127.0.0.1"
    port = 65432

    objects_data = load_objects_data()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor ouvindo em {host}:{port}...")

    def object_detection_and_hand_detection():
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        if not cap.isOpened():
            print("Erro ao acessar a câmera.")
            return

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.ObjectDetectorOptions(
            base_options=base_options, score_threshold=0.5
        )
        detector = vision.ObjectDetector.create_from_options(options)

        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            min_detection_confidence=0.7, min_tracking_confidence=0.7
        )

        try:
            background = cv2.imread("assets/images/background.png")
            if background is None:
                background = (
                    np.ones((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8) * 255
                )
            else:
                background = cv2.resize(background, (FRAME_WIDTH, FRAME_HEIGHT))
        except Exception:
            background = np.ones((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8) * 255

        last_detection_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            current_time = time.time()
            if current_time - last_detection_time >= 3:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                detection_result = detector.detect(mp_image)

                for detection in detection_result.detections:
                    detection_class = detection.categories[0].category_name
                    detection_score = detection.categories[0].score

                    if detection_class in allowed_classes:
                        location = [0, 0, 0.1]
                        if not any(obj["location"] == location for obj in objects_data):
                            if detection_class == "cup" and detection_score >= 0.5:
                                uid = get_next_uid(objects_data, "coffee-table")
                                objects_data.append(
                                    {
                                        "uid": uid,
                                        "dimensions": [0.002, 0.002, 0.001],
                                        "location": location,
                                        "rotation": [90, 0, 0],
                                        "model": "C:/Users/joaossousa/Desktop/CompVisual/Design3DStudio/Objects/coffee-table.obj",
                                    }
                                )

                last_detection_time = current_time

            frame_with_background = background.copy()

            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    for landmark in hand_landmarks.landmark:
                        x = int(landmark.x * FRAME_WIDTH)
                        y = int(landmark.y * FRAME_HEIGHT)
                        cv2.circle(frame_with_background, (x, y), 5, (0, 0, 255), -1)

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
            frame_with_background = display_objects_grid(
                frame_with_background, objects_data
            )

            cv2.imshow("Hand Detection", frame_with_background)

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
    object_detection_and_hand_detection()
    print("Servidor está rodando. Pressione 'Q' para parar.")


if __name__ == "__main__":
    start_server()
