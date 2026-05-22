"""
ForzaBot - Görüntü Karşılaştırma / Durum Tespiti Modülü
OpenCV template matching ile oyun durumunu tespit eder.
"""

import os
import cv2
import numpy as np
from config import TRAINING_DATA_DIR, STATE_FOLDERS, MATCH_THRESHOLD, USE_GRAYSCALE


class StateDetector:
    """Ekran görüntüsünü referans görüntülerle karşılaştırarak durumu tespit eder."""

    def __init__(self, threshold=None):
        """
        Args:
            threshold: Eşleşme eşik değeri (0.0 - 1.0). None ise config'den alınır.
        """
        self.threshold = threshold or MATCH_THRESHOLD
        self.templates = {}  # {durum_adı: [template_görüntüleri]}
        self._load_templates()

    def _load_templates(self):
        """Eğitim verilerini yükle - her durum için referans görüntüleri."""
        print("[Detector] Training verileri yükleniyor...")

        for state_name, folder_path in STATE_FOLDERS.items():
            self.templates[state_name] = []

            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                print(f"  [{state_name}] Klasör oluşturuldu: {folder_path}")
                continue

            # Klasördeki tüm görüntü dosyalarını yükle
            supported_ext = ('.png', '.jpg', '.jpeg', '.bmp')
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(supported_ext)]

            for filename in sorted(files):
                filepath = os.path.join(folder_path, filename)
                if USE_GRAYSCALE:
                    img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
                else:
                    img = cv2.imread(filepath, cv2.IMREAD_COLOR)

                if img is not None:
                    self.templates[state_name].append({
                        "image": img,
                        "filename": filename,
                        "path": filepath,
                    })

            count = len(self.templates[state_name])
            if count > 0:
                print(f"  [{state_name}] {count} referans görüntü yüklendi")
            else:
                print(f"  [{state_name}] Henüz eğitim verisi yok!")

    def reload_templates(self):
        """Eğitim verilerini yeniden yükle (yeni görüntü eklendikten sonra)."""
        self.templates.clear()
        self._load_templates()

    def match_template(self, screenshot, template_img):
        """
        Tek bir template ile eşleşme skoru hesapla.
        
        Args:
            screenshot: Yakalanan ekran görüntüsü (BGR veya gri)
            template_img: Karşılaştırılacak referans görüntü
        
        Returns:
            float: Eşleşme skoru (0.0 - 1.0)
        """
        # Gri tonlamaya çevir (gerekirse)
        if USE_GRAYSCALE:
            if len(screenshot.shape) == 3:
                gray_screen = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            else:
                gray_screen = screenshot
            template = template_img
        else:
            gray_screen = screenshot
            template = template_img

        # Template boyutlarını kontrol et
        t_h, t_w = template.shape[:2]
        s_h, s_w = gray_screen.shape[:2]

        if t_h > s_h or t_w > s_w:
            # Template ekrandan büyükse, eşleşme mümkün değil
            return 0.0

        # Template matching uygula
        result = cv2.matchTemplate(gray_screen, template, cv2.TM_CCOEFF_NORMED)

        # En yüksek eşleşme skorunu bul
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        return max_val

    def detect_state(self, screenshot):
        """
        Ekran görüntüsünü tüm durumlarla karşılaştır ve en iyi eşleşeni döndür.
        
        Args:
            screenshot: BGR formatında ekran görüntüsü (numpy array)
        
        Returns:
            tuple: (durum_adı, en_yüksek_skor) veya ("unknown", 0.0)
        """
        best_state = "unknown"
        best_score = 0.0
        all_scores = {}

        for state_name, templates in self.templates.items():
            if not templates:
                continue

            # Bu durum için en yüksek skoru bul
            state_best = 0.0
            for tmpl in templates:
                score = self.match_template(screenshot, tmpl["image"])
                if score > state_best:
                    state_best = score

            all_scores[state_name] = state_best

            if state_best > best_score and state_best >= self.threshold:
                best_score = state_best
                best_state = state_name

        return best_state, best_score, all_scores

    def get_match_details(self, screenshot):
        """
        Detaylı eşleşme raporu (debug için).
        
        Args:
            screenshot: BGR formatında ekran görüntüsü
        
        Returns:
            dict: Her durum ve her template için skorlar
        """
        details = {}

        for state_name, templates in self.templates.items():
            details[state_name] = []
            for tmpl in templates:
                score = self.match_template(screenshot, tmpl["image"])
                details[state_name].append({
                    "filename": tmpl["filename"],
                    "score": round(score, 4),
                    "matched": score >= self.threshold,
                })

        return details

    def has_training_data(self):
        """En az bir durum için eğitim verisi var mı?"""
        for templates in self.templates.values():
            if templates:
                return True
        return False

    def get_training_summary(self):
        """Eğitim verisi özetini döndür."""
        summary = {}
        for state_name, templates in self.templates.items():
            summary[state_name] = len(templates)
        return summary


# === Test ===
if __name__ == "__main__":
    print("=== Durum Tespiti Testi ===")
    detector = StateDetector()

    summary = detector.get_training_summary()
    print("\nEğitim verisi özeti:")
    for state, count in summary.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {state}: {count} görüntü")

    if detector.has_training_data():
        from capture import ScreenCapture
        cap = ScreenCapture()
        frame = cap.grab_frame()

        state, score, all_scores = detector.detect_state(frame)
        print(f"\nTespit edilen durum: {state} (skor: {score:.4f})")
        print("Tüm skorlar:")
        for s, sc in all_scores.items():
            print(f"  {s}: {sc:.4f}")

        cap.close()
    else:
        print("\n⚠️  Training verisi bulunamadı!")
        print("Önce trainer.py ile ekran görüntüleri kaydedin.")

    print("=== Test Tamamlandı ===")
