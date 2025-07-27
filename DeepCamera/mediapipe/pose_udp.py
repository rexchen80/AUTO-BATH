import cv2
import mediapipe as mp
import numpy as np
from openni import openni2
from openni import _openni2 as c_api
import os
import sys
import socket
import json
import time

# 设置OpenNI2的DLL路径
OPENNI_DLL_PATH = r"C:\Users\ASUS\Desktop\mediapipe\OrbbecViewer"

# UDP通信设置
UDP_IP = "172.20.10.2"  # 本地回环地址
UDP_PORT = 62345       # 端口号

# 相机参数
class CameraParams:
    # IR相机内参
    IR_FX = 477.926
    IR_FY = 477.926
    IR_CX = 322.908
    IR_CY = 200.439
    
    # RGB相机内参
    RGB_FX = 453.522
    RGB_FY = 453.522
    RGB_CX = 324.408
    RGB_CY = 245.338
    
    # 外参 - 旋转矩阵
    R = np.array([
        [0.99999, 0.00293038, 0.00323079],
        [-0.00292299, 0.999993, -0.00229206],
        [-0.00323749, 0.00228259, 0.999992]
    ])
    
    # 外参 - 平移向量 (mm)
    T = np.array([-9.86164, 0.0916355, -0.443493]) / 1000.0  # 转换为米

    # 畸变参数
    k1 = 0
    k2 = 0
    k3 = 0
    p1 = 0
    p2 = 0

def get_world_coordinates(x_rgb, y_rgb, depth, params):
    """
    将RGB图像坐标和深度值转换为世界坐标系下的3D坐标（左手坐标系）
    x_rgb, y_rgb: RGB图像坐标（像素）
    depth: 深度值(mm)
    返回：左手坐标系下的3D坐标 (X, Y, Z)，单位：m
    X: 向右为正
    Y: 向上为正
    Z: 向前为正
    """
    # 将深度值转换为米
    depth_m = depth / 1000.0
    
    # 1. RGB图像坐标转换到RGB相机坐标系
    # 注意：图像坐标系原点在左上角，Y轴向下为正
    # 需要将Y轴翻转使其向上为正
    X_rgb = (x_rgb - params.RGB_CX) * depth_m / params.RGB_FX
    Y_rgb = -(y_rgb - params.RGB_CY) * depth_m / params.RGB_FY  # 翻转Y轴
    Z_rgb = depth_m

    # 2. RGB相机坐标系转换到深度相机坐标系（世界坐标系）
    R_inv = np.linalg.inv(params.R)
    XYZ_rgb = np.array([X_rgb, Y_rgb, Z_rgb])
    XYZ_world = np.dot(R_inv, (XYZ_rgb - params.T))
    
    return XYZ_world

def rgb_to_depth_point(x_rgb, y_rgb, depth, params):
    """
    将RGB图像坐标转换到深度图像坐标
    x_rgb, y_rgb: RGB图像坐标（像素）
    depth: 深度值(mm)
    返回：深度图像坐标 (x_depth, y_depth)
    """
    # 1. 获取世界坐标
    XYZ_world = get_world_coordinates(x_rgb, y_rgb, depth, params)
    
    # 2. 世界坐标投影到深度图像平面
    x_depth = params.IR_FX * XYZ_world[0] / XYZ_world[2] + params.IR_CX
    y_depth = -params.IR_FY * XYZ_world[1] / XYZ_world[2] + params.IR_CY  # 注意Y轴方向
    
    return int(x_depth), int(y_depth)

# MediaPipe初始化
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils
pose = mp_pose.Pose()

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

def initialize_openni():
    """初始化OpenNI设备"""
    try:
        if not os.path.exists(os.path.join(OPENNI_DLL_PATH, "OpenNI2.dll")):
            raise FileNotFoundError(f"OpenNI2.dll not found in {OPENNI_DLL_PATH}")
        
        openni2.initialize(OPENNI_DLL_PATH)
        dev = openni2.Device.open_any()
        
        if dev is None:
            raise RuntimeError("No OpenNI device found")
            
        print("成功连接到深度相机")
        print(f"设备信息: {dev.get_device_info()}")
        
        return dev
    except Exception as e:
        print(f"深度相机初始化失败: {str(e)}")
        sys.exit(1)

