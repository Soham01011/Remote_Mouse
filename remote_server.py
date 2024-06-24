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
import qrcode
from PIL import Image, ImageTk

client_ip = None
current_dir = "/"  
qr_session_tk = uuid.uuid4()
print("session tocken : " ,qr_session_tk)
qr_show = True

def generate_qr_code(data,ip,file_path="qr_code.png"):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=4,
    )
    qr.add_data(str(data)+' '+str(ip))
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    img.save(file_path)
    return file_path

async def handle_client(websocket, path, current_conn):
    global current_dir
    async for message in websocket:
        try:
            if path == "/auth":
                await authorize_user(websocket, message,current_conn)
            if path == "/mouse":
                await handle_mouse_command(websocket,message)
            elif path == "/apps":
                await handle_apps_command(websocket)
            else:
                await handle_general_command(websocket, message)
        except Exception as e:
            print(f"Error handling command '{message}': {e}")

async def authorize_user(websocket, message,current_conn):
    global client_ip
    data = json.loads(message)
    if data.get("password") == pwd_entry.get():
        await websocket.send(json.dumps({"status": "authenticated"}))
        client_ip = websocket.remote_address[0]
        current_conn.config(text=f"Connected: {client_ip}")
    elif data.get("qr") == qr_session_tk:
        print("QR : ", websocket.remote_address[0])
        await websocket.send(json.dumps({"status": "authenticated"}))
        client_ip = websocket.remote_address[0]
        current_conn.config(text=f"Connected: {client_ip}")
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

def focus_app(app_name):
    try:
        window = gw.getWindowsWithTitle(app_name)
        if window:
            window[0].activate()
            return f"Focused on {app_name}"
        else:
            return f"Application {app_name} not found"
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

            
async def handle_mouse_command(websocket, message):
    if (message.startswith("MOUSE_MOVE") & (client_ip == websocket.remote_address[0])):
        _, dx, dy = message.split(',')
        current_x, current_y = pyautogui.position()
        pyautogui.moveTo(current_x + float(dx), current_y + float(dy))

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
        parts = message.split(',', 1)
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
                focus_app(app_name)
        elif action == "START":
            quickStart(parts[1])
        else:
            pass

async def main(current_conn):
    general_server = await websockets.serve(lambda ws, path: handle_client(ws, path, current_conn), "0.0.0.0", 9999)
    mouse_server = await websockets.serve(lambda ws, path: handle_client(ws, path, current_conn), "0.0.0.0", 9998)
    app_list_server = await websockets.serve(lambda ws, path: handle_client(ws, path, current_conn), "0.0.0.0", 9997)
    await asyncio.gather(general_server.wait_closed(), mouse_server.wait_closed(), app_list_server.wait_closed())


def start_server(current_conn):
    asyncio.run(main(current_conn))

def start_server_thread(current_conn):
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

def qr_dis():
    global qr_show
    if(qr_show):
        qr_code_label.place_forget()
        qr_show = False
        dsiplay_qr.config(text='Show QR')
    else:
        qr_code_label.place(x=450 , y=270)
        qr_show = True
        dsiplay_qr.config(text='Hide QR')


if __name__ == "__main__":
    IP = socket.gethostbyname(socket.gethostname())
    generate_qr_code(qr_session_tk,IP)
    root = Tk()
    menubar = Menu(root)
    homeFrame = Frame(root, height=600, width=800, bg="#19A7CE")

    startServerButton = Button(homeFrame, height=2, width=10, text="Start server", font=('Arial', 15), bg="#19A7CE", fg='#FFFFFF', activebackground='#F6F1F1', activeforeground='#19A7CE', command=lambda: start_server_thread(current_conn))
    stopServerButton = Button(homeFrame, height=2, width=10, text="Stop server", font=('Arial', 15), bg="#19A7CE", fg='#FFFFFF', activebackground='#F6F1F1', activeforeground='#19A7CE', command=stop_server)
    yourIPAddr = Label(homeFrame, height=2, width=20, text="Your IP: " + IP, font=('Arial', 15), bg="#3ABEF9", fg='#FFFFFF')
    current_conn = Label(homeFrame, height=2, width=40, bg="#3ABEF9", fg='#FFFFFF', text='START SERVER', font=('Arial', 15))
    pwd_lbl = Label(homeFrame, height=2 , width=15, bg="#3ABEF9", fg='#FFFFFF', text='Password', font=('Arial', 15))
    pwd_entry = Entry(homeFrame, width= 10 ,bg="#3ABEF9", fg='#FFFFFF',show='*',font=(15))
    dsiplay_qr = Button(homeFrame, height=2, width=10, text="Hide QR", font=('Arial', 15), bg="#19A7CE", fg='#FFFFFF', activebackground='#F6F1F1', activeforeground='#19A7CE', command=qr_dis)
    img = Image.open("qr_code.png")
    photo_img = ImageTk.PhotoImage(img)
    qr_code_label = Label(homeFrame, image=photo_img)


    yourIPAddr.place(x=10, y=10)
    startServerButton.place(x=320, y=10)
    stopServerButton.place(x=500, y=10)
    current_conn.place(x=10, y=200)
    pwd_lbl.place(x = 10 , y = 130)
    pwd_entry.place(x  =320 , y = 130)
    dsiplay_qr.place(x =10 , y = 270)
    qr_code_label.place(x=450 , y=270)
    

    homeFrame.propagate(0)
    homeFrame.pack()
    root.protocol("WM_DELETE_WINDOW", stop_server)
    root.mainloop()