import tkinter as tk
from tkinter import scrolledtext
import socket
import threading
import time
import requests
import cv2
from PIL import Image, ImageTk


# ============================================================
# CAMERA CONFIG
# ============================================================

CAMERA_IP = "192.168.1.229"

# Your requested URL
PREFERRED_URL = "http://192.168.1.229:8080/video"


# Common HTTP/MJPEG endpoints
TEST_URLS = [
    "http://192.168.1.229:8080/video",
    "http://192.168.1.229:8080/video.mjpg",
    "http://192.168.1.229:8080/stream",
    "http://192.168.1.229:8080/stream.mjpg",
    "http://192.168.1.229:8080/live",
    "http://192.168.1.229:8080/live.mjpg",
    "http://192.168.1.229:8080/mjpeg",
    "http://192.168.1.229:8080/mjpegstream",
    "http://192.168.1.229:8080/video_feed",
    "http://192.168.1.229:8080/mjpg/video.mjpg",

    "http://192.168.1.229/video",
    "http://192.168.1.229:8000/video",
    "http://192.168.1.229:8081/video",
    "http://192.168.1.229:8899/video",
]


# ============================================================
# COLORS
# ============================================================

BG = "#101010"
PANEL = "#181818"
BLACK = "#000000"

WHITE = "#FFFFFF"
GRAY = "#AAAAAA"
GREEN = "#00D26A"
RED = "#FF4444"
YELLOW = "#FFD43B"


# ============================================================
# MAIN APPLICATION
# ============================================================

class CameraApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Mi 360 Network Camera Monitor"
        )

        self.root.geometry(
            "1250x850"
        )

        self.root.configure(
            bg=BG
        )

        # ----------------------------------------------------
        # Camera state
        # ----------------------------------------------------

        self.running = False

        self.cap = None

        self.current_url = None

        self.frame = None

        self.lock = threading.Lock()

        self.fps = 0

        self.frame_counter = 0

        self.fps_time = time.time()

        # ====================================================
        # HEADER
        # ====================================================

        header = tk.Frame(
            root,
            bg=PANEL,
            height=70
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="MI 360 CAMERA MONITOR",
            font=("Segoe UI", 23, "bold"),
            fg=WHITE,
            bg=PANEL
        )

        title.pack(
            side="left",
            padx=25
        )

        ip = tk.Label(
            header,
            text=f"IP: {CAMERA_IP}",
            font=("Consolas", 12),
            fg=GRAY,
            bg=PANEL
        )

        ip.pack(
            side="right",
            padx=25
        )

        # ====================================================
        # MAIN AREA
        # ====================================================

        main = tk.Frame(
            root,
            bg=BG
        )

        main.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # ====================================================
        # VIDEO FRAME
        # ====================================================

        self.video_frame = tk.Frame(
            main,
            bg=BLACK,
            highlightthickness=2,
            highlightbackground="#333333"
        )

        self.video_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.video_label = tk.Label(
            self.video_frame,
            text="CAMERA OFFLINE",
            font=("Segoe UI", 23, "bold"),
            fg=GRAY,
            bg=BLACK
        )

        self.video_label.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # RIGHT SIDE PANEL
        # ====================================================

        side = tk.Frame(
            main,
            bg=PANEL,
            width=350
        )

        side.pack(
            side="right",
            fill="y",
            padx=(15, 0)
        )

        side.pack_propagate(False)

        # Status title

        tk.Label(
            side,
            text="NETWORK STATUS",
            font=("Segoe UI", 14, "bold"),
            fg=WHITE,
            bg=PANEL
        ).pack(
            pady=(20, 10)
        )

        # Status

        self.status_label = tk.Label(
            side,
            text="● OFFLINE",
            font=("Segoe UI", 14, "bold"),
            fg=RED,
            bg=PANEL
        )

        self.status_label.pack(
            pady=5
        )

        # IP

        tk.Label(
            side,
            text=f"Camera IP\n{CAMERA_IP}",
            font=("Consolas", 11),
            fg=GRAY,
            bg=PANEL
        ).pack(
            pady=10
        )

        # FPS

        self.fps_label = tk.Label(
            side,
            text="FPS: 0",
            font=("Consolas", 11),
            fg=WHITE,
            bg=PANEL
        )

        self.fps_label.pack(
            pady=5
        )

        # Current URL

        self.url_label = tk.Label(
            side,
            text="Stream:\nNot detected",
            font=("Consolas", 9),
            fg=GRAY,
            bg=PANEL,
            wraplength=310,
            justify="left"
        )

        self.url_label.pack(
            padx=15,
            pady=15
        )

        # ====================================================
        # BUTTONS
        # ====================================================

        self.test_button = tk.Button(
            side,
            text="🔍 TEST CAMERA",
            font=("Segoe UI", 11, "bold"),
            fg=WHITE,
            bg="#333333",
            activebackground="#444444",
            relief="flat",
            padx=15,
            pady=10,
            command=self.start_test
        )

        self.test_button.pack(
            fill="x",
            padx=25,
            pady=5
        )

        self.start_button = tk.Button(
            side,
            text="▶ START STREAM",
            font=("Segoe UI", 11, "bold"),
            fg=WHITE,
            bg="#087F5B",
            activebackground="#0A9F70",
            relief="flat",
            padx=15,
            pady=10,
            command=self.start_stream
        )

        self.start_button.pack(
            fill="x",
            padx=25,
            pady=5
        )

        self.stop_button = tk.Button(
            side,
            text="■ STOP STREAM",
            font=("Segoe UI", 11, "bold"),
            fg=WHITE,
            bg="#A61E1E",
            activebackground="#C52A2A",
            relief="flat",
            padx=15,
            pady=10,
            command=self.stop_stream
        )

        self.stop_button.pack(
            fill="x",
            padx=25,
            pady=5
        )

        # ====================================================
        # LOG
        # ====================================================

        tk.Label(
            side,
            text="DIAGNOSTIC LOG",
            font=("Segoe UI", 11, "bold"),
            fg=WHITE,
            bg=PANEL
        ).pack(
            pady=(20, 5)
        )

        self.log_box = scrolledtext.ScrolledText(
            side,
            height=18,
            bg="#0B0B0B",
            fg="#DDDDDD",
            insertbackground=WHITE,
            font=("Consolas", 9),
            relief="flat"
        )

        self.log_box.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        # ====================================================
        # CLOSE
        # ====================================================

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )

    # ========================================================
    # LOG FUNCTION
    # ========================================================

    def log(self, message):

        def write():

            self.log_box.insert(
                tk.END,
                message + "\n"
            )

            self.log_box.see(
                tk.END
            )

        self.root.after(
            0,
            write
        )

    # ========================================================
    # STATUS
    # ========================================================

    def set_status(
        self,
        text,
        color
    ):

        self.root.after(
            0,
            lambda: self.status_label.config(
                text=text,
                fg=color
            )
        )

    # ========================================================
    # TCP PORT TEST
    # ========================================================

    def test_port(
        self,
        port
    ):

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(2)

        try:

            result = sock.connect_ex(
                (
                    CAMERA_IP,
                    port
                )
            )

            if result == 0:

                self.log(
                    f"✓ TCP {port} OPEN"
                )

                return True

            self.log(
                f"✗ TCP {port} unavailable"
            )

            return False

        except Exception as e:

            self.log(
                f"✗ TCP {port}: {e}"
            )

            return False

        finally:

            sock.close()

    # ========================================================
    # HTTP TEST
    # ========================================================

    def test_http(
        self,
        url
    ):

        try:

            response = requests.get(
                url,
                timeout=3,
                stream=True,
                allow_redirects=False
            )

            status = response.status_code

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            server = response.headers.get(
                "Server",
                ""
            )

            self.log(
                f"{url}"
            )

            self.log(
                f"  Status: {status}"
            )

            self.log(
                f"  Type: {content_type}"
            )

            if server:

                self.log(
                    f"  Server: {server}"
                )

            content = content_type.lower()

            possible_video = (
                "multipart" in content
                or "mjpeg" in content
                or content.startswith("video/")
            )

            response.close()

            if possible_video:

                self.log(
                    "  ✓ VIDEO STREAM DETECTED"
                )

                return True

            if status < 400:

                self.log(
                    "  ✓ HTTP SERVICE FOUND"
                )

            else:

                self.log(
                    "  ✗ HTTP ERROR"
                )

            return False

        except requests.exceptions.Timeout:

            self.log(
                f"  ✗ TIMEOUT: {url}"
            )

        except requests.exceptions.ConnectionError:

            self.log(
                f"  ✗ CONNECTION FAILED: {url}"
            )

        except Exception as e:

            self.log(
                f"  ✗ ERROR: {e}"
            )

        return False

    # ========================================================
    # START TEST
    # ========================================================

    def start_test(self):

        self.test_button.config(
            state="disabled"
        )

        self.set_status(
            "● TESTING...",
            YELLOW
        )

        self.log_box.delete(
            "1.0",
            tk.END
        )

        threading.Thread(
            target=self.test_camera,
            daemon=True
        ).start()

    # ========================================================
    # FULL CAMERA TEST
    # ========================================================

    def test_camera(self):

        self.log(
            "=" * 35
        )

        self.log(
            "CAMERA NETWORK DIAGNOSTIC"
        )

        self.log(
            "=" * 35
        )

        self.log(
            f"IP: {CAMERA_IP}"
        )

        self.log(
            f"Preferred URL: {PREFERRED_URL}"
        )

        self.log("")

        # ----------------------------------------------------
        # TEST TCP
        # ----------------------------------------------------

        open_ports = []

        for port in [80, 443, 8080]:

            if self.test_port(port):

                open_ports.append(
                    port
                )

        self.log("")

        if not open_ports:

            self.log(
                "❌ No TCP ports available."
            )

            self.set_status(
                "● DEVICE UNREACHABLE",
                RED
            )

            self.root.after(
                0,
                lambda: self.test_button.config(
                    state="normal"
                )
            )

            return

        self.log(
            f"Open ports: {open_ports}"
        )

        self.log("")

        # ----------------------------------------------------
        # TEST STREAM URLS
        # ----------------------------------------------------

        found = None

        for url in TEST_URLS:

            self.log(
                f"Testing: {url}"
            )

            if self.test_http(url):

                found = url

                break

        # ----------------------------------------------------
        # FOUND
        # ----------------------------------------------------

        if found:

            self.current_url = found

            self.log("")
            self.log(
                "================================"
            )

            self.log(
                "✓ COMPATIBLE VIDEO STREAM FOUND"
            )

            self.log(
                found
            )

            self.log(
                "================================"
            )

            self.root.after(
                0,
                lambda: self.url_label.config(
                    text=f"Stream:\n{found}",
                    fg=GREEN
                )
            )

            self.set_status(
                "● STREAM FOUND",
                GREEN
            )

            self.root.after(
                0,
                lambda: self.test_button.config(
                    state="normal"
                )
            )

        else:

            self.log("")
            self.log(
                "================================"
            )

            self.log(
                "❌ NO HTTP VIDEO STREAM FOUND"
            )

            self.log(
                "================================"
            )

            self.log("")
            self.log(
                "The IP may be a network device,"
            )

            self.log(
                "but /video is not a valid stream."
            )

            self.set_status(
                "● NO VIDEO STREAM",
                RED
            )

            self.root.after(
                0,
                lambda: self.test_button.config(
                    state="normal"
                )
            )

    # ========================================================
    # START STREAM
    # ========================================================

    def start_stream(self):

        if self.running:

            return

        # ----------------------------------------------------
        # If no detected URL, use requested URL
        # ----------------------------------------------------

        if not self.current_url:

            self.current_url = PREFERRED_URL

            self.log(
                "Using requested URL:"
            )

            self.log(
                self.current_url
            )

        self.running = True

        self.start_button.config(
            state="disabled"
        )

        self.set_status(
            "● CONNECTING...",
            YELLOW
        )

        threading.Thread(
            target=self.camera_worker,
            daemon=True
        ).start()

    # ========================================================
    # CAMERA WORKER
    # ========================================================

    def camera_worker(self):

        url = self.current_url

        self.log("")
        self.log(
            "Opening stream:"
        )

        self.log(
            url
        )

        # ----------------------------------------------------
        # OpenCV
        # ----------------------------------------------------

        self.cap = cv2.VideoCapture(
            url
        )

        try:

            self.cap.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

        except Exception:

            pass

        # ----------------------------------------------------
        # Connection
        # ----------------------------------------------------

        if not self.cap.isOpened():

            self.log(
                "❌ OpenCV could not open stream."
            )

            self.running = False

            self.root.after(
                0,
                self.stream_failed
            )

            return

        self.log(
            "✓ OpenCV stream opened."
        )

        self.set_status(
            "● CONNECTED",
            GREEN
        )

        self.root.after(
            0,
            lambda: self.url_label.config(
                text=f"Stream:\n{url}",
                fg=GREEN
            )
        )

        # ----------------------------------------------------
        # Read frames
        # ----------------------------------------------------

        while self.running:

            ret, frame = (
                self.cap.read()
            )

            if not ret:

                self.log(
                    "⚠ Frame read failed."
                )

                time.sleep(
                    0.5
                )

                continue

            # ------------------------------------------------
            # FPS
            # ------------------------------------------------

            self.frame_counter += 1

            elapsed = (
                time.time()
                - self.fps_time
            )

            if elapsed >= 1:

                self.fps = (
                    self.frame_counter
                    / elapsed
                )

                self.frame_counter = 0

                self.fps_time = time.time()

                self.root.after(
                    0,
                    lambda fps=self.fps:
                    self.fps_label.config(
                        text=f"FPS: {fps:.1f}"
                    )
                )

            # ------------------------------------------------
            # Save frame
            # ------------------------------------------------

            with self.lock:

                self.frame = frame.copy()

            self.root.after(
                1,
                self.update_video
            )

        # ----------------------------------------------------
        # Release
        # ----------------------------------------------------

        if self.cap:

            self.cap.release()

            self.cap = None

        self.log(
            "Stream released."
        )

    # ========================================================
    # STREAM FAILED
    # ========================================================

    def stream_failed(self):

        self.set_status(
            "● STREAM FAILED",
            RED
        )

        self.video_label.config(
            image="",
            text=(
                "STREAM COULD NOT BE OPENED\n\n"
                f"{self.current_url}"
            )
        )

        self.video_label.image = None

        self.start_button.config(
            state="normal"
        )

    # ========================================================
    # UPDATE VIDEO
    # ========================================================

    def update_video(self):

        if not self.running:

            return

        with self.lock:

            if self.frame is None:

                return

            frame = self.frame.copy()

        # ----------------------------------------------------
        # BGR → RGB
        # ----------------------------------------------------

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # ----------------------------------------------------
        # Available area
        # ----------------------------------------------------

        width = (
            self.video_frame.winfo_width()
        )

        height = (
            self.video_frame.winfo_height()
        )

        if width < 100:

            width = 850

        if height < 100:

            height = 650

        # ----------------------------------------------------
        # Aspect ratio
        # ----------------------------------------------------

        h, w = frame.shape[:2]

        scale = min(
            width / w,
            height / h
        )

        new_w = max(
            1,
            int(w * scale)
        )

        new_h = max(
            1,
            int(h * scale)
        )

        frame = cv2.resize(
            frame,
            (
                new_w,
                new_h
            ),
            interpolation=cv2.INTER_AREA
        )

        # ----------------------------------------------------
        # PIL
        # ----------------------------------------------------

        image = Image.fromarray(
            frame
        )

        photo = ImageTk.PhotoImage(
            image=image
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        self.video_label.config(
            image=photo,
            text=""
        )

        self.video_label.image = photo

    # ========================================================
    # STOP STREAM
    # ========================================================

    def stop_stream(self):

        self.running = False

        if self.cap:

            self.cap.release()

            self.cap = None

        with self.lock:

            self.frame = None

        self.video_label.config(
            image="",
            text="CAMERA OFFLINE"
        )

        self.video_label.image = None

        self.set_status(
            "● OFFLINE",
            RED
        )

        self.fps_label.config(
            text="FPS: 0"
        )

        self.start_button.config(
            state="normal"
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.running = False

        if self.cap:

            self.cap.release()

            self.cap = None

        self.root.destroy()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = CameraApp(
        root
    )

    root.mainloop()