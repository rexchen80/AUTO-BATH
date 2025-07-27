from hx711 import HX711
import json
import os

class HX711_Calibration:
    def __init__(self, d_out_pin, pd_sck_pin, calibration_file='calibration.json'):
        # 修改这里，使用位置参数而不是关键字参数
        self.hx = HX711(d_out_pin, pd_sck_pin)
        self.calibration_file = calibration_file
        self.scale_ratio = 1
        self.offset = 0
        self.load_calibration()
    
    def load_calibration(self):
        """Load calibration data from file if exists"""
        try:
            if os.path.exists(self.calibration_file):
                with open(self.calibration_file, 'r') as f:
                    data = json.load(f)
                    self.scale_ratio = data.get('scale_ratio', 1)
                    self.offset = data.get('offset', 0)
                print("已加载校准数据")
        except Exception as e:
            print(f"加载校准数据失败: {e}")
    
    def save_calibration(self):
        """Save calibration data to file"""
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump({
                    'scale_ratio': self.scale_ratio,
                    'offset': self.offset
                }, f)
            print("校准数据已保存")
        except Exception as e:
            print(f"保存校准数据失败: {e}")

    def tare(self, times=10):
        """Tare the scale - set current weight as zero"""
        print("开始去皮...")
        values = []
        for _ in range(times):
            values.append(self.hx.read())
        self.offset = sum(values) / len(values)
        print("去皮完成")
        self.save_calibration()
        
    def calibrate(self, real_weight, times=10):
        """Calibrate using a known weight (in grams)"""
        print(f"开始使用 {real_weight}g 进行校准...")
        values = []
        for _ in range(times):
            values.append(self.hx.read())
        measured_value = sum(values) / len(values)
        
        # Calculate scale ratio
        self.scale_ratio = real_weight / (measured_value - self.offset)
        print("校准完成")
        self.save_calibration()
    
    def get_weight(self, times=1):
        """Get current weight in grams"""
        values = []
        for _ in range(times):
            values.append(self.hx.read())
        measured_value = sum(values) / len(values)
        weight = (measured_value - self.offset) * self.scale_ratio
        return weight

def main():
    # 示例使用方法
    # 根据实际连接的引脚修改这些值
    d_out_pin = 5  # GPIO5
    pd_sck_pin = 4  # GPIO4
    
    # 修改这里，使用位置参数而不是关键字参数
    scale = HX711_Calibration(d_out_pin, pd_sck_pin)
    
    while True:
        print("\n=== HX711 校准程序 ===")
        print("1. 去皮(设置零点)")
        print("2. 校准(使用已知重量)")
        print("3. 读取当前重量")
        print("4. 退出")
        
        choice = input("请选择操作 (1-4): ")
        
        if choice == '1':
            print("请确保秤上没有任何重物")
            input("按回车继续...")
            scale.tare()
            
        elif choice == '2':
            try:
                weight = float(input("请输入校准重物的实际重量(克): "))
                print("请将校准重物放在秤上")
                input("按回车继续...")
                scale.calibrate(weight)
            except ValueError:
                print("请输入有效的数字!")
                
        elif choice == '3':
            weight = scale.get_weight(times=10)
            print(f"当前重量: {weight:.2f}g")
            
        elif choice == '4':
            print("程序退出")
            break
            
        else:
            print("无效的选择，请重试")

if __name__ == "__main__":
    main() 