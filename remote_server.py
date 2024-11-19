import io
from tkinter import *
import asyncio
import websockets
import pyautogui
import json
import socket
import threading
import sys
import time
import pygetwindow as gw
import hashlib
import keyboard
from PIL import ImageGrab
import ctypes
import cv2
import numpy as np

client_ip = None
qr_show = True
broadcasting = True
connected_clients = set()
current_pressed_keys = set()
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
mouse_sen = 10


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
            elif path == "/joystick":
                await handle_joystick_command(websocket, message)
            elif path == "/mousemovement":
                await handle_mousemovement_command(websocket, message)
            elif path == "/buttonpress":
                await handle_buttonpress_command(websocket, message)  # Handle the button press events
            else:
                await handle_general_command(websocket, message)
        except Exception as e:
            print(f"Error handling command '{message}': {e}")
            response = {"error": str(e)}
            await websocket.send(json.dumps(response))  # Send error response if any error occurs
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


def move_mouse(x, y, absolute=False):
    """
    Move the mouse pointer based on x and y coordinates.

    :param x: X-axis movement or position.
    :param y: Y-axis movement or position.
    :param absolute: If True, moves to absolute coordinates; otherwise, moves relatively.
    """
    flags = MOUSEEVENTF_MOVE
    if absolute:
        flags |= MOUSEEVENTF_ABSOLUTE
        # Convert x, y to absolute coordinates (0-65535 range)
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        x = int((x / screen_width) * 65535)
        y = int((y / screen_height) * 65535)
    ctypes.windll.user32.mouse_event(flags, x, y, 0, 0)

async def handle_mousemovement_command(websocket, message):
    """
    Handles mouse movement commands (x, y) received from the client and moves the mouse accordingly.
    Allows for dynamic sensitivity updates.
    """
    global mouse_sen, client_ip  # Declare the global variable to modify it inside the function

    try:
        # Ensure the command comes from the same client
        if client_ip != websocket.remote_address[0]:
            raise ConnectionError("Unauthorized client access detected.")

        # Parse the incoming message
        data = json.loads(message)
        joystick_type = data.get("joystickType", "")
        x = data.get("x", 0)
        y = data.get("y", 0)
        sensitivity = data.get("sensitivity", None)  # Check for a sensitivity update

        if sensitivity is not None:
            # Update global sensitivity
            try:
                mouse_sen = float(sensitivity)
                print(f"Mouse sensitivity updated to: {mouse_sen}")

                # Send acknowledgment for sensitivity update
                response = {"status": "success", "action": "update_sensitivity", "sensitivity": mouse_sen}
                await websocket.send(json.dumps(response))
                return  # No need to process further if this was only a sensitivity update
            except ValueError:
                print("Invalid sensitivity value received")
                response = {"error": "Invalid sensitivity value"}
                await websocket.send(json.dumps(response))
                return

        if joystick_type == "Mouse":
            # Scale mouse movement with the global sensitivity value
            adjusted_x = int(x * mouse_sen)
            adjusted_y = int(y * mouse_sen)

            # Perform the mouse movement
            move_mouse(adjusted_x, adjusted_y)  # Replace pyautogui.move() with move_mouse
            print(f"Mouse moved: x={adjusted_x}, y={adjusted_y}")

            # Send acknowledgment to the client
            response = {"status": "success", "action": "mouse_movement", "x": adjusted_x, "y": adjusted_y}
            await websocket.send(json.dumps(response))
        else:
            print("Unknown joystick type received")
            response = {"error": "Unknown joystick type"}
            await websocket.send(json.dumps(response))

    except json.JSONDecodeError:
        print("Invalid JSON data received for mouse movement")
        response = {"error": "Invalid JSON data"}
        await websocket.send(json.dumps(response))
    except Exception as e:
        print(f"Error handling mouse movement: {e}")
        response = {"error": str(e)}
        await websocket.send(json.dumps(response))

