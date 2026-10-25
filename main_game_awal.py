import os
import sys
import cv2
import numpy as np
import pygame

BASE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(BASE, "ASSET")

SCREEN_W, SCREEN_H = 1920, 1080
FPS = 60
CAMERA_INDEX = 0

HSV_LOWER = np.array([35, 50, 40], dtype=np.uint8)
HSV_UPPER = np.array([90, 255, 255], dtype=np.uint8)
MIN_AREA = 1500

# Kamera: area kiri/kanan dibagi berdasarkan persentase frame.
X_LEFT = 0.35
X_RIGHT = 0.65
Y_TOP = 0.35

MOVE_SPEED = 360
PLAYER_SIZE = (200, 200)
PLAYER_START_X = 160
PLAYER_START_Y = SCREEN_H * 0.53

JUMP_DURATION = 0.85
JUMP_HEIGHT = 200

CAMERA_W, CAMERA_H = 320, 240
CAMERA_MARGIN_RIGHT = 1400
CAMERA_MARGIN_TOP = 150

BG_FILES = [
    os.path.join(ASSET, "Background", "Background 1.png"),
    os.path.join(ASSET, "Background", "Background 2.png"),
    os.path.join(ASSET, "Background", "Background 3.png"),
]

ANIMATION_FILES = {
    "RUN_RIGHT": os.path.join(ASSET, "kakak", "run_right.gif"),
    "RUN_LEFT": os.path.join(ASSET, "kakak", "run_left.gif"),
    "JUMP_RIGHT": os.path.join(ASSET, "kakak", "jump_right.gif"),
    "JUMP_LEFT": os.path.join(ASSET, "kakak", "jump_left.gif"),
    "IDLE_RIGHT": os.path.join(ASSET, "kakak", "idle_right.gif"),
    "IDLE_LEFT": os.path.join(ASSET, "kakak", "idle_left.gif"),
}

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Menyelamatkan Adik - Prototype Full HD")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)
small_font = pygame.font.SysFont("Arial", 22)


