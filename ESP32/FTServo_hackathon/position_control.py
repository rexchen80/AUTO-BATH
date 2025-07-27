#!/usr/bin/env python
#
# Position and Speed Control for FTServo
# This example is designed for controlling a servo on COM3 with ID=1
# Position range is limited to 0-500

import sys
import os
import time

sys.path.append("..")
from scservo_sdk import *

class ServoController:
    def __init__(self, port='COM3', baudrate=115200, servo_id=1):
        # Initialize PortHandler instance
        self.portHandler = PortHandler(port)
        
        # Initialize PacketHandler instance
        self.packetHandler = scscl(self.portHandler)
        
        self.servo_id = servo_id
        
        # Open port
        if self.portHandler.openPort():
            print("Succeeded to open the port")
        else:
            raise Exception("Failed to open the port")

        # Set port baudrate
        if self.portHandler.setBaudRate(baudrate):
            print("Succeeded to change the baudrate")
        else:
            raise Exception("Failed to change the baudrate")
            
    def set_position(self, position, speed=1000, acceleration=50):
        """
        设置舵机位置和速度，增加过载保护
        :param position: 目标位置 (0-500)
        :param speed: 最大速度 (0-32767), 默认1000 (约59rpm，降低以防过载)
        :param acceleration: 加速度 (0-254), 默认50 (降低加速度减少冲击)
        :return: 是否成功
        """
        # 确保位置在有效范围内
        position = max(0, min(500, position))
        
        # 确保速度在有效范围内，并设置上限以防过载
        speed = max(0, min(5000, speed))  # 限制最大速度为5000
        
        # 获取当前位置
        current_pos = self.get_current_position()
        if current_pos is not None:
            # 如果移动距离过大，分段移动
            if abs(position - current_pos) > 200:
                mid_position = current_pos + (1 if position > current_pos else -1) * 200
                print(f"Moving in steps: {current_pos} -> {mid_position} -> {position}")
                
                # 先移动到中间位置
                result = self._execute_position_command(mid_position, speed, acceleration)
                if not result:
                    return False
                    
                # 等待移动完成
                time.sleep(1)
                
                # 移动到最终位置
                return self._execute_position_command(position, speed, acceleration)
                
        return self._execute_position_command(position, speed, acceleration)
        
    def _execute_position_command(self, position, speed, acceleration):
        """
        执行位置命令并检查错误
        """
        scs_comm_result, scs_error = self.packetHandler.WritePos(
            self.servo_id, 
            position,
            acceleration,
            speed
        )
        
        if scs_comm_result != COMM_SUCCESS:
            print("Communication error: %s" % self.packetHandler.getTxRxResult(scs_comm_result))
            return False
            
        if scs_error != 0:
            print("Servo error: %s" % self.packetHandler.getRxPacketError(scs_error))
            # 如果发生过载，立即停止
            if "Overload" in self.packetHandler.getRxPacketError(scs_error):
                print("Overload detected! Stopping servo...")
                self.stop_servo()
            return False
            
        return True
        
    def stop_servo(self):
        """
        立即停止舵机运动
        """
        current_pos = self.get_current_position()
        if current_pos is not None:
            self._execute_position_command(current_pos, 0, 0)
            
    def get_current_position(self):
        """
        获取当前位置
        :return: 当前位置值，如果出错则返回None
        """
        pos, scs_comm_result, scs_error = self.packetHandler.ReadPos(self.servo_id)
        
        if scs_comm_result != COMM_SUCCESS:
            print("Communication error: %s" % self.packetHandler.getTxRxResult(scs_comm_result))
            return None
            
        if scs_error != 0:
            print("Servo error: %s" % self.packetHandler.getRxPacketError(scs_error))
            return None
            
        return pos
        
    def close(self):
        """
        关闭串口连接
        """
        self.portHandler.closePort()

# 使用示例
if __name__ == "__main__":
    try:
        # 创建舵机控制器实例
        servo = ServoController()
        
        while True:
            print("Moving to position 250 with safe speed...")
            servo.set_position(250, 2000)  # 使用较低的速度
            time.sleep(0.1)  # 给予更多时间完成运动
            
            servo.set_position(0, 2000)
            time.sleep(0.1)
            
            servo.set_position(330, 2000)
            time.sleep(0.1)
        
    finally:
        # 确保关闭串口
        servo.close() 