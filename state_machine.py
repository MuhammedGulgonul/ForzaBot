"""
ForzaBot - Durum Makinesi Modülü
Bot'un çalışma akışını yöneten durum makinesi.
"""

import time
import enum
from config import STATE_TRANSITION_DELAY, ACTION_COOLDOWN


class BotState(enum.Enum):
    """Bot durumları."""
    IDLE = "idle"
    DETECTING = "detecting"
    RACING = "racing"
    RACE_FINISHED = "race_finished"
    MENU = "menu"
    LOADING = "loading"
    STOPPED = "stopped"


class StateMachine:
    """
    Bot durum makinesi.
    
    Durum Akışı:
        IDLE → DETECTING → RACING → RACE_FINISHED → MENU → LOADING → DETECTING → ...
    """

    def __init__(self):
        self.state = BotState.IDLE
        self.previous_state = BotState.IDLE
        self._state_enter_time = time.time()
        self._last_action_time = 0
        self._race_count = 0
        self._state_change_callbacks = []
        self._log_callback = None

    def set_log_callback(self, callback):
        """Log mesajları için callback ayarla."""
        self._log_callback = callback

    def _log(self, message):
        """Log mesajı yaz."""
        try:
            print(f"[StateMachine] {message}")
        except UnicodeEncodeError:
            print(f"[StateMachine] {message.encode('ascii', 'replace').decode()}")
        if self._log_callback:
            self._log_callback(message)

    def on_state_change(self, callback):
        """
        Durum değişikliği callback'i ekle.
        
        Args:
            callback: func(old_state, new_state) imzalı fonksiyon
        """
        self._state_change_callbacks.append(callback)

    @property
    def current_state(self):
        """Mevcut durumu döndür."""
        return self.state

    @property
    def state_name(self):
        """Mevcut durum adını döndür (string)."""
        return self.state.value

    @property
    def race_count(self):
        """Tamamlanan yarış sayısı."""
        return self._race_count

    @property
    def time_in_state(self):
        """Mevcut durumda geçen süre (saniye)."""
        return time.time() - self._state_enter_time

    def can_perform_action(self):
        """Aksiyon cooldown'ı geçmiş mi?"""
        return (time.time() - self._last_action_time) >= ACTION_COOLDOWN

    def mark_action_performed(self):
        """Aksiyonun gerçekleştirildiğini işaretle."""
        self._last_action_time = time.time()

    def transition_to(self, new_state):
        """
        Yeni duruma geçiş yap.
        
        Args:
            new_state: BotState enum değeri veya string durum adı
        """
        # String'den enum'a çevir
        if isinstance(new_state, str):
            try:
                new_state = BotState(new_state)
            except ValueError:
                self._log(f"⚠️ Bilinmeyen durum: {new_state}")
                return

        if new_state == self.state:
            return  # Aynı duruma geçiş yapma

        old_state = self.state
        self.previous_state = old_state
        self.state = new_state
        self._state_enter_time = time.time()

        # Racing bitişini say
        if old_state == BotState.RACING and new_state == BotState.RACE_FINISHED:
            self._race_count += 1

        self._log(f"🔄 {old_state.value} → {new_state.value}")

        # Callback'leri çağır
        for callback in self._state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                self._log(f"Callback hatası: {e}")

    def update_from_detection(self, detected_state_name):
        """
        Detector'dan gelen durum bilgisine göre durumu güncelle.
        
        Args:
            detected_state_name: Tespit edilen durum adı ('racing', 'race_finished', vb.)
        """
        if self.state == BotState.IDLE or self.state == BotState.STOPPED:
            return  # IDLE veya STOPPED durumunda tespit sonuçlarını yok say

        if detected_state_name == "unknown":
            return  # Bilinmeyen durum - mevcut durumu koru

        # Geçiş kuralları
        current = self.state
        detected = detected_state_name

        # DETECTING → herhangi bir geçerli durum
        if current == BotState.DETECTING:
            self.transition_to(detected)

        # RACING → sadece race_finished'e geçebilir
        elif current == BotState.RACING:
            if detected == "race_finished":
                self.transition_to(BotState.RACE_FINISHED)

        # RACE_FINISHED → menu veya loading
        elif current == BotState.RACE_FINISHED:
            if detected in ("menu", "loading"):
                self.transition_to(detected)

        # MENU → loading veya racing
        elif current == BotState.MENU:
            if detected in ("loading", "racing"):
                self.transition_to(detected)

        # LOADING → racing veya detecting
        elif current == BotState.LOADING:
            if detected == "racing":
                self.transition_to(BotState.RACING)
            elif detected in ("menu", "race_finished"):
                self.transition_to(detected)

    def start(self):
        """Botu başlat (DETECTING durumuna geç)."""
        self._log("🟢 Bot starting...")
        self.transition_to(BotState.DETECTING)

    def stop(self):
        """Botu durdur."""
        self._log("🔴 Bot durduruluyor...")
        self.transition_to(BotState.STOPPED)

    def reset(self):
        """Botu sıfırla."""
        self.state = BotState.IDLE
        self.previous_state = BotState.IDLE
        self._race_count = 0
        self._state_enter_time = time.time()
        self._last_action_time = 0
        self._log("🔃 Bot sıfırlandı")

    def get_status(self):
        """Durum özetini döndür."""
        return {
            "state": self.state.value,
            "previous_state": self.previous_state.value,
            "time_in_state": round(self.time_in_state, 1),
            "race_count": self._race_count,
        }


# === Test ===
if __name__ == "__main__":
    print("=== Durum Makinesi Testi ===")
    sm = StateMachine()

    print(f"Başlangıç: {sm.state_name}")

    sm.start()
    print(f"Başlatıldı: {sm.state_name}")

    sm.update_from_detection("racing")
    print(f"Racing tespit: {sm.state_name}")

    sm.update_from_detection("race_finished")
    print(f"Racing bitti: {sm.state_name}, Racing sayısı: {sm.race_count}")

    sm.update_from_detection("menu")
    print(f"Menu tespit: {sm.state_name}")

    sm.update_from_detection("loading")
    print(f"Loading: {sm.state_name}")

    sm.update_from_detection("racing")
    print(f"Tekrar yarış: {sm.state_name}")

    sm.stop()
    print(f"Durduruldu: {sm.state_name}")

    print(f"\nDurum özeti: {sm.get_status()}")
    print("=== Test Tamamlandı ===")
