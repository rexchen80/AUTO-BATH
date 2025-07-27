from ultralytics import YOLO
import cv2
import numpy as np
from openni import openni2
from openni import _openni2 as c_api
import os
import time

# OpenNI2 DLL路径
OPENNI_DLL_PATH = r"C:\Users\ASUS\Desktop\keypoint3d\OrbbecViewer"

# 相机内参和外参
class CameraParams:
    def __init__(self):
        # 相机内参 (根据实际输出更新)
        self.width = 640
        self.height = 400
        self.fx = 945.028
        self.fy = 945.028
        self.cx = 640
        self.cy = 400
        self.baseline = 40
        
        # 外参 - 旋转矩阵
        self.R = np.array([
            [0.99999, 0.00293038, 0.00323079],
            [-0.00292299, 0.999993, -0.00229206],
            [-0.00323749, 0.00228259, 0.999992]
        ])
        
        # 外参 - 平移向量 (mm)
        self.T = np.array([[-9.86164], [0.0916355], [-0.443493]])

# Keypoint index mapping
KEYPOINT_DICT = {
    0: "Nose",
    1: "Left Eye",
    2: "Right Eye",
    3: "Left Ear",
    4: "Right Ear",
    5: "Left Shoulder",
    6: "Right Shoulder",
    7: "Left Elbow",
    8: "Right Elbow",
    9: "Left Wrist",
    10: "Right Wrist",
    11: "Left Hip",
    12: "Right Hip",
    13: "Left Knee",
    14: "Right Knee",
    15: "Left Ankle",
    16: "Right Ankle"
}

def calculate_angle(point1, point2, point3):
    """
    计算三个3D点形成的角度
    point2是角的顶点
    返回角度(度)
    """
    vector1 = point1 - point2
    vector2 = point3 - point2
    
    # 计算向量的点积
    dot_product = np.dot(vector1, vector2)
    # 计算向量的模
    norm1 = np.linalg.norm(vector1)
    norm2 = np.linalg.norm(vector2)
    
    # 计算角度（弧度）
    cos_angle = dot_product / (norm1 * norm2)
    # 确保cos_angle在[-1, 1]范围内
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle_rad = np.arccos(cos_angle)
    
    # 转换为角度
    angle_deg = np.degrees(angle_rad)
    return angle_deg

def calculate_joint_angles(keypoints_3d):
    """
    计算主要关节的角度
    keypoints_3d: 包含所有关键点3D坐标的字典
    返回各个关节的角度
    """
    angles = {}
    
    # 确保所有需要的关键点都存在
    required_points = ["Left Shoulder", "Left Elbow", "Left Wrist",
                      "Right Shoulder", "Right Elbow", "Right Wrist",
                      "Left Hip", "Left Knee", "Left Ankle",
                      "Right Hip", "Right Knee", "Right Ankle"]
                      
    if all(point in keypoints_3d for point in required_points):
        # 计算左肘角度
        angles["Left Elbow"] = calculate_angle(
            keypoints_3d["Left Shoulder"],
            keypoints_3d["Left Elbow"],
            keypoints_3d["Left Wrist"]
        )
        
        # 计算右肘角度
        angles["Right Elbow"] = calculate_angle(
            keypoints_3d["Right Shoulder"],
            keypoints_3d["Right Elbow"],
            keypoints_3d["Right Wrist"]
        )
        
        # 计算左膝角度
        angles["Left Knee"] = calculate_angle(
            keypoints_3d["Left Hip"],
            keypoints_3d["Left Knee"],
            keypoints_3d["Left Ankle"]
        )
        
        # 计算右膝角度
        angles["Right Knee"] = calculate_angle(
            keypoints_3d["Right Hip"],
            keypoints_3d["Right Knee"],
            keypoints_3d["Right Ankle"]
        )
        
    return angles

def initialize_device():
    """初始化设备并进行错误检查"""
    try:
        # 检查OpenNI2.dll是否存在
        if not os.path.exists(os.path.join(OPENNI_DLL_PATH, "OpenNI2.dll")):
            raise FileNotFoundError(f"OpenNI2.dll not found in {OPENNI_DLL_PATH}")
        
        # 初始化OpenNI2
        openni2.initialize(OPENNI_DLL_PATH)
        print("OpenNI2初始化成功")
        
        # 等待设备连接
        for i in range(5):  # 最多尝试5次
            try:
                dev = openni2.Device.open_any()
                if dev is not None:
                    print("成功连接到设备")
                    return dev
            except Exception as e:
                print(f"尝试{i+1}/5: 连接设备失败，等待重试...")
                time.sleep(1)
        
        raise Exception("无法连接到设备，请检查设备连接")
        
    except Exception as e:
        print(f"设备初始化失败: {str(e)}")
        raise

def configure_depth_stream(depth_stream):
    """配置深度流的参数"""
    try:
        # 设置视频模式
        depth_stream.set_video_mode(c_api.OniVideoMode(
            pixelFormat=c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM,
            resolutionX=640,
            resolutionY=400,
            fps=30
        ))
        print("深度流配置成功")
        return True
    except Exception as e:
        print(f"深度流配置失败: {str(e)}")
        return False

def start_depth_stream(device):
    """启动深度数据流"""
    try:
        # 创建深度流
        depth_stream = device.create_depth_stream()
        if depth_stream is None:
            raise Exception("无法创建深度流")
        
        # 配置深度流
        if not configure_depth_stream(depth_stream):
            raise Exception("深度流配置失败")
        
        # 启动深度流
        depth_stream.start()
        print("深度流启动成功")
        
        return depth_stream
        
    except Exception as e:
        print(f"深度流启动失败: {str(e)}")
        if 'depth_stream' in locals() and depth_stream is not None:
            depth_stream.stop()
        raise