async def handle_joystick_command(websocket, message):
    """
    Handles joystick commands (WASD directions) received from the client.
    Sends corresponding keyboard inputs using the keyboard module and keeps the keys pressed as long as the joystick is in a direction.
    """
    global current_pressed_keys,client_ip
    if(client_ip != websocket.remote_address[0]):
        return ConnectionError

    try:
        data = json.loads(message)  # Parse the incoming message
        joystick_type = data.get("joystickType", "")
        direction = data.get("direction", "")

        # Release all keys if no direction is specified
        if not direction:
            # Release all pressed keys and reset the set of pressed keys
            for key in current_pressed_keys:
                keyboard.release(key)
            current_pressed_keys.clear()
            print("Joystick released - No direction")
            return

        # Handle WASD commands
        if joystick_type == "WASD":
            # Create a set of the current direction keys to be pressed
            direction_keys = set()

            if 'w' in direction.lower():
                direction_keys.add('w')
            if 'a' in direction.lower():
                direction_keys.add('a')
            if 's' in direction.lower():
                direction_keys.add('s')
            if 'd' in direction.lower():
                direction_keys.add('d')

            # Find keys that need to be pressed
            keys_to_press = direction_keys - current_pressed_keys
            # Find keys that need to be released
            keys_to_release = current_pressed_keys - direction_keys

            # Press keys that are not yet pressed
            for key in keys_to_press:
                keyboard.press(key)
                current_pressed_keys.add(key)
                print(f"Pressed key: {key}")

            # Release keys that are no longer needed
            for key in keys_to_release:
                keyboard.release(key)
                current_pressed_keys.remove(key)
                print(f"Released key: {key}")

            print(f"Joystick direction: {direction}")

    except json.JSONDecodeError:
        print("Invalid JSON data received for joystick command")
        await websocket.send(json.dumps({"error": "Invalid JSON data"}))
    except Exception as e:
        print(f"Error handling joystick command: {e}")
        await websocket.send(json.dumps({"error": str(e)}))

async def handle_buttonpress_command(websocket, message):
    global client_ip
    if(client_ip != websocket.remote_address[0]):
        return ConnectionError
    try:
        # Parse the incoming message
        data = json.loads(message)
        button = data.get("button")
        state = data.get("state")

        if button and state:
            # Handle the left mouse button
            if button == "left":
                if state == "pressed":
                    # Simulate a single-click: press down and immediately release
                    pyautogui.mouseDown(button='left')
                    pyautogui.mouseUp(button='left')
                    print("Left mouse button pressed (single-click)")
                elif state == "held":
                    # Simulate holding down the left mouse button
                    pyautogui.mouseDown(button='left')
                    print("Left mouse button held down")
                elif state == "released":
                    # Simulate releasing the left mouse button
                    pyautogui.mouseUp(button='left')
                    print("Left mouse button released")
                else:
                    print("Unknown state for left mouse button")

            # Handle the right mouse button
            elif button == "right":
                if state == "pressed":
                    # Simulate a single-click: press down and immediately release
                    pyautogui.mouseDown(button='right')
                    pyautogui.mouseUp(button='right')
                    print("Right mouse button pressed (single-click)")
                elif state == "held":
                    # Simulate holding down the right mouse button
                    pyautogui.mouseDown(button='right')
                    print("Right mouse button held down")
                elif state == "released":
                    # Simulate releasing the right mouse button
                    pyautogui.mouseUp(button='right')
                    print("Right mouse button released")
                else:
                    print("Unknown state for right mouse button")

            # Handle keyboard input (button press, hold, release)
            elif button:  # For any key (letters, numbers, symbols, modifier keys)
                if state == "pressed":
                    keyboard.press(button)  # Simulate key press
                    time.sleep(0.05)
                    keyboard.release(button)
                    print(f"Key {button} pressed")
                elif state == "released":
                    keyboard.release(button)  # Simulate key release
                    print(f"Key {button} released")
                elif state == "held":
                    keyboard.press(button)
                    print(f"Key {button} held")  # In case you want to track if the key is still pressed (no direct handling needed)
                else:
                    print(f"Unknown state for key {button}")
            else:
                print(f"Unknown button: {button}")

        else:
            print("Invalid data received for button press")

    except Exception as e:
        print(f"Error processing button press: {e}")

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

