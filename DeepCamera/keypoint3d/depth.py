import cv2
import numpy as np
from openni import openni2
from openni import _openni2 as c_api
import os

# 设置OpenNI2的DLL路径
OPENNI_DLL_PATH = r"C:\Users\ASUS\Desktop\keypoint3d\OrbbecViewer"

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
    depth_stream.start()
    return depth_stream

def main():
    try:
        # 初始化设备
        device = initialize_device()
        depth_stream = start_depth_stream(device)
        
        print("深度相机已启动，按'q'键退出")
        
        while True:
            # 读取深度帧
            frame = depth_stream.read_frame()
            frame_data = frame.get_buffer_as_uint16()
            
            # 将深度数据转换为numpy数组
            depth_array = np.frombuffer(frame_data, dtype=np.uint16)
            depth_array.shape = (480, 640)  # 根据实际分辨率调整
            
            # 归一化深度图像以便显示
            depth_normalized = cv2.normalize(depth_array, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            
            # 应用伪彩色映射
            depth_colormap = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)
            
            # 显示深度图像
            cv2.imshow('Gemini Depth View', depth_colormap)
            
            # 检查退出条件
            if cv2.waitKey(1) & 0xFF == ord('q'):
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
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 