#Imports Nessasary Libaries
import bluetooth
import time
from micropython import const

# Define BLE Event Connect and Disconnect Constants(Const used for optimization in compiler, regular int 1,2 work)
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

class XiaoBLE:
    #Initiates Bluetooth Device with name
    def __init__(self, name="XIAO-C3-BLE"):
        #Creates Bluetooth Object and Enables it
        self.ble = bluetooth.BLE()
        self.ble.active(True)

		#Interrupt handler for BLE events (connect/disconnect)
        self.ble.irq(self._ble_irq)

		#Sets the device name for advertising
        self.name = name
        
        # Define a simple custom service and characteristic 
        # (Using a standard 16-bit UUID for testing)
        _SERVICE_UUID = bluetooth.UUID(0x181A) # Environmenstal Sensing Service
        _CHAR_UUID = bluetooth.UUID(0x2A6E)    # Temperature Characteristic
        
        # Register the service (Read property enabled)
        # Type flags: 0x02 = Read
        _CHAR = (_CHAR_UUID, bluetooth.FLAG_READ,)
        _SERVICE = (_SERVICE_UUID, (_CHAR,),)
        
        ((self.char_handle,),) = self.ble.gatts_register_services((_SERVICE,))
        
        # Start advertising the device name
        self.advertise()

    def _ble_irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            print(f"[{time.ticks_ms()}] Central device connected!")
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            print(f"[{time.ticks_ms()}] Central device disconnected. Re-advertising...")
            self.advertise()

    def advertise(self):
        # Payload construction for BLE advertising packets
        name_bytes = self.name.encode('utf-8')
        payload = bytearray([
            2, 0x01, 0x06,                  # Flags: General discoverable mode
            len(name_bytes) + 1, 0x09       # 0x09 standard data type for Complete Local Name
        ]) + name_bytes
        
        # Broadcast interval = 100ms (100000 microseconds)
        self.ble.gap_advertise(100000, payload, resp_data=None, connectable=True)

    def update_value(self, number):
        # Write dummy data to the characteristic (e.g., packing an integer)
        # Convert integer to a 2-byte little-endian format
        data = int(number).to_bytes(2, 'little')
        self.ble.gatts_write(self.char_handle, data)

# --- Execution ---
print("Initializing BLE on XIAO ESP32C3...")
xiao_ble = XiaoBLE()

# Mock loop: Changes the characteristic value every 2 seconds
counter = 20
while True:
    xiao_ble.update_value(counter)
    print(f"Updated sensor data value to: {counter}")
    counter += 1
    if counter > 40:
        counter = 20
    time.sleep(2)
