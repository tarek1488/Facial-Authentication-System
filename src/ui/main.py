import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import threading
import requests
import io
import time

# -------------------------
# Configuration
# -------------------------
BASE_URL = "http://localhost:5000/api/v1"
REGISTER_ENDPOINT = f"{BASE_URL}/client/register_client"
PROCESS_ENDPOINT_TEMPLATE = f"{BASE_URL}/client/proccess_client_image/{{client_id}}"
AUTH_ENDPOINT = f"{BASE_URL}/authenticate/authenticate"

# How often (seconds) to send a frame for authentication when streaming continuously
AUTH_SEND_INTERVAL = 1.5

# How long (ms) to display recognized client info before resuming
DISPLAY_MS_ON_RECOGNIZED = 3000

# Webcam index (0 default)
CAMERA_INDEX = 0

# -------------------------
# API Wrapper
# -------------------------
class ClientAPI:
    def __init__(self, register_url=REGISTER_ENDPOINT, process_template=PROCESS_ENDPOINT_TEMPLATE, auth_url=AUTH_ENDPOINT):
        self.register_url = register_url
        self.process_template = process_template
        self.auth_url = auth_url
        self.session = requests.Session()

    def _image_bytes_from_frame(self, frame_bgr):
        """Encode BGR frame (numpy) to JPEG bytes."""
        ret, buf = cv2.imencode('.jpg', frame_bgr)
        if not ret:
            raise ValueError("Failed to encode image to JPEG")
        return io.BytesIO(buf.tobytes())

    def register_client(self, client_name: str, client_id: str, frame_bgr) -> requests.Response:
        """
        POST multipart/form-data: 'client_name', 'client_id', 'image' file
        Returns requests.Response
        """
        img_buffer = self._image_bytes_from_frame(frame_bgr)
        files = {
            "image": ("photo.jpg", img_buffer.getvalue(), "image/jpeg")
        }
        data = {
            "client_name": client_name,
            "client_id": client_id
        }
        resp = self.session.post(self.register_url, data=data, files=files, timeout=30)
        return resp

    def process_client_image(self, client_id: str) -> requests.Response:
        """
        POST to /proccess_client_image/{client_id} (no body expected)
        """
        url = self.process_template.format(client_id=client_id)
        resp = self.session.post(url, timeout=30)
        return resp

    def authenticate(self, frame_bgr) -> requests.Response:
        """
        POST multipart/form-data with only image file to auth endpoint.
        """
        img_buffer = self._image_bytes_from_frame(frame_bgr)
        files = {
            "image": ("photo.jpg", img_buffer.getvalue(), "image/jpeg")
        }
        resp = self.session.post(self.auth_url, files=files, timeout=30)
        return resp

# -------------------------
# Camera Controller
# -------------------------
class CameraController:
    def __init__(self, index=CAMERA_INDEX):
        self.index = index
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW) if hasattr(cv2, 'CAP_DSHOW') else cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {self.index}")
        # try to set a reasonable size
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.lock = threading.Lock()

    def read_frame(self):
        with self.lock:
            ret, frame = self.cap.read()
            if not ret:
                raise RuntimeError("Camera read failed")
            return frame.copy()  # BGR numpy array

    def release(self):
        with self.lock:
            if self.cap and self.cap.isOpened():
                self.cap.release()

