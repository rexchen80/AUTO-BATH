import socket
import json
import time

# UDP通信设置
UDP_IP = "172.20.10.2"  # 目标IP
UDP_PORT = 62345          # 目标端口

def main():
    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"UDP发送端已启动")
        print(f"目标地址: {UDP_IP}:{UDP_PORT}")
        
        # 测试数据
        test_data = {
            "frame": 0,
            "landmarks": [
                {"id": 0, "x": 0.123, "y": 0.456, "z": 0.789},
                {"id": 11, "x": 0.234, "y": 0.567, "z": 0.890},
                {"id": 12, "x": 0.345, "y": 0.678, "z": 0.901}
            ]
        }
        
        frame_count = 0
        while True:
            # 更新帧号
            test_data["frame"] = frame_count
            
            # 转换为JSON字符串
            json_data = json.dumps(test_data)
            
            try:
                # 发送数据
                sock.sendto(json_data.encode(), (UDP_IP, UDP_PORT))
                print(f"\r已发送第 {frame_count} 帧测试数据", end="")
                
            except Exception as e:
                print(f"\n发送数据失败: {str(e)}")
                break
            
            frame_count += 1
            time.sleep(0.033)  # 约30fps
            
            # 每100帧打印一次完整数据
            if frame_count % 100 == 0:
                print(f"\n第 {frame_count} 帧发送的数据:")
                print(json_data)
                print("-" * 50)
    
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
    finally:
        sock.close()
        print(f"\n程序已退出，共发送 {frame_count} 帧")

if __name__ == "__main__":
    main() 