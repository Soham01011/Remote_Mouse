import io
from tkinter import *
import asyncio
import websockets
import pyautogui
import psutil
import json
import os
import socket
import threading
import sys
import time
import pygetwindow as gw
import subprocess
import uuid
import hashlib
import qrcode
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from comtypes import CLSCTX_ALL
from PIL import Image, ImageTk, ImageGrab

client_ip = None
qr_show = True
broadcasting = True
connected_clients = set()


async def main(current_conn):
    broadcast_task = asyncio.create_task(broadcast_server_ready())

    general_server = await websockets.serve(lambda ws, path: handle_client(ws, path, current_conn, broadcast_task), "0.0.0.0", 9999)
    mouse_server = await websockets.serve(lambda ws, path: handle_client(ws, path, current_conn, broadcast_task), "0.0.0.0", 9998)
    app_list_server = await websockets.serve(lambda ws, path: handle_client(ws, path, current_conn, broadcast_task), "0.0.0.0", 9997)
    screen_mirror_server = await websockets.serve(lambda ws, path: handle_client(ws, path, current_conn, broadcast_task), "0.0.0.0", 9996)

    await asyncio.gather(
        general_server.wait_closed(),
        mouse_server.wait_closed(),
        app_list_server.wait_closed(),
        screen_mirror_server.wait_closed(),
    )


async def authorize_user(websocket, message, current_conn, broadcast_task):
    global client_ip, broadcasting
    data = json.loads(message)

    if data.get("password") == pwd_entry.get() and broadcasting:
        await websocket.send(json.dumps({"status": "authenticated"}))
        client_ip = websocket.remote_address[0]
        current_conn.config(text=f"Connected: {client_ip}")
        broadcasting = False  
        broadcast_task.cancel()  

    elif "client_ip" in data and data.get("client_ip") == websocket.remote_address[0] and not broadcasting:
        client_ip = websocket.remote_address[0]
        print(f"Client IP authenticated: {client_ip}")
        await websocket.send(json.dumps({"status": "authenticated"}))
        current_conn.config(text=f"Connected: {client_ip}")
        broadcasting = False  
        broadcast_task.cancel()  

    else:
        await websocket.send(json.dumps({"status": "unauthorized"}))

async def broadcast_server_ready():
    device_name = socket.gethostname()
    server_ip = socket.gethostbyname(socket.gethostname())
    password = pwd_entry.get()
    broadcast_port = 9995  # The port the Flutter app is listening on
    message = f"IP: {server_ip}, Device: {device_name},Password : {password}".encode('utf-8')

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while broadcasting:
        udp_socket.sendto(message, ('<broadcast>', broadcast_port))  # Send broadcast
        print(f"Broadcasting message: {message}")
        await asyncio.sleep(5)

async def handle_client(websocket, path, current_conn, broadcast_task):
    global current_dir
    async for message in websocket:
        try:
            if path == "/auth":
                await authorize_user(websocket, message, current_conn, broadcast_task)
            elif path == "/mouse":
                await handle_mouse_command(websocket, message)
            elif path == "/apps":
                await handle_apps_command(websocket)
            elif path == "/screen_mirror":
                await handle_screen_mirroring(websocket)
            else:
                await handle_general_command(websocket, message)
        except Exception as e:
            print(f"Error handling command '{message}': {e}")
    else:
        await websocket.send(json.dumps({"status": "unauthorized"}))

def quickStart(search):
    pyautogui.press('win')
    pyautogui.write(search)
    pyautogui.press('enter')

async def handle_apps_command(websocket):
    if(client_ip == websocket.remote_address[0]):
        running_apps = get_running_apps()
        await websocket.send(json.dumps(running_apps))

def get_running_apps():
    running_apps = []
    for window in gw.getAllTitles():
        if str(window) in {'', 'Windows Input Experience', 'Program Manager','NVIDIA GeForce Overlay'}:
            pass
        else:
            running_apps.append({"name": window})
    return running_apps

def focus_app(app_name, action):
    try:
        windows = gw.getWindowsWithTitle(app_name)
        
        if not windows:
            return f"Application {app_name} not found"
        
        window = windows[0]

        if action == 'open':
            window.activate()
            return f"Focused on {app_name}"
        elif action == 'close':
            window.close()
            return f"Closed {app_name}"
        else:
            return f"Unknown action {action} for {app_name}"
    except Exception as e:
        return f"Error focusing on {app_name}: {e}"
