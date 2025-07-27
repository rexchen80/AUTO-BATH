import socket
import json
from ultralytics import YOLO
import cv2
import numpy as np
import time

# Unity connection settings
UNITY_IP = '30.201.209.68'
UNITY_PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 添加数据传输统计
class TransmissionStats:
    def __init__(self):
        self.packets_sent = 0
        self.last_send_time = 0
        self.send_fps = 0
        
    def update(self):
        current_time = time.time()
        if self.last_send_time > 0:
            self.send_fps = 1 / (current_time - self.last_send_time)
        self.last_send_time = current_time
        self.packets_sent += 1
        
    def get_stats(self):
        return f"Packets: {self.packets_sent}, Send FPS: {self.send_fps:.1f}"

stats = TransmissionStats()

def validate_skeleton_data(data):
    """验证骨骼数据的格式是否正确"""
    try:
        if not isinstance(data, dict):
            return False, "数据必须是字典格式"
        
        if "landmarks" not in data:
            return False, "缺少landmarks字段"
            
        landmarks = data["landmarks"]
        if not isinstance(landmarks, dict):
            return False, "landmarks必须是字典格式"
            
        # 检查所有值是否为有效的坐标
        for idx, coords in landmarks.items():
            if not isinstance(coords, list) or len(coords) != 3:
                return False, f"landmark {idx} 必须是包含3个坐标的列表"
                
        return True, "数据格式正确"
    except Exception as e:
        return False, f"验证时发生错误: {str(e)}"

def send_to_unity(data):
    """发送数据到Unity并处理可能的错误"""
    try:
        # 验证数据格式
        is_valid, message = validate_skeleton_data(data)
        if not is_valid:
            print(f"数据验证失败: {message}")
            return False
            
        # 转换为JSON并发送
        json_str = json.dumps(data)
        sock.sendto(json_str.encode('utf-8'), (UNITY_IP, UNITY_PORT))
        
        # 更新统计信息
        stats.update()
        return True
        
    except socket.error as e:
        print(f"发送数据时发生网络错误: {str(e)}")
        return False
    except Exception as e:
        print(f"发送数据时发生未知错误: {str(e)}")
        return False

# YOLO keypoint names
YOLO_KEYPOINT_NAMES = {
    0: "nose",
    1: "left_eye",
    2: "right_eye",
    3: "left_ear",
    4: "right_ear",
    5: "left_shoulder",
    6: "right_shoulder",
    7: "left_elbow",
    8: "right_elbow",
    9: "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip",
    13: "left_knee",
    14: "right_knee",
    15: "left_ankle",
    16: "right_ankle",
    17: "left_foot",
    18: "right_foot"
}

def draw_keypoint_label(frame, x, y, label, confidence):
    """Helper function to draw keypoint label with background"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    
    (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
    
    padding = 2
    rect_x = x + 5
    rect_y = y - text_height - padding
    
    cv2.rectangle(frame, 
                 (rect_x, rect_y), 
                 (rect_x + text_width + 2*padding, rect_y + text_height + 2*padding), 
                 (0, 0, 0), 
                 -1)
    
    cv2.putText(frame, 
                label, 
                (rect_x + padding, rect_y + text_height + padding), 
                font, 
                font_scale, 
                (255, 255, 255), 
                font_thickness)

def create_skeleton_data(keypoints):
    """Convert keypoints to Unity format using YOLO keypoints directly"""
    landmarks = {}
    
    for i, kpt in enumerate(keypoints):
        x, y = float(kpt[0]), float(kpt[1])
        confidence = float(kpt[2]) if len(kpt) > 2 else 1.0
        
        if confidence > 0.5:  # Only include keypoints with confidence > 0.5
            # Convert to Unity coordinate system
            unity_x = x
            unity_y = -y  # Flip Y coordinate for Unity
            unity_z = 0.0
            
            landmarks[i] = [unity_x, unity_y, unity_z]
    
    return {"landmarks": landmarks}

# 加载两个模型
model_pose = YOLO("yolo11l-pose.pt")  # 关键点检测模型
model_seg = YOLO("yolo11l-seg.pt")   # 分割模型

# 打开摄像头
cap = cv2.VideoCapture(1)  # 使用ID=1的摄像头

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 初始化FPS计算变量
prev_time = 0
curr_time = 0

try:
    while True:
        # 读取视频帧
        ret, frame = cap.read()
        if not ret:
            print("无法获取视频帧")
            break

        # 计算FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time

        # 使用分割模型进行预测
        results_seg = model_seg(frame)
        result_seg = results_seg[0]
        
        # 创建一个掩码，只保留人物类别，并选择最靠近的人物
        person_masks = []
        person_boxes = []
        person_confs = []
        if result_seg.masks is not None:
            for mask, box, cls, conf in zip(result_seg.masks.data, result_seg.boxes.data, result_seg.boxes.cls, result_seg.boxes.conf):
                if result_seg.names[int(cls)] == 'person':  # 只保留人物类别
                    person_masks.append(mask.cpu().numpy())
                    person_boxes.append(box.cpu().numpy())  # [x1, y1, x2, y2, conf, class]
                    person_confs.append(conf.cpu().numpy())

        # 如果检测到人物，选择最靠近且置信度最高的人物
        if person_masks:
            # 计算每个边界框的面积（越大表示越靠近）
            areas = [(box[2] - box[0]) * (box[3] - box[1]) for box in person_boxes]
            # 结合面积和置信度的综合得分
            scores = [area * conf for area, conf in zip(areas, person_confs)]
            # 选择得分最高的人物
            best_idx = np.argmax(scores)
            
            # 只保留最佳人物的掩码，并确保是布尔类型
            best_mask = person_masks[best_idx].astype(bool)
            
            # 创建一个半透明的遮罩
            overlay = frame.copy()
            overlay[~best_mask] = [0, 0, 0]  # 非人物区域设为黑色
            
            # 合并原始图像和遮罩
            alpha = 0.6
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # 使用关键点检测模型进行预测
        results_pose = model_pose(frame)

        # 在分割后的图像上绘制关键点，只处理置信度最高的人物
        best_confidence = 0
        best_keypoints = None
        
        for result in results_pose:
            if result.keypoints.data is not None and len(result.keypoints.data) > 0:
                kpts = result.keypoints.data[0]  # 获取关键点
                # 计算平均置信度
                avg_confidence = float(kpts[:, 2].mean())
                
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    best_keypoints = kpts
        
        # 只绘制最佳关键点
        if best_keypoints is not None:
            # 创建骨架数据
            skeleton_data = create_skeleton_data(best_keypoints)
            
            # 发送数据到Unity
            if send_to_unity(skeleton_data):
                print(f"Sent data to Unity. Stats: {stats.get_stats()}")
            else:
                print(f"Failed to send data to Unity. Stats: {stats.get_stats()}")
            
            # 绘制每个关键点
            for i, kpt in enumerate(best_keypoints):
                x, y = int(kpt[0]), int(kpt[1])
                confidence = kpt[2] if len(kpt) > 2 else 1.0
                
                # 根据置信度使用不同颜色绘制关键点
                color = (0, int(255 * confidence), int(255 * (1 - confidence)))
                cv2.circle(frame, (x, y), 5, color, -1)
                
                # 绘制关键点标签
                label = YOLO_KEYPOINT_NAMES.get(i, f"Point {i}")
                draw_keypoint_label(frame, x, y, f"{label} ({confidence:.2f})", confidence)

        # 在画面上显示FPS
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 显示结果
        cv2.imshow("人物分割和关键点检测", frame)

        # 按'q'键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # 释放资源
    cap.release()
    cv2.destroyAllWindows() 