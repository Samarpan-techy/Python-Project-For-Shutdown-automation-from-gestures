import os 
import sys 
import threading 
import time 
import tkinter as tk 
import cv2 
import mediapipe as mp 
from mediapipe.tasks import python 
from mediapipe.tasks.python import vision 

# ग्लोबल स्टेट
is_active = False 

# --- नए MediaPipe Tasks API का सेटअप --- 
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path): 
    print(f"[ERROR] '{model_path}' फाइल नहीं मिली! कृपया इसे स्क्रिप्ट वाले फोल्डर में डाउनलोड करके रखें।") 

base_options = python.BaseOptions(model_asset_path=model_path) 
options = vision.HandLandmarkerOptions( 
    base_options=base_options, 
    num_hands=1, 
    min_hand_detection_confidence=0.7 
) 
detector = vision.HandLandmarker.create_from_options(options) 

def shutdown_pc(): 
    """सिस्टम को तुरंत शटडाउन करने का कमांड"""
    if sys.platform == "win32": 
        os.system("shutdown /s /t 1") 
    elif sys.platform == "darwin": 
        os.system("osascript -e 'tell app \"System Events\" to shut down'") 
    elif sys.platform.startswith("linux"): 
        os.system("shutdown -h now") 

def vision_tracking_loop(on_reset_callback): 
    global is_active 
    INDEX_FINGER_TIP = 8 
    cap = cv2.VideoCapture(0) 
    while is_active: 
        success, frame = cap.read() 
        if not success: 
            continue 
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame) 
        detection_result = detector.detect(mp_image) 
        
        if detection_result.hand_landmarks: 
            for hand_landmarks in detection_result.hand_landmarks: 
                landmark = hand_landmarks[INDEX_FINGER_TIP] 
                if 0 <= landmark.x <= 1 and 0 <= landmark.y <= 1: 
                    cap.release() 
                    is_active = False 
                    on_reset_callback() 
                    shutdown_pc() 
                    return 
        time.sleep(0.05) 
    cap.release() 

# --- 1. मॉडर्न फ्लोटिंग बटन विजेट --- 
class FloatingOverlayButton(tk.Toplevel): 
    def __init__(self, main_window): 
        super().__init__() 
        self.main_window = main_window 
        self.initUI() 
        
    def initUI(self): 
        self.overrideredirect(True) 
        self.attributes("-topmost", True) 
        self.config(bg="gray") 
        self.attributes("-transparentcolor", "gray") 
        
        # आकर्षक राउंडेड-लुक बटन
        self.button = tk.Button( 
            self, text="● OFF", font=("Segoe UI", 10, "bold"), 
            bg="#2A2A32", fg="#FF5555", 
            activebackground="#3A3A45", activeforeground="#FF5555", 
            bd=0, width=8, height=2, cursor="hand2",
            relief="flat", highlightthickness=0
        ) 
        self.button.pack() 
        
        self.button.bind("<Button-1>", self.start_drag) 
        self.button.bind("<B1-Motion>", self.drag) 
        self.button.bind("<Double-Button-1>", self.restore_main) 
        self.geometry("80x45+100+100") 
        self.withdraw() 
        
    def update_style(self, active): 
        if active: 
            self.button.config(bg="#1E3A2F", fg="#50FA7B", text="● ACTIVE") 
        else: 
            self.button.config(bg="#2A2A32", fg="#FF5555", text="● OFF") 

    def handle_click(self): 
        self.main_window.toggle_gesture_system() 
        
    def start_drag(self, event): 
        self.x = event.x 
        self.y = event.y 
        
    def drag(self, event): 
        deltax = event.x - self.x 
        deltay = event.y - self.y 
        x = self.winfo_x() + deltax 
        y = self.winfo_y() + deltay 
        self.geometry(f"+{x}+{y}") 
        
    def restore_main(self, event): 
        self.main_window.deiconify() 
        self.withdraw() 