def get_abs_coordinates(norm_x, norm_y):
    screen_width, screen_height = pyautogui.size()
    abs_x = max(0, min(float(norm_x) * screen_width, screen_width - 1))
    abs_y = max(0, min(float(norm_y) * screen_height, screen_height - 1))
    return abs_x, abs_y

# Handle screen mirroring
async def handle_screen_mirroring(websocket):
    """Stream screen live feed continuously for connected clients."""
    previous_resolution = None  # To track the last sent resolution

    try:
        while True:
            # Capture the screen
            screen = ImageGrab.grab()  # Captures the screen
            screen_np = np.array(screen)  # Convert to NumPy array
            frame = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for encoding

            # Get the screen resolution
            current_resolution = (frame.shape[1], frame.shape[0])  # Width, Height

            # Send the resolution if it has changed
            if current_resolution != previous_resolution:
                resolution_message = f"RESOLUTION,{current_resolution[0]},{current_resolution[1]}"
                await websocket.send(resolution_message)
                previous_resolution = current_resolution

            # Encode the frame as JPEG
            success, jpeg_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])  # Adjust quality for bandwidth
            if not success:
                print("Failed to encode frame.")
                continue

            # Get the binary data
            img_bytes = jpeg_frame.tobytes()

            # Send the JPEG frame as binary data to the client
            await websocket.send(img_bytes)

            # Throttle to control frame rate (e.g., 30 FPS)
            await asyncio.sleep(0.033)  # Approx. 30 frames per second

    except websockets.ConnectionClosed:
        print("Screen mirroring client disconnected.")
    except Exception as e:
        print(f"Error in screen mirroring: {e}")
    finally:
        connected_clients.remove(websocket)


async def handle_mouse_command(websocket, message):
    global client_ip
    try:
        if message.startswith("MOUSE_MOVE") and (client_ip == websocket.remote_address[0]):
            _, dx, dy = message.split(',')
            current_x, current_y = pyautogui.position()
            pyautogui.moveTo(current_x + float(dx), current_y + float(dy))

        elif message.startswith("MOUSE_ABS") and (client_ip == websocket.remote_address[0]):
            _, norm_x, norm_y = message.split(',')
            abs_x, abs_y = get_abs_coordinates(norm_x, norm_y)
            pyautogui.moveTo(abs_x, abs_y)

        elif message.startswith("MOUSE_CLICK") and (client_ip == websocket.remote_address[0]):
            _, norm_x, norm_y = message.split(',')
            abs_x, abs_y = get_abs_coordinates(norm_x, norm_y)
            pyautogui.click(x=abs_x, y=abs_y)

        elif message.startswith("MOUSE_CLICK_RIGHT") and (client_ip == websocket.remote_address[0]):
            _, norm_x, norm_y = message.split(',')
            abs_x, abs_y = get_abs_coordinates(norm_x, norm_y)
            pyautogui.click(x=abs_x, y=abs_y, button='right')

        elif message.startswith("MOUSE_DOUBLE_CLICK") and (client_ip == websocket.remote_address[0]):
            _, norm_x, norm_y = message.split(',')
            abs_x, abs_y = get_abs_coordinates(norm_x, norm_y)
            pyautogui.doubleClick(x=abs_x, y=abs_y)

        elif message.startswith("SCROLL") and (client_ip == websocket.remote_address[0]):
            _, direction = message.split(',')
            if direction == "UP":
                pyautogui.scroll(100)  # Scroll up
            elif direction == "DOWN":
                pyautogui.scroll(-100)  # Scroll down

    except Exception as e:
        print(f"Error handling mouse command: {e}")

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
