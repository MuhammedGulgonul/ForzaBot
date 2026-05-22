"""
ForzaBot - Tuş Simülasyonu Modülü
pydirectinput ile DirectInput tuş simülasyonu (oyunlar için).
"""

import time
import random
import pydirectinput
from config import (
    STATE_ACTIONS,
    EMERGENCY_STOP_KEY,
    RANDOM_DELAY_MIN,
    RANDOM_DELAY_MAX,
)


class GameController:
    """Oyuna tuş girdisi gönderen kontrolcü."""

    def __init__(self):
        """Controller'ı başlat."""
        # pydirectinput ayarları
        pydirectinput.PAUSE = 0.03  # Tuş işlemleri arası minimum gecikme
        
        # Şu anda basılı tutulan tuşlar
        self._held_keys = set()
        
        # Son aksiyon zamanları (cooldown için)
        self._last_action_time = {}
        
        print("[Controller] DirectInput controller hazır")

    def press_key(self, key):
        """
        Bir tuşa bas ve bırak.
        
        Args:
            key: Tuş adı (örn: 'w', 'enter', 'space')
        """
        pydirectinput.press(key)

    def hold_key(self, key):
        """
        Bir tuşu basılı tut.
        Her çağrıda keyDown gönderir (DirectX oyunları için gerekli).
        
        Args:
            key: Tuş adı
        """
        pydirectinput.keyDown(key)
        self._held_keys.add(key)

    def release_key(self, key):
        """
        Basılı tutulan bir tuşu bırak.
        
        Args:
            key: Tuş adı
        """
        if key in self._held_keys:
            pydirectinput.keyUp(key)
            self._held_keys.discard(key)

    def release_all(self):
        """Tüm basılı tutulan tuşları bırak."""
        for key in list(self._held_keys):
            try:
                pydirectinput.keyUp(key)
            except Exception:
                pass
        self._held_keys.clear()

        # Yaygın kullanılan tuşları da güvenlik için bırak
        safety_keys = ['w', 'a', 's', 'd', 'enter', 'escape', 'space', 'shift']
        for key in safety_keys:
            try:
                pydirectinput.keyUp(key)
            except Exception:
                pass

    def press_sequence(self, keys, delay_between=1.0):
        """
        Sırayla birden fazla tuşa bas.
        
        Args:
            keys: Tuş listesi ['enter', 'down', 'enter']
            delay_between: Tuşlar arası bekleme süresi (saniye)
        """
        for key in keys:
            self.press_key(key)
            # Rastgele gecikme ekle (daha doğal)
            actual_delay = delay_between * random.uniform(RANDOM_DELAY_MIN, RANDOM_DELAY_MAX)
            time.sleep(actual_delay)

    def execute_action(self, state_name):
        """
        Verilen durum için tanımlı aksiyonu çalıştır.
        
        Args:
            state_name: Durum adı ('racing', 'race_finished', 'menu', 'loading')
        
        Returns:
            bool: Aksiyon çalıştırıldıysa True
        """
        if state_name not in STATE_ACTIONS:
            return False

        action = STATE_ACTIONS[state_name]
        action_type = action.get("type", "wait")

        if action_type == "hold":
            # Tuşu basılı tut
            key = action.get("key", "w")
            self.hold_key(key)
            return True

        elif action_type == "press_sequence":
            # Önce bekleme
            delay_before = action.get("delay_before", 0)
            if delay_before > 0:
                time.sleep(delay_before * random.uniform(RANDOM_DELAY_MIN, RANDOM_DELAY_MAX))

            # Sırayla tuşlara bas
            keys = action.get("keys", [])
            delay_between = action.get("delay_between", 1.0)
            self.press_sequence(keys, delay_between)
            return True

        elif action_type == "wait":
            # Sadece bekle
            duration = action.get("duration", 1.0)
            time.sleep(duration)
            return True

        return False

    def on_state_change(self, old_state, new_state):
        """
        Durum değişikliğinde çağrılır - eski durumun tuşlarını bırakır.
        
        Args:
            old_state: Önceki durum adı
            new_state: Yeni durum adı
        """
        # Eski durumda basılı tutulan tuşları bırak
        if old_state in STATE_ACTIONS:
            old_action = STATE_ACTIONS[old_state]
            if old_action.get("type") == "hold":
                key = old_action.get("key", "w")
                self.release_key(key)

    def cleanup(self):
        """Temizlik - tüm tuşları bırak."""
        print("[Controller] Temizlik yapılıyor - tüm tuşlar bırakılıyor...")
        self.release_all()

    def needs_cooldown(self, state_name):
        """
        Bu durum için cooldown gerekli mi?
        'hold' türü aksiyonlar cooldown'a tabi değildir (her frame çalışmalı).
        
        Returns:
            bool: Cooldown gerekiyorsa True
        """
        if state_name not in STATE_ACTIONS:
            return True
        return STATE_ACTIONS[state_name].get("type") != "hold"


# === Test ===
if __name__ == "__main__":
    print("=== Controller Testi ===")
    print("⚠️  Bu test gerçek tuş girdisi gönderir!")
    print("3 saniye içinde test başlayacak... (İptal: Ctrl+C)")

    try:
        time.sleep(3)

        ctrl = GameController()

        # Basit test: 'w' tuşuna 1 saniye basılı tut
        print("W tuşu basılı tutulacak (1 saniye)...")
        ctrl.hold_key('w')
        time.sleep(1)
        ctrl.release_key('w')
        print("W tuşu bırakıldı.")

        ctrl.cleanup()
        print("=== Test Tamamlandı ===")

    except KeyboardInterrupt:
        print("\nTest iptal edildi.")
        ctrl = GameController()
        ctrl.cleanup()