# -------------------------
# Tkinter GUI
# -------------------------
class GymApp(tk.Tk):
    def __init__(self, api: ClientAPI, camera: CameraController):
        super().__init__()
        self.title("Gym Client - Registration & Authentication")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.api = api
        self.camera = camera

        # Tab control
        self.notebook = ttk.Notebook(self)
        self.auth_frame = ttk.Frame(self.notebook)
        self.reg_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.auth_frame, text="Authentication (Live)")
        self.notebook.add(self.reg_frame, text="Register Client")
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Shared attributes
        self.current_photo_image = None  # keep reference for tkinter
        self.streaming = True

        # Authentication view
        self._build_auth_view()

        # Registration view
        self._build_reg_view()

        # Background auth sending control
        self._last_auth_send = 0
        self._auth_call_running = False
        self._overlay_active = False

        # Start update loop for camera frames
        self.update_frame()

    def _build_auth_view(self):
        # Camera display
        self.auth_canvas = tk.Label(self.auth_frame)
        self.auth_canvas.pack(padx=8, pady=8)

        # Status and controls
        controls = ttk.Frame(self.auth_frame)
        controls.pack(fill=tk.X, padx=8, pady=(0,8))

        self.auth_status_var = tk.StringVar(value="Streaming...")
        ttk.Label(controls, textvariable=self.auth_status_var).pack(side=tk.LEFT)

        ttk.Button(controls, text="Pause Streaming", command=self.toggle_streaming).pack(side=tk.RIGHT)

    def _build_reg_view(self):
        frm = ttk.Frame(self.reg_frame, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # Name and ID fields
        row = ttk.Frame(frm)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="Client Name:", width=15).pack(side=tk.LEFT)
        self.entry_name = ttk.Entry(row)
        self.entry_name.pack(side=tk.LEFT, fill=tk.X, expand=True)

        row2 = ttk.Frame(frm)
        row2.pack(fill=tk.X, pady=4)
        ttk.Label(row2, text="Client ID:", width=15).pack(side=tk.LEFT)
        self.entry_id = ttk.Entry(row2)
        self.entry_id.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Capture preview
        self.capture_preview = tk.Label(frm, text="[No preview captured]", relief=tk.SUNKEN, width=40, height=10)
        self.capture_preview.pack(pady=8)

        # Buttons
        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=4)

        ttk.Button(btns, text="Capture Photo (from camera)", command=self.capture_preview_from_camera).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Register Client", command=self.register_client_flow).pack(side=tk.RIGHT, padx=4)

        # Status
        self.reg_status_var = tk.StringVar(value="")
        ttk.Label(frm, textvariable=self.reg_status_var).pack(pady=(8,0))

        # internal preview frame
        self._captured_frame_bgr = None

    def toggle_streaming(self):
        self.streaming = not self.streaming
        self.auth_status_var.set("Streaming paused." if not self.streaming else "Streaming...")

    def update_frame(self):
        """Main GUI loop to update camera frames into the UI using OpenCV only."""
        try:
            frame_bgr = self.camera.read_frame()
        except Exception as e:
            self.auth_status_var.set(f"Camera error: {e}")
            return

        # Resize using OpenCV
        resized = cv2.resize(frame_bgr, (640, 480))

        # Convert BGR → RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Encode to PNG in memory
        _, buf = cv2.imencode(".png", rgb)

        # Tk-compatible image
        img = tk.PhotoImage(data=buf.tobytes())
        self.current_photo_image = img  # prevent garbage collection

        self.auth_canvas.config(image=img)

        # Authentication logic identical to before
        now = time.time()
        if self.streaming and not self._overlay_active:
            if now - self._last_auth_send >= AUTH_SEND_INTERVAL and not self._auth_call_running:
                self._last_auth_send = now
                threading.Thread(target=self._auth_call_thread, args=(frame_bgr.copy(),), daemon=True).start()

        self.after(30, self.update_frame)


    def _show_overlay(self, text):
        """Displays overlay text centered on the canvas for DISPLAY_MS_ON_RECOGNIZED ms."""
        if hasattr(self, "_overlay_label") and self._overlay_label.winfo_exists():
            self._overlay_label.destroy()

        self._overlay_label = tk.Label(self.auth_frame, text=text, bg="black", fg="white", font=("Arial", 20), bd=2, relief=tk.RIDGE)
        # place overlay in same location as auth_canvas
        self._overlay_label.place(in_=self.auth_canvas, relx=0.5, rely=0.1, anchor="n")
        self._overlay_active = True
        # Pause streaming while overlay is active (but keep the image display)
        prev_streaming = self.streaming
        self.streaming = False
        # schedule removal
        self.after(DISPLAY_MS_ON_RECOGNIZED, lambda: self._clear_overlay(prev_streaming))

    def _clear_overlay(self, restore_streaming=True):
        if hasattr(self, "_overlay_label") and self._overlay_label.winfo_exists():
            self._overlay_label.destroy()
        self._overlay_active = False
        self.streaming = restore_streaming
        self.auth_status_var.set("Streaming..." if self.streaming else "Streaming paused.")

    def _auth_call_thread(self, frame_bgr):
        """Background authentication call. Handles displaying recognized info."""
        self._auth_call_running = True
        try:
            resp = self.api.authenticate(frame_bgr)
        except Exception as e:
            # network error
            self.auth_status_var.set(f"Auth request error: {e}")
            self._auth_call_running = False
            return

        # Expecting JSON if recognized, otherwise maybe status or different code.
        recognized = False
        display_text = None
        try:
            if resp.status_code == 200:
                # Try parse JSON
                data = resp.json()
                # Common return shape: {"client_id": "...", "client_name": "..."} OR {"status":"unknown"}.
                cid = data.get("client_id") or data.get("id") or data.get("clientId")
                cname = data.get("client_name") or data.get("name") or data.get("clientName")
                if cid and cname:
                    recognized = True
                    display_text = f"Recognized: {cname} ({cid})"
                else:
                    # if API returns something else but 200 it's ambiguous; treat as unknown if no fields found
                    display_text = "Unknown"
            else:
                # Not 200 -> treat as unknown or error
                try:
                    data = resp.json()
                    # If the API returns a specific unknown structure like {"status":"unknown"} we handle that
                    if isinstance(data, dict) and data.get("status") == "unknown":
                        display_text = "Unknown"
                    else:
                        display_text = f"Auth error {resp.status_code}"
                except Exception:
                    display_text = f"Auth error {resp.status_code}"
        except Exception as e:
            display_text = f"Auth parse error: {e}"

        # Update UI on main thread
        def ui_update():
            self.auth_status_var.set(display_text)
            if recognized:
                self._show_overlay(display_text)
        self.after(0, ui_update)
        self._auth_call_running = False

    # -----------------
    # Registration flow
    # -----------------
    def capture_preview_from_camera(self):
        try:
            frame = self.camera.read_frame()
            self._captured_frame_bgr = frame

            # Resize for preview
            preview = cv2.resize(frame, (320, 240))
            preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            _, buf = cv2.imencode(".png", preview_rgb)

            img = tk.PhotoImage(data=buf.tobytes())
            self.capture_preview.config(image=img, text="")
            self.capture_preview.image = img

            self.reg_status_var.set("Preview captured from camera.")
        except Exception as e:
            self.reg_status_var.set(f"Capture failed: {e}")


    def register_client_flow(self):
        name = self.entry_name.get().strip()
        cid = self.entry_id.get().strip()
        if not name or not cid:
            messagebox.showwarning("Missing Data", "Please enter both client name and client ID.")
            return
        if self._captured_frame_bgr is None:
            messagebox.showwarning("No Photo", "Please capture a photo from the camera first.")
            return

        # Disable buttons / show status
        self.reg_status_var.set("Registering client...")
        threading.Thread(target=self._register_thread, args=(name, cid, self._captured_frame_bgr.copy()), daemon=True).start()

    def _register_thread(self, name, cid, frame_bgr):
        try:
            # 1) register_client
            resp_reg = self.api.register_client(client_name=name, client_id=cid, frame_bgr=frame_bgr)
        except Exception as e:
            self.after(0, lambda: self.reg_status_var.set(f"Register request failed: {e}"))
            return

        if resp_reg.status_code not in (200, 201):
            # show server response text if available
            msg = f"Register failed: {resp_reg.status_code}"
            try:
                msg += " - " + resp_reg.text
            except Exception:
                pass
            self.after(0, lambda: self.reg_status_var.set(msg))
            return

        # 2) process_client_image
        try:
            resp_proc = self.api.process_client_image(client_id=cid)
        except Exception as e:
            self.after(0, lambda: self.reg_status_var.set(f"Processing request failed: {e}"))
            return

        if resp_proc.status_code not in (200, 201):
            msg = f"Process failed: {resp_proc.status_code}"
            try:
                msg += " - " + resp_proc.text
            except Exception:
                pass
            self.after(0, lambda: self.reg_status_var.set(msg))
            return

        # success
        self.after(0, lambda: self.reg_status_var.set("Client registered and processed successfully."))

    # -----------------
    # Shutdown
    # -----------------
    def on_close(self):
        # release camera and destroy
        self.streaming = False
        try:
            self.camera.release()
        except Exception:
            pass
        self.destroy()

# -------------------------
# Entry point
# -------------------------
def main():
    try:
        camera = CameraController(index=CAMERA_INDEX)
    except Exception as e:
        tk.messagebox.showerror("Camera Error", f"Unable to start camera: {e}")
        return

    api = ClientAPI()
    app = GymApp(api=api, camera=camera)
    app.geometry("700x700")
    app.mainloop()

if __name__ == "__main__":
    main()