def start_depth_stream(device):
    """只启动深度流"""
    try:
        depth_stream = device.create_depth_stream()
        if depth_stream is None:
            raise RuntimeError("Failed to create depth stream")
        
        # 配置深度流
        print("正在配置深度流...")
        depth_stream.set_video_mode(c_api.OniVideoMode(
            pixelFormat=c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM,
            resolutionX=640,
            resolutionY=480,
            fps=30
        ))
        
        depth_stream.start()
        print("深度流启动成功")
        return depth_stream
        
    except Exception as e:
        print(f"深度流启动失败: {str(e)}")
        if 'depth_stream' in locals() and depth_stream is not None:
            depth_stream.stop()
        device.close()
        openni2.unload()
        sys.exit(1)

def main():
    try:
        # 初始化UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"UDP发送端已启动 - {UDP_IP}:{UDP_PORT}")
        
        # 初始化RGB相机
        print("正在初始化RGB相机...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("无法打开RGB相机")
        
        # 设置RGB相机分辨率
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # 初始化深度相机
        print("正在初始化深度相机...")
        device = initialize_openni()
        depth_stream = start_depth_stream(device)
        camera_params = CameraParams()
        
        print("所有设备初始化完成")
        print("左手坐标系：X向右为正，Y向上为正，Z向前为正")
        
        frame_count = 0
        
        while True:
            # 读取RGB图像
            ret, color_frame = cap.read()
            if not ret:
                print("无法读取RGB图像")
                continue
            
            # 读取深度图像
            depth_frame = depth_stream.read_frame()
            if depth_frame is None:
                print("无法读取深度图像")
                continue
            
            # 处理深度数据
            depth_data = depth_frame.get_buffer_as_uint16()
            depth_array = np.frombuffer(depth_data, dtype=np.uint16)
            depth_array = depth_array.reshape(480, 640)
            
            # MediaPipe处理
            frame_rgb = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)
            
            if results.pose_landmarks:
                # 准备发送的数据
                landmarks_data = []
                
                for idx, landmark in enumerate(results.pose_landmarks.landmark):
                    # 只处理选定的关键点
                    if idx not in SELECTED_LANDMARKS:
                        continue
                        
                    # 获取RGB图像中的坐标（像素坐标）
                    x_px = int(landmark.x * 640)
                    y_px = int(landmark.y * 480)
                    
                    # 确保坐标在有效范围内
                    x_px = max(0, min(x_px, 639))
                    y_px = max(0, min(y_px, 479))
                    
                    # 获取深度图中对应的坐标
                    x_depth, y_depth = rgb_to_depth_point(x_px, y_px, 1000, camera_params)  # 初始深度估计为1米
                    
                    # 确保深度图坐标在有效范围内
                    x_depth = max(0, min(x_depth, 639))
                    y_depth = max(0, min(y_depth, 479))
                    
                    # 获取实际深度值
                    depth_value = depth_array[y_depth, x_depth]
                    
                    if depth_value > 0:
                        # 使用实际深度值重新计算世界坐标
                        world_coords = get_world_coordinates(x_px, y_px, depth_value, camera_params)
                        
                        # 添加关键点数据
                        landmark_info = {
                            "id": idx,
                            "x": float(world_coords[0]),  # 转换为float以便JSON序列化
                            "y": float(world_coords[1]),
                            "z": float(world_coords[2])
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
            
            # 检查退出条件
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n正在清理资源...")
        if 'cap' in locals():
            cap.release()
        if 'depth_stream' in locals() and depth_stream is not None:
            depth_stream.stop()
        if 'device' in locals() and device is not None:
            device.close()
        openni2.unload()
        cv2.destroyAllWindows()
        print(f"程序已退出，共处理 {frame_count} 帧")

if __name__ == "__main__":
    main() 