import socket
import struct
import threading
import time
import queue
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich import box
from rich.progress import Progress, BarColumn, TextColumn

class UDPReceiver:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.running = True
        self.data_queue = queue.Queue(maxsize=100)  # 限制队列大小，防止内存溢出
        self.last_stats_time = time.time()
        self.packet_count = 0
        self.current_packet_rate = 0.0  # 添加当前接收速率变量

    def start(self):
        # 创建接收线程
        receive_thread = threading.Thread(target=self._receive_data)
        receive_thread.daemon = True
        receive_thread.start()

        # 创建显示线程
        display_thread = threading.Thread(target=self._display_data)
        display_thread.daemon = True
        display_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            print("\n正在关闭接收器...")

    def _receive_data(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))
        sock.settimeout(1.0)  # 设置超时，使能够响应Ctrl+C
        print(f"UDP接收器已启动，监听地址：{self.host}:{self.port}")

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                if len(data) == 85:  # 检查数据包长度
                    # 检查帧头
                    if data[0] == 0xAA and data[1] == 0xBB:
                        # 更新统计信息
                        self.packet_count += 1
                        current_time = time.time()
                        if current_time - self.last_stats_time >= 1.0:
                            self.current_packet_rate = self.packet_count
                            self.packet_count = 0
                            self.last_stats_time = current_time

                        # 如果队列满了，移除最旧的数据
                        if self.data_queue.full():
                            try:
                                self.data_queue.get_nowait()
                            except queue.Empty:
                                pass
                        
                        self.data_queue.put(data)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"接收数据出错: {e}")
                time.sleep(1)

        sock.close()

    def _create_table(self, torque, angles):
        table = Table(box=box.ROUNDED)
        table.add_column("参数", style="cyan")
        table.add_column("数值", style="green")
        
        # 添加接收速率和进度条
        max_rate = 100  # 最大速率设为100包/秒
        progress = Progress(
            TextColumn("{task.description}", justify="right"),
            BarColumn(
                bar_width=40,  # 调整进度条长度
                style="blue",  # 未完成部分为蓝色
                complete_style="yellow",  # 完成部分为黄色
                pulse_style="red",  # 脱冲效果为红色
                finished_style="bright_yellow",  # 完成时为亮黄色
            ),
            TextColumn("{task.completed:.1f}/秒", style="bright_yellow"),  # 显示具体速率
            expand=False,
            auto_refresh=False
        )
        progress.add_task("接收速率", total=max_rate, completed=min(self.current_packet_rate, max_rate))
        table.add_row("接收速率", progress)
        
        # 添加扭矩值
        table.add_row("扭矩值", f"{torque:>6.1f}")  # 右对齐数值，后面显示进度条
        
        # 添加左手关节数据
        left_angles = [f"{angle:.2f}" for angle in angles[0:8]]
        table.add_row("左手关节 (0-7)", " ".join(left_angles))
        
        # 添加右手关节数据
        right_angles = [f"{angle:.2f}" for angle in angles[8:16]]
        table.add_row("右手关节 (8-15)", " ".join(right_angles))
        
        return table

    def _display_data(self):
        console = Console()
        update_interval = 0.01  # 控制更新频率，每10ms更新一次
        last_update = 0

        with Live(console=console, refresh_per_second=10) as live:
            while self.running:
                try:
                    data = self.data_queue.get(timeout=1.0)
                    current_time = time.time()
                    
                    # 控制更新频率
                    if current_time - last_update < update_interval:
                        continue
                    
                    # 解析扭矩值
                    torque = struct.unpack('<h', data[3:5])[0] / 10.0

                    # 解析角度数据
                    angles = []
                    for i in range(20):
                        offset = 5 + i * 4
                        angle = struct.unpack('<f', data[offset:offset+4])[0]
                        angles.append(angle)

                    # 更新显示
                    table = self._create_table(torque, angles)
                    live.update(table)
                    last_update = current_time

                except queue.Empty:
                    continue
                except Exception as e:
                    console.print(f"[red]处理数据出错: {e}[/red]")
                    time.sleep(0.1)

if __name__ == "__main__":
    receiver = UDPReceiver()
    receiver.start()
