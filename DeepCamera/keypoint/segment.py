from ultralytics import YOLO
import cv2
import numpy as np

# 加载模型
model = YOLO("yolo11l-seg.pt")  # 加载官方模型

# 打开摄像头
cap = cv2.VideoCapture(1)  # 使用ID=1的摄像头

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

try:
    while True:
        # 读取视频帧
        ret, frame = cap.read()
        if not ret:
            print("无法获取视频帧")
            break

        # 使用模型进行预测
        results = model(frame)
        
        # 获取结果
        result = results[0]
        
        # 创建一个掩码，只保留人物类别
        person_masks = []
        person_boxes = []
        person_confs = []
        if result.masks is not None:
            for mask, box, cls, conf in zip(result.masks.data, result.boxes.data, result.boxes.cls, result.boxes.conf):
                if result.names[int(cls)] == 'person':  # 只保留人物类别
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

        # 显示结果
        cv2.imshow("人物分割", frame)

        # 按'q'键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()