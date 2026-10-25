import cv2
import numpy as np

# Ganti 0 ke 1 jika webcam yang digunakan bukan kamera default.
CAMERA_INDEX = 0

# Nilai awal untuk sarung tangan hijau. Sesuaikan melalui slider jika perlu.
DEFAULT_H_MIN = 35
DEFAULT_H_MAX = 90
DEFAULT_S_MIN = 45
DEFAULT_S_MAX = 255
DEFAULT_V_MIN = 40
DEFAULT_V_MAX = 255
DEFAULT_MIN_AREA = 2500

def nothing(_):
    pass

cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    raise RuntimeError(
        "Webcam tidak dapat dibuka. Tutup aplikasi lain yang memakai kamera "
        "atau coba ubah CAMERA_INDEX = 0 menjadi 1."
    )

cv2.namedWindow("Pengaturan HSV", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Pengaturan HSV", 520, 330)

cv2.createTrackbar("H min", "Pengaturan HSV", DEFAULT_H_MIN, 179, nothing)
cv2.createTrackbar("H max", "Pengaturan HSV", DEFAULT_H_MAX, 179, nothing)
cv2.createTrackbar("S min", "Pengaturan HSV", DEFAULT_S_MIN, 255, nothing)
cv2.createTrackbar("S max", "Pengaturan HSV", DEFAULT_S_MAX, 255, nothing)
cv2.createTrackbar("V min", "Pengaturan HSV", DEFAULT_V_MIN, 255, nothing)
cv2.createTrackbar("V max", "Pengaturan HSV", DEFAULT_V_MAX, 255, nothing)
cv2.createTrackbar("Area minimum", "Pengaturan HSV", DEFAULT_MIN_AREA, 30000, nothing)

kernel = np.ones((5, 5), np.uint8)

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Gagal membaca frame dari webcam.")
            break

        # Efek cermin supaya gerakan terasa alami.
        frame = cv2.flip(frame, 1)
        frame = cv2.GaussianBlur(frame, (7, 7), 0)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        h_min = cv2.getTrackbarPos("H min", "Pengaturan HSV")
        h_max = cv2.getTrackbarPos("H max", "Pengaturan HSV")
        s_min = cv2.getTrackbarPos("S min", "Pengaturan HSV")
        s_max = cv2.getTrackbarPos("S max", "Pengaturan HSV")
        v_min = cv2.getTrackbarPos("V min", "Pengaturan HSV")
        v_max = cv2.getTrackbarPos("V max", "Pengaturan HSV")
        min_area = cv2.getTrackbarPos("Area minimum", "Pengaturan HSV")

        lower = np.array([min(h_min, h_max), min(s_min, s_max), min(v_min, v_max)], dtype=np.uint8)
        upper = np.array([max(h_min, h_max), max(s_min, s_max), max(v_min, v_max)], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Cari objek hijau terbesar yang melewati batas area minimum.
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected = False
        display = frame.copy()

        valid_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
        if valid_contours:
            contour = max(valid_contours, key=cv2.contourArea)
            area = int(cv2.contourArea(contour))
            x, y, w, h = cv2.boundingRect(contour)
            moments = cv2.moments(contour)

            cv2.drawContours(display, [contour], -1, (0, 255, 0), 2)
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 255), 2)

            if moments["m00"] > 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
                cv2.circle(display, (cx, cy), 7, (0, 0, 255), -1)
                cv2.putText(display, f"Posisi: ({cx}, {cy})", (x, max(25, y - 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.putText(display, f"SARUNG TANGAN TERDETEKSI | Area: {area}",
                        (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            detected = True
        else:
            cv2.putText(display, "SARUNG TANGAN TIDAK TERDETEKSI",
                        (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Deteksi Sarung Tangan Hijau", display)
        cv2.imshow("Mask Hijau (putih = terdeteksi)", mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
