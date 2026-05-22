"""
ForzaBot - Konfigürasyon Dosyası
Tüm ayarları buradan değiştirebilirsiniz.
"""

import os

# ============================================================
# PROJE YOLLARİ
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINING_DATA_DIR = os.path.join(BASE_DIR, "training_data")

# Durum klasörleri
STATE_FOLDERS = {
    "racing": os.path.join(TRAINING_DATA_DIR, "racing"),
    "race_finished": os.path.join(TRAINING_DATA_DIR, "race_finished"),
    "menu": os.path.join(TRAINING_DATA_DIR, "menu"),
    "loading": os.path.join(TRAINING_DATA_DIR, "loading"),
}

# ============================================================
# EKRAN YAKALAMA AYARLARI
# ============================================================
# None = tüm ekranı yakala, veya {"top": y, "left": x, "width": w, "height": h}
SCREEN_REGION = None

# Saniyede kaç kare yakalanacak (durum tespiti için)
CAPTURE_FPS = 10

# Birincil monitör indeksi (1 = ana monitör)
MONITOR_INDEX = 1

# ============================================================
# TEMPLATE MATCHING AYARLARI
# ============================================================
# Eşleşme eşik değeri (0.0 - 1.0 arası)
# Yüksek = daha kesin eşleşme gerekir, Düşük = daha toleranslı
MATCH_THRESHOLD = 0.75

# Karşılaştırma için görüntüleri gri tonlamaya dönüştür (daha hızlı + güvenilir)
USE_GRAYSCALE = True

# ============================================================
# TUŞ AYARLARI
# ============================================================
# Acil durdurma tuşu - bu tuşa basınca bot durur
EMERGENCY_STOP_KEY = "f12"

# Training modu ekran görüntüsü alma tuşu
TRAINING_CAPTURE_KEY = "f5"

# ============================================================
# DURUM AKSİYONLARI
# ============================================================
# Her durum için hangi tuşlara basılacağını tanımlar
STATE_ACTIONS = {
    "racing": {
        "type": "hold",           # Tuşu basılı tut
        "key": "w",               # İleri git
    },
    "race_finished": {
        "type": "press_sequence",  # Sırayla tuşlara bas
        "keys": ["x"],             # X bas (devam et)
        "delay_before": 2.0,       # Aksiyondan önce bekleme (saniye)
        "delay_between": 1.0,      # Tuşlar arası bekleme (saniye)
    },
    "menu": {
        "type": "press_sequence",
        "keys": ["enter"],         # Racingı tekrar başlat
        "delay_before": 1.5,
        "delay_between": 1.0,
    },
    "loading": {
        "type": "wait",            # Sadece bekle
        "duration": 1.0,
    },
}

# ============================================================
# ZAMANLAMA AYARLARI
# ============================================================
# Durum değişikliği sonrası bekleme süresi (saniye)
STATE_TRANSITION_DELAY = 0.5

# Aynı aksiyonu tekrarlama arası minimum süre (saniye)
ACTION_COOLDOWN = 1.0

# Rastgele gecikme aralığı (daha doğal görünmesi için)
RANDOM_DELAY_MIN = 0.8
RANDOM_DELAY_MAX = 1.3

# ============================================================
# GUI AYARLARI
# ============================================================
GUI_WIDTH = 700
GUI_HEIGHT = 550
GUI_TITLE = "🎮 ForzaBot - Forza Horizon 6 Automation"
GUI_THEME_BG = "#1a1a2e"
GUI_THEME_FG = "#e0e0e0"
GUI_THEME_ACCENT = "#0f3460"
GUI_THEME_SUCCESS = "#00b894"
GUI_THEME_DANGER = "#e74c3c"
GUI_THEME_WARNING = "#f39c12"
GUI_THEME_BUTTON = "#16213e"