def initialize_color_stream():
    """初始化彩色相机流"""
    try:
        cap = cv2.VideoCapture(0)  # 使用camera ID 1
        if not cap.isOpened():
            raise Exception("无法打开彩色相机")
        
        # 设置分辨率
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 400)
        print("彩色相机初始化成功")
        return cap
    except Exception as e:
        print(f"彩色相机初始化失败: {str(e)}")
        raise

def pixel_to_point(x, y, depth, params):
    """
    将像素坐标和深度值转换为相机坐标系下的3D点
    """
    # 反投影得到相机坐标系下的点
    z = float(depth)
    x = (x - params.cx) * z / params.fx
    y = (y - params.cy) * z / params.fy
    return np.array([[x], [y], [z]])

def rgb_to_world(point_rgb, params):
    """
    将RGB相机坐标系下的点转换到世界坐标系
    """
    # 使用外参将RGB相机坐标系下的点转换到世界坐标系
    point_world = np.dot(params.R, point_rgb) + params.T
    return point_world

def get_3d_coordinates(x_pixel, y_pixel, depth, params):
    """
    获取像素点在世界坐标系下的3D坐标
    """
    # 首先转换到相机坐标系
    point_camera = pixel_to_point(x_pixel, y_pixel, depth, params)
    # 然后转换到世界坐标系
    point_world = rgb_to_world(point_camera, params)
    return point_world.flatten()

def main():
    device = None
    depth_stream = None
    color_cap = None
    
    try:
        print("正在初始化3D姿态检测系统...")
        
        # 初始化相机参数
        camera_params = CameraParams()
        
        # 初始化深度设备和数据流
        device = initialize_device()
        depth_stream = start_depth_stream(device)
        
        # 初始化彩色相机
        color_cap = initialize_color_stream()
        
        # 加载YOLO模型
        print("正在加载YOLO模型...")
        model = YOLO("yolo11l-pose.pt")
        print("模型加载完成")
        
        print("系统初始化完成，按'q'键退出")
        
        while True:
            # 读取彩色帧
            ret, rgb_frame = color_cap.read()
            if not ret:
                print("无法读取彩色帧")
                break
            
            # 读取深度帧
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
            depth_data.shape = (camera_params.height, camera_params.width)
            
            # YOLO姿态检测
            results = model(rgb_frame)
            
            # 处理检测结果
            for result in results:
                keypoints = result.keypoints.data  # 获取关键点数据 [x, y, confidence]
                
                # 存储所有关键点的3D坐标
                keypoints_3d = {}
                nose_coords = None
                
                # 首先获取鼻子的3D坐标作为原点
                nose_kpt = keypoints[0][0]  # 鼻子是第一个关键点
                if nose_kpt[2] > 0.5:  # 确保置信度足够高
                    x_int, y_int = int(nose_kpt[0]), int(nose_kpt[1])
                    if (0 <= y_int < camera_params.height and 
                        0 <= x_int < camera_params.width):
                        nose_depth = depth_data[y_int, x_int]
                        nose_coords = get_3d_coordinates(x_int, y_int, nose_depth, camera_params)
                
                # 如果检测到鼻子，处理其他关键点
                if nose_coords is not None:
                    keypoints_3d["Nose"] = np.array([0, 0, 0])  # 鼻子作为原点
                    
                    # 处理其他关键点
                    for idx, kpt in enumerate(keypoints[0]):
                        if idx == 0:  # 跳过鼻子
                            continue
                            
                        x, y, conf = kpt
                        if conf > 0.5:  # 只处理置信度高的关键点
                            x_int, y_int = int(x), int(y)
                            
                            if (0 <= y_int < camera_params.height and 
                                0 <= x_int < camera_params.width):
                                
                                depth = depth_data[y_int, x_int]
                                world_coords = get_3d_coordinates(x_int, y_int, depth, camera_params)
                                
                                # 计算相对于鼻子的坐标
                                relative_coords = world_coords - nose_coords
                                keypoints_3d[KEYPOINT_DICT[idx]] = relative_coords
                                
                                # 绘制关键点
                                cv2.circle(rgb_frame, (x_int, y_int), 5, (0, 255, 0), -1)
                                
                                # 添加标签（相对坐标）
                                label = f"{KEYPOINT_DICT[idx]}: ({relative_coords[0]:.1f}, {relative_coords[1]:.1f}, {relative_coords[2]:.1f})mm"
                                cv2.putText(rgb_frame, label, (x_int, y_int - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # 计算关节角度
                    angles = calculate_joint_angles(keypoints_3d)
                    
                    # 显示关节角度
                    y_offset = 30
                    for joint, angle in angles.items():
                        text = f"{joint} Angle: {angle:.1f}°"
                        cv2.putText(rgb_frame, text, (10, y_offset),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                        y_offset += 30
            
            # 显示结果
            cv2.imshow('3D Pose Detection', rgb_frame)
            
            # 按'q'退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except Exception as e:
        print(f"发生错误: {str(e)}")
        
    finally:
        print("正在清理资源...")
        # 清理资源
        if depth_stream is not None:
            try:
                depth_stream.stop()
                print("深度流已停止")
            except:
                pass
            
        if color_cap is not None:
            try:
                color_cap.release()
                print("彩色相机已释放")
            except:
                pass
            
        if device is not None:
            try:
                device.close()
                print("设备已关闭")
            except:
                pass
            
        try:
            openni2.unload()
            print("OpenNI2已卸载")
        except:
            pass
            
        cv2.destroyAllWindows()
        print("程序已退出")

if __name__ == "__main__":
    main()