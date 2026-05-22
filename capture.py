"""
ForzaBot - Ekran Yakalama Modülü
mss kütüphanesi ile hızlı ekran yakalama.
"""

import numpy as np
import cv2
import mss
import time
from config import SCREEN_REGION, MONITOR_INDEX


class ScreenCapture:
    """Ekran görüntüsü yakalama sınıfı."""

    def __init__(self, region=None, monitor_index=None):
        """
        Args:
            region: Yakalanacak bölge dict {"top": y, "left": x, "width": w, "height": h}
                    None ise tüm ekranı yakalar.
            monitor_index: Monitör indeksi (1 = ana monitör)
        """
        self.sct = mss.mss()
        self.monitor_index = monitor_index or MONITOR_INDEX
        self.region = region or SCREEN_REGION
        self._setup_monitor()

    def _setup_monitor(self):
        """Monitör bilgilerini ayarla."""
        if self.region:
            self.monitor = self.region
        else:
            self.monitor = self.sct.monitors[self.monitor_index]
        
        print(f"[Capture] Monitör ayarlandı: {self.monitor['width']}x{self.monitor['height']}")

    def grab_frame(self):
        """
        Ekran görüntüsü al ve BGR numpy array olarak döndür.
        
        Returns:
            numpy.ndarray: BGR formatında ekran görüntüsü
        """
        screenshot = self.sct.grab(self.monitor)
        frame = np.array(screenshot)
        # mss BGRA formatında döndürür, OpenCV BGR'ye çevir
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame_bgr

    def grab_gray(self):
        """
        Ekran görüntüsü al ve gri tonlama numpy array olarak döndür.
        
        Returns:
            numpy.ndarray: Gri tonlama ekran görüntüsü
        """
        frame = self.grab_frame()
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def save_screenshot(self, filepath):
        """
        Ekran görüntüsünü dosyaya kaydet.
        
        Args:
            filepath: Kaydedilecek dosya yolu (.png önerilir)
        
        Returns:
            numpy.ndarray: Kaydedilen BGR görüntü
        """
        frame = self.grab_frame()
        cv2.imwrite(filepath, frame)
        print(f"[Capture] Ekran görüntüsü kaydedildi: {filepath}")
        return frame

    def get_fps_test(self, duration=3):
        """
        Yakalama FPS'ini test et.
        
        Args:
            duration: Test süresi (saniye)
        
        Returns:
            float: Ortalama FPS
        """
        print(f"[Capture] FPS testi başlıyor ({duration} saniye)...")
        frame_count = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            self.grab_frame()
            frame_count += 1

        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        print(f"[Capture] FPS Testi: {frame_count} kare / {elapsed:.2f}s = {fps:.1f} FPS")
        return fps

    def close(self):
        """Kaynakları temizle."""
        self.sct.close()


# === Test ===
if __name__ == "__main__":
    print("=== Ekran Yakalama Testi ===")
    cap = ScreenCapture()
    
    # FPS testi
    cap.get_fps_test(duration=3)
    
    # Tek kare yakala ve kaydet
    import os
    test_path = os.path.join(os.path.dirname(__file__), "test_screenshot.png")
    frame = cap.save_screenshot(test_path)
    print(f"Görüntü boyutu: {frame.shape[1]}x{frame.shape[0]}")
    
    cap.close()
    print("=== Test Tamamlandı ===")
