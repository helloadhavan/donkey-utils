#!/usr/bin/env python3
"""
DonkeyCar motor test script for PiRacer Pro AI Kit
Based on DonkeyCar PWM controller implementation
"""

import time
import smbus2

class PCA9685:
    """
    DonkeyCar-style PCA9685 PWM controller
    """
    def __init__(self, channel=1, address=0x40, frequency=60):
        self.bus = smbus2.SMBus(channel)
        self.address = address
        self.frequency = frequency
        self.init_pca9685()
    
    def init_pca9685(self):
        """Initialize PCA9685 with DonkeyCar settings"""
        # Wake up
        self.bus.write_byte_data(self.address, 0x00, 0x00)
        time.sleep(0.01)
        
        # Set frequency (DonkeyCar typically uses 60Hz for servos/ESCs)
        prescale = int(25000000.0 / (4096.0 * self.frequency) - 1.0)
        
        old_mode = self.bus.read_byte_data(self.address, 0x00)
        sleep_mode = (old_mode & 0x7F) | 0x10
        self.bus.write_byte_data(self.address, 0x00, sleep_mode)
        self.bus.write_byte_data(self.address, 0xFE, prescale)
        self.bus.write_byte_data(self.address, 0x00, old_mode)
        time.sleep(0.01)
        self.bus.write_byte_data(self.address, 0x00, old_mode | 0x20)
        
        print(f"PCA9685 initialized at {self.frequency}Hz for DonkeyCar")
    
    def set_pulse(self, channel, pulse_ms):
        """
        Set pulse width in milliseconds (DonkeyCar style)
        Typical servo range: 1.0ms to 2.0ms (center at 1.5ms)
        """
        if pulse_ms < 0.5:
            pulse_ms = 0.5
        elif pulse_ms > 2.5:
            pulse_ms = 2.5
        
        # Convert ms to 12-bit value
        pulse_length = 1000000.0 / self.frequency / 4096.0  # microseconds per bit
        pulse_value = int(pulse_ms * 1000.0 / pulse_length)
        
        self.set_pwm(channel, 0, pulse_value)
    
    def set_pwm(self, channel, on, off):
        """Set PWM values for channel"""
        base_reg = 0x06 + 4 * channel
        self.bus.write_byte_data(self.address, base_reg, on & 0xFF)
        self.bus.write_byte_data(self.address, base_reg + 1, on >> 8)
        self.bus.write_byte_data(self.address, base_reg + 2, off & 0xFF)
        self.bus.write_byte_data(self.address, base_reg + 3, off >> 8)
    
    def stop_all_channels(self):
        """Stop all PWM channels completely"""
        for channel in range(16):
            # Set all PWM registers to 0 to completely stop output
            base_reg = 0x06 + 4 * channel
            self.bus.write_byte_data(self.address, base_reg, 0)      # ON_L
            self.bus.write_byte_data(self.address, base_reg + 1, 0)  # ON_H
            self.bus.write_byte_data(self.address, base_reg + 2, 0)  # OFF_L
            self.bus.write_byte_data(self.address, base_reg + 3, 0)  # OFF_H
        print("All PWM channels completely stopped")
    
    def close(self):
        """Close I2C bus"""
        self.bus.close()

class DonkeyCarController:
    """
    DonkeyCar-style motor and steering controller
    """
    def __init__(self):
        self.pwm = PCA9685(frequency=60)  # 60Hz for servos/ESCs
        
        # Correct channel assignments for this PiRacer
        self.steering_channel = 0  # Steering servo (Channel 0)
        self.throttle_channel = 1  # ESC/Motor controller (Channel 1)
        
        # DonkeyCar pulse width ranges (in milliseconds)
        # Calibrated servo range for this PiRacer
        self.steering_center = 1.8   # User preferred center position
        self.steering_range = 0.5    # +/- 0.5ms from center (1.3ms to 2.3ms)
        # Full range: Right=1.3ms, Center=1.8ms, Left=2.3ms
        
        self.throttle_neutral = 1.5
        self.throttle_range = 0.4   # +/- 0.4ms from neutral
        
        print("DonkeyCar controller initialized")
        print(f"Steering channel: {self.steering_channel}")
        print(f"Throttle channel: {self.throttle_channel}")
        
        # Initialize to neutral positions
        self.set_steering(0)
        self.set_throttle(0)
    
    def set_steering_center(self, center_ms):
        """Update the steering center value"""
        self.steering_center = center_ms
        print(f"Steering center updated to {center_ms:.3f}ms")
    
    def set_steering(self, angle):
        """
        Set steering angle
        angle: -1.0 (full left) to +1.0 (full right), 0 = center
        """
        if angle < -1.0:
            angle = -1.0
        elif angle > 1.0:
            angle = 1.0
        
        pulse_ms = self.steering_center + (angle * self.steering_range)
        self.pwm.set_pulse(self.steering_channel, pulse_ms)
        print(f"Steering: {angle:.2f} ({pulse_ms:.3f}ms, center={self.steering_center:.3f}ms)")
    
    def set_throttle(self, speed):
        """
        Set throttle/motor speed
        speed: -1.0 (full reverse) to +1.0 (full forward), 0 = stop
        """
        if speed < -1.0:
            speed = -1.0
        elif speed > 1.0:
            speed = 1.0
        
        pulse_ms = self.throttle_neutral + (speed * self.throttle_range)
        self.pwm.set_pulse(self.throttle_channel, pulse_ms)
        print(f"Throttle: {speed:.2f} ({pulse_ms:.3f}ms)")
    
    def stop(self):
        """Stop motor and center steering"""
        self.set_throttle(0)
        self.set_steering(0)
        print("Stopped - throttle neutral, steering centered")
    
    def cleanup(self):
        """Clean up and stop all PWM output"""
        self.stop()  # Set neutral positions first
        self.pwm.stop_all_channels()  # Then completely stop all PWM output
        self.pwm.close()
        print("DonkeyCar controller cleanup completed - all PWM stopped")

def test_donkey_car():
    """Test DonkeyCar motor and steering"""
    print("=== DonkeyCar Motor Test ===")
    print("Testing PiRacer with DonkeyCar-style control")
    
    try:
        car = DonkeyCarController()
        
        print("\n1. Testing steering...")
        print("Center steering...")
        car.set_steering(0)
        time.sleep(1)
        
        print("Left steering...")
        car.set_steering(-0.5)
        time.sleep(1)
        
        print("Right steering...")
        car.set_steering(0.5)
        time.sleep(1)
        
        print("Center steering...")
        car.set_steering(0)
        time.sleep(1)
        
        print("\n2. Testing throttle...")
        print("Neutral throttle...")
        car.set_throttle(0)
        time.sleep(2)
        
        print("Slow forward...")
        car.set_throttle(0.2)
        time.sleep(3)
        
        print("Stop...")
        car.set_throttle(0)
        time.sleep(2)
        
        print("Slow reverse...")
        car.set_throttle(-0.2)
        time.sleep(3)
        
        print("Stop...")
        car.set_throttle(0)
        time.sleep(1)
        
        print("\n3. Testing combined movements...")
        print("Forward with left turn...")
        car.set_throttle(0.3)
        car.set_steering(-0.3)
        time.sleep(2)
        
        print("Forward with right turn...")
        car.set_steering(0.3)
        time.sleep(2)
        
        print("Stop and center...")
        car.stop()
        time.sleep(1)
        
        print("\n4. Testing speed variations...")
        speeds = [0.1, 0.2, 0.3, 0.4]
        for speed in speeds:
            print(f"Forward at {speed:.1f}...")
            car.set_throttle(speed)
            time.sleep(1.5)
            car.set_throttle(0)
            time.sleep(0.5)
        
        print("\nDonkeyCar test completed successfully!")
        car.cleanup()
        return True
        
    except Exception as e:
        print(f"DonkeyCar test failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            car.cleanup()
        except:
            pass
        return False

def test_simple_donkey():
    """Simple DonkeyCar test"""
    print("=== Simple DonkeyCar Test ===")
    
    try:
        car = DonkeyCarController()
        
        print("Testing forward...")
        car.set_throttle(0.2)
        time.sleep(2)
        car.set_throttle(0)
        
        print("Testing reverse...")
        car.set_throttle(-0.2)
        time.sleep(2)
        car.set_throttle(0)
        
        print("Testing steering...")
        car.set_steering(-0.5)
        time.sleep(1)
        car.set_steering(0.5)
        time.sleep(1)
        car.set_steering(0)
        
        print("Simple DonkeyCar test completed!")
        car.cleanup()
        return True
        
    except Exception as e:
        print(f"Simple test failed: {e}")
        return False

def debug_motor_channels():
    """Debug which channel the motor is actually on"""
    print("=== MOTOR CHANNEL DEBUG ===")
    print("Testing all channels to find the motor")
    
    try:
        pwm = PCA9685(frequency=60)
        
        # Test channels 0-7 for motor response
        for channel in range(8):
            print(f"\n--- Testing Channel {channel} ---")
            
            # Test forward pulse
            print(f"Channel {channel}: Forward (1.7ms)")
            pwm.set_pulse(channel, 1.7)
            time.sleep(3)
            
            # Test reverse pulse
            print(f"Channel {channel}: Reverse (1.3ms)")
            pwm.set_pulse(channel, 1.3)
            time.sleep(3)
            
            # Stop
            print(f"Channel {channel}: Stop (1.5ms)")
            pwm.set_pulse(channel, 1.5)
            time.sleep(1)
            
            # Ask user for feedback
            print(f"Did Channel {channel} move the MOTOR? (not servo)")
            
        # Test extreme pulse widths on suspected channels
        print("\n--- Testing Extreme Pulse Widths ---")
        for channel in [1, 2, 3]:
            print(f"\nChannel {channel} extreme test:")
            
            # Very wide range test
            test_pulses = [0.8, 1.0, 1.2, 1.8, 2.0, 2.2]
            for pulse in test_pulses:
                print(f"Channel {channel}: {pulse:.1f}ms")
                pwm.set_pulse(channel, pulse)
                time.sleep(2)
            
            # Back to neutral
            pwm.set_pulse(channel, 1.5)
            time.sleep(1)
        
        pwm.stop_all_channels()
        pwm.close()
        print("\nDEBUG COMPLETE - Report which channel moved the motor")
        return True
        
    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("DonkeyCar PiRacer Motor Test")
    print("Compatible with DonkeyCar framework")
    print("\nMake sure:")
    print("1. PiRacer is on a stand or wheels are off the ground")
    print("2. Battery is connected and charged")
    print("3. ESC is calibrated (if using brushless motor)")
    print("\nPress Ctrl+C to stop at any time")
    
    try:
        choice = input("\nChoose: (1) Full test, (2) Simple test, (3) Debug motor channels, or Enter for simple: ")
        if choice == "1":
            test_donkey_car()
        elif choice == "3":
            debug_motor_channels()
        else:
            test_simple_donkey()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")