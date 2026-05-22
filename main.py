"""
ForzaBot - Ana Bot Döngüsü
Tüm modülleri birleştiren ana çalışma döngüsü.
"""

import sys
import time
import threading
from capture import ScreenCapture
from detector import StateDetector
from controller import GameController
from state_machine import StateMachine, BotState
from config import CAPTURE_FPS, EMERGENCY_STOP_KEY


class ForzaBot:
    """Ana bot sınıfı - tüm modülleri koordine eder."""

    def __init__(self):
        print("=" * 60)
        print("  🎮 ForzaBot - Forza Horizon 6 Automation Botu")
        print("=" * 60)
        print()

        # Modülleri başlat
        print("Modüller yükleniyor...")
        self.capture = ScreenCapture()
        self.detector = StateDetector()
        self.controller = GameController()
        self.state_machine = StateMachine()

        # Durum değişikliği callback'i
        self.state_machine.on_state_change(self._on_state_change)

        # Çalışma kontrolü
        self._running = False
        self._bot_thread = None
        self._lock = threading.Lock()

        # İstatistikler
        self._start_time = None
        self._total_detections = 0

        print("✅ ForzaBot hazır!\n")

    def _on_state_change(self, old_state, new_state):
        """Durum değişikliğinde tuşları güncelle."""
        self.controller.on_state_change(old_state.value, new_state.value)

    def _bot_loop(self):
        """Ana bot döngüsü (ayrı thread'de çalışır)."""
        interval = 1.0 / CAPTURE_FPS

        while self._running:
            try:
                loop_start = time.time()

                # 1. Ekran görüntüsü al
                frame = self.capture.grab_frame()

                # 2. Durumu tespit et
                detected_state, score, all_scores = self.detector.detect_state(frame)
                self._total_detections += 1

                # 3. Durum makinesini güncelle
                self.state_machine.update_from_detection(detected_state)

                # 4. Mevcut durum için aksiyonu çalıştır
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

                # FPS kontrolü
                elapsed = time.time() - loop_start
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                print(f"❌ Bot döngüsü hatası: {e}")
                time.sleep(1)

        # Döngü bittiğinde temizlik
        self.controller.release_all()

    def start(self):
        """Botu başlat."""
        if self._running:
            print("⚠️  Bot zaten çalışıyor!")
            return

        # Training verisi kontrolü
        if not self.detector.has_training_data():
            print("❌ Training verisi bulunamadı!")
            print("   Önce trainer.py ile ekran görüntüleri kaydedin.")
            print("   Çalıştır: python trainer.py")
            return

        self._running = True
        self._start_time = time.time()
        self.state_machine.start()

        # Bot döngüsünü ayrı thread'de başlat
        self._bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
        self._bot_thread.start()

        print(f"🟢 Bot started! (To stop: {EMERGENCY_STOP_KEY.upper()} tuşu)")

    def stop(self):
        """Botu durdur."""
        if not self._running:
            return

        self._running = False
        self.state_machine.stop()
        self.controller.cleanup()

        if self._bot_thread:
            self._bot_thread.join(timeout=3)

        print("🔴 Bot stopped.")

    def reload_training(self):
        """Eğitim verilerini yeniden yükle."""
        self.detector.reload_templates()
        print("🔄 Training verileri yeniden yüklendi.")

    def get_status(self):
        """Bot durumunu döndür."""
        status = self.state_machine.get_status()
        status["running"] = self._running
        status["total_detections"] = self._total_detections
        status["training_data"] = self.detector.get_training_summary()

        if self._start_time:
            status["uptime"] = round(time.time() - self._start_time, 1)

        return status

    def cleanup(self):
        """Tüm kaynakları temizle."""
        self.stop()
        self.capture.close()
        print("✅ Kaynaklar temizlendi.")


def console_mode():
    """Konsol tabanlı çalışma modu."""
    bot = ForzaBot()

    print("Komutlar:")
    print("  start  = Botu başlat")
    print("  stop   = Botu durdur")
    print("  status = Durum bilgisi")
    print("  reload = Training verilerini yeniden yükle")
    print("  quit   = Exit")
    print()

    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd == "start":
                bot.start()
            elif cmd == "stop":
                bot.stop()
            elif cmd == "status":
                status = bot.get_status()
                print(f"\n📊 Bot Durumu:")
                for key, val in status.items():
                    print(f"  {key}: {val}")
                print()
            elif cmd == "reload":
                bot.reload_training()
            elif cmd in ("quit", "exit", "q"):
                break
            else:
                print("❌ Bilinmeyen komut")

    except KeyboardInterrupt:
        print("\n")

    bot.cleanup()


if __name__ == "__main__":
    console_mode()
