#!/usr/bin/env python3
"""
PiRacer Demo Script - Slow Circling for 1 Minute
Demonstrates working motor and steering control
"""

import time
import smbus2
import signal
import sys

class PCA9685:
    """PCA9685 PWM controller for PiRacer"""
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
    
    def set_pulse(self, channel, pulse_ms):
        """Set pulse width in milliseconds"""
        pulse_length = 1000000.0 / self.frequency / 4096.0
        pulse_value = int(pulse_ms * 1000.0 / pulse_length)
        base_reg = 0x06 + 4 * channel
        self.bus.write_byte_data(self.address, base_reg, 0)
        self.bus.write_byte_data(self.address, base_reg + 1, 0)
        self.bus.write_byte_data(self.address, base_reg + 2, pulse_value & 0xFF)
        self.bus.write_byte_data(self.address, base_reg + 3, pulse_value >> 8)
    
    def stop_all_channels(self):
        """Stop all PWM channels"""
        for channel in range(16):
            base_reg = 0x06 + 4 * channel
            self.bus.write_byte_data(self.address, base_reg, 0)
            self.bus.write_byte_data(self.address, base_reg + 1, 0)
            self.bus.write_byte_data(self.address, base_reg + 2, 0)
            self.bus.write_byte_data(self.address, base_reg + 3, 0)
    
    def close(self):
        """Close I2C bus"""
        self.bus.close()

class PiRacerDemo:
    """PiRacer demo controller"""
    def __init__(self):
        self.pwm = PCA9685(frequency=60)
        
        # Channel assignments
        self.steering_channel = 0  # Servo
        self.throttle_channel = 1  # Motor
        
        # Calibrated values
        self.steering_center = 1.8
        self.steering_left = 1.55    # Left turn
        self.steering_right = 2.05   # Right turn
        
        self.throttle_neutral = 1.5
        self.throttle_slow_forward = 1.67  # Slow forward speed
        
        print("PiRacer Demo Controller initialized")
        print("Channels: Steering=0, Throttle=1")
        
        # Start in neutral
        self.stop()
    
    def set_steering(self, pulse_ms):
        """Set steering position"""
        self.pwm.set_pulse(self.steering_channel, pulse_ms)
    
    def set_throttle(self, pulse_ms):
        """Set throttle position"""
        self.pwm.set_pulse(self.throttle_channel, pulse_ms)
    
    def stop(self):
        """Stop and center"""
        self.set_throttle(self.throttle_neutral)
        self.set_steering(self.steering_center)
    
    def cleanup(self):
        """Clean shutdown"""
        self.stop()
        time.sleep(0.5)
        self.pwm.stop_all_channels()
        self.pwm.close()
        print("Demo cleanup completed - all PWM stopped")

# Global demo instance for signal handler
demo = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nDemo interrupted by user")
    if demo:
        demo.cleanup()
    sys.exit(0)

def run_demo():
    """Run the circling demo for 1 minute"""
    global demo
    
    print("=== PiRacer Circling Demo ===")
    print("Duration: 1 minute")
    print("Motion: Slow forward with left turn (circling)")
    print("Press Ctrl+C to stop early")
    print("\nMake sure:")
    print("1. PiRacer has enough space to circle")
    print("2. Battery is connected and charged")
    print("3. You can safely stop the demo if needed")
    
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        demo = PiRacerDemo()
        
        print("\nStarting demo in 3 seconds...")
        time.sleep(1)
        print("3...")
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        print("GO!")
        
        # Record start time
        start_time = time.time()
        demo_duration = 60  # 1 minute
        
        # Set slow forward and left turn for circling
        print(f"Setting slow forward ({demo.throttle_slow_forward:.1f}ms) and left turn ({demo.steering_left:.2f}ms)")
        demo.set_throttle(demo.throttle_slow_forward)  # Slow forward
        demo.set_steering(demo.steering_left)          # Left turn for circling
        
        # Run for 1 minute with status updates
        while True:
            elapsed = time.time() - start_time
            remaining = demo_duration - elapsed
            
            if elapsed >= demo_duration:
                break
            
            # Print status every 10 seconds
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(f"Demo running... {remaining:.0f} seconds remaining")
            
            time.sleep(1)
        
        print("\nDemo completed! Stopping...")
        demo.stop()
        time.sleep(2)
        
        print("Demo finished successfully!")
        demo.cleanup()
        return True
        
    except Exception as e:
        print(f"Demo failed: {e}")
        if demo:
            demo.cleanup()
        return False

if __name__ == "__main__":
    run_demo()