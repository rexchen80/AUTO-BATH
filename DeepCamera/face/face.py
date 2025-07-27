import cv2
import numpy as np
from ultralytics import YOLO

# 加载YOLO姿态检测模型
pose_model = YOLO("yolo11l-pose.pt")

# 加载OpenCV预训练的人脸检测器
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
# 加载眼睛检测器
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
# 加载笑容检测器
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

def get_best_person(pose_results):
    """获取置信度最高的人"""
    try:
        if len(pose_results) > 0:
            result = pose_results[0]
            if hasattr(result.boxes, 'conf'):
                # 获取所有人的置信度
                confs = result.boxes.conf.cpu().numpy()
                # 获取置信度最高的人的索引
                best_idx = np.argmax(confs)
                return result, best_idx, confs[best_idx]
    except Exception as e:
        print(f"Error in get_best_person: {e}")
    return None, None, 0

def analyze_head_pose(keypoints):
    """分析头部姿态"""
    try:
        # 确保关键点数据在CPU上并转换为numpy
        keypoints_np = keypoints.cpu().numpy()
        
        # 获取头部关键点
        if len(keypoints_np) >= 5:
            left_eye = keypoints_np[1]
            right_eye = keypoints_np[2]
            
            # 只在置信度高的情况下计算角度
            if left_eye[2] > 0.5 and right_eye[2] > 0.5:
                dx = right_eye[0] - left_eye[0]
                dy = right_eye[1] - left_eye[1]
                angle = np.degrees(np.arctan2(dy, dx))
                return angle, True
    except Exception as e:
        print(f"Error in analyze_head_pose: {e}")
    return 0, False

def detect_expression(frame, face, keypoints):
    """检测表情"""
    x, y, w, h = face
    roi_gray = gray[y:y+h, x:x+w]
    
    # 检测眼睛和笑容
    eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 15)
    smiles = smile_cascade.detectMultiScale(roi_gray, 1.7, 20)
    
    # 获取头部姿态
    head_angle, angle_valid = analyze_head_pose(keypoints)
    
    # 分析表情
    expression = "Neutral"
    confidence = 0.5  # 基础置信度
    
    # 根据多个特征判断表情
    if len(smiles) > 0:
        expression = "Happy"
        confidence = 0.8
    elif len(eyes) < 2:
        expression = "Blink"
        confidence = 0.7
        
    return expression, confidence, eyes, smiles, head_angle

# 打开摄像头
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 转换为灰度图
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    try:
        # YOLO姿态检测
        pose_results = pose_model(frame)
        
        # 获取置信度最高的人
        result, best_idx, person_conf = get_best_person(pose_results)
        
        if result is not None and best_idx is not None and person_conf > 0.5:
            # 获取最佳人选的关键点
            keypoints = result.keypoints.data[best_idx]
            
            # OpenCV人脸检测
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # 选择最大的人脸（假设最大的人脸属于置信度最高的人）
                face = max(faces, key=lambda x: x[2] * x[3])
                x, y, w, h = face
                
                # 分析表情
                expression, confidence, eyes, smiles, head_angle = detect_expression(frame, face, keypoints)
                
                # 绘制人脸框
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # 绘制眼睛
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (255, 0, 0), 2)
                
                # 绘制笑容
                for (sx, sy, sw, sh) in smiles:
                    cv2.rectangle(frame, (x+sx, y+sy), (x+sx+sw, y+sy+sh), (0, 0, 255), 2)
                
                # 显示表情和人物置信度
                text = f"{expression} ({confidence:.2f}) Person: {person_conf:.2f}"
                cv2.putText(frame, text, (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                
                # 显示头部角度
                angle_text = f"Head Angle: {head_angle:.1f}"
                cv2.putText(frame, angle_text, (x, y+h+25), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # 绘制关键点
                keypoints_np = keypoints.cpu().numpy()
                for kp in keypoints_np:
                    if kp[2] > 0.5:  # 只显示置信度高的关键点
                        x, y = int(kp[0]), int(kp[1])
                        cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
    
    except Exception as e:
        print(f"Error in main loop: {e}")
    
    # 显示结果
    cv2.imshow("Face Expression", frame)
    
    # 按q退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()