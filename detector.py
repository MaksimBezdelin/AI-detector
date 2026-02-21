"""
🏭 УМНЫЙ ИНСПЕКТОР ТРЕЩИН
✅ ИЗОБРАЖЕНИЯ + ВИДЕО | Центр → 50/50 | ПОЛОНОЕ ИЗОБРАЖЕНИЕ
✅ ИСПРАВЛЕНА ОШИБКА UnboundLocalError
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from ultralytics import YOLO
import os
from PIL import Image, ImageTk
import threading
import time

class SmartInspector:
    def __init__(self, root):
        self.root = root
        self.root.title("🏭 УМНЫЙ ИНСПЕКТОР ТРЕЩИН")
        self.root.geometry("2000x1200")
        self.root.configure(bg='#0a0e17')
        self.root.resizable(True, True)
        
        self.model = self.load_model()
        if not self.model:
            messagebox.showerror("❌ ОШИБКА", "Не найден best.pt!\nПоместите best.pt в папку с программой!")
            return
        
        self.classes = self.model.names
        print(f"🔍 КЛАССЫ: {self.classes}")
        self.model_name = self.get_model_name()
        self.showing_results = False
        self.result_image = None
        self.split_mode = False
        self.cap = None
        self.video_thread = None
        self.playing_video = False
        
        self.setup_centered_ui()
    
    def load_model(self):
        model_paths = ['best.pt', 'yolov8s.pt', 'yolov8m.pt', 'last.pt']
        for model_path in model_paths:
            if os.path.exists(model_path):
                print(f"✅ Загружаем: {model_path}")
                return YOLO(model_path)
        try:
            return YOLO('yolov8s.pt')
        except:
            return None
    
    def get_model_name(self):
        if os.path.exists('best.pt'):
            return "best.pt"
        elif os.path.exists('yolov8s.pt'):
            return "yolov8s.pt"
        else:
            return "yolov8m.pt"
    
    def setup_centered_ui(self):
        self.main_frame = tk.Frame(self.root, bg='#0a0e17')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        header_frame = tk.Frame(self.main_frame, bg='#1a1f2e', relief=tk.RAISED, bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_frame = tk.Frame(header_frame, bg='#1a1f2e')
        title_frame.pack(pady=25)
        
        tk.Label(title_frame, text="🏭 УМНЫЙ ИНСПЕКТОР ТРЕЩИН", 
                font=('Segoe UI', 36, 'bold'), bg='#1a1f2e', fg='#00ff88').pack()
        
        tk.Label(title_frame, text="🖼️ ИЗОБРАЖЕНИЯ + 🎥 ВИДЕО", 
                font=('Segoe UI', 16), bg='#1a1f2e', fg='#a0a8c0').pack(pady=(5, 0))
        
        model_frame = tk.Frame(header_frame, bg='#16213e', relief=tk.RAISED, bd=1)
        model_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        self.model_label = tk.Label(model_frame, text=f"🧠 Активная модель: {self.model_name}", 
                                   font=('Segoe UI', 14, 'bold'), bg='#16213e', fg='#00ff88')
        self.model_label.pack(pady=12)
        
        tk.Label(model_frame, text="🔵 s_scratch | 🔴 l_scratch", 
                font=('Segoe UI', 12), bg='#16213e', fg='#88ccff').pack(pady=(0, 12))
        
        btn_frame = tk.Frame(self.main_frame, bg='#0a0e17')
        btn_frame.pack(expand=True)
        
        self.scan_btn = tk.Button(btn_frame, text="🚀 ЗАПУСТИТЬ СКАНИРОВАНИЕ\n🖼️ JPG/PNG + 🎥 MP4/AVI/MKV", 
                                 command=self.scan_cracks,
                                 font=('Segoe UI', 18, 'bold'),
                                 bg='#00d4ff', fg='white',
                                 activebackground='#00b8e6',
                                 relief=tk.FLAT, bd=0,
                                 width=30, height=3,
                                 cursor="hand2")
        self.scan_btn.configure(highlightthickness=0, borderwidth=0)
        self.scan_btn.pack(pady=50)
        self.animate_button()
        
        status_container = tk.Frame(self.main_frame, bg='#1a1f2e', relief=tk.RAISED, bd=2)
        status_container.pack(fill=tk.X, pady=(30, 20))
        
        self.status_var = tk.StringVar(value="👆 Нажмите кнопку для анализа изображения/видео")
        tk.Label(status_container, textvariable=self.status_var,
                font=('Segoe UI', 16, 'bold'), bg='#1a1f2e', fg='#ffffff').pack(pady=20)
        
        self.stats_var = tk.StringVar(value="📊 Готов к работе")
        self.stats_label = tk.Label(status_container, textvariable=self.stats_var,
                                   font=('Segoe UI', 15, 'bold'), bg='#1a1f2e', fg='#44ff44')
        self.stats_label.pack(pady=(0, 20))
        
        self.add_decorations(self.main_frame)
    
    def switch_to_split_layout(self):
        if self.split_mode:
            return
            
        self.main_frame.destroy()
        
        self.split_container = tk.Frame(self.root, bg='#0a0e17')
        self.split_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        left_frame = tk.Frame(self.split_container, bg='#1a1f2e', relief=tk.RAISED, bd=2)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        right_frame = tk.Frame(self.split_container, bg='#16213e', relief=tk.RAISED, bd=2)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        self.split_container.grid_columnconfigure(0, weight=1)
        self.split_container.grid_columnconfigure(1, weight=3)
        self.split_container.grid_rowconfigure(0, weight=1)
        
        self.setup_split_left_panel(left_frame)
        self.setup_split_right_panel(right_frame)
        
        self.split_mode = True
    
    def setup_split_left_panel(self, parent):
        title_frame = tk.Frame(parent, bg='#1a1f2e')
        title_frame.pack(fill=tk.X, pady=(15, 10))
        tk.Label(title_frame, text="🏭 ИНСПЕКТОР", 
                font=('Segoe UI', 22, 'bold'), bg='#1a1f2e', fg='#00ff88').pack()
        
        model_frame = tk.Frame(parent, bg='#0d1422', relief=tk.RAISED, bd=1)
        model_frame.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(model_frame, text=f"🧠 {self.model_name}", 
                font=('Segoe UI', 12, 'bold'), bg='#0d1422', fg='#00ff88').pack(pady=12)
        tk.Label(model_frame, text="🔵 s_scratch | 🔴 l_scratch", 
                font=('Segoe UI', 11), bg='#0d1422', fg='#88ccff').pack(pady=(0, 12))
        
        btn_frame = tk.Frame(parent, bg='#1a1f2e')
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        tk.Button(btn_frame, text="🔄 НОВЫЙ АНАЛИЗ", 
                 command=self.new_analysis,
                 font=('Segoe UI', 13, 'bold'),
                 bg='#00d4ff', fg='white',
                 activebackground='#00b8e6',
                 relief=tk.FLAT, bd=0,
                 cursor="hand2").pack(pady=10)
        
        status_frame = tk.Frame(parent, bg='#0d1422', relief=tk.RAISED, bd=1)
        status_frame.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(status_frame, textvariable=self.status_var,
                font=('Segoe UI', 13, 'bold'), bg='#0d1422', fg='#ffffff').pack(pady=10)
        tk.Label(status_frame, textvariable=self.stats_var,
                font=('Segoe UI', 12, 'bold'), bg='#0d1422', fg='#44ff44').pack(pady=(0, 10))
    
    def setup_split_right_panel(self, parent):
        header = tk.Frame(parent, bg='#16213e')
        header.pack(fill=tk.X, pady=(10, 5))
        tk.Label(header, text="📸 РЕЗУЛЬТАТ АНАЛИЗА", 
                font=('Segoe UI', 16, 'bold'), bg='#16213e', fg='#00ff88').pack(pady=10)
        
        self.canvas = tk.Canvas(parent, bg='#0d1422', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stop_btn = tk.Button(parent, text="⏹️ STOP ВИДЕО", 
                                 command=self.stop_video,
                                 font=('Segoe UI', 12, 'bold'),
                                 bg='#ff4444', fg='white',
                                 activebackground='#cc3333',
                                 relief=tk.FLAT, bd=0,
                                 cursor="hand2")
        self.stop_btn.pack(pady=5)
        self.stop_btn.pack_forget()
    
    def animate_button(self):
        try:
            self.root.after(2000, self.animate_button)
        except:
            pass
    
    def add_decorations(self, parent):
        try:
            left_line = tk.Frame(parent, bg='#00ff88', width=4)
            left_line.place(relx=0.05, rely=0.1, relheight=0.8, anchor='w')
            right_line = tk.Frame(parent, bg='#00d4ff', width=4)
            right_line.place(relx=0.95, rely=0.1, relheight=0.8, anchor='e')
        except:
            pass
    
    def scan_cracks(self):
        file_path = filedialog.askopenfilename(
            title="🚀 Выберите файл",
            filetypes=[
                ("Все медиа", "*.jpg *.jpeg *.png *.bmp *.mp4 *.avi *.mkv *.mov *.flv"),
                ("Изображения", "*.jpg *.jpeg *.png *.bmp"),
                ("Видео", "*.mp4 *.avi *.mkv *.mov *.flv"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path and os.path.exists(file_path):
            print(f"✅ Файл выбран: {file_path}")
            self.switch_to_split_layout()
            self.process_file(file_path)
    
    def new_analysis(self):
        self.scan_cracks()
    
    def process_file(self, file_path):
        if file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.flv')):
            self.process_video(file_path)
        else:
            self.process_image(file_path)
    
    def process_image(self, image_path):
        self.status_var.set("🔍 Анализ изображения...")
        self.stats_var.set("⏳ Обработка...")
        self.root.update()
        
        self.playing_video = False
        self.stop_btn.pack_forget()
        
        try:
            conf_thresh = 0.08
            results = self.model(image_path, conf=conf_thresh, verbose=False, imgsz=800)
            filtered_result = self.smart_filter(results[0])
            
            self.canvas.update_idletasks()
            canvas_w = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 1200
            canvas_h = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 800
            
            annotated = filtered_result.plot(line_width=3, font_size=11, labels=True)
            annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            img_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
            
            h, w = img_rgb.shape[:2]
            scale = min(canvas_w/w * 0.95, canvas_h/h * 0.95)
            new_w, new_h = int(w * scale), int(h * scale)
            img_resized = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            img_pil = Image.fromarray(img_resized)
            self.photo = ImageTk.PhotoImage(img_pil)
            
            self.canvas.delete("all")
            self.canvas.create_image(canvas_w//2, canvas_h//2, image=self.photo, anchor=tk.CENTER)
            
            stats = self.get_priority_stats(filtered_result)
            self.update_stats(stats)
            
        except Exception as e:
            self.status_var.set(f"❌ Ошибка: {str(e)}")
            self.stats_var.set("❌ Ошибка анализа")
            print(f"❌ Ошибка: {e}")
    
    def process_video(self, video_path):
        self.status_var.set("🎥 Загрузка видео...")
        self.stats_var.set("⏳ Инициализация...")
        self.root.update()
        
        self.playing_video = True
        self.stop_btn.pack(pady=5)
        
        self.video_thread = threading.Thread(target=self.video_analysis_thread, args=(video_path,))
        self.video_thread.daemon = True
        self.video_thread.start()
    
    def video_analysis_thread(self, video_path):
        """✅ ИСПРАВЛЕНА ОШИБКА - всегда есть filtered_result"""
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            self.root.after(0, lambda: self.status_var.set("❌ Не удалось открыть видео"))
            return
        
        frame_count = 0
        
        while self.playing_video and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Анализируем каждый 30-й кадр
            if frame_count % 30 == 0:
                frame_resized = cv2.resize(frame, (800, 800))
                results = self.model(frame_resized, conf=0.08, verbose=False, imgsz=800)
                
                # ✅ ГАРАНТИРОВАННО создаем filtered_result
                filtered_result = self.smart_filter(results[0])
                stats = self.get_priority_stats(filtered_result)
                self.root.after(0, lambda s=stats: self.update_stats(s))
            
            # ✅ Всегда создаем annotated для отображения
            frame_resized = cv2.resize(frame, (800, 640))
            results = self.model(frame_resized, conf=0.08, verbose=False, imgsz=800)
            filtered_result = self.smart_filter(results[0])  # ← ВТОРОЙ вызов для отображения
            
            annotated = filtered_result.plot(line_width=2, font_size=9, labels=True)
            annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            
            self.root.after(0, lambda f=annotated_bgr.copy(): self.update_video_frame(f))
            time.sleep(0.033)  # ~30 FPS
        
        self.cap.release()
        self.root.after(0, self.video_ended)
    
    def video_ended(self):
        """Видео закончилось"""
        self.playing_video = False
        self.stop_btn.pack_forget()
        self.status_var.set("✅ Видео завершено")
    
    def update_video_frame(self, frame):
        if not self.playing_video:
            return
            
        self.canvas.update_idletasks()
        canvas_w = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 1200
        canvas_h = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 800
        
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        scale = min(canvas_w/w * 0.95, canvas_h/h * 0.95)
        new_w, new_h = int(w * scale), int(h * scale)
        img_resized = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        img_pil = Image.fromarray(img_resized)
        self.photo = ImageTk.PhotoImage(img_pil)
        
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w//2, canvas_h//2, image=self.photo, anchor=tk.CENTER)
    
    def stop_video(self):
        self.playing_video = False
        if self.cap:
            self.cap.release()
        self.stop_btn.pack_forget()
        self.status_var.set("⏹️ Видео остановлено")
    
    def update_stats(self, stats):
        s_count, l_count = stats['s_scratch'], stats['l_scratch']
        defects = s_count + l_count
        
        if defects == 0:
            stats_text = "📊 Трещин не найдено"
        else:
            stats_text = f"📊 Малые: {s_count} | Большие: {l_count}"
        
        self.stats_var.set(stats_text)
    
    def smart_filter(self, result):
        if result.boxes is None:
            result.boxes = np.empty((0, 6), dtype=np.float32)  # Пустой результат
            return result
        
        img_area = 800 * 800
        keep_boxes = []
        
        for i, box in enumerate(result.boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            cls_name = self.classes.get(cls_id, '').lower()
            
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            box_area = (x2-x1) * (y2-y1)
            area_ratio = box_area / img_area
            
            keep = False
            if 's_scratch' in cls_name or 'l_scratch' in cls_name:
                if 0.0005 < area_ratio < 0.25 and conf > 0.08:
                    keep = True
            elif 'normal' in cls_name and area_ratio > 0.08:
                keep = True
            
            if keep:
                keep_boxes.append(i)
        
        if keep_boxes:
            result.boxes = result.boxes[keep_boxes]
        else:
            result.boxes = np.empty((0, 6), dtype=np.float32)
        
        return result
    
    def get_priority_stats(self, result):
        stats = {'s_scratch': 0, 'l_scratch': 0}
        
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.classes.get(cls_id, '').lower()
                
                if 's_scratch' in cls_name:
                    stats['s_scratch'] += 1
                elif 'l_scratch' in cls_name:
                    stats['l_scratch'] += 1
        
        return stats

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartInspector(root)
    root.mainloop()
