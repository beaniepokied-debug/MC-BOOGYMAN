from machine import Pin, PWM
import bluetooth
from micropython import const
from time import sleep
import math

def mapD_GPIO(pin_number:int) -> int:
	if pin_number >= 0 and pin_number <= 5:
		value = int(pin_number + 2)  # GPIO 0-5
	elif pin_number == 6:
		value = int(21)  # GPIO 6
	elif pin_number == 7:
		value = int(20)  # GPIO 7
	elif pin_number >= 8 and pin_number <= 10:
		value = int(pin_number)  # GPIO 8-10
	return int(value)

myLED = Pin(mapD_GPIO(8), Pin.OUT)
SW = Pin(mapD_GPIO(7), Pin.IN, Pin.PULL_DOWN)

def flashLED(repeat=3):
	for i in range(repeat):
		myLED.on()
		sleep(0.3)
		myLED.off()
		sleep(0.3)
	print("LED flash complete.")

class Motor:
	def __init__(self, pwm:int, pinA:int, pinB:int):
		self.pwm = PWM(Pin(pwm), freq=1000)  # Wrap the integer pin number in Pin() object
		self.pinA = Pin(pinA, Pin.OUT)
		self.pinB = Pin(pinB, Pin.OUT)
		self.state = 0  # 0: stopped, 1: forward, -1: backward
		self.pwm.duty_u16(32768)  # Start with 50% initial duty cycle helper
		
	def status(self):
		return self.state
		
	def forward(self):
		if self.state != 1:
			self.pinB.on()
			self.pinA.off()
			self.state = 1
		else:
			self.stop()
			self.state = 0

	def backward(self):
		if self.state != -1:
			self.pinA.on()
			self.pinB.off()
			self.state = -1
		else:
			self.stop()
			self.state = 0

	def speed(self, speed:int):
		if speed < 0 or speed > 100:
			raise ValueError("Speed must be between 0 and 100")
		if speed < 20:
			speed = 0
		duty = int((speed / 100) * 65535)
		if duty < 0 or duty > 65535:
			raise ValueError("Duty cycle must be between 0 and 65535")
		self.pwm.duty_u16(duty)
		print(f"Motor speed set to {speed}% (duty cycle: {duty})")

	def stop(self):
		self.pinA.off()
		self.pinB.off()

class Servo:
	def __init__(self, pin):
		self.servo = PWM(Pin(pin))  # Wrap the integer pin number in Pin() object
		self.pin = pin
		self.servo.freq(50)

	def set_angle(self, angle):
		self.servo.duty_u16(0)
		sleep(0.1)
		if angle < 0 or angle > 180:
			raise ValueError("Angle must be between 0 and 180 degrees")
		
		pulse_width = float(0.5 + (angle / 180)*2)
		duty = int(((pulse_width)/20.0) * 65535)
		if (duty < 0 or duty > 65535):
			raise ValueError("Duty cycle must be between 0 and 65535")
		
		print(f"Setting angle to {angle} degrees, duty cycle: {duty}, pulse width: {pulse_width}ms")
		self.servo.duty_u16(duty)

	def stop(self):
		self.servo.deinit()
		print("Stopping servo PWM signal.")

def joystick_to_angle(angle, mag):
	if mag < 0.05:
		return 90  # Neutral position
	x = float(math.cos(angle/180 * math.pi))  # Convert angle to radians and compute cosine
	return int(90 + (x * 45)*mag)  # Scale to a range of 50-130 degrees
		
	

# Instantiate Hardware Modules
motor2 = Motor(mapD_GPIO(0), mapD_GPIO(1), mapD_GPIO(2))
motor1 = Motor(mapD_GPIO(3), mapD_GPIO(4), mapD_GPIO(5))

motor1.stop()
motor2.stop()

servo1 = Servo(mapD_GPIO(10))
flashLED(10)

### START OF BLE CODE
def bluetooth_init():
	global _IRQ_CENTRAL_CONNECT, _IRQ_CENTRAL_DISCONNECT, _IRQ_GATTS_WRITE
	global _SERIAL_SERVICE, NAME, ble, tx_handle, rx_handle
	
	# Define BLE CONSTANTS
	_IRQ_CENTRAL_CONNECT = const(1)
	_IRQ_CENTRAL_DISCONNECT = const(2)
	_IRQ_GATTS_WRITE = const(3)
	
	# Updated to FFE0 Custom Serial Profile UUID mappings
	_SERVICE_UUID = bluetooth.UUID(0xFFE0)
	_CHAR_UUID = bluetooth.UUID(0xFFE1)
	
	# Characteristic allows writing (rx) and notifying (tx)
	_SERIAL_CHAR = (_CHAR_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE | bluetooth.FLAG_NOTIFY)
	_SERIAL_SERVICE = (_SERVICE_UUID, (_SERIAL_CHAR,))

	NAME = b'MW_XIAO-C3'

	# Initialize BLE Stack
	ble = bluetooth.BLE()
	ble.active(True)
	
	# Register layout returns a tuple of lists containing dynamic attribute handles
	((handles,),) = ble.gatts_register_services((_SERIAL_SERVICE,))
	tx_handle = handles
	rx_handle = handles # For single-characteristic serial (FFE1), RX and TX share the same link handle



def message_received(msg):
	# Strips away unexpected trailing whitespace/newlines from mobile terminals
	msg = msg.strip()
	print('Message received:', msg)
	
	if msg in ['T0:0', 'D']:
		print("Toggle motor drive")
		motor1.forward()
		motor2.forward()
	elif msg in ['T0:1', "R"]:
		print("Toggle motor reverse")
		motor1.backward()
		motor2.backward()
	elif msg in ['B0:D', 'B0:U']:
		print("Stop motor")
		motor1.stop()
		motor2.stop()
	elif msg in ['B1:D', 'B1:U']:
		print("Flash LED")
		flashLED()
	elif "J0:" in msg:
		try:
			angle = joystick_to_angle(int(msg.split(':')[1].split(',')[0]), float(msg.split(':')[1].split(',')[1]))
			print(f"Setting servo angle to {angle} degrees")
			servo1.set_angle(angle)
		except ValueError:
			print("Invalid angle received.")
		sleep(3)  # Cooldown to prevent rapid-fire commands

	elif "S0:" in msg:
		try:
			speed_value = int(msg.split(':')[1])
			print(f"Setting motor speed to {speed_value}%")
			motor1.speed(speed_value)
			motor2.speed(speed_value)
		except ValueError:
			print("Invalid speed value received.")
	else:
		print("Unknown command")

def advertise():
	# Simple BLE payload string matching the KING_BOB identifier layout
	adv_data = bytearray(b'\x02\x01\x06') + bytearray((len(NAME) + 1, 0x09)) + NAME
	ble.gap_advertise(100, adv_data)
	print('Advertising as', NAME)

def irq(event, data):
	if event == _IRQ_CENTRAL_CONNECT:
		print('Phone connected')
	elif event == _IRQ_CENTRAL_DISCONNECT:
		print('Phone disconnected')
		advertise()
	elif event == _IRQ_GATTS_WRITE:
		conn_handle, attr_handle = data
		if attr_handle == rx_handle:
			# Safely capture incoming byte strings and transform them into readable strings
			msg = ble.gatts_read(rx_handle).decode('utf-8')
			message_received(msg)

# Run initialization procedures
bluetooth_init()
ble.irq(irq)
advertise()

# Main infinite run loop to keep the asynchronous BLE stack alive
while True:
	sleep(1)
