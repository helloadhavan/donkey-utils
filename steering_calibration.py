#!/usr/bin/env python3
"""
Steering servo calibration script for DonkeyCar PiRacer
Find the correct center position for your specific servo
"""

import time
import smbus2

class PCA9685:
    def __init__(self, channel=1, address=0x40, frequency=60):
        self.bus = smbus2.SMBus(channel)
        self.address = address
        self.frequency = frequency
        self.init_pca9685()
    
    def init_pca9685(self):
        """Initialize PCA9685"""
        self.bus.write_byte_data(self.address, 0x00, 0x00)
        time.sleep(0.01)
        
        prescale = int(25000000.0 / (4096.0 * self.frequency) - 1.0)
        old_mode = self.bus.read_byte_data(self.address, 0x00)
        sleep_mode = (old_mode & 0x7F) | 0x10
        self.bus.write_byte_data(self.address, 0x00, sleep_mode)
        self.bus.write_byte_data(self.address, 0xFE, prescale)
        self.bus.write_byte_data(self.address, 0x00, old_mode)
        time.sleep(0.01)
        self.bus.write_byte_data(self.address, 0x00, old_mode | 0x20)
        
        print(f"PCA9685 initialized at {self.frequency}Hz")
    
    def set_pulse(self, channel, pulse_ms):
        """Set pulse width in milliseconds"""
        pulse_length = 1000000.0 / self.frequency / 4096.0
        pulse_value = int(pulse_ms * 1000.0 / pulse_length)
        self.set_pwm(channel, 0, pulse_value)
    
    def set_pwm(self, channel, on, off):
        """Set PWM values"""
        base_reg = 0x06 + 4 * channel
        self.bus.write_byte_data(self.address, base_reg, on & 0xFF)
        self.bus.write_byte_data(self.address, base_reg + 1, on >> 8)
        self.bus.write_byte_data(self.address, base_reg + 2, off & 0xFF)
        self.bus.write_byte_data(self.address, base_reg + 3, off >> 8)
    
    def close(self):
        self.bus.close()

def calibrate_steering():
    """Interactive steering calibration"""
    print("=== Steering Servo Calibration ===")
    print("This will help you find the correct center position for your steering servo")
    print("Watch the wheels and find the position where they point straight ahead")
    
    pwm = PCA9685()
    steering_channel = 1  # DonkeyCar standard steering channel
    
    # Test different center positions
    test_positions = [
        1.3, 1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7
    ]
    
    try:
        print(f"\nTesting different center positions on channel {steering_channel}:")
        print("Look at the wheels and note which position makes them point straight ahead")
        
        for i, pulse_ms in enumerate(test_positions):
            print(f"\nPosition {i+1}: {pulse_ms}ms")
            pwm.set_pulse(steering_channel, pulse_ms)
            time.sleep(2)
            
            response = input("Is this centered? (y/n/q to quit): ").lower()
            if response == 'y':
                print(f"\nGreat! Your steering center is at {pulse_ms}ms")
                print(f"Update your DonkeyCar config with: steering_center = {pulse_ms}")
                break
            elif response == 'q':
                break
        
        # Fine tuning
        print(f"\nFine tuning around the best position...")
        best_position = float(input("Enter the best position from above (or press Enter for 1.5): ") or "1.5")
        
        print("Fine tuning in 0.01ms steps. Use +/- to adjust, 'c' when centered:")
        current_pos = best_position
        
        while True:
            pwm.set_pulse(steering_channel, current_pos)
            print(f"Current position: {current_pos:.3f}ms")
            
            cmd = input("Adjust: + (increase), - (decrease), c (centered), q (quit): ").lower()
            if cmd == '+':
                current_pos += 0.01
            elif cmd == '-':
                current_pos -= 0.01
            elif cmd == 'c':
                print(f"\nPerfect! Your steering center is: {current_pos:.3f}ms")
                break
            elif cmd == 'q':
                break
        
        # Test the calibrated center
        print(f"\nTesting calibrated center at {current_pos:.3f}ms...")
        pwm.set_pulse(steering_channel, current_pos)
        time.sleep(1)
        
        print("Testing left turn...")
        pwm.set_pulse(steering_channel, current_pos - 0.3)
        time.sleep(1)
        
        print("Back to center...")
        pwm.set_pulse(steering_channel, current_pos)
        time.sleep(1)
        
        print("Testing right turn...")
        pwm.set_pulse(steering_channel, current_pos + 0.3)
        time.sleep(1)
        
        print("Back to center...")
        pwm.set_pulse(steering_channel, current_pos)
        time.sleep(1)
        
        print(f"\nCalibration complete!")
        print(f"Your steering center value: {current_pos:.3f}ms")
        print(f"Update your DonkeyCar script with: self.steering_center = {current_pos:.3f}")
        
    except KeyboardInterrupt:
        print("\nCalibration interrupted")
    finally:
        # Stop servo
        pwm.set_pulse(steering_channel, 0)
        pwm.close()

def quick_test_center(center_ms=1.5):
    """Quick test of a specific center value"""
    print(f"=== Quick Test: Center = {center_ms}ms ===")
    
    pwm = PCA9685()
    steering_channel = 1
    
    try:
        print("Setting center position...")
        pwm.set_pulse(steering_channel, center_ms)
        time.sleep(2)
        
        print("Testing left...")
        pwm.set_pulse(steering_channel, center_ms - 0.3)
        time.sleep(1)
        
        print("Back to center...")
        pwm.set_pulse(steering_channel, center_ms)
        time.sleep(1)
        
        print("Testing right...")
        pwm.set_pulse(steering_channel, center_ms + 0.3)
        time.sleep(1)
        
        print("Back to center...")
        pwm.set_pulse(steering_channel, center_ms)
        time.sleep(1)
        
        print("Test complete!")
        
    finally:
        pwm.set_pulse(steering_channel, 0)
        pwm.close()

if __name__ == "__main__":
    print("Steering Servo Calibration Tool")
    print("Make sure the PiRacer is on a stand so you can see the wheels")
    
    try:
        choice = input("\nChoose: (1) Full calibration, (2) Quick test, or Enter for full: ")
        if choice == "2":
            center = input("Enter center value to test (default 1.5): ")
            quick_test_center(float(center) if center else 1.5)
        else:
            calibrate_steering()
    except KeyboardInterrupt:
        print("\nCalibration stopped")
    except Exception as e:
        print(f"Error: {e}")