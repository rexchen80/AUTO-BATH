import sys
import math
import socket
import struct
import threading
import time
import queue
from typing import Dict
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich import box
from rich.progress import Progress, BarColumn, TextColumn

sys.path.append("..")
from scservo_sdk import *
from DM_CAN import *

class UDPMotorController:
    # UDP配置
    UDP_HOST = '0.0.0.0'
    UDP_PORT = 8080

    # DM电机配置
    DM_PORT = "COM3"
    DM_MOTORS = {1: 0x01, 2: 0x02, 3: 0x03, 4: 0x04, 5: 0x05, 6: 0x06, 7: 0x07, 8: 0x08}  # 1-8号电机

    # DM电机参数
    DM_DEFAULT_SPEED = 400    # DM电机速度
    DM_DEFAULT_TORQUE = 10000  # DM电机扭矩

    def __init__(self):
        # 初始化状态变量
        self.running = True
        self.packet_count = 0
        self.current_packet_rate = 0.0  # 当前接收速率
        self.last_stats_time = time.time()
        self._last_angles = {}
        
        # 初始化队列
        self.data_queue = queue.LifoQueue(maxsize=1)  # 只保留最新的数据
        self.motor_queue = queue.Queue(maxsize=1)  # 电机控制数据队列
        
        # 初始化DM电机控制
        self._init_dm_motors()

    def _init_dm_motors(self):
        """
        初始化DM电机控制
        """
        try:
            self.dm_control = MotorControl(self.DM_PORT)
            self.dm_motors = {}
            for motor_id, can_id in self.DM_MOTORS.items():
                motor = Motor(DM_Motor_Type.DM4310, can_id, 0x00)
                self.dm_control.addMotor(motor)
                self.dm_motors[motor_id] = motor
                self.dm_control.enable(motor)
            print(f'成功连接DM电机，端口：{self.DM_PORT}')
        except Exception as e:
            raise Exception(f"DM电机初始化错误: {e}")
            
    def sync_write_position(self, positions: Dict[int, float], torque_value: float = None):
        """
        同步写入多个电机位置和速度
        
        Args:
            positions: Dict[int, float] - 电机ID和目标角度/速度的字典
                - 关节1-6: 角度范围-180到180度 (位置控制)
                - 关节7: 速度值 (速度控制)
            torque_value: float - 扭力值，范围0-100，如果为None则使用默认值
        """
        # 计算扭力值
        dm_torque = int(torque_value * 100) if torque_value is not None else self.DM_DEFAULT_TORQUE
        
        # 处理所有有效的电机位置
        for motor_id, angle in positions.items():
            if motor_id in self.DM_MOTORS:
                try:
                    motor = self.dm_motors[motor_id]
                    
                    # 关节8使用速度控制，其他关节使用位置控制
                    if motor_id == 8:
                        # 将角度转换为速度 (rad/s)
                        velocity_rad_s = angle * math.pi / 180.0  # 角度转换为弧度作为速度
                        self.dm_control.control_Vel(motor, velocity_rad_s)
                    else:
                        # 其他关节使用位置控制
                        angle_rad = angle * math.pi / 180.0  # 角度转换为弧度
                        self.dm_control.control_pos_force(motor, angle_rad, self.DM_DEFAULT_SPEED, dm_torque)
                except Exception as e:
                    print(f"DM电机 {motor_id} 控制错误: {e}")
        

    def _create_table(self, torque, angles):
        """
        创建显示表格
        
        Args:
            torque: float - 扭矩值
            angles: list - 角度列表
            
        Returns:
            Table - rich表格对象
        """
        table = Table(box=box.ROUNDED)
        table.add_column("参数", style="cyan")
        table.add_column("数值", style="green")
        
        # 添加接收速率进度条
        table.add_row("接收速率", self._create_rate_progress_bar())
        
        # 添加扭矩值
        table.add_row("扭矩值", f"{torque:>6.1f}")
        
        # 添加关节数据
        self._add_joint_data_to_table(table, angles)
        
        return table
        
    def _create_rate_progress_bar(self):
        """
        创建接收速率进度条
        
        Returns:
            Progress - rich进度条对象
        """
        max_rate = 100  # 最大速率设为100包/秒
        progress = Progress(
            TextColumn("{task.description}", justify="right"),
            BarColumn(
                bar_width=40,
                style="blue",
                complete_style="yellow",
                pulse_style="red",
                finished_style="bright_yellow",
            ),
            TextColumn("{task.completed:.1f}/秒", style="bright_yellow"),
            expand=False,
            auto_refresh=False
        )
        progress.add_task("接收速率", total=max_rate, completed=min(self.current_packet_rate, max_rate))
        return progress
        
    def _add_joint_data_to_table(self, table, angles):
        """
        将关节数据添加到表格中
        
        Args:
            table: Table - rich表格对象
            angles: list - 角度列表
        """
        # 添加左手关节数据（包括8号关节）
        left_angles = [f"{angle:.2f}" for angle in angles[0:8]]
        table.add_row("左手关节 (0-7, 8号关节=索引7)", " ".join(left_angles))
        
        # 特别显示8号关节的值
        if len(angles) > 7:
            table.add_row("8号关节值", f"{angles[7]:.2f}")
        
        # 添加右手关节数据
        right_angles = [f"{angle:.2f}" for angle in angles[8:16]]
        table.add_row("右手关节 (8-15)", " ".join(right_angles))
        
        # 添加剩余角度数据（如果有的话）
        if len(angles) > 16:
            remaining_angles = [f"{angle:.2f}" for angle in angles[16:20]]
            table.add_row("剩余角度 (16-19)", " ".join(remaining_angles))

    def _receive_data(self):
        """
        UDP数据接收线程
        """
        sock = None
        try:
            # 初始化UDP套接字
            sock = self._init_udp_socket()
            
            # 初始化接收速率统计
            self.packet_count = 0
            self.last_stats_time = time.time()

            # 主接收循环
            while self.running:
                try:
                    # 使用更短的超时，以便更快响应self.running状态变化
                    self._receive_and_process_packet(sock)
                except socket.timeout:
                    # 超时后检查running状态
                    continue
                except Exception as e:
                    if self.running:  # 只在程序仍在运行时打印错误
                        print(f"接收数据出错: {e}")
                        time.sleep(0.2)
        except KeyboardInterrupt:
            # 明确捕获KeyboardInterrupt
            pass
        finally:
            # 确保套接字关闭
            if sock:
                sock.close()
            print("UDP接收线程已关闭")
                
    def _init_udp_socket(self):
        """
        初始化UDP套接字
        
        Returns:
            socket - UDP套接字对象
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.UDP_HOST, self.UDP_PORT))
        # 设置较短的超时时间，以便更快响应Ctrl+C
        sock.settimeout(0.2)
        print(f"UDP接收器已启动，监听地址：{self.UDP_HOST}:{self.UDP_PORT}")
        return sock
        
    def _receive_and_process_packet(self, sock):
        """
        接收并处理单个UDP数据包
        
        Args:
            sock: socket - UDP套接字对象
        """
        data, _ = sock.recvfrom(1024)
        
        # 验证数据包格式
        if len(data) == 85 and data[0] == 0xAA and data[1] == 0xBB:
            # 调试：打印数据包长度字段
            #print(f"接收数据包 - 长度字段: {data[2]}")
            
            # 更新统计信息
            self._update_statistics()
            
            # 将数据放入队列
            self._update_data_queue(data)
            
    def _update_statistics(self):
        """
        更新数据接收统计信息
        """
        self.packet_count += 1
        current_time = time.time()
        
        if current_time - self.last_stats_time >= 1.0:
            self.current_packet_rate = self.packet_count
            self.packet_count = 0
            self.last_stats_time = current_time
            
    def _update_data_queue(self, data):
        """
        更新数据队列
        
        Args:
            data: bytes - 接收到的数据
        """
        # 如果队列满了，移除最旧的数据
        if self.data_queue.full():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                pass
        
        # 将新数据放入队列
        self.data_queue.put(data)

    def _process_data(self):
        """
        数据处理和显示线程
        """
        console = Console()

        try:
            with Live(console=console, refresh_per_second=10) as live:
                while self.running:
                    try:
                        # 获取数据
                        data = self._get_data_from_queue()
                        if data is None:
                            continue
                        
                        # 解析数据
                        torque, angles = self._parse_data(data)
                        
                        # 更新显示
                        table = self._create_table(torque, angles)
                        live.update(table)
                        
                        # 准备电机控制数据
                        self._prepare_motor_control_data(angles, torque)
                        
                    except Exception as e:
                        if self.running:  # 只在程序仍在运行时打印错误
                            console.print(f"[red]处理数据出错: {e}[/red]")
                            time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            print("数据处理线程已关闭")
                    
    def _get_data_from_queue(self):
        """
        从队列中获取数据
        
        Returns:
            bytes - 数据包或None
        """
        try:
            return self.data_queue.get(timeout=1.0)
        except queue.Empty:
            return None
            
    def _parse_data(self, data):
        """
        解析数据包
        
        Args:
            data: bytes - 原始数据包
            
        Returns:
            tuple - (torque, angles)扭矩值和角度列表
        """
        # 解析扭矩值
        torque = struct.unpack('<h', data[3:5])[0] / 10.0
        
        # 解析角度数据
        angles = []
        for i in range(20):
            offset = 5 + i * 4
            angle = struct.unpack('<f', data[offset:offset+4])[0]
            angles.append(angle)
            
        return torque, angles
        
    def _prepare_motor_control_data(self, angles, torque):
        """
        准备电机控制数据
        
        Args:
            angles: list - 角度列表
            torque: float - 扭矩值
        """
        # 存储上一次的扭矩值，如果不存在则初始化为None
        if not hasattr(self, '_last_torque'):
            self._last_torque = None
            
        # 过滤变化较小的角度
        positions = {}
        for i, angle in enumerate(angles[:20], 1):
            if abs(angle - self._last_angles.get(i, 0)) < 0.1:
                continue
            positions[i] = angle
            self._last_angles[i] = angle

        # 检测扭矩值变化
        torque_changed = self._last_torque is None or abs(torque - self._last_torque) > 0.5
        self._last_torque = torque
        
        # 如果有变化较大的角度或扭矩值变化，则更新电机控制队列
        if positions or torque_changed:
            # 如果positions为空但扭矩变化了，使用上次的角度值
            if not positions and torque_changed:
                positions = {i: angle for i, angle in self._last_angles.items()}
            
            self._update_motor_queue(positions, torque)
            
    def _update_motor_queue(self, positions, torque):
        """
        更新电机控制队列
        
        Args:
            positions: dict - 电机ID和角度的字典
            torque: float - 扭矩值
        """
        # 如果队列满了，移除旧的数据
        if self.motor_queue.full():
            try:
                self.motor_queue.get_nowait()
            except queue.Empty:
                pass
                
        # 将新的控制数据放入队列
        self.motor_queue.put((positions, torque))

    def _motor_control(self):
        """
        电机控制线程
        """
        try:
            while self.running:
                try:
                    # 从队列获取控制数据
                    control_data = self._get_motor_control_data()
                    if control_data is None:
                        continue
                        
                    # 控制电机
                    positions, torque = control_data
                    self.sync_write_position(positions, torque)
                    
                except Exception as e:
                    if self.running:  # 只在程序仍在运行时处理错误
                        self._handle_motor_control_error(e)
        except KeyboardInterrupt:
            pass
        finally:
            print("电机控制线程已关闭")
                
    def _get_motor_control_data(self):
        """
        从队列中获取电机控制数据
        
        Returns:
            tuple - (positions, torque) 或 None
        """
        try:
            return self.motor_queue.get(timeout=1.0)
        except queue.Empty:
            return None
            
    def _handle_motor_control_error(self, error):
        """
        处理电机控制错误
        
        Args:
            error: Exception - 错误对象
        """
        print(f"电机控制错误: {error}")
        # 错误后等待一段时间再继续
        time.sleep(0.1)

    def start(self):
        """
        启动UDP电机控制器
        """
        try:
            # 创建并启动所有线程
            threads = self._create_and_start_threads()
            
            # 等待处理和电机控制线程结束
            self._wait_for_threads(threads)
            
        except KeyboardInterrupt:
            self._handle_shutdown()
            
    def _create_and_start_threads(self):
        """
        创建并启动所有工作线程
        
        Returns:
            dict - 包含所有线程的字典
        """
        # 创建接收线程
        receive_thread = threading.Thread(target=self._receive_data, name="UDP接收线程")
        receive_thread.daemon = True
        
        # 创建处理线程
        process_thread = threading.Thread(target=self._process_data, name="数据处理线程")
        process_thread.daemon = True

        # 创建电机控制线程
        motor_thread = threading.Thread(target=self._motor_control, name="电机控制线程")
        motor_thread.daemon = True
        
        # 启动所有线程
        receive_thread.start()
        process_thread.start()
        motor_thread.start()
        
        print(f"UDP电机控制器已启动，监听地址: {self.UDP_HOST}:{self.UDP_PORT}")
        
        return {
            "receive": receive_thread,
            "process": process_thread,
            "motor": motor_thread
        }
        
    def _wait_for_threads(self, threads):
        """
        等待线程结束
        
        Args:
            threads: dict - 包含所有线程的字典
        """
        try:
            # 使用超时等待，这样可以定期检查self.running状态并响应KeyboardInterrupt
            while self.running:
                # 检查线程是否还活着，如果都结束了就退出循环
                if not (threads["process"].is_alive() or threads["motor"].is_alive()):
                    break
                # 短暂等待，允许响应Ctrl+C
                time.sleep(0.1)
        except Exception as e:
            print(f"线程等待错误: {e}")
            self._handle_shutdown()
            
    def _handle_shutdown(self):
        """
        处理程序关闭
        """
        print("正在关闭...")
        self.running = False
        # 给线程一些时间来响应关闭信号
        time.sleep(0.5)
        print("UDP电机控制器已关闭")

if __name__ == "__main__":
    try:
        controller = UDPMotorController()
        controller.start()
    except KeyboardInterrupt:
        # 在主程序级别也捕获KeyboardInterrupt，确保程序能够被Ctrl+C终止
        print("\n程序被用户终止 (Ctrl+C)")
        if 'controller' in locals():
            controller._handle_shutdown()
    finally:
        print("程序已退出")
