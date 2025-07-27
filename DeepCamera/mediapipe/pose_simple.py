import cv2
import mediapipe as mp
import numpy as np
import socket
import json

# UDP通信设置
UDP_IP = "172.20.10.2"  # 本地回环地址
UDP_PORT = 62345       # 端口号

# 定义需要的关键点
SELECTED_LANDMARKS = {
    0: "NOSE",
    11: "LEFT_SHOULDER",
    12: "RIGHT_SHOULDER",
    13: "LEFT_ELBOW",
    14: "RIGHT_ELBOW",
    15: "LEFT_WRIST",
    16: "RIGHT_WRIST",
    23: "LEFT_HIP",
    24: "RIGHT_HIP",
    25: "LEFT_KNEE",
    26: "RIGHT_KNEE",
    27: "LEFT_ANKLE",
    28: "RIGHT_ANKLE"
}

def Pose_Images():
    # 初始化UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"UDP发送端已启动 - {UDP_IP}:{UDP_PORT}")
    
    #使用算法包进行姿态估计时设置的参数
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    frame_count = 0
    
    with mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.8) as pose:
        #打开摄像头
        cap = cv2.VideoCapture(1)
        
        # 设置摄像头分辨率
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        while(True):
            #读取摄像头图像
            hx, image = cap.read() 
            if hx is False:
                print('read video error')
                exit(0)
                
            image.flags.writeable = False
            # Convert the BGR image to RGB before processing.
            # 姿态估计
            results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # 如果检测到姿态关键点
            if results.pose_landmarks:
                image.flags.writeable = True
                # 准备发送的数据
                landmarks_data = []
                
                # 处理选定的关键点
                for idx, landmark in enumerate(results.pose_landmarks.landmark):
                    if idx in SELECTED_LANDMARKS:
                        # 在图像上标记关键点
                        h, w, c = image.shape
                        cx, cy = int(landmark.x * w), int(landmark.y * h)
                        cv2.circle(image, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
                        cv2.putText(image, SELECTED_LANDMARKS[idx], (cx + 10, cy + 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                        
                        # 添加关键点数据（使用相对坐标）
                        landmark_info = {
                            "id": idx,
                            "x": float(landmark.x),
                            "y": float(landmark.y),
                            "z": float(landmark.z)
                        }
                        landmarks_data.append(landmark_info)
                
                # 构建完整的数据包
                data_packet = {
                    "frame": frame_count,
                    "landmarks": landmarks_data
                }
                
                # 转换为JSON字符串并发送
                json_data = json.dumps(data_packet)
                sock.sendto(json_data.encode(), (UDP_IP, UDP_PORT))
                
                # 打印发送信息
                print(f"\r已发送第 {frame_count} 帧数据，包含 {len(landmarks_data)} 个关键点", end="")
                
                frame_count += 1
                
            cv2.imshow('image', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):       # 按q退出
                break
                
        print("\n正在清理资源...")
        cap.release()
        cv2.destroyAllWindows()
        print(f"程序已退出，共处理 {frame_count} 帧")


if __name__ == '__main__':
    Pose_Images()
