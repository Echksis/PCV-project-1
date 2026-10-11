import cv2
import numpy as np

# Hand Color Detection: sarung tangan hijau
# Tekan Q atau ESC untuk keluar.
# Tekan S untuk menyimpan screenshot mask.

def nothing(_):
    pass

cap = cv2.VideoCapture(0)  # ganti ke 1 jika webcam tidak terbuka
if not cap.isOpened():
    raise RuntimeError("Webcam tidak dapat dibuka. Coba ganti VideoCapture(0) menjadi VideoCapture(1).")

cv2.namedWindow("Pengaturan HSV")
cv2.createTrackbar("H min", "Pengaturan HSV", 35, 179, nothing)
cv2.createTrackbar("H max", "Pengaturan HSV", 90, 179, nothing)
cv2.createTrackbar("S min", "Pengaturan HSV", 50, 255, nothing)
cv2.createTrackbar("S max", "Pengaturan HSV", 255, 255, nothing)
cv2.createTrackbar("V min", "Pengaturan HSV", 40, 255, nothing)
cv2.createTrackbar("V max", "Pengaturan HSV", 255, 255, nothing)
cv2.createTrackbar("Area minimum", "Pengaturan HSV", 1500, 20000, nothing)

while True:
    ok, frame = cap.read()
    if not ok:
        print("Frame webcam tidak terbaca.")
        break

    # Mirror agar gerakan terasa seperti bercermin
    frame = cv2.flip(frame, 1)
    blurred = cv2.GaussianBlur(frame, (7, 7), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    h_min = cv2.getTrackbarPos("H min", "Pengaturan HSV")
    h_max = cv2.getTrackbarPos("H max", "Pengaturan HSV")
    s_min = cv2.getTrackbarPos("S min", "Pengaturan HSV")
    s_max = cv2.getTrackbarPos("S max", "Pengaturan HSV")
    v_min = cv2.getTrackbarPos("V min", "Pengaturan HSV")
    v_max = cv2.getTrackbarPos("V max", "Pengaturan HSV")
    min_area = cv2.getTrackbarPos("Area minimum", "Pengaturan HSV")

    lower = np.array([h_min, s_min, v_min], dtype=np.uint8)
    upper = np.array([h_max, s_max, v_max], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)

    # Kurangi bintik kecil dan rapikan area terdeteksi
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detected = False

    if contours:
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        if area >= min_area:
            detected = True
            x, y, w, h = cv2.boundingRect(largest)
            M = cv2.moments(largest)

            cv2.drawContours(frame, [largest], -1, (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.circle(frame, (cx, cy), 7, (0, 0, 255), -1)
                cv2.putText(frame, f"Posisi: ({cx}, {cy})", (x, max(25, y - 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

            cv2.putText(frame, f"SARUNG TANGAN TERDETEKSI | Area: {int(area)}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

    if not detected:
        cv2.putText(frame, "SARUNG TANGAN BELUM TERDETEKSI",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

    cv2.imshow("Deteksi Sarung Tangan Hijau", frame)
    cv2.imshow("Mask Hijau (putih = terdeteksi)", mask)

    key = cv2.waitKey(1) & 0xFF
    if key in (ord("q"), 27):
        break
    elif key == ord("s"):
        cv2.imwrite("mask_hijau.png", mask)
        print("Mask disimpan sebagai mask_hijau.png")

cap.release()
cv2.destroyAllWindows()
