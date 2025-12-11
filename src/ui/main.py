import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import requests
import threading
import queue
import time
import sys

# ======================
# API ENDPOINTS
# ======================
BASE_URL = "http://localhost:5000/api/v1"
REGISTER_ENDPOINT = f"{BASE_URL}/client/register_client"
PROCESS_ENDPOINT_TEMPLATE = f"{BASE_URL}/client/proccess_client_image/{{client_id}}"
AUTH_ENDPOINT = f"{BASE_URL}/authenticate/authenticate"

# ======================
# Shared resources
# ======================
camera = None
camera_lock = threading.Lock()
auth_thread = None
auth_running = threading.Event()
ui_queue = queue.Queue()


# ======================
# Utility helpers
# ======================
def encode_frame_to_jpeg_bytes(frame_bgr):
    ret, buf = cv2.imencode(".jpg", frame_bgr)
    if not ret:
        return None
    return buf.tobytes()


# ======================
# Authentication Loop
# ======================
def auth_loop(poll_interval=2.0):
    try:
        while auth_running.is_set():

            # --- read frame ---
            with camera_lock:
                if camera is None or not camera.isOpened():
                    ui_queue.put(("status", "Camera not opened"))
                    break
                ret, frame = camera.read()

            if not ret:
                ui_queue.put(("status", "Failed to read from camera"))
                if auth_running.wait(1.0):
                    break
                continue

            # --- update live preview ---
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)
                ui_queue.put(("frame", pil_img))
            except Exception as e:
                ui_queue.put(("status", f"Frame display error: {e}"))

            # --- encode & send to API ---
            jpeg_bytes = encode_frame_to_jpeg_bytes(frame)
            if jpeg_bytes:
                files = {"image1": ("frame.jpg", jpeg_bytes, "image/jpeg")}

                try:
                    resp = requests.post(AUTH_ENDPOINT, files=files, timeout=10)

                    # response output
                    try:
                        text = resp.json()
                    except:
                        text = resp.text

                    ui_queue.put(("response", str(text)))

                except Exception as e:
                    ui_queue.put(("response", f"Auth error: {e}"))
            else:
                ui_queue.put(("response", "Failed to encode frame"))

            # Wait
            if auth_running.wait(poll_interval):
                break

    except Exception as e:
        ui_queue.put(("response", f"Auth loop error: {e}"))


# ======================
# Camera management
# ======================
def start_camera(index=0):
    global camera
    with camera_lock:
        if camera is None or not camera.isOpened():
            cam = cv2.VideoCapture(index)
            if not cam or not cam.isOpened():
                return False
            camera = cam
    return True


def stop_camera():
    global camera
    with camera_lock:
        if camera is not None:
            try:
                camera.release()
            except:
                pass
            camera = None


# ======================
# GUI Actions
# ======================
def start_authentication():
    global auth_thread
    if auth_running.is_set():
        return

    if not start_camera():
        messagebox.showerror("Camera Error", "Unable to open webcam.")
        return

    auth_running.set()
    auth_thread = threading.Thread(target=auth_loop, daemon=True)
    auth_thread.start()
    status_var.set("Authentication started")


def stop_authentication():
    if auth_running.is_set():
        auth_running.clear()
        status_var.set("Stopping...")
    else:
        status_var.set("Already stopped")


