import serial
import time

def read_serial_data(port='COM15', baudrate=115200):
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        
        while True:
            try:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    print(line)
                time.sleep(0.01)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                continue
                
    except serial.SerialException as e:
        print(f"串口错误: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    PORT = 'COM15'
    BAUDRATE = 115200
    
    read_serial_data(PORT, BAUDRATE) 