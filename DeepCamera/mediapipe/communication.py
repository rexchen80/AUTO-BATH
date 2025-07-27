import socket
import json

UDP_IP = "30.201.209.68"
UDP_PORT = 62345
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_mediapipe_landmarks(landmarks, frame_id=0):
    data = {
        "frame": frame_id,
        "landmarks": [
            {"id": idx, "x": lm.x, "y": lm.y, "z": lm.z}
            for idx, lm in enumerate(landmarks)
        ]
    }
    packet = json.dumps(data)
    sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
