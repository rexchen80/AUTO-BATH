import numpy as np
import open3d as o3d
from openni import openni2
from openni import _openni2 as c_api
import os
import time

# 设置OpenNI2的DLL路径
OPENNI_DLL_PATH = r"C:\Users\ASUS\Desktop\keypoint\OrbbecViewer"

def initialize_device():
    # 初始化OpenNI2，指定DLL路径
    if not os.path.exists(os.path.join(OPENNI_DLL_PATH, "OpenNI2.dll")):
        raise FileNotFoundError(f"OpenNI2.dll not found in {OPENNI_DLL_PATH}")
    
    openni2.initialize(OPENNI_DLL_PATH)
    
    # 打开设备
    dev = openni2.Device.open_any()
    return dev

def start_depth_stream(device):
    # 创建深度数据流
    depth_stream = device.create_depth_stream()
    # 设置深度图像模式：分辨率和FPS
    depth_stream.set_video_mode(c_api.OniVideoMode(
        pixelFormat=c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM,
        resolutionX=640,
        resolutionY=480,
        fps=30
    ))
    depth_stream.start()
    return depth_stream

def create_point_cloud(depth_data, fx=580, fy=580, cx=320, cy=240):
    """将深度图转换为点云"""
    rows, cols = depth_data.shape
    
    # 创建网格点坐标
    x_grid, y_grid = np.meshgrid(np.arange(cols), np.arange(rows))
    
    # 计算三维坐标
    Z = depth_data / 1000.0  # 转换为米
    X = (x_grid - cx) * Z / fx
    Y = (y_grid - cy) * Z / fy
    
    # 将坐标组合为点云数据
    points = np.stack([X, Y, Z], axis=-1)
    points = points.reshape(-1, 3)
    
    # 移除无效点（深度为0的点）
    valid_points = points[Z.flatten() > 0]
    
    return valid_points

def main():
    try:
        # 初始化设备
        device = initialize_device()
        depth_stream = start_depth_stream(device)
        
        # 创建Open3D可视化窗口
        vis = o3d.visualization.Visualizer()
        vis.create_window("Gemini Point Cloud Viewer", width=1280, height=720)
        
        # 设置视角
        ctr = vis.get_view_control()
        ctr.set_zoom(0.3)
        
        # 创建点云对象
        pcd = o3d.geometry.PointCloud()
        
        print("点云可视化已启动，关闭窗口退出")
        
        while True:
            # 读取深度帧
            frame = depth_stream.read_frame()
            frame_data = frame.get_buffer_as_uint16()
            
            # 转换为numpy数组
            depth_array = np.frombuffer(frame_data, dtype=np.uint16)
            depth_array = depth_array.reshape(480, 640)
            
            # 生成点云数据
            points = create_point_cloud(depth_array)
            
            # 更新点云
            pcd.points = o3d.utility.Vector3dVector(points)
            
            # 清除之前的点云
            vis.clear_geometries()
            # 添加新的点云
            vis.add_geometry(pcd)
            
            # 更新可视化
            vis.poll_events()
            vis.update_renderer()
            
            # 控制帧率
            time.sleep(0.01)
            
            # 检查窗口是否关闭
            if not vis.poll_events():
                break
                
    except Exception as e:
        print(f"发生错误: {str(e)}")
        
    finally:
        # 清理资源
        if 'depth_stream' in locals():
            depth_stream.stop()
        if 'device' in locals():
            device.close()
        openni2.unload()
        if 'vis' in locals():
            vis.destroy_window()

if __name__ == "__main__":
    main() 