def capture_and_register():
    name = entry_name.get().strip()
    cid = entry_client_id.get().strip()

    if not name or not cid:
        messagebox.showerror("Input Error", "Please enter Client Name and Client ID.")
        return

    if not start_camera():
        messagebox.showerror("Camera Error", "Cannot open webcam.")
        return

    # --- capture frame ---
    with camera_lock:
        ret, frame = camera.read()

    if not ret:
        messagebox.showerror("Capture Error", "Failed to capture image.")
        return

    # --- show frame in UI ---
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(frame_rgb)
    ui_queue.put(("frame", pil_img))

    jpeg_bytes = encode_frame_to_jpeg_bytes(frame)
    if jpeg_bytes is None:
        messagebox.showerror("Encode Error", "Failed to encode frame.")
        return

    files = {"image1": ("capture.jpg", jpeg_bytes, "image/jpeg")}
    data = {"client_name": name, "client_id": cid}

    # ================
    # 1) REGISTER
    # ================
    try:
        resp = requests.post(REGISTER_ENDPOINT, files=files, data=data, timeout=10)

        try:
            reg_result = resp.json()
        except:
            reg_result = resp.text

        ui_queue.put(("response", f"REGISTER RESULT:\n{reg_result}"))

        if resp.status_code != 200:
            return  # stop if register failed

    except Exception as e:
        ui_queue.put(("response", f"Register Error: {e}"))
        return

    # ================
    # 2) PROCESS IMAGE  (After successful register)
    # ================
    try:
        process_url = PROCESS_ENDPOINT_TEMPLATE.format(client_id=cid)
        resp2 = requests.post(process_url, files=files, timeout=10)

        try:
            proc_result = resp2.json()
        except:
            proc_result = resp2.text

        ui_queue.put(("response", f"REGISTER RESULT:\n{reg_result}\n\nPROCESS RESULT:\n{proc_result}"))

    except Exception as e:
        ui_queue.put(("response", f"Process Error: {e}"))


# ======================
# Update UI thread-safely
# ======================
def poll_ui_queue():
    try:
        while True:
            kind, payload = ui_queue.get_nowait()

            if kind == "frame":
                img = payload.copy()
                img.thumbnail((640, 480))
                tk_img = ImageTk.PhotoImage(img)
                lbl_live.imgtk = tk_img
                lbl_live.config(image=tk_img)

            elif kind == "response":
                txt_output.delete("1.0", tk.END)
                txt_output.insert("1.0", payload)

            elif kind == "status":
                status_var.set(payload)

    except queue.Empty:
        pass

    root.after(100, poll_ui_queue)


# ======================
# Graceful shutdown
# ======================
def on_close():
    stop_authentication()
    stop_camera()
    root.after(200, lambda: (root.destroy(), sys.exit(0)))


# ======================
# Build GUI
# ======================
root = tk.Tk()
root.title("Client System - Webcam Register & Authenticate")
root.geometry("800x700")

# REGISTER frame
frame_reg = tk.LabelFrame(root, text="Register Client", padx=10, pady=10)
frame_reg.pack(fill="x", padx=10, pady=6)

tk.Label(frame_reg, text="Client Name:").grid(row=0, column=0, sticky="w")
entry_name = tk.Entry(frame_reg, width=30)
entry_name.grid(row=0, column=1, padx=6, pady=4)

tk.Label(frame_reg, text="Client ID:").grid(row=1, column=0, sticky="w")
entry_client_id = tk.Entry(frame_reg, width=30)
entry_client_id.grid(row=1, column=1, padx=6, pady=4)

btn_capture = tk.Button(frame_reg, text="Capture & Register", command=capture_and_register)
btn_capture.grid(row=2, column=0, columnspan=2, pady=8)

# AUTH frame
frame_auth = tk.LabelFrame(root, text="Authenticate (Live)", padx=10, pady=10)
frame_auth.pack(fill="both", expand=False, padx=10, pady=6)

lbl_live = tk.Label(frame_auth, text="No camera feed", bg="black")
lbl_live.pack(padx=6, pady=6)

controls_frame = tk.Frame(frame_auth)
controls_frame.pack(fill="x", padx=6, pady=4)

btn_start = tk.Button(controls_frame, text="Start Authentication", command=start_authentication)
btn_start.pack(side="left", padx=6)

btn_stop = tk.Button(controls_frame, text="Stop Authentication", command=stop_authentication)
btn_stop.pack(side="left", padx=6)

status_var = tk.StringVar(value="Idle")
tk.Label(controls_frame, textvariable=status_var).pack(side="left", padx=12)

# OUTPUT frame
frame_out = tk.LabelFrame(root, text="API Response / Status", padx=10, pady=10)
frame_out.pack(fill="both", expand=True, padx=10, pady=6)

txt_output = tk.Text(frame_out, height=10)
txt_output.pack(fill="both", expand=True)

root.after(100, poll_ui_queue)
root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