def hotkey(command):
    if(command == "COPY"):
        pyautogui.keyDown("ctrl")
        pyautogui.keyDown('c')
        pyautogui.keyUp('c')
        pyautogui.keyUp('ctrl')        
    elif(command == "COPY"):
        pyautogui.keyDown("ctrl")
        pyautogui.keyDown('v')
        pyautogui.keyUp('v')
        pyautogui.keyUp('ctrl') 
    elif(command == "ATL_TAB"):
        pyautogui.keyDown("atl")
        pyautogui.keyDown('tab')
        pyautogui.keyUp('tab')
        pyautogui.keyUp('alt') 
    elif(command == "UNDO"):
        pyautogui.keyDown("ctrl")
        pyautogui.keyDown('z')
        pyautogui.keyUp('z')
        pyautogui.keyUp('ctrl') 
    elif(command == "REDO"):
        pyautogui.keyDown("ctrl")
        pyautogui.keyDown('y')
        pyautogui.keyUp('y')
        pyautogui.keyUp('ctrl') 
    elif(command == "ATL_F4"):
        pyautogui.keyDown('alt')
        pyautogui.keyDown('f4')
        pyautogui.keyUp('f4')
        pyautogui.keyUp('alt')

def handle_webbrowser_command(command):
    if (command=="OPEN"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("t")
        pyautogui.keyUp("t")
        pyautogui.keyUp('ctrl')
    elif(command == "CLOSE"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("w")
        pyautogui.keyUp("w")
        pyautogui.keyUp('ctrl')    
    elif(command == "RELOAD"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("r")
        pyautogui.keyUp("r")
        pyautogui.keyUp('ctrl')
    elif(command == "NEXT"):
        pyautogui.keyDown('alt')
        pyautogui.keyDown("left")
        pyautogui.keyUp("left")
        pyautogui.keyUp('atl')
    elif(command == "PREV"):
        pyautogui.keyDown('alt')
        pyautogui.keyDown("right")
        pyautogui.keyUp("right")
        pyautogui.keyUp('atl')
    elif(command == "1"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("1")
        pyautogui.keyUp("1")
        pyautogui.keyUp('ctrl')
    elif(command == "2"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("2")
        pyautogui.keyUp("2")
        pyautogui.keyUp('ctrl')
    elif(command == "3"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("3")
        pyautogui.keyUp("3")
        pyautogui.keyUp('ctrl')
    elif(command == "4"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("4")
        pyautogui.keyUp("4")
        pyautogui.keyUp('ctrl')
    elif(command == "5"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("5")
        pyautogui.keyUp("5")
        pyautogui.keyUp('ctrl')
    elif(command == "6"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("6")
        pyautogui.keyUp("6")
        pyautogui.keyUp('ctrl')
    elif(command == "7"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("7")
        pyautogui.keyUp("7")
        pyautogui.keyUp('ctrl')
    elif(command == "8"):
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("8")
        pyautogui.keyUp("8")
        pyautogui.keyUp('ctrl')
    elif(command == "9"): 
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown("9")
        pyautogui.keyUp("9")
        pyautogui.keyUp('ctrl')
    elif(command == "YT"):
        handle_webbrowser_command("OPEN")
        time.sleep(0.5)
        pyautogui.write("https://www.youtube.com/")
        pyautogui.press('enter')
    elif(command == "CG"):
        handle_webbrowser_command("OPEN")
        time.sleep(0.5)
        pyautogui.write("https://chatgpt.com/")
        pyautogui.press('enter')
    elif(command == "GH"):
        handle_webbrowser_command("OPEN")
        time.sleep(0.5)
        pyautogui.write("https://github.com/")
        pyautogui.press('enter')
    else:
        pass

async def handle_screen_mirroring(websocket):
    """Capture screen and send images continuously for screen mirroring."""
    connected_clients.add(websocket)
    try:
        previous_hash = None
        while True:
            # Capture the screen
            screen = ImageGrab.grab()
            buffered = io.BytesIO()
            screen.save(buffered, format="JPEG")
            img_bytes = buffered.getvalue()

            # Create a hash to check if the image is different from the last one
            current_hash = hashlib.md5(img_bytes).hexdigest()

            if current_hash != previous_hash:
                # Only send the image if it's different from the last one
                await websocket.send(img_bytes)
                previous_hash = current_hash

            # Send a ping to keep the connection alive
            try:
                await websocket.ping()
            except Exception as e:
                print(f"Error in sending ping: {e}")

            # Adjust based on performance (throttling the update rate)
            await asyncio.sleep(0.1)

    except websockets.ConnectionClosed:
        print("Screen mirroring stopped.")
    finally:
        connected_clients.remove(websocket)
           
async def handle_mouse_command(websocket, message):
    if message.startswith("MOUSE_MOVE") and (client_ip == websocket.remote_address[0]):
        _, dx, dy = message.split(',')
        current_x, current_y = pyautogui.position()
        pyautogui.moveTo(current_x + float(dx), current_y + float(dy))
    elif message.startswith("MOUSE_ABS") and (client_ip == websocket.remote_address[0]):
        # Handle MOUSE_ABS command
        parts = message.split(',')
        if len(parts) == 3:
            _, norm_x, norm_y = parts
            screen_width, screen_height = pyautogui.size()
            abs_x = float(norm_x) * screen_width
            abs_y = float(norm_y) * screen_height
            pyautogui.moveTo(abs_x, abs_y)
    elif message.startswith("MOUSE_CLICK") and (client_ip == websocket.remote_address[0]):
        # Handle MOUSE_CLICK command
        parts = message.split(',')
        if len(parts) == 3:
            _, norm_x, norm_y = parts
            screen_width, screen_height = pyautogui.size()
            abs_x = float(norm_x) * screen_width
            abs_y = float(norm_y) * screen_height
            pyautogui.click(x=abs_x, y=abs_y)
    elif message.startswith("MOUSE_CLICK_RIGHT") and (client_ip == websocket.remote_address[0]):
        # Handle MOUSE_CLICK command
        parts = message.split(',')
        if len(parts) == 3:
            _, norm_x, norm_y = parts
            screen_width, screen_height = pyautogui.size()
            abs_x = float(norm_x) * screen_width
            abs_y = float(norm_y) * screen_height
            pyautogui.click(x=abs_x, y=abs_y,button='right')
    elif message.startswith("MOUSE_DOUBLE_CLICK") and (client_ip == websocket.remote_address[0]):
        # Handle MOUSE_DOUBLE_CLICK command
        parts = message.split(',')
        if len(parts) == 3:
            _, norm_x, norm_y = parts
            screen_width, screen_height = pyautogui.size()
            abs_x = float(norm_x) * screen_width
            abs_y = float(norm_y) * screen_height
            pyautogui.doubleClick(x=abs_x, y=abs_y)
    elif message.startswith("SCROLL") and (client_ip == websocket.remote_address[0]):
        # Handle SCROLL command
        _, direction = message.split(',')
        if direction == "UP":
            pyautogui.scroll(100)  # Scroll up
        elif direction == "DOWN":
            pyautogui.scroll(-100)  # Scroll down


async def handle_general_command(websocket, message):
    if(client_ip == websocket.remote_address[0]):
        command = {
            "LEFT_CLICK":  lambda: pyautogui.click(button='left'),
            "LEFT_CLICK_UP": lambda: pyautogui.mouseUp(),
            "LEFT_CLICK_DOWN": lambda:pyautogui.mouseDown(),
            "RIGHT_CLICK": lambda: pyautogui.click(button='right'),
            "SCROLL_UP": lambda: pyautogui.press("pageup"),
            "SCROLL_DOWN": lambda: pyautogui.press("pagedown"),
            "MIDDLE_CLICK": lambda: pyautogui.click(button='middle'),
            "PLAY_PAUSE": lambda: pyautogui.press("playpause"),
            "VOLUME_UP": lambda: pyautogui.press("volumeup"),
            "VOLUME_DOWN": lambda: pyautogui.press("volumedown"),
            "BACKSPACE": lambda: pyautogui.press("backspace"),
            "ENTER": lambda : pyautogui.press("enter"),
            "PREV": lambda: pyautogui.press("prevtrack"),
            "NEXT": lambda: pyautogui.press("nexttrack"),
            "MUTE": lambda: pyautogui.press('volumemute'),
            "TAB_DOWN": lambda: pyautogui.keyDown('tab'),
            "TAB_UP": lambda: pyautogui.keyUp('tab'),
            "SHIFT_DOWN": lambda: pyautogui.keyDown('shift'),
            "SHIFT_UP": lambda: pyautogui.keyUp('shift'),
            "ALT_DOWN": lambda: pyautogui.keyDown('alt'),
            "ALT_UP": lambda: pyautogui.keyUp('alt'),
            "ESC_DOWN": lambda: pyautogui.keyDown('esc'),
            "ESC_UP": lambda: pyautogui.keyUp('esc'),
            "CTRL_DOWN": lambda: pyautogui.keyDown('ctrl'),
            "CTRL_UP": lambda: pyautogui.keyUp('ctrl'),
            "ALT_DOWN": lambda: pyautogui.keyDown('alt'),
            "ALT_UP": lambda: pyautogui.keyUp('alt'),
            "HOTKEY_CTRL_C": lambda: hotkey("COPY"),
            "HOTKEY_CTRL_V": lambda: hotkey("PASTE"),
            "HOTKEY_ALT_TAB":lambda: hotkey("ALT_TAB"),
            "HOTKEY_ALT_F4": lambda: hotkey("ALT_F4"),
            "HOTKEY_CTRL_Z": lambda: hotkey("UNDO"),
            "HOTKEY_CTRL_Y": lambda: hotkey("REDO"),
            "WB_OT": lambda: handle_webbrowser_command("OPEN"),
            "WB_CT": lambda: handle_webbrowser_command("CLOSE"),
            "WB_RE": lambda: handle_webbrowser_command("RELOAD"),
            "WB_NXT": lambda: handle_webbrowser_command("NEXT"),
            "WB_PRE": lambda: handle_webbrowser_command("PREV"),
            "WB_1": lambda: handle_webbrowser_command("1"),
            "WB_2": lambda: handle_webbrowser_command("2"),
            "WB_3": lambda: handle_webbrowser_command("3"),
            "WB_4": lambda: handle_webbrowser_command("4"),
            "WB_5": lambda: handle_webbrowser_command("5"),
            "WB_6": lambda: handle_webbrowser_command("6"),
            "WB_7": lambda: handle_webbrowser_command("7"),
            "WB_8": lambda: handle_webbrowser_command("8"),
            "WB_9": lambda: handle_webbrowser_command("9"),
            "YT": lambda: handle_webbrowser_command("YT"),
            "CG": lambda: handle_webbrowser_command("CG"),
        }
        parts = message.split(',', 2)
        action = parts[0]
        if action == "TYPE" and len(parts) == 2:
            _, text = parts
            pyautogui.write(text)
        elif action in command:
            if action == "WEBBROWSER":
                await command[action](message)
            elif action == "GET_RUNNING_APPS":  # Change made here
                await command[action]()  # Await the coroutine call
            elif action == "FOCUS_APP":
                app_name = parts[1]  # Extract the app name from the message
                focus_app(app_name)
            else:
                command[action]()
        elif action == "FOCUS_APP":
                app_name = parts[1]
                act = parts[2]
                focus_app(app_name,act)
        elif action == "START":
            quickStart(parts[1])
        else:
            pass




def start_server(current_conn):
    global broadcasting
    broadcasting = True
    asyncio.run(main(current_conn))

def start_server_thread(current_conn):
    global broadcasting
    broadcasting = True
    current_conn.config(text=f"Waiting for connection ...")
    server_thread = threading.Thread(target=start_server, args=(current_conn,))
    server_thread.start()

def stop_server():
    client_ip = None
    loop = asyncio.get_event_loop()
    for task in asyncio.all_tasks(loop=loop):
        task.cancel()
    loop.stop()
    loop.close()
    sys.exit()


if __name__ == "__main__":
    IP = socket.gethostbyname(socket.gethostname())
    root = Tk()
    menubar = Menu(root)
    homeFrame = Frame(root, height=600, width=800, bg="#19A7CE")

    startServerButton = Button(homeFrame, height=2, width=10, text="Start server", font=('Arial', 15), bg="#19A7CE", fg='#FFFFFF', activebackground='#F6F1F1', activeforeground='#19A7CE', command=lambda: start_server_thread(current_conn))
    stopServerButton = Button(homeFrame, height=2, width=10, text="Stop server", font=('Arial', 15), bg="#19A7CE", fg='#FFFFFF', activebackground='#F6F1F1', activeforeground='#19A7CE', command=stop_server)
    yourIPAddr = Label(homeFrame, height=2, width=20, text="Your IP: " + IP, font=('Arial', 15), bg="#3ABEF9", fg='#FFFFFF')
    current_conn = Label(homeFrame, height=2, width=40, bg="#3ABEF9", fg='#FFFFFF', text='START SERVER', font=('Arial', 15))
    pwd_lbl = Label(homeFrame, height=2 , width=15, bg="#3ABEF9", fg='#FFFFFF', text='Password', font=('Arial', 15))
    pwd_entry = Entry(homeFrame, width= 10 ,bg="#3ABEF9", fg='#FFFFFF',show='*',font=(15))

    yourIPAddr.place(x=10, y=10)
    startServerButton.place(x=320, y=10)
    stopServerButton.place(x=500, y=10)
    current_conn.place(x=10, y=200)
    pwd_lbl.place(x = 10 , y = 130)
    pwd_entry.place(x  =320 , y = 130)
    
    homeFrame.propagate(0)
    homeFrame.pack()
    root.protocol("WM_DELETE_WINDOW", stop_server)
    root.mainloop()