# --- 2. मुख्य मॉडर्न सॉफ्टवेयर इंटरफ़ेस विंडो --- 
class MainWindow(tk.Tk): 
    def __init__(self): 
        super().__init__() 
        self.initUI() 
        self.overlay = FloatingOverlayButton(self) 
        
    def initUI(self): 
        self.title("Gesture Control Panel v1.0") 
        self.geometry("460x340") 
        self.configure(bg="#1E1E24") # मॉडर्न डार्क ग्रे बैकग्राउंड
        self.resizable(False, False)

        # टाइटल बार / हेडर
        self.title_label = tk.Label( 
            self, text="Gesture Shutdown", font=("Segoe UI", 18, "bold"), 
            bg="#1E1E24", fg="#E2E8F0" 
        ) 
        self.title_label.pack(pady=(30, 5)) 
        
        self.subtitle_label = tk.Label( 
            self, text="Control your PC with simple hand gestures", font=("Segoe UI", 9), 
            bg="#1E1E24", fg="#94A3B8" 
        ) 
        self.subtitle_label.pack(pady=(0, 20)) 

        # स्टेटस कार्ड (विजुअल बॉक्स)
        self.status_frame = tk.Frame(self, bg="#2D2D37", bd=0, padx=15, pady=10)
        self.status_frame.pack(fill="x", padx=40, pady=10)
        
        self.status_label = tk.Label( 
            self.status_frame, text="System Status: IDLE", font=("Segoe UI", 11, "bold"), 
            bg="#2D2D37", fg="#94A3B8" 
        ) 
        self.status_label.pack() 

        # मुख्य एक्शन बटन (टॉगल बटन)
        self.toggle_btn = tk.Button( 
            self, text="START SCANNING", font=("Segoe UI", 12, "bold"), 
            bg="#FF5555", fg="white", 
            activebackground="#FF4444", activeforeground="white", 
            bd=0, padx=25, pady=12, cursor="hand2",
            relief="flat", highlightthickness=0, command=self.toggle_gesture_system
        ) 
        self.toggle_btn.pack(pady=25) 
        
        # बटन होवर इफेक्ट्स (Hover Effects)
        self.toggle_btn.bind("<Enter>", lambda e: self.on_hover(self.toggle_btn))
        self.toggle_btn.bind("<Leave>", lambda e: self.on_leave(self.toggle_btn))

        # बॉटम बार
        bottom_frame = tk.Frame(self, bg="#1E1E24") 
        bottom_frame.pack(side="bottom", fill="x", padx=30, pady=20) 
        
        info_text = tk.Label( 
            bottom_frame, text="💡 Tip: Minimize to enter Mini-Overlay mode", font=("Segoe UI", 9, "italic"), 
            bg="#1E1E24", fg="#64748B" 
        ) 
        info_text.pack(side="left") 
        
        self.hide_btn = tk.Button( 
            bottom_frame, text="Mini Mode", font=("Segoe UI", 9, "bold"), 
            bg="#3A3A45", fg="#E2E8F0", 
            activebackground="#4A4A56", activeforeground="white", 
            bd=0, padx=12, pady=6, cursor="hand2", command=self.switch_to_overlay 
        ) 
        self.hide_btn.pack(side="right") 
        
        self.bind("<Unmap>", self.on_minimize) 

    def on_hover(self, button):
        if not is_active:
            button.config(bg="#FF6666")
        else:
            button.config(bg="#40E070")

    def on_leave(self, button):
        if not is_active:
            button.config(bg="#FF5555")
        else:
            button.config(bg="#50FA7B")

    def toggle_gesture_system(self): 
        global is_active 
        if not is_active: 
            is_active = True 
            self.toggle_btn.config(text="STOP SYSTEM", bg="#50FA7B", fg="#1E1E24") 
            self.status_frame.config(bg="#1E3A2F")
            self.status_label.config(text="System Status: SCANNING FOR INDEX FINGER...", fg="#50FA7B", bg="#1E3A2F") 
            self.overlay.update_style(active=True) 
            threading.Thread( 
                target=vision_tracking_loop, args=(self.reset_ui_state,), daemon=True 
            ).start() 
        else: 
            self.reset_ui_state()

    def reset_ui_state(self): 
        self.after(0, self._reset_ui) 

    def _reset_ui(self): 
        global is_active 
        is_active = False 
        self.toggle_btn.config(text="START SCANNING", bg="#FF5555", fg="white") 
        self.status_frame.config(bg="#2D2D37")
        self.status_label.config(text="System Status: IDLE", fg="#94A3B8", bg="#2D2D37") 
        self.overlay.update_style(active=False) 

    def switch_to_overlay(self): 
        self.withdraw() 
        self.overlay.deiconify() 

    def on_minimize(self, event): 
        if event.widget == self: 
            self.switch_to_overlay() 

if __name__ == "__main__": 
    app = MainWindow() 
    app.mainloop()

