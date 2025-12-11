import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import threading
import requests
import queue
import io
import time

# ==============================
# API ENDPOINTS
# ==============================
BASE_URL = "http://localhost:5000/api/v1"
REGISTER_ENDPOINT = f"{BASE_URL}/client/register_client"
PROCESS_ENDPOINT_TEMPLATE = f"{BASE_URL}/client/proccess_client_image/{{client_id}}"
AUTH_ENDPOINT = f"{BASE_URL}/authenticate/authenticate"

# ==============================
# GLOBAL SHARED OBJECTS
# ==============================
camera = None
camera_running = False
frame_lock = threading.Lock()
last_frame = None
ui_queue = queue.Queue()

# ==============================
# CAMERA THREAD
# ==============================
def camera_loop():
    global camera_running, last_frame
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        ui_queue.put(("error", "Cannot open camera"))
        return

    camera_running = True

    while camera_running:
        ret, frame = cap.read()
        if not ret:
            continue

        with frame_lock:
            last_frame = frame

        time.sleep(0.01)  # Very small sleep to reduce CPU usage

    cap.release()


# ==============================
# UTILITY: Capture Current Frame as Bytes
# ==============================
def get_frame_bytes():
    global last_frame
    with frame_lock:
        if last_frame is None:
            return None
        ret, buf = cv2.imencode(".jpg", last_frame)
        if not ret:
            return None
        return buf.tobytes()


# ==============================
# API THREAD HANDLER
# ==============================
def run_api_thread(target, *args):
    thread = threading.Thread(target=target, args=args)
    thread.daemon = True
    thread.start()


# ==============================
# REGISTER CLIENT
# ==============================
def register_client(client_name, client_id):
    frame_bytes = get_frame_bytes()
    if frame_bytes is None:
        ui_queue.put(("error", "No camera frame available"))
        return

    try:
        files = {"image1": ("image.jpg", frame_bytes, "image/jpeg")}
        data = {"client_name": client_name, "client_id": client_id}

        resp = requests.post(REGISTER_ENDPOINT, files=files, data=data, timeout=15)

        if resp.status_code == 200:
            # After successful register → call process endpoint
            process_endpoint = PROCESS_ENDPOINT_TEMPLATE.format(client_id=client_id)
            resp2 = requests.post(process_endpoint, files=files, timeout=15)

            if resp2.status_code == 200:
                ui_queue.put(("info", "Registration + Processing completed successfully!"))
            else:
                ui_queue.put(("error", f"Registered but processing failed: {resp2.text}"))
        else:
            ui_queue.put(("error", f"Registration failed: {resp.text}"))

    except Exception as e:
        ui_queue.put(("error", f"Exception: {e}"))


# ==============================
# AUTHENTICATE
# ==============================
def authenticate_client(client_id):
    frame_bytes = get_frame_bytes()
    if frame_bytes is None:
        ui_queue.put(("error", "No frame available for authentication"))
        return

    try:
        files = {"image1": ("image.jpg", frame_bytes, "image/jpeg")}
        data = {"client_id": client_id}

        resp = requests.post(AUTH_ENDPOINT, files=files, data=data, timeout=15)

        if resp.status_code == 200:
            ui_queue.put(("info", f"Authenticated Successfully: {resp.text}"))
        else:
            ui_queue.put(("error", f"Authentication failed: {resp.text}"))

    except Exception as e:
        ui_queue.put(("error", f"Exception: {e}"))


# ==============================
# TKINTER APP
# ==============================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Registration / Authentication System")

        # ===== Main Layout =====
        self.left_frame = tk.Frame(root)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10)

        self.right_frame = tk.Frame(root)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        # ===== Camera Preview =====
        self.preview_label = tk.Label(self.left_frame)
        self.preview_label.pack()

        # ===== Form Fields =====
        tk.Label(self.right_frame, text="Client Name:").pack()
        self.name_entry = tk.Entry(self.right_frame, width=30)
        self.name_entry.pack(pady=5)

        tk.Label(self.right_frame, text="Client ID:").pack()
        self.id_entry = tk.Entry(self.right_frame, width=30)
        self.id_entry.pack(pady=5)

        # ===== Buttons =====
        tk.Button(self.right_frame, text="Register", width=20,
                  command=self.on_register).pack(pady=10)

        tk.Button(self.right_frame, text="Authenticate", width=20,
                  command=self.on_authenticate).pack(pady=10)

        # Start camera thread
        threading.Thread(target=camera_loop, daemon=True).start()

        # Update UI loop
        self.update_ui()

    # ---- CALLBACKS ----
    def on_register(self):
        name = self.name_entry.get().strip()
        client_id = self.id_entry.get().strip()
        if not name or not client_id:
            messagebox.showerror("Error", "Please enter name + ID")
            return
        run_api_thread(register_client, name, client_id)

    def on_authenticate(self):
        client_id = self.id_entry.get().strip()
        if not client_id:
            messagebox.showerror("Error", "Enter Client ID")
            return
        run_api_thread(authenticate_client, client_id)

    # ---- UI LOOP ----
    def update_ui(self):
        # Update camera preview
        global last_frame
        with frame_lock:
            if last_frame is not None:
                rgb = cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.preview_label.imgtk = imgtk
                self.preview_label.config(image=imgtk)

        # Handle queue messages
        try:
            while True:
                key, msg = ui_queue.get_nowait()
                if key == "error":
                    messagebox.showerror("Error", msg)
                elif key == "info":
                    messagebox.showinfo("Success", msg)
        except queue.Empty:
            pass

        # Run again
        self.root.after(10, self.update_ui)


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

    camera_running = False
