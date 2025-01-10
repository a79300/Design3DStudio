from math import sqrt
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
selected_object_index = 0
old_l_wrist_x = None
old_r_wrist_x = None
selected_axis = None
side = 0
scale = None


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
            json.dump(data, file)
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
        if obj["uid"] not in ["floor", "rotate"]:
            img_path = "assets/images/" + obj.get("uid", "").split("_")[0] + ".png"
            if os.path.exists(img_path):
                if i == 2:
                    margin_x += 11
                else:
                    margin_x += 20
                y_offset = FRAME_HEIGHT - square_height - margin_y
                x_offset = square_width * (i - 2) + margin_x
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

                    if i - 2 == selected_object_index:

                        border_x_offset = (
                            square_width * selected_object_index + margin_x
                        )
                        cv2.rectangle(
                            frame_with_background,
                            (border_x_offset - 2, y_offset - 2),
                            (
                                border_x_offset + square_width + 2,
                                y_offset + square_height + 2,
                            ),
                            (0, 215, 255),
                            3,
                        )

                        center_x = FRAME_WIDTH // 2
                        center_y = FRAME_HEIGHT // 2

                        selected_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                        if selected_img is not None:
                            selected_img = cv2.resize(selected_img, (150, 150))
                            alpha_channel = (
                                selected_img[:, :, 3] / 255.0
                                if selected_img.shape[2] == 4
                                else None
                            )

                            img_height, img_width = selected_img.shape[:2]
                            y1 = center_y - img_height // 2
                            y2 = y1 + img_height
                            x1 = center_x - img_width // 2
                            x2 = x1 + img_width

                            if alpha_channel is not None:
                                for c in range(3):
                                    frame_with_background[y1:y2, x1:x2, c] = (
                                        alpha_channel * selected_img[:, :, c]
                                        + (1 - alpha_channel)
                                        * frame_with_background[y1:y2, x1:x2, c]
                                    )
                            else:
                                frame_with_background[y1:y2, x1:x2] = selected_img

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

    def dict_to_object(uid, dimensions, location, rotation, model):
        return {
            "uid": uid,
            "dimensions": dimensions,
            "location": location,
            "rotation": rotation,
            "model": model,
        }

    def object_detection_and_hand_detection():
        global selected_object_index, old_l_wrist_x, old_r_wrist_x, selected_axis, scale, side
        face_left_location = None
        face_right_location = None
        head_rotation = False
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        if not cap.isOpened():
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

        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5, min_tracking_confidence=0.5
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

        grabbed = False

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
                        rotation = [90, 0, 0]
                        filtered_objects = objects_data[2:]
                        if not any(
                            obj["location"] == location for obj in filtered_objects
                        ):
                            if detection_class == "cup" and detection_score >= 0.5:
                                uid = get_next_uid(objects_data, "coffee-table")
                                data = dict_to_object(
                                    uid,
                                    [0.002, 0.002, 0.001],
                                    location,
                                    rotation,
                                    "coffee-table.obj",
                                )
                                objects_data.append(data)
                            elif detection_class == "chair" and detection_score >= 0.5:
                                uid = get_next_uid(objects_data, "couch")
                                data = dict_to_object(
                                    uid,
                                    [0.002, 0.002, 0.002],
                                    location,
                                    rotation,
                                    "couch.obj",
                                )
                                objects_data.append(data)

                last_detection_time = current_time

            frame_with_background = background.copy()

            face_results = face_mesh.process(rgb_frame)

            if face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    for index, landmark in enumerate(face_landmarks.landmark):
                        y = int(landmark.y * frame.shape[0])
                        if index == 234:
                            face_left_location = y
                        elif index == 454:
                            face_right_location = y

                        if face_left_location and face_right_location:
                            diff = face_left_location - face_right_location
                            if diff > 50 and not head_rotation:
                                head_rotation = True
                                if side < 3:
                                    side += 1
                                else:
                                    side = 0
                            elif diff < -50 and not head_rotation:
                                if side == 0:
                                    side = 3
                                else:
                                    side -= 1
                                head_rotation = True
                            elif diff > -50 and diff < 50:
                                head_rotation = False

                        objects_data[1]["side"] = side

            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                    thumb = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_CMC]
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    index_fingertip = hand_landmarks.landmark[
                        mp_hands.HandLandmark.INDEX_FINGER_TIP
                    ]

                    thumb_x, thumb_y = int(thumb_tip.x * FRAME_WIDTH), int(
                        thumb_tip.y * FRAME_HEIGHT
                    )
                    index_x, index_y = int(index_fingertip.x * FRAME_WIDTH), int(
                        index_fingertip.y * FRAME_HEIGHT
                    )
                    distance = sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)

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
                            (0, 0, 255),
                            2,
                        )

                    for idx, landmark in enumerate(hand_landmarks.landmark):
                        x = int(landmark.x * FRAME_WIDTH)
                        y = int(landmark.y * FRAME_HEIGHT)
                        cv2.circle(frame_with_background, (x, y), 5, (0, 0, 255), -1)

                    if selected_axis is None:
                        if wrist.x < thumb.x:
                            if selected_object_index < len(objects_data) - 3:
                                if old_l_wrist_x is None:
                                    old_l_wrist_x = wrist.x
                                else:
                                    wrist_x_diff = wrist.x - old_l_wrist_x
                                    if wrist_x_diff > 0.25:
                                        selected_object_index += 1
                                        old_l_wrist_x = wrist.x
                        elif wrist.x > thumb.x and selected_object_index > 0:
                            if old_r_wrist_x is None:
                                old_r_wrist_x = wrist.x
                            else:
                                wrist_x_diff = old_r_wrist_x - wrist.x
                                if wrist_x_diff > 0.25:
                                    selected_object_index -= 1
                                    old_r_wrist_x = wrist.x

                    if scale:
                        if wrist.x > thumb.x and distance < 50:
                            grabbed = True
                        elif wrist.x > thumb.x and distance > 50:
                            grabbed = False

                        if (
                            grabbed
                            and wrist.x < thumb.x
                            and 0 <= selected_object_index < len(objects_data)
                        ):
                            selected_object = objects_data[selected_object_index + 2]

                            scale_size = round(distance / 10000, 4)

                            if selected_axis == "x":
                                selected_object["dimensions"][0] = scale_size
                            elif selected_axis == "y":
                                selected_object["dimensions"][1] = scale_size
                            elif selected_axis == "z":
                                selected_object["dimensions"][2] = scale_size
                    else:
                        if 0 <= selected_object_index < len(objects_data):
                            selected_object = objects_data[selected_object_index + 2]
                            if wrist.x > thumb.x and distance < 50:
                                if (
                                    "initial_thumb_x" not in selected_object
                                    or "initial_thumb_y" not in selected_object
                                    or selected_object["initial_thumb_x"] is None
                                    or selected_object["initial_thumb_y"] is None
                                ):
                                    selected_object["initial_thumb_x"] = thumb.x
                                    selected_object["initial_thumb_y"] = thumb.y

                                delta_x = thumb.x - selected_object["initial_thumb_x"]
                                delta_y = thumb.y - selected_object["initial_thumb_y"]

                                if selected_axis == "x":
                                    location_x = round(
                                        selected_object["location"][0] + delta_x, 2
                                    )

                                    if "couch" in selected_object["uid"]:
                                        if location_x > 6:
                                            location_x = 6

                                        if location_x < -6:
                                            location_x = -6
                                    elif "coffee-table" in selected_object["uid"]:
                                        if location_x > 5.8:
                                            location_x = 5.8

                                        if location_x < -5.8:
                                            location_x = -5.8

                                    selected_object["location"][0] = location_x
                                elif selected_axis == "y":
                                    location_y = round(
                                        selected_object["location"][1] + delta_x, 2
                                    )

                                    if "couch" in selected_object["uid"]:
                                        if location_y > 6:
                                            location_y = 6

                                        if location_y < -6:
                                            location_y = -6
                                    elif "coffee-table" in selected_object["uid"]:
                                        if location_y > 5.8:
                                            location_y = 5.8

                                        if location_y < -5.8:
                                            location_y = -5.8

                                    selected_object["location"][1] = location_y
                                elif selected_axis == "z":
                                    location_z = round(
                                        selected_object["location"][2] - delta_y, 2
                                    )
                                    if location_z < 0.1:
                                        location_z = 0.1

                                    if location_z > 2.5:
                                        location_z = 2.5

                                    selected_object["location"][2] = location_z
                            elif wrist.x > thumb.x and distance > 50:
                                selected_object["initial_thumb_x"] = None
                                selected_object["initial_thumb_y"] = None

            else:
                old_l_wrist_x = None
                old_r_wrist_x = None

            frame_with_background = display_objects_grid(
                frame_with_background, objects_data
            )

            cv2.imshow("Hand Detection", frame_with_background)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                save_objects_data(objects_data)
                break
            elif key == ord("x"):
                selected_axis = "x"
            elif key == ord("y"):
                selected_axis = "y"
            elif key == ord("z"):
                selected_axis = "z"
            elif key == ord("c"):
                selected_axis = None
            elif key == ord("s"):
                scale = not scale

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
