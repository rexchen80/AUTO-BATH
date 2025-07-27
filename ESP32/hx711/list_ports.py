from serial.tools import list_ports

def list_serial_ports():
    """列出系统中所有可用的串口"""
    ports = list_ports.comports()
    
    if not ports:
        print("没有找到任何串口设备")
        return
    
    print("\n可用的串口设备：")
    for port in ports:
        print(f"端口: {port.device}")
        print(f"描述: {port.description}")
        print(f"硬件ID: {port.hwid}")
        print("-" * 50)

if __name__ == "__main__":
    list_serial_ports() 