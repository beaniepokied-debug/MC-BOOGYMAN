from machine import Pin, PWM
import bluetooth
from micropython import const
from time import sleep


def mapD_GPIO(pin_number:int) -> int:
	if pin_number >= 0 and pin_number <= 5:
		value = int(pin_number + 2)  # GPIO 0-5
	elif pin_number == 6:
		value = int(21)  # GPIO 6
	elif pin_number == 7:
		value = int(20)  # GPIO 6
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
		self.pwm = PWM(pwm, freq=1000)  # Initialize PWM on the specified pin with a frequency of 1kHz
		self.pinA = Pin(pinA, Pin.OUT)
		self.pinB = Pin(pinB, Pin.OUT)
		self.state = 0  # 0: stopped, 1: forward, -1: backward

		self.pwm.duty_u16(32768)  # Start with 0% duty cycle (motor off)
	def status(self):
		return self.state
	def forward(self):
		if self.state != 1:  # Only change state if not already moving forward
			self.pinB.on()
			self.pinA.off()
			self.state = 1
		else:
			self.stop()
			self.state = 0  # Reset state to stopped if already moving forward

	def backward(self):
		if self.state != -1:  # Only change state if not already moving backward
			self.pinA.on()
			self.pinB.off()
			self.state = -1
		else:
			self.stop()
			self.state = 0  # Reset state to stopped if already moving backward

	def speed(self, speed:int):
		if speed < 0 or speed > 100:
			raise ValueError("Speed must be between 0 and 100")
		duty = int((speed / 100) * 65535)  # Convert speed percentage to duty cycle
		if duty < 0 or duty > 65535:
			raise ValueError("Duty cycle must be between 0 and 65535")
		self.pwm.duty_u16(duty)
		print(f"Motor speed set to {speed}% (duty cycle: {duty})")

	def stop(self):
		self.pinA.off()
		self.pinB.off()

class Servo:
	def __init__(self, pin):
		self.servo = PWM(pin)
		self.pin = pin
		self.servo.freq(50)  # Set frequency to 50Hz for standard servo

	def set_angle(self, angle):
		self.servo.duty_u16(0)
		sleep(0.1)  # Allow time for the servo to stop before changing angle
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


motor2 = Motor(mapD_GPIO(0), mapD_GPIO(1), mapD_GPIO(2))
motor1 = Motor(mapD_GPIO(3), mapD_GPIO(4), mapD_GPIO(5))


motor1.stop()
motor2.stop()

servo1 = Servo(mapD_GPIO(10))

flashLED(10)  # Flash the LED 10 times to indicate that the program has started


###START OF BLE CODE (Mostly copied from web)
def bluetooth_init():
	global _IRQ_CENTRAL_CONNECT
	global _IRQ_CENTRAL_DISCONNECT
	global _IRQ_GATTS_WRITE
	global _UART_UUID
	global _UART_TX
	global _UART_RX
	global _UART_SERVICE
	global NAME
	#Define BLE CONSTANTS
	_IRQ_CENTRAL_CONNECT = const(1)
	_IRQ_CENTRAL_DISCONNECT = const(2)
	_IRQ_GATTS_WRITE = const(3)
	# Nordic UART Service (NUS) - standard UUIDs recognized by most BLE terminal apps
	_UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
	_UART_TX = (bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_NOTIFY)
	_UART_RX = (bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_WRITE)
	_UART_SERVICE = (_UART_UUID, (_UART_TX, _UART_RX))

	NAME = b'KING_BOB'

	global ble, tx_handle, rx_handle
	# Initialize BLE
	ble = bluetooth.BLE()
	ble.active(True)
	((tx_handle, rx_handle),) = ble.gatts_register_services((_UART_SERVICE,))

bluetooth_init()

#Input interpreter for BLE messages (Handwritten)
def message_received(msg, analog_on=False):
	if analog_on == False:
		print('Message received:', msg)
		if msg == 'Drive':
			print("Toggle motor drive")
			motor1.forward()
			motor2.forward()

		elif msg == 'Reverse':
			print("Toggle motor reverse")
			motor1.backward()
			motor2.backward()

		elif msg == 'Stop':
			print("Stop motor")
			motor1.stop()
			motor2.stop()

		elif msg == 'LED':
			print("Flash LED")
			flashLED()

		elif msg == 'LEFT':
			print("Turn Left")
			servo1.set_angle(70)

		elif msg == 'RIGHT':
			print("Toggle Turn Right")
			servo1.set_angle(130)

		elif msg == 'UP':
			print("Toggle Forward")
			servo1.set_angle(90)
		elif "S_" in msg:
			try:
				speed_value = int(msg.split('_')[1])
				print(f"Setting motor speed to {speed_value}%")
				motor1.speed(speed_value)
				motor2.speed(speed_value)
			except ValueError:
				print("Invalid speed value received. Please send a valid integer between 0 and 100.")
		else:
			print("Unknown command")
	else:
		print('Message received:', msg)
		if msg == 'D':
			print("Toggle motor drive")
			motor1.forward()
			motor2.forward()

		elif msg == 'Reverse':
			print("Toggle motor reverse")
			motor1.backward()
			motor2.backward()

		elif msg == 'Stop':
			print("Stop motor")
			motor1.stop()
			motor2.stop()

		elif msg == 'LED':
			print("Flash LED")
			flashLED()

		elif msg == 'LEFT':
			print("Turn Left")
			servo1.set_angle(70)

		elif msg == 'RIGHT':
			print("Toggle Turn Right")
			servo1.set_angle(130)

		elif msg == 'UP':
			print("Toggle Forward")
			servo1.set_angle(90)
		elif "S_" in msg:
			try:
				speed_value = int(msg.split('_')[1])
				print(f"Setting motor speed to {speed_value}%")
				motor1.speed(speed_value)
				motor2.speed(speed_value)
			except ValueError:
				print("Invalid speed value received. Please send a valid integer between 0 and 100.")
		else:
			print("Unknown command")


def advertise():
	adv_data = bytearray(b'\x02\x01\x06') + bytearray((len(NAME) + 1, 0x09)) + NAME
	ble.gap_advertise(100, adv_data)
	print('Advertising as', NAME)

def irq(event, data):
	if event == _IRQ_CENTRAL_CONNECT:
		print('Phone connected')
	elif event == _IRQ_CENTRAL_DISCONNECT:
		print('Phone disconnected')
		advertise()  # start advertising again so it can reconnect
	elif event == _IRQ_GATTS_WRITE:
		conn_handle, attr_handle = data
		if attr_handle == rx_handle:
			msg = ble.gatts_read(rx_handle).decode()
			message_received(msg)

#Hosts BLE server

ble.irq(irq)
advertise()

while True:
	sleep(1)