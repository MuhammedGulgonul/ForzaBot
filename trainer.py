"""
ForzaBot - Training Aracı
Referans ekran görüntülerini kategorize ederek kaydetme aracı.
"""

import os
import sys
import time
import threading
import cv2
from datetime import datetime
from capture import ScreenCapture
from config import TRAINING_DATA_DIR, STATE_FOLDERS, TRAINING_CAPTURE_KEY


class Trainer:
    """
    Ekran görüntüsü eğitim aracı.
    
    Kullanım:
        1. Oyunu istediğin duruma getir (yarış, menü, vb.)
        2. Kategori seç
        3. Ekran görüntüsünü al
        4. Her durum için 3-5 görüntü kaydet
    """

    def __init__(self):
        self.capture = ScreenCapture()
        self._ensure_directories()

    def _ensure_directories(self):
        """Eğitim veri klasörlerini oluştur."""
        for folder in STATE_FOLDERS.values():
            os.makedirs(folder, exist_ok=True)
        print("[Trainer] Training klasörleri hazır")

    def capture_for_state(self, state_name, crop_region=None):
        """
        Belirli bir durum için ekran görüntüsü kaydet.
        
        Args:
            state_name: Durum adı ('racing', 'race_finished', 'menu', 'loading')
            crop_region: İsteğe bağlı kırpma bölgesi (x, y, w, h) tuple
        
        Returns:
            str: Kaydedilen dosya yolu veya None
        """
        if state_name not in STATE_FOLDERS:
            print(f"❌ Geçersiz durum: {state_name}")
            print(f"   Geçerli durumlar: {list(STATE_FOLDERS.keys())}")
            return None

        # Ekran görüntüsü al
        frame = self.capture.grab_frame()

        # Kırpma (isteğe bağlı)
        if crop_region:
            x, y, w, h = crop_region
            frame = frame[y:y+h, x:x+w]

        # Dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{state_name}_{timestamp}.png"
        filepath = os.path.join(STATE_FOLDERS[state_name], filename)

        # Kaydet
        cv2.imwrite(filepath, frame)
        print(f"✅ Kaydedildi: {filepath}")
        print(f"   Boyut: {frame.shape[1]}x{frame.shape[0]}")

        return filepath

    def capture_roi(self, state_name):
        """
        Ekran görüntüsü alıp, kullanıcının belirli bir bölgeyi seçmesini sağlar.
        ROI (Region of Interest) seçici ile daha kesin eğitim verisi oluşturur.
        
        Args:
            state_name: Durum adı
        
        Returns:
            str: Kaydedilen dosya yolu veya None
        """
        print("📸 Tam ekran görüntüsü alınıyor...")
        frame = self.capture.grab_frame()

        print("🖱️  Bölge seçmek için fare ile bir dikdörtgen çizin.")
        print("   Enter: Seçimi onayla | C: İptal | Esc: Çık")

        # Görüntüyü küçült (seçim kolaylığı için)
        scale = 0.5
        display = cv2.resize(frame, None, fx=scale, fy=scale)

        # ROI seçimi
        roi = cv2.selectROI("Bolge Secin - Enter: Onayla, C: Iptal", display, fromCenter=False)
        cv2.destroyAllWindows()

        if roi[2] == 0 or roi[3] == 0:
            print("❌ Seçim iptal edildi")
            return None

        # Koordinatları orijinal boyuta geri ölçekle
        x = int(roi[0] / scale)
        y = int(roi[1] / scale)
        w = int(roi[2] / scale)
        h = int(roi[3] / scale)

        # Seçilen bölgeyi kırp
        cropped = frame[y:y+h, x:x+w]

        # Kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{state_name}_roi_{timestamp}.png"
        filepath = os.path.join(STATE_FOLDERS[state_name], filename)

        cv2.imwrite(filepath, cropped)
        print(f"✅ ROI kaydedildi: {filepath}")
        print(f"   Bölge: ({x}, {y}) - {w}x{h}")

        return filepath

    def list_training_data(self):
        """Mevcut eğitim verilerini listele."""
        print("\n📊 Training Verisi Özeti:")
        print("=" * 50)

        total = 0
        for state_name, folder in STATE_FOLDERS.items():
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
                count = len(files)
            else:
                count = 0

            status = "✅" if count >= 3 else "⚠️" if count > 0 else "❌"
            print(f"  {status} {state_name:20s}: {count} görüntü")
            total += count

        print("=" * 50)
        print(f"  Toplam: {total} görüntü")

        if total == 0:
            print("\n💡 İpucu: Önce her durum için en az 3 ekran görüntüsü kaydedin!")

    def delete_training_data(self, state_name=None):
        """
        Training verilerini sil.
        
        Args:
            state_name: Belirli bir durumun verisini sil. None ise tümünü sil.
        """
        if state_name:
            folders = {state_name: STATE_FOLDERS.get(state_name)}
        else:
            folders = STATE_FOLDERS

        for name, folder in folders.items():
            if folder and os.path.exists(folder):
                files = [f for f in os.listdir(folder) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
                for f in files:
                    os.remove(os.path.join(folder, f))
                print(f"🗑️  {name}: {len(files)} dosya silindi")

    def close(self):
        """Kaynakları temizle."""
        self.capture.close()


def interactive_mode():
    """Konsol tabanlı interaktif eğitim modu."""
    trainer = Trainer()

    print("\n" + "=" * 60)
    print("  🎮 ForzaBot - Training Modu")
    print("=" * 60)
    print()
    print("Oyunu istediğiniz duruma getirin, ardından bir komut girin.")
    print()
    print("Komutlar:")
    print("  1 = Racing ekranı (racing) görüntüsü al")
    print("  2 = Racing bitişi (race_finished) görüntüsü al")
    print("  3 = Menu (menu) görüntüsü al")
    print("  4 = Loading (loading) görüntüsü al")
    print("  r = ROI seçerek görüntü al (bölge seçici)")
    print("  l = Mevcut eğitim verilerini listele")
    print("  d = Training verilerini sil")
    print("  q = Exit")
    print()

    state_map = {
        "1": "racing",
        "2": "race_finished",
        "3": "menu",
        "4": "loading",
    }

    try:
        while True:
            cmd = input("\n> Komut: ").strip().lower()

            if cmd == "q":
                break
            elif cmd == "l":
                trainer.list_training_data()
            elif cmd == "d":
                confirm = input("  Tüm eğitim verilerini silmek istediğinize emin misiniz? (e/h): ")
                if confirm.lower() == "e":
                    trainer.delete_training_data()
            elif cmd in state_map:
                state = state_map[cmd]
                print(f"\n⏳ 3 saniye sonra {state} için ekran görüntüsü alınacak...")
                print("   (Oyuna geçin!)")
                time.sleep(3)
                trainer.capture_for_state(state)
            elif cmd == "r":
                print("  Hangi durum için? (1=racing, 2=finished, 3=menu, 4=loading)")
                sub = input("  > ").strip()
                if sub in state_map:
                    print(f"\n⏳ 3 saniye sonra ROI seçimi açılacak...")
                    time.sleep(3)
                    trainer.capture_roi(state_map[sub])
            else:
                print("❌ Geçersiz komut")

    except KeyboardInterrupt:
        print("\n")

    trainer.close()
    print("Eğitim modu kapatıldı.")


if __name__ == "__main__":
    interactive_mode()
