"""
ForzaBot - Grafik Control Paneli (GUI)
Tkinter ile modern, koyu temalı kontrol arayüzü.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from capture import ScreenCapture
from detector import StateDetector
from controller import GameController
from state_machine import StateMachine, BotState
from trainer import Trainer
from config import (
    GUI_WIDTH, GUI_HEIGHT, GUI_TITLE,
    GUI_THEME_BG, GUI_THEME_FG, GUI_THEME_ACCENT,
    GUI_THEME_SUCCESS, GUI_THEME_DANGER, GUI_THEME_WARNING,
    GUI_THEME_BUTTON, CAPTURE_FPS, EMERGENCY_STOP_KEY,
    STATE_FOLDERS,
)


class ForzaBotGUI:
    """ForzaBot grafik kontrol paneli."""

    def __init__(self):
        # Ana pencere
        self.root = tk.Tk()
        self.root.title(GUI_TITLE)
        self.root.geometry(f"{GUI_WIDTH}x{GUI_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=GUI_THEME_BG)

        # İkon ayarı (varsa)
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        # Bot modülleri
        self.capture = ScreenCapture()
        self.detector = StateDetector()
        self.controller = GameController()
        self.state_machine = StateMachine()
        self.trainer = Trainer()

        # Durum değişkenleri
        self._running = False
        self._bot_thread = None
        self._total_detections = 0
        self._start_time = None

        # Durum değişikliği callback'i
        self.state_machine.on_state_change(self._on_state_change)
        self.state_machine.set_log_callback(self._add_log)

        # GUI oluştur
        self._create_widgets()
        self._update_training_status()

        # Kapatma olayı
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """Tüm GUI widgetlarını oluştur."""

        # === BAŞLIK ===
        header = tk.Frame(self.root, bg=GUI_THEME_ACCENT, height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🎮 ForzaBot",
            font=("Segoe UI", 20, "bold"),
            fg="#ffffff",
            bg=GUI_THEME_ACCENT,
        ).pack(side="left", padx=20, pady=10)

        tk.Label(
            header,
            text="Forza Horizon 6 Automation",
            font=("Segoe UI", 10),
            fg="#b0b0b0",
            bg=GUI_THEME_ACCENT,
        ).pack(side="left", pady=10)

        # Durum etiketi (sağ üst)
        self.status_label = tk.Label(
            header,
            text="● READY",
            font=("Segoe UI", 12, "bold"),
            fg=GUI_THEME_WARNING,
            bg=GUI_THEME_ACCENT,
        )
        self.status_label.pack(side="right", padx=20)

        # === ANA İÇERİK ===
        main_frame = tk.Frame(self.root, bg=GUI_THEME_BG)
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # --- Sol Panel: Kontroller ---
        left = tk.Frame(main_frame, bg=GUI_THEME_BG, width=300)
        left.pack(side="left", fill="y", padx=(0, 10))

        # Control Butonları
        ctrl_frame = tk.LabelFrame(
            left, text=" Control ",
            font=("Segoe UI", 10, "bold"),
            fg=GUI_THEME_FG, bg=GUI_THEME_BG,
            bd=1, relief="groove",
        )
        ctrl_frame.pack(fill="x", pady=(0, 10))

        btn_style = {
            "font": ("Segoe UI", 11, "bold"),
            "width": 18,
            "height": 2,
            "bd": 0,
            "cursor": "hand2",
            "relief": "flat",
        }

        self.start_btn = tk.Button(
            ctrl_frame,
            text="▶  START",
            bg=GUI_THEME_SUCCESS,
            fg="#ffffff",
            activebackground="#00a884",
            command=self._start_bot,
            **btn_style,
        )
        self.start_btn.pack(padx=10, pady=(10, 5))

        self.stop_btn = tk.Button(
            ctrl_frame,
            text="■  STOP",
            bg=GUI_THEME_DANGER,
            fg="#ffffff",
            activebackground="#c0392b",
            command=self._stop_bot,
            state="disabled",
            **btn_style,
        )
        self.stop_btn.pack(padx=10, pady=(0, 10))

        # Training Butonları
        train_frame = tk.LabelFrame(
            left, text=" Training ",
            font=("Segoe UI", 10, "bold"),
            fg=GUI_THEME_FG, bg=GUI_THEME_BG,
            bd=1, relief="groove",
        )
        train_frame.pack(fill="x", pady=(0, 10))

        train_btn_style = {
            "font": ("Segoe UI", 9),
            "width": 18,
            "height": 1,
            "bd": 0,
            "cursor": "hand2",
            "relief": "flat",
            "bg": GUI_THEME_BUTTON,
            "fg": GUI_THEME_FG,
            "activebackground": "#1a2744",
        }

        states_tr = {
            "racing": "🏎️  Racing Screen",
            "race_finished": "🏁  Race Finished",
            "menu": "📋  Menu Screen",
            "loading": "⏳  Loading Screen",
        }

        for state_key, label_text in states_tr.items():
            btn = tk.Button(
                train_frame,
                text=label_text,
                command=lambda s=state_key: self._capture_training(s),
                **train_btn_style,
            )
            btn.pack(padx=10, pady=2)

        # ROI buton
        tk.Button(
            train_frame,
            text="✂️  Capture by Region (ROI)",
            command=self._capture_roi,
            **train_btn_style,
        ).pack(padx=10, pady=(2, 5))

        # Yenile butonu
        tk.Button(
            train_frame,
            text="🔄  Training Verilerini Yenile",
            command=self._reload_training,
            **train_btn_style,
        ).pack(padx=10, pady=(0, 10))

        # --- Sağ Panel: Bilgi ---
        right = tk.Frame(main_frame, bg=GUI_THEME_BG)
        right.pack(side="right", fill="both", expand=True)

        # İstatistikler
        stats_frame = tk.LabelFrame(
            right, text=" Status Info ",
            font=("Segoe UI", 10, "bold"),
            fg=GUI_THEME_FG, bg=GUI_THEME_BG,
            bd=1, relief="groove",
        )
        stats_frame.pack(fill="x", pady=(0, 10))

        stats_inner = tk.Frame(stats_frame, bg=GUI_THEME_BG)
        stats_inner.pack(fill="x", padx=10, pady=8)

        stat_style = {"font": ("Segoe UI", 10), "fg": GUI_THEME_FG, "bg": GUI_THEME_BG, "anchor": "w"}

        self.state_var = tk.StringVar(value="READY")
        self.race_count_var = tk.StringVar(value="0")
        self.uptime_var = tk.StringVar(value="00:00:00")
        self.detection_var = tk.StringVar(value="-")

        labels_data = [
            ("Current State:", self.state_var),
            ("Race Count:", self.race_count_var),
            ("Uptime:", self.uptime_var),
            ("Last Detection:", self.detection_var),
        ]

        for i, (label, var) in enumerate(labels_data):
            tk.Label(stats_inner, text=label, **stat_style).grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(stats_inner, textvariable=var, font=("Segoe UI", 10, "bold"),
                     fg=GUI_THEME_SUCCESS, bg=GUI_THEME_BG, anchor="w").grid(row=i, column=1, sticky="w", padx=(10, 0), pady=2)

        # Training verisi durumu
        self.training_frame = tk.LabelFrame(
            right, text=" Training Verileri ",
            font=("Segoe UI", 10, "bold"),
            fg=GUI_THEME_FG, bg=GUI_THEME_BG,
            bd=1, relief="groove",
        )
        self.training_frame.pack(fill="x", pady=(0, 10))

        self.training_labels = {}

        # Log penceresi
        log_frame = tk.LabelFrame(
            right, text=" Log ",
            font=("Segoe UI", 10, "bold"),
            fg=GUI_THEME_FG, bg=GUI_THEME_BG,
            bd=1, relief="groove",
        )
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            height=8,
            bg="#0d1117",
            fg="#c9d1d9",
            font=("Consolas", 9),
            bd=0,
            wrap="word",
            state="disabled",
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = tk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # === ALT BAR ===
        footer = tk.Frame(self.root, bg="#111122", height=30)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text=f"Emergency Stop: {EMERGENCY_STOP_KEY.upper()} | ForzaBot v1.0",
            font=("Segoe UI", 8),
            fg="#666666",
            bg="#111122",
        ).pack(side="left", padx=10)

        # İlk log
        self._add_log("ForzaBot hazır. Training verilerini yükleyin ve başlatın.")

    def _update_training_status(self):
        """Eğitim verisi durumunu güncelle."""
        # Mevcut etiketleri temizle
        for widget in self.training_frame.winfo_children():
            widget.destroy()

        inner = tk.Frame(self.training_frame, bg=GUI_THEME_BG)
        inner.pack(fill="x", padx=10, pady=5)

        summary = self.detector.get_training_summary()
        states_tr = {
            "racing": "Racing",
            "race_finished": "Finished",
            "menu": "Menu",
            "loading": "Loading",
        }

        for i, (state, count) in enumerate(summary.items()):
            name = states_tr.get(state, state)
            if count >= 3:
                icon, color = "✅", GUI_THEME_SUCCESS
            elif count > 0:
                icon, color = "⚠️", GUI_THEME_WARNING
            else:
                icon, color = "❌", GUI_THEME_DANGER

            tk.Label(
                inner,
                text=f"{icon} {name}: {count}",
                font=("Segoe UI", 9),
                fg=color,
                bg=GUI_THEME_BG,
                anchor="w",
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=5, pady=1)

    def _add_log(self, message):
        """Log mesajı ekle."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        def _update():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        # Thread-safe GUI güncelleme
        self.root.after(0, _update)

    def _update_status_display(self):
        """Durum göstergesini güncelle (periyodik)."""
        if not self._running:
            return

        # Durumu güncelle
        state = self.state_machine.current_state
        state_names_tr = {
            "idle": "IDLE",
            "detecting": "DETECTING",
            "racing": "🏎️ RACING",
            "race_finished": "🏁 RACE FINISHED",
            "menu": "📋 IN MENU",
            "loading": "⏳ LOADING",
            "stopped": "STOPULDU",
        }
        self.state_var.set(state_names_tr.get(state.value, state.value))
        self.race_count_var.set(str(self.state_machine.race_count))

        # Çalışma süresi
        if self._start_time:
            elapsed = int(time.time() - self._start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.uptime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Durum rengini güncelle
        color_map = {
            BotState.RACING: GUI_THEME_SUCCESS,
            BotState.RACE_FINISHED: GUI_THEME_WARNING,
            BotState.DETECTING: "#3498db",
            BotState.MENU: GUI_THEME_WARNING,
            BotState.LOADING: "#9b59b6",
        }
        self.status_label.configure(
            text=f"● {state_names_tr.get(state.value, state.value)}",
            fg=color_map.get(state, GUI_THEME_FG),
        )

        # 500ms sonra tekrar çağır
        if self._running:
            self.root.after(500, self._update_status_display)

    def _on_state_change(self, old_state, new_state):
        """Durum değişikliği callback'i."""
        self.controller.on_state_change(old_state.value, new_state.value)

    # === Bot Kontrolleri ===

    def _bot_loop(self):
        """Ana bot döngüsü."""
        interval = 1.0 / CAPTURE_FPS

        while self._running:
            try:
                loop_start = time.time()

                frame = self.capture.grab_frame()
                detected_state, score, all_scores = self.detector.detect_state(frame)
                self._total_detections += 1

                # Son tespit bilgisini güncelle
                self.root.after(0, lambda s=detected_state, sc=score:
                    self.detection_var.set(f"{s} ({sc:.2f})"))

                self.state_machine.update_from_detection(detected_state)

                current = self.state_machine.current_state
                if current not in (BotState.IDLE, BotState.STOPPED, BotState.DETECTING):
                    state_name = current.value
                    if not self.controller.needs_cooldown(state_name):
                        # hold aksiyonları her frame çalışır (W tuşu gibi)
                        self.controller.execute_action(state_name)
                    elif self.state_machine.can_perform_action():
                        # press_sequence aksiyonları cooldown ile çalışır
                        self.controller.execute_action(state_name)
                        self.state_machine.mark_action_performed()

                elapsed = time.time() - loop_start
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                self._add_log(f"❌ Error: {e}")
                time.sleep(1)

        self.controller.release_all()

    def _start_bot(self):
        """Botu başlat."""
        if self._running:
            return

        if not self.detector.has_training_data():
            messagebox.showwarning(
                "No Training Data",
                "Create training data first!\n\n"
                "Use the training buttons on the left panel to save\n"
                "at least 3 screenshots for each state."
            )
            return

        self._running = True
        self._start_time = time.time()
        self.state_machine.reset()
        self.state_machine.start()

        self._bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
        self._bot_thread.start()

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="● ÇALIŞIYOR", fg=GUI_THEME_SUCCESS)

        self._add_log("🟢 Bot started!")
        self._update_status_display()

    def _stop_bot(self):
        """Botu durdur."""
        if not self._running:
            return

        self._running = False
        self.state_machine.stop()
        self.controller.cleanup()

        if self._bot_thread:
            self._bot_thread.join(timeout=3)

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="● STOPULDU", fg=GUI_THEME_DANGER)
        self.state_var.set("STOPULDU")

        self._add_log("🔴 Bot stopped.")

    # === Training ===

    def _capture_training(self, state_name):
        """Eğitim ekran görüntüsü al."""
        states_tr = {
            "racing": "Racing", "race_finished": "Finished",
            "menu": "Menu", "loading": "Loading",
        }
        name = states_tr.get(state_name, state_name)
        self._add_log(f"📸 {name} screenshot will be taken in 3s...")

        # 3 saniye sonra yakala
        def _delayed_capture():
            filepath = self.trainer.capture_for_state(state_name)
            if filepath:
                self._add_log(f"✅ {name} saved!")
                self.detector.reload_templates()
                self._update_training_status()
            else:
                self._add_log(f"❌ {name} could not be saved!")

        self.root.after(3000, lambda: threading.Thread(target=_delayed_capture, daemon=True).start())

    def _capture_roi(self):
        """ROI seçerek eğitim görüntüsü al."""
        self._add_log("✂️ ROI mode - select state first...")
        # Basit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select State")
        dialog.geometry("250x200")
        dialog.configure(bg=GUI_THEME_BG)
        dialog.transient(self.root)

        tk.Label(dialog, text="ROI for which state?",
                 font=("Segoe UI", 11), fg=GUI_THEME_FG, bg=GUI_THEME_BG).pack(pady=10)

        for state_key, label in [("racing", "🏎️ Racing"), ("race_finished", "🏁 Finished"),
                                   ("menu", "📋 Menu"), ("loading", "⏳ Loading")]:
            tk.Button(
                dialog, text=label,
                font=("Segoe UI", 10), bg=GUI_THEME_BUTTON, fg=GUI_THEME_FG,
                width=20, bd=0, cursor="hand2",
                command=lambda s=state_key, d=dialog: self._do_roi_capture(s, d),
            ).pack(pady=2)

    def _do_roi_capture(self, state_name, dialog):
        """ROI yakalama işlemini gerçekleştir."""
        dialog.destroy()
        self._add_log(f"✂️ ROI selection will open in 3s...")

        def _delayed():
            filepath = self.trainer.capture_roi(state_name)
            if filepath:
                self._add_log(f"✅ ROI saved!")
                self.detector.reload_templates()
                self.root.after(0, self._update_training_status)

        self.root.after(3000, lambda: threading.Thread(target=_delayed, daemon=True).start())

    def _reload_training(self):
        """Eğitim verilerini yeniden yükle."""
        self.detector.reload_templates()
        self._update_training_status()
        self._add_log("🔄 Training verileri yenilendi.")

    # === Pencere Yönetimi ===

    def _on_close(self):
        """Pencere kapatıldığında."""
        if self._running:
            if messagebox.askyesno("Exit", "Bot is running! Stop and exit?"):
                self._stop_bot()
            else:
                return

        self.capture.close()
        self.root.destroy()

    def run(self):
        """GUI'yi başlat."""
        self.root.mainloop()


if __name__ == "__main__":
    app = ForzaBotGUI()
    app.run()
