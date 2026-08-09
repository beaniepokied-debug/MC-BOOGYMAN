from machine import PWM
import time

class Servo:
	def __init__(self, pin):
		self.servo = PWM(pin)
		self.pin = pin
		self.servo.freq(50)  # Set frequency to 50Hz for standard servo

	def set_angle(self, angle):
		self.servo.duty_u16(0)
		time.sleep(0.1)  # Allow time for the servo to stop before changing angle
		if angle < 0 or angle > 180:
			raise ValueError("Angle must be between 0 and 180 degrees")
		
		# Convert angle (0-180) to duty cycle (0-65535)
		pulse_width = float(0.5 + (angle / 180)*2)  # Pulse width in microseconds (1ms to 2ms)
		duty = int(((pulse_width)/20.0) * 65535)  # Map angle to duty cycle
		if (duty < 0 or duty > 65535):
			raise ValueError("Duty cycle must be between 0 and 65535")
		
		print(f"Setting angle to {angle} degrees, duty cycle: {duty}, pulse width: {pulse_width}ms")
		self.servo.duty_u16(duty)

	def stop(self):
		self.servo.deinit()  # Stop the PWM signal
		print("Stopping servo PWM signal.")


print("Servo test script loaded. Use obj.set_angle(angle) to set the servo angle.")
obj = Servo(10)  # Initialize servo on pin D10


obj.set_angle(90)  # Set initial angle to 90 degrees

time.sleep(8)
while True:
	time.sleep(2)
	print("Hgdjsjg")
	obj.set_angle(0)
	time.sleep(2)
	print("Hgdjsjg")
	obj.set_angle(90)
	time.sleep(2)
	print("Hgdjsjg")
	obj.set_angle(180)