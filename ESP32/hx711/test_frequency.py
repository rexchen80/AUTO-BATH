from hx711 import HX711
import time
from machine import Pin

def test_sampling_rate(samples=100):
    """
    测试HX711的采样频率
    :param samples: 要采集的样本数量
    :return: 平均采样频率（Hz）
    """
    # 初始化HX711，请根据实际接线修改引脚号
    hx = HX711(d_out=5, pd_sck=4)  # 示例引脚号，请根据实际情况修改
    
    print("开始测试采样频率...")
    print(f"将采集 {samples} 个样本")
    
    # 等待传感器准备就绪
    while not hx.is_ready():
        time.sleep(0.1)
    
    # 记录开始时间
    start_time = time.time()
    
    # 采集数据
    readings = []
    for i in range(samples):
        value = hx.read()
        readings.append(value)
        if i % 10 == 0:  # 每采集10个样本打印一次进度
            print(f"已采集: {i}/{samples}")
    
    # 计算总时间
    end_time = time.time()
    total_time = end_time - start_time
    
    # 计算频率
    frequency = samples / total_time
    
    print("\n测试结果:")
    print(f"总采样数: {samples}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均采样频率: {frequency:.2f} Hz")
    print(f"平均采样周期: {(total_time/samples)*1000:.2f} ms")
    
    return frequency, readings

def calculate_mean(data):
    """计算平均值"""
    return sum(data) / len(data)

def calculate_stdev(data):
    """计算标准差"""
    mean = calculate_mean(data)
    variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1) if len(data) > 1 else 0
    return (variance ** 0.5)

def analyze_data(readings):
    """
    分析采集到的数据
    """
    if not readings:
        return
    
    mean = calculate_mean(readings)
    stdev = calculate_stdev(readings) if len(readings) > 1 else 0
    
    print("\n数据分析:")
    print(f"平均值: {mean:.2f}")
    print(f"标准差: {stdev:.2f}")
    print(f"最大值: {max(readings)}")
    print(f"最小值: {min(readings)}")

if __name__ == "__main__":
    try:
        # 运行测试
        frequency, readings = test_sampling_rate(samples=100)
        
        # 分析数据
        analyze_data(readings)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        print("\n测试结束") 