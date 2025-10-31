import serial
import time
from textwrap import dedent
from datetime import datetime
import csv

class AdvancedArduinoTester:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.test_results = []
        self.log_file = f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self._init_log_file()
        time.sleep(2)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.ser.close()
        self._generate_report()

    def _init_log_file(self):
        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:  # أضف encoding='utf-8'
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp', 
                'Test Name', 
                'Command', 
                'Parameters',
                'Response', 
                'Status', 
                'Details'
            ])

    def _log_test(self, test_data):
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:  # أضف encoding='utf-8'
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                test_data['name'],
                test_data['cmd'],
                ' '.join(f"{b:02X}" for b in test_data['params']),
                ' '.join(f"{b:02X}" for b in test_data['response']) if test_data['response'] else 'None',
                test_data['status'],
                test_data['details']
            ])

    def send_packet(self, cmd, params=[]):
        packet = bytes([0xEB, cmd] + params + [0xEE])
        self.ser.write(packet)
        return packet

    def read_response(self, timeout=2):
        start = time.time()
        buffer = bytearray()
        
        while time.time() - start < timeout:
            b = self.ser.read(1)
            if not b:
                continue
                
            if b[0] == 0xEB:
                buffer = bytearray()
            elif b[0] == 0xEE:
                return bytes(buffer)
            else:
                buffer.append(b[0])
                
        return None

    def run_comprehensive_test(self):
        """تشغيل جميع الاختبارات التالية"""
        tests = [
            self.test_analog_read,
            self.test_digital_operations,
            self.test_pwm_operations,
            self.test_error_conditions,
            #self.test_stress
        ]
        
        for test in tests:
            test()

    # region Test Cases
    def test_analog_read(self):
        test_cases = [
            ('A0 Read', 0xAE, [0x00], lambda r: len(r) == 4 and r[0] == 0xAE),
            ('All Pins Read', 0xAE, [0xAA], lambda r: len(r) == 17 and r[0] == 0xAE),
            ('Invalid Pin High', 0xAE, [0x08], lambda r: r[0] == 0xE3),
            ('Invalid Pin Low', 0xAE, [0xF0], lambda r: r[0] == 0xE3),
            ('Boundary Check', 0xAE, [0x07], lambda r: len(r) == 4)
        ]
        self._run_test_suite("Analog Read Tests", test_cases)

    def test_digital_operations(self):
        test_cases = [
            ('Set DDRB', 0xDD, [0xBB, 0xFF], lambda r: r[0] == 0xDD and r[1] == 0xBB),
            ('Set Invalid DDR', 0xDD, [0x00, 0xFF], lambda r: r[0] == 0xE4),
            ('Write PORTB', 0xBF, [0xBB, 0xAA], lambda r: r[0] == 0xBF and r[1] == 0xBB),
            ('Read PORTB', 0xFE, [0xBB], lambda r: r[0] == 0xFE and r[1] == 0xBB),
            ('Invalid Port Write', 0xBF, [0x00, 0xFF], lambda r: r[0] == 0xE4)
        ]
        self._run_test_suite("Digital Operations Tests", test_cases)

    def test_pwm_operations(self):
        test_cases = [
            ('Valid PWM 9', 0xE4, [0x09, 0x80], lambda r: r[0] == 0xE4 and r[1] == 0x09),
            ('Min PWM Value', 0xE4, [0x09, 0x00], lambda r: r[0] == 0xE4 and r[2] == 0x00),
            ('Max PWM Value', 0xE4, [0x09, 0xFF], lambda r: r[0] == 0xE4 and r[2] == 0xFF),
            ('Invalid PWM Pin', 0xE4, [0x02, 0x80], lambda r: r[0] == 0xE5),
            ('Unsupported PWM', 0xE4, [0x04, 0xFF], lambda r: r[0] == 0xE5)
        ]
        self._run_test_suite("PWM Tests", test_cases)

    def test_error_conditions(self):
        test_cases = [
            ('Unknown Command', 0xFF, [], lambda r: r[0] == 0xE1),
            ('Short Packet', 0xAE, [], lambda r: r[0] == 0xE2),
            ('Extra Parameters', 0xAE, [0x00, 0x00], lambda r: r[0] == 0xE2),
            ('Buffer Overflow', 'special', [0xAE]*30, lambda r: r[0] == 0xE6)
        ]
        self._run_test_suite("Error Handling Tests", test_cases)

    def test_stress(self):
        print("\n=== Stress Tests ===")
        for i in range(100):
            self._run_test(
                f"Stress Write {i+1}", 
                0xBF, 
                [0xBB, i % 256],
                lambda r: r[0] == 0xBF and r[1] == 0xBB
            )
        for i in range(50):
            self._run_test(
                f"Stress Read {i+1}", 
                0xFE, 
                [0xBB],
                lambda r: r[0] == 0xFE and r[1] == 0xBB
            )
    # endregion

    # region Helper Functions
    def _run_test_suite(self, suite_name, test_cases):
        print(f"\n=== {suite_name} ===")
        for case in test_cases:
            self._run_test(*case)

    def _run_test(self, name, cmd, params, validator):
        # معالجة الحالات الخاصة
        if cmd == 'special':  # Buffer Overflow
            overflow_packet = bytes([0xEB] + [0xAE]*30 + [0xEE])
            self.ser.write(overflow_packet)
            response = self.read_response()
            cmd_code = '0xAE*30'
        else:
            packet = self.send_packet(cmd, params)
            response = self.read_response()
            cmd_code = f"{cmd:02X}"

        test_data = {
            'name': name,
            'cmd': cmd_code,
            'params': params,
            'response': response,
            'status': 'PENDING',
            'details': ''
        }

        try:
            if not response:
                test_data.update({'status': 'FAIL', 'details': 'No response'})
            elif validator(response):
                test_data.update({'status': 'PASS', 'details': self._format_response(response)})
            else:
                test_data.update({'status': 'FAIL', 'details': 'Validation failed'})
        except Exception as e:
            test_data.update({'status': 'ERROR', 'details': str(e)})

        self._log_test(test_data)
        self._print_test_result(test_data)

    def _format_response(self, data):
        if data[0] in ERROR_CODES:
            return f"Error: {ERROR_CODES[data[0]]} (0x{data[0]:02X})"
        
        formatters = {
            0xAE: self._format_analog,
            0xBF: self._format_port,
            0xDD: self._format_ddr,
            0xE4: self._format_pwm,
            0xFE: self._format_pin_read
        }
        return formatters.get(data[0], lambda x: 'Unknown response')(data)

    def _format_analog(self, data):
        if len(data) == 17:
            values = [((data[i*2+1] << 8) | data[i*2+2]) for i in range(8)]
            return f"Analog Values: {', '.join(f'{v:4d}' for v in values)}"
        return f"A{data[1]}: {(data[2] << 8) | data[3]:4d}"


    def _format_ddr(self, data):
        return f"DDR{data[1]:02X} <- 0x{data[2]:02X}"

    def _format_port(self, data):
        return f"PORT{data[1]:02X} <- 0x{data[2]:02X}"

    def _format_pwm(self, data):
        return f"PWM Pin {data[1]} = {data[2]}"

    def _format_pin_read(self, data):
        return f"PORT{data[1]:02X} = {data[2]:08b}b"

    def _print_test_result(self, test_data):
        color_map = {'PASS': '32', 'FAIL': '31', 'ERROR': '33'}
        color = color_map.get(test_data['status'], '37')
        print(f"\033[1;{color}m[{test_data['status']}]\033[0m {test_data['name']}")
        print(f"   Details: {test_data['details']}")

    def _generate_report(self):
        print("\n=== Final Test Report ===")
        with open(self.log_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                print(f"{row[1]:<25} {row[5]:<6} {row[6]}")
    # endregion

# تعريف أكواد الأخطاء
ERROR_CODES = {
    0xE1: "Invalid Command",
    0xE2: "Bad Parameters",
    0xE3: "Pin Out of Range",
    0xE4: "Port Range Error",
    0xE5: "PWM Not Supported",
    0xE6: "Buffer Overflow"
}

if __name__ == "__main__":
    with AdvancedArduinoTester('COM4') as tester:
        print(dedent("""
        ******************************
        * Advanced Arduino Tester *
        ******************************
        """))
        tester.run_comprehensive_test()