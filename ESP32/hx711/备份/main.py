from hx711 import HX711
from utime import sleep_us, sleep
from machine import Pin
import json

class Scales(HX711):
    def __init__(self, d_out, pd_sck):
        super(Scales, self).__init__(d_out, pd_sck)
        # 直接设置校准值
        self.offset = -305492.6
        self.scale_ratio = -0.004456556

    def reset(self):
        self.power_off()
        self.power_on()

    def get_stable_raw_value(self, reads=10, delay_us=500):
        values = []
        for _ in range(reads):
            values.append(self.read())
            sleep_us(delay_us)
        return self._stabilizer(values)
    
    @staticmethod
    def _stabilizer(values, deviation=10):
        if not values:
            return 0
        weights = []
        for prev in values:
            if abs(prev) < 1e-9:
                weights.append(sum(1 for current in values if abs(current) < 1e-9))
            else:
                weights.append(sum(1 for current in values if (abs(prev - current) * 100 / abs(prev)) <= deviation))
        
        if not weights:
            return values[0] if values else 0
            
        return sorted(zip(values, weights), key=lambda x: x[1]).pop()[0]
    
    def get_weight(self, reads=10):
        raw_value = self.get_stable_raw_value(reads=reads)
        return (raw_value - self.offset) * self.scale_ratio

# Initialize HX711
scales = Scales(d_out=5, pd_sck=4)
scales.reset()

# Main loop
while True:
    try:
        weight = scales.get_weight(reads=1)
        # Create JSON format string, format weight with rounding
        data = json.dumps({"pressure": f"{round(weight)}g"})
        # Print data (will be sent through USB CDC)
        print(data)
        sleep(0.0125)  # Reduced sleep time to increase frequency
    except Exception as e:
        print("Error:", e)
        sleep(0.1)

