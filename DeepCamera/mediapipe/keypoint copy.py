import cv2
import mediapipe as mp
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils
pose = mp_pose.Pose()

# 创建3D图表
plt.ion()  # 开启交互模式
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        continue

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)

    if results.pose_landmarks:
        # 2D可视化
        mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # 3D可视化
        ax.clear()
        landmarks = results.pose_landmarks.landmark
        
        # 收集所有关键点的坐标
        x = [landmark.x for landmark in landmarks]
        y = [landmark.y for landmark in landmarks]
        z = [landmark.z for landmark in landmarks]
        
        # 绘制3D散点图
        ax.scatter(x, y, z, c='red', marker='o')
        
        # 绘制连线
        for connection in mp_pose.POSE_CONNECTIONS:
            start_idx = connection[0]
            end_idx = connection[1]
            ax.plot([x[start_idx], x[end_idx]],
                   [y[start_idx], y[end_idx]],
                   [z[start_idx], z[end_idx]], 'b-')
        
        # 设置坐标轴
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('3D Pose Landmarks')
        
        # 设置坐标轴范围
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_zlim(-1, 1)
        
        # 设置观察角度以便更好地观察
        ax.view_init(elev=10, azim=45)
        
        # 更新图表
        plt.draw()
        plt.pause(0.001)

    cv2.imshow('MediaPipe Pose', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
plt.close()
