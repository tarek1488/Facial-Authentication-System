import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading
import requests
import queue
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
camera_running = False
frame_lock = threading.Lock()
last_frame = None
ui_queue = queue.Queue()
AUTH_INTERVAL = 5  # seconds between automatic authentications

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

        time.sleep(0.01)  # small sleep to reduce CPU usage

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
        self.preview_label = tk.Label(self.left_frame, width=640, height=480, bg="black")
        self.preview_label.pack()

        # ===== Form Fields =====
        form_frame = tk.Frame(self.right_frame)
        form_frame.pack(pady=5)

        tk.Label(form_frame, text="Client Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(form_frame, width=30)
        self.name_entry.grid(row=0, column=1, pady=2)

        tk.Label(form_frame, text="Client ID:").grid(row=1, column=0, sticky="w")
        self.id_entry = tk.Entry(form_frame, width=30)
        self.id_entry.grid(row=1, column=1, pady=2)

        # ===== Buttons =====
        button_frame = tk.Frame(self.right_frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Register", width=20,
                  command=self.on_register).grid(row=0, column=0, padx=5, pady=2)

        # ===== API Response Preview (Scrollable) =====
        tk.Label(self.right_frame, text="API Response:").pack(pady=(10, 0))

        self.response_text_frame = tk.Frame(self.right_frame)
        self.response_text_frame.pack(fill="both", expand=True)

        self.response_text = tk.Text(self.response_text_frame, width=50, height=15, wrap="word")
        self.response_text.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.response_text_frame, command=self.response_text.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.response_text.config(yscrollcommand=self.scrollbar.set, state=tk.DISABLED)

        # Start camera thread
        threading.Thread(target=camera_loop, daemon=True).start()

        # Start regular authentication
        self.schedule_authentication()

        # Update UI loop
        self.update_ui()

    # ---- CALLBACKS ----
    def on_register(self):
        name = self.name_entry.get().strip()
        client_id = self.id_entry.get().strip()
        if not name or not client_id:
            self.show_response("Error: Please enter name + ID")
            return
        run_api_thread(register_client, name, client_id)

    # ---- AUTO AUTHENTICATION ----
    def schedule_authentication(self):
        client_id = self.id_entry.get().strip()
        if client_id:
            run_api_thread(authenticate_client, client_id)
        # schedule next authentication after AUTH_INTERVAL seconds
        self.root.after(AUTH_INTERVAL * 1000, self.schedule_authentication)

    # ---- SHOW RESPONSE ----
    def show_response(self, msg):
        self.response_text.config(state=tk.NORMAL)
        self.response_text.insert(tk.END, msg + "\n")
        self.response_text.see(tk.END)
        self.response_text.config(state=tk.DISABLED)

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
                    self.show_response(f"Error: {msg}")
                elif key == "info":
                    self.show_response(f"Success: {msg}")
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
