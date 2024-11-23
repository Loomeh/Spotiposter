import network
import socket
from time import sleep
from picozero import pico_led, DistanceSensor
import machine

# Network credentials
ssid = ''
password = ''

# Initialize ultrasonic sensor
ultrasonic = DistanceSensor(echo=26, trigger=27)

def connect():
    """Connect to WiFi network"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    print(f'Network config: {wlan.ifconfig()}')  # Print full network configuration
    return ip

def send_signal(host, port):
    """Send trigger signal to server with debug info"""
    print(f"Attempting to connect to {host}:{port}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(5.0)  # Set timeout for connection attempts
        print("Connecting...")
        s.connect((host, port))
        print("Connected! Sending data...")
        s.sendall(b'\x01')
        
        # Wait for acknowledgment
        try:
            ack = s.recv(1024)
            print(f"Received acknowledgment: {ack}")
        except Exception as e:
            print(f"No acknowledgment received: {e}")
            
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        s.close()
        print("Socket closed")

# Connect to WiFi
try:
    ip = connect()
except KeyboardInterrupt:
    machine.reset()

prev_trigger = False

# Main loop
while True:
    try:
        trigger = (ultrasonic.distance <= 0.1)
        
        if trigger and not prev_trigger:
            print("\n--- New trigger detected ---")
            pico_led.on()  # Visual indicator
            send_signal("192.168.1.64", 5001)
            pico_led.off()
            
        prev_trigger = trigger
        sleep(0.1)
        
    except Exception as e:
        print(f"Error in main loop: {e}")
        sleep(1)