def load_background(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Background tidak ditemukan:\n{path}")
    image = pygame.image.load(path).convert()
    return pygame.transform.smoothscale(image, (SCREEN_W, SCREEN_H))


def load_gif_frames(path, size):
    """
    Baca frame GIF menggunakan OpenCV.
    Piksel putih yang tersambung ke tepi frame dibuat transparan.
    Jika putih menyatu dengan bagian karakter, hasil transparansi mungkin perlu
    pemrosesan sprite yang lebih presisi.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"File animasi tidak ditemukan:\n{path}\n"
            "Pastikan file GIF berada langsung di folder ASSET/kakak."
        )

    gif = cv2.VideoCapture(path)
    frames = []

    while True:
        ok, bgr = gif.read()
        if not ok:
            break

        h, w = bgr.shape[:2]
        # Putih / hampir putih.
        white = (
            (bgr[:, :, 0] >= 220) &
            (bgr[:, :, 1] >= 220) &
            (bgr[:, :, 2] >= 220)
        ).astype(np.uint8)

        # Hapus hanya komponen putih yang tersambung ke tepi frame.
        num_labels, labels = cv2.connectedComponents(white, connectivity=8)
        edge_labels = set()
        edge_labels.update(np.unique(labels[0, :]).tolist())
        edge_labels.update(np.unique(labels[h - 1, :]).tolist())
        edge_labels.update(np.unique(labels[:, 0]).tolist())
        edge_labels.update(np.unique(labels[:, w - 1]).tolist())

        bg_mask = np.isin(labels, list(edge_labels))
        bg_mask[white == 0] = False

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
        rgba = np.dstack((rgb, alpha))

        surface = pygame.image.frombuffer(
            rgba.tobytes(), (w, h), "RGBA"
        ).copy()
        surface = pygame.transform.smoothscale(surface, size)
        frames.append(surface)

    gif.release()

    if not frames:
        raise RuntimeError(
            f"GIF tidak berhasil dibaca:\n{path}\n"
            "Coba pasang Pillow: python -m pip install pillow"
        )
    return frames


# ---------------- LOAD ASSETS ----------------
backgrounds = [load_background(path) for path in BG_FILES]
animations = {
    name: load_gif_frames(path, PLAYER_SIZE)
    for name, path in ANIMATION_FILES.items()
}

# ---------------- WEBCAM ----------------
cap = cv2.VideoCapture(CAMERA_INDEX)
camera_available = cap.isOpened()
if camera_available:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
else:
    print("PERINGATAN: Webcam tidak terbuka. Kontrol keyboard masih bisa dipakai.")

kernel = np.ones((5, 5), np.uint8)
hand_detected = False
last_camera_preview = None
camera_direction = "TENGAH"


def read_hand_direction():
    global hand_detected, last_camera_preview, camera_direction

    if not camera_available:
        hand_detected = False
        camera_direction = "TENGAH"
        last_camera_preview = None
        return camera_direction

    ok, frame = cap.read()
    if not ok:
        hand_detected = False
        camera_direction = "TENGAH"
        return camera_direction

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (640, 480))
    hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (7, 7), 0), cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    valid = [c for c in contours if cv2.contourArea(c) >= MIN_AREA]

    hand_detected = False
    camera_direction = "TENGAH"

    if valid:
        contour = max(valid, key=cv2.contourArea)
        moments = cv2.moments(contour)
        if moments["m00"] > 0:
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])
            nx, ny = cx / 640.0, cy / 480.0
            hand_detected = True

            # Zona atas untuk lompat; zona kiri/kanan untuk berlari;
            # sisanya (termasuk bawah/tengah) membuat karakter diam.
            if ny < Y_TOP:
                camera_direction = "ATAS"
            elif nx < X_LEFT:
                camera_direction = "KIRI"
            elif nx > X_RIGHT:
                camera_direction = "KANAN"
            else:
                camera_direction = "TENGAH"

            cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 7, (0, 0, 255), -1)

    # Garis empat sisi zona kamera: kiri, kanan, atas, bawah.
    x_left_px = int(X_LEFT * 640)
    x_right_px = int(X_RIGHT * 640)
    y_top_px = int(Y_TOP * 480)
    y_bottom_px = int(0.65 * 480)

    cv2.line(frame, (x_left_px, 0), (x_left_px, 480), (255, 255, 0), 2)
    cv2.line(frame, (x_right_px, 0), (x_right_px, 480), (255, 255, 0), 2)
    cv2.line(frame, (0, y_top_px), (640, y_top_px), (255, 255, 0), 2)
    cv2.line(frame, (0, y_bottom_px), (640, y_bottom_px), (255, 255, 0), 2)

    cv2.putText(
        frame, camera_direction, (15, 35),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2
    )

    preview = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    preview = cv2.resize(preview, (CAMERA_W, CAMERA_H))
    last_camera_preview = pygame.surfarray.make_surface(
        np.transpose(preview, (1, 0, 2))
    )
    return camera_direction


# ---------------- GAME STATE ----------------
player_x = float(PLAYER_START_X)
player_y = float(PLAYER_START_Y)
jump_origin_y = player_y
facing = "RIGHT"
current_animation = "RUN_RIGHT"
frame_index = 0
animation_timer = 0.0
jump_timer = 0.0
was_in_jump_zone = False

level = 0
message = "Level 1: cari jalan melewati rintangan"
message_timer = 3.0


def set_animation(name):
    global current_animation, frame_index, animation_timer
    if current_animation != name:
        current_animation = name
        frame_index = 0
        animation_timer = 0.0


def draw_text(text, x, y, color=(255, 255, 255), font_obj=font):
    screen.blit(font_obj.render(text, True, color), (x, y))


def main():
    global player_x, player_y, jump_origin_y, facing
    global current_animation, frame_index, animation_timer, jump_timer
    global was_in_jump_zone, level, message, message_timer

    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.04)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

        keys = pygame.key.get_pressed()

        # Keyboard overrides webcam for testing.
        if keys[pygame.K_LEFT]:
            direction = "KIRI"
        elif keys[pygame.K_RIGHT]:
            direction = "KANAN"
        elif keys[pygame.K_UP]:
            direction = "ATAS"
        else:
            direction = read_hand_direction()

        dx = 0.0
        if direction == "KIRI":
            dx = -MOVE_SPEED * dt
            facing = "LEFT"
            if jump_timer <= 0:
                set_animation("RUN_LEFT")
        elif direction == "KANAN":
            dx = MOVE_SPEED * dt
            facing = "RIGHT"
            if jump_timer <= 0:
                set_animation("RUN_RIGHT")
        elif direction in ("TENGAH", "BAWAH") and jump_timer <= 0:
            # Zona tengah/bawah: karakter berhenti dan memainkan idle
            # sesuai arah terakhir karakter menghadap.
            set_animation("IDLE_LEFT" if facing == "LEFT" else "IDLE_RIGHT")

        in_jump_zone = direction == "ATAS"
        if in_jump_zone and not was_in_jump_zone and jump_timer <= 0:
            jump_timer = JUMP_DURATION
            jump_origin_y = player_y
            set_animation("JUMP_LEFT" if facing == "LEFT" else "JUMP_RIGHT")
        was_in_jump_zone = in_jump_zone

        player_x += dx

        if jump_timer > 0:
            elapsed = JUMP_DURATION - jump_timer
            progress = max(0.0, min(1.0, elapsed / JUMP_DURATION))
            player_y = jump_origin_y - JUMP_HEIGHT * 4 * progress * (1 - progress)
            jump_timer = max(0.0, jump_timer - dt)
            if jump_timer <= 0:
                player_y = jump_origin_y
                if direction == "KIRI":
                    set_animation("RUN_LEFT")
                elif direction == "KANAN":
                    set_animation("RUN_RIGHT")

        animation_timer += dt
        if animation_timer >= 0.08:
            animation_timer = 0.0
            frames = animations[current_animation]
            if current_animation.startswith("JUMP"):
                # Animasi lompat maju sampai frame terakhir.
                frame_index = min(frame_index + 1, len(frames) - 1)
            else:
                # Run dan idle sama-sama dianimasikan berulang.
                frame_index = (frame_index + 1) % len(frames)

        # Transisi level sementara melalui tepi layar.
        if player_x > SCREEN_W - PLAYER_SIZE[0] - 5 and level < 2:
            level += 1
            player_x = 40
            message = f"Level {level + 1}"
            message_timer = 2.0
        elif player_x < 5 and level > 0:
            level -= 1
            player_x = SCREEN_W - PLAYER_SIZE[0] - 40
            message = f"Level {level + 1}"
            message_timer = 2.0

        player_x = max(0, min(SCREEN_W - PLAYER_SIZE[0], player_x))
        player_y = max(0, min(SCREEN_H - PLAYER_SIZE[1], player_y))

        screen.blit(backgrounds[level], (0, 0))
        screen.blit(
            animations[current_animation][frame_index],
            (int(player_x), int(player_y))
        )

        draw_text(f"LEVEL {level + 1}/3", 24, 20, (255, 240, 190))
        draw_text(f"Kontrol: {direction}", 24, 60)
        if not camera_available:
            draw_text(
                "Webcam tidak tersedia - gunakan tombol panah",
                24, 100, (255, 170, 170), small_font
            )
        elif not hand_detected and not any([
            keys[pygame.K_LEFT], keys[pygame.K_RIGHT], keys[pygame.K_UP]
        ]):
            draw_text(
                "Sarung tangan belum terdeteksi",
                210, 120, (255, 170, 170), small_font
            )

        if message_timer > 0:
            message_timer -= dt
            label = font.render(message, True, (255, 255, 255))
            plate = pygame.Surface(
                (label.get_width() + 32, label.get_height() + 24),
                pygame.SRCALPHA
            )
            plate.fill((0, 0, 0, 150))
            screen.blit(
                plate,
                (SCREEN_W // 2 - plate.get_width() // 2, 30)
            )
            screen.blit(
                label,
                (SCREEN_W // 2 - label.get_width() // 2, 42)
            )

        # Camera preview placed safely inside the Full HD window.
        if last_camera_preview is not None:
            camera_x = SCREEN_W - CAMERA_W - CAMERA_MARGIN_RIGHT
            camera_y = CAMERA_MARGIN_TOP
            screen.blit(last_camera_preview, (camera_x, camera_y))
            pygame.draw.rect(
                screen, (230, 230, 230),
                (camera_x, camera_y, CAMERA_W, CAMERA_H), 3
            )

        pygame.display.flip()

    if cap:
        cap.release()
    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    finally:
        if cap:
            cap.release()
        pygame.quit()
