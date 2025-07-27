import socket
import json
import time
from datetime import datetime

# UDP通信设置
UDP_IP = "0.0.0.0"  # 监听所有可用的网络接口
UDP_PORT = 62345    # 与发送端相同的端口

def main():
    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 绑定地址和端口
        sock.bind((UDP_IP, UDP_PORT))
        print(f"UDP接收端已启动")
        print(f"监听地址: {UDP_IP}:{UDP_PORT}")
        print("等待数据中...")
        
        # 设置接收超时为1秒
        sock.settimeout(1.0)
        
        last_frame = -1
        frame_count = 0
        start_time = time.time()
        last_print_time = start_time
        
        while True:
            try:
                # 接收数据
                data, addr = sock.recvfrom(4096)  # 缓冲区大小4KB
                current_time = time.time()
                
                # 解析JSON数据
                try:
                    json_data = json.loads(data.decode())
                    frame_num = json_data["frame"]
                    landmarks = json_data["landmarks"]
                    
                    # 计算丢帧
                    if last_frame != -1 and frame_num - last_frame > 1:
                        print(f"\n丢失了 {frame_num - last_frame - 1} 帧")
                    last_frame = frame_num
                    
                    frame_count += 1
                    
                    # 每秒更新一次统计信息
                    if current_time - last_print_time >= 1.0:
                        elapsed_time = current_time - start_time
                        fps = frame_count / elapsed_time
                        print(f"\r接收状态 - 来自 {addr[0]}:{addr[1]} | "
                              f"当前帧: {frame_num} | "
                              f"总帧数: {frame_count} | "
                              f"运行时间: {elapsed_time:.1f}秒 | "
                              f"平均帧率: {fps:.1f}fps", end="")
                        last_print_time = current_time
                    
                    # 每100帧显示一次完整数据
                    if frame_num % 100 == 0:
                        print(f"\n\n收到第 {frame_num} 帧数据 - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                        print(f"发送方地址: {addr[0]}:{addr[1]}")
                        print("数据内容:")
                        print(json.dumps(json_data, indent=2))
                        print("-" * 50)
                    
                except json.JSONDecodeError:
                    print(f"\n收到无效的JSON数据")
                    print(f"原始数据: {data.decode()}")
                    continue
                
            except socket.timeout:
                # 接收超时，检查是否需要退出
                continue
            except KeyboardInterrupt:
                break
    
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
    finally:
        sock.close()
        if frame_count > 0:
            total_time = time.time() - start_time
            average_fps = frame_count / total_time
            print(f"\n\n程序已退出")
            print(f"运行时间: {total_time:.1f}秒")
            print(f"总接收帧数: {frame_count}")
            print(f"平均帧率: {average_fps:.1f}fps")

if __name__ == "__main__":
    main() 