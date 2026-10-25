import os
import sys
import math
import cv2
import numpy as np
import pygame
from PIL import Image, ImageSequence

BASE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(BASE, "ASSET")

SCREEN_W, SCREEN_H = 1920, 1080
FPS = 60
CAMERA_INDEX = 0

HSV_LOWER = np.array([35, 50, 40], dtype=np.uint8)
HSV_UPPER = np.array([90, 255, 255], dtype=np.uint8)
MIN_AREA = 1500

# Zona kamera 5 kotak:
# baris atas: kiri + tengah = lompat, kanan = interaksi (Z)
# baris bawah: kiri = bergerak kiri, tengah = diam, kanan = bergerak kanan.
X_LEFT = 1.0 / 3.0
X_RIGHT = 2.0 / 3.0
Y_SPLIT = 0.50

MOVE_SPEED = 360
PLAYER_SIZE = (200, 200)
PLAYER_START_X = 160
PLAYER_START_Y = SCREEN_H * 0.53

# ---------------- BOSS (hanya muncul di Background 2) ----------------
# Sesuaikan nama file ini jika nama asset-mu berbeda.
BOSS_FOLDER = os.path.join(ASSET, "MONSTER")
BOSS_SEMI_FILE = os.path.join(BOSS_FOLDER, "semi buka.gif")
BOSS_OPEN_FILE = os.path.join(BOSS_FOLDER, "mata buka.gif")
BOSS_CLOSED_FILE = os.path.join(BOSS_FOLDER, "mata tutup.gif")
BOSS_X = 1000             # posisi horizontal monster
BOSS_Y = 0              # posisi vertikal monster
BOSS_SIZE = (900, 720)    # ukuran monster (lebar, tinggi)
BOSS_SEMI_SECONDS = 1.0   # fase semi terbuka
BOSS_OPEN_SECONDS = 2.0   # mata terbuka: pemain tidak boleh bergerak
BOSS_CLOSED_SECONDS = 2.0 # mata tertutup: pemain boleh bergerak
BOSS_GIF_FPS = 12         # kecepatan frame GIF monster di game
BOSS_HIT_COOLDOWN = 1.0   # jeda antarhit agar nyawa tidak berkurang tiap frame

# ---------------- NYAWA & ANIMASI KENA SERANGAN ----------------
MAX_HEALTH = 3
HEART_SIZE = (52, 52)
HEART_X = 630             # posisi X hati, bisa diubah
HEART_Y = 100   
HEART_SCALE = 0.55       # skala hati: 1.0 = ukuran asli
HEART_GAP = 10           # jarak antarhati
HURT_DURATION = 0.45
HURT_FRAME_INTERVAL = 0.035  # lebih kecil = animasi hurt lebih cepat

JUMP_DURATION = 0.85
JUMP_HEIGHT = 200

CAMERA_W, CAMERA_H = 400, 300
CAMERA_MARGIN_RIGHT = 1320
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

# Overlay warna atmosfer untuk boss di Background 2 (tanpa tulisan).
# Alpha dibuat berdenyut pelan supaya suasananya lebih dramatis.
boss_color_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
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


def load_optional_image(path, size=None):
    """Muat PNG transparan. Jika size=None, pertahankan ukuran asli."""
    if not path or not os.path.isfile(path):
        return None
    image = pygame.image.load(path).convert_alpha()
    if size is not None:
        image = pygame.transform.smoothscale(image, size)
    return image


def load_transparent_gif_frames(path, size):
    """
    Memuat frame GIF monster dan mempertahankan alpha.
    Jika GIF memiliki latar hitam solid, warna hitam yang tersambung ke tepi
    frame dibuat transparan agar monster bisa ditaruh di atas background game.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"GIF monster tidak ditemukan: {path}")

    frames = []
    with Image.open(path) as gif:
        for frame in ImageSequence.Iterator(gif):
            rgba = frame.convert("RGBA")
            arr = np.array(rgba)
            rgb = arr[:, :, :3]
            alpha = arr[:, :, 3]

            # Kandidat piksel hitam; hanya komponen yang tersambung ke tepi
            # yang dihapus supaya detail gelap di tubuh monster tetap terjaga.
            black = (
                (rgb[:, :, 0] <= 22) &
                (rgb[:, :, 1] <= 22) &
                (rgb[:, :, 2] <= 22) &
                (alpha > 0)
            ).astype(np.uint8)

            if black.any():
                count, labels = cv2.connectedComponents(black, connectivity=8)
                edge_ids = set(np.unique(labels[0, :]).tolist())
                edge_ids.update(np.unique(labels[-1, :]).tolist())
                edge_ids.update(np.unique(labels[:, 0]).tolist())
                edge_ids.update(np.unique(labels[:, -1]).tolist())
                bg = np.isin(labels, list(edge_ids)) & (black == 1)
                arr[bg, 3] = 0

            rgba = Image.fromarray(arr, "RGBA").resize(
                size, Image.Resampling.LANCZOS
            )
            surface = pygame.image.fromstring(
                rgba.tobytes(), rgba.size, "RGBA"
            ).convert_alpha()
            frames.append(surface)

    if not frames:
        raise RuntimeError(f"GIF monster tidak memiliki frame: {path}")
    return frames


# Tiga GIF monster, disimpan di ASSET/MONSTER.
boss_animations = {
    "SEMI": load_transparent_gif_frames(BOSS_SEMI_FILE, BOSS_SIZE),
    "OPEN": load_transparent_gif_frames(BOSS_OPEN_FILE, BOSS_SIZE),
    "CLOSED": load_transparent_gif_frames(BOSS_CLOSED_FILE, BOSS_SIZE),
}

# Cari gambar hati berdasarkan nama file, termasuk jika ekstensi huruf besar.
def find_asset_by_name(root, target_name):
    target = target_name.lower()
    for folder, _, filenames in os.walk(root):
        for filename in filenames:
            stem, _ = os.path.splitext(filename)
            if stem.lower() == target:
                return os.path.join(folder, filename)
    return None

heart_full_path = find_asset_by_name(ASSET, "darah")
heart_empty_path = find_asset_by_name(ASSET, "darah kosong")
heart_full = load_optional_image(heart_full_path) if heart_full_path else None
heart_empty = load_optional_image(heart_empty_path) if heart_empty_path else None

def scale_heart(image):
    if image is None:
        return None
    w = max(1, int(image.get_width() * HEART_SCALE))
    h = max(1, int(image.get_height() * HEART_SCALE))
    return pygame.transform.smoothscale(image, (w, h))

heart_full = scale_heart(heart_full)
heart_empty = scale_heart(heart_empty)
HEART_W = heart_full.get_width() if heart_full else 52

# Animasi hurt opsional: dicari di ASSET/kakak/hurt.gif lalu di folder utama.
hurt_path = os.path.join(ASSET, "kakak", "hurt.gif")
if not os.path.isfile(hurt_path):
    hurt_path = os.path.join(BASE, "hurt.gif")
hurt_frames = load_gif_frames(hurt_path, PLAYER_SIZE) if os.path.isfile(hurt_path) else []

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

            # Lima zona:
            # ATAS-KIRI dan ATAS-TENGAH = lompat
            # ATAS-KANAN = interaksi (Z)
            # BAWAH-KIRI = kiri, BAWAH-TENGAH = diam, BAWAH-KANAN = kanan
            if ny < Y_SPLIT:
                if nx > X_RIGHT:
                    camera_direction = "INTERAKSI"
                else:
                    camera_direction = "ATAS"
            elif nx < X_LEFT:
                camera_direction = "KIRI"
            elif nx > X_RIGHT:
                camera_direction = "KANAN"
            else:
                camera_direction = "TENGAH"

            cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 7, (0, 0, 255), -1)

    # Garis pembagi zona: tiga kolom dan dua baris.
    x_left_px = int(X_LEFT * 640)
    x_right_px = int(X_RIGHT * 640)
    y_split_px = int(Y_SPLIT * 480)

    # Atas kiri+tengah digabung menjadi satu kotak besar untuk lompat.
    cv2.line(frame, (x_right_px, 0), (x_right_px, 480), (255, 255, 0), 2)
    cv2.line(frame, (x_left_px, y_split_px), (x_left_px, 480), (255, 255, 0), 2)
    cv2.line(frame, (0, y_split_px), (640, y_split_px), (255, 255, 0), 2)

    # Label visual untuk membantu kalibrasi posisi sarung tangan.
    cv2.putText(frame, "LOMPAT", (245, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, "Z", (510, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
    cv2.putText(frame, "KIRI", (45, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, "DIAM", (265, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, "KANAN", (485, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

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

health = MAX_HEALTH
hurt_timer = 0.0
hurt_animation_timer = 0.0
hurt_frame_index = 0
hit_cooldown = 0.0
boss_phase = "SEMI"
boss_state_timer = BOSS_SEMI_SECONDS
boss_frame_index = 0
boss_frame_timer = 0.0
game_over = False


def set_animation(name):
    global current_animation, frame_index, animation_timer
    if current_animation != name:
        current_animation = name
        frame_index = 0
        animation_timer = 0.0


def draw_text(text, x, y, color=(255, 255, 255), font_obj=font):
    screen.blit(font_obj.render(text, True, color), (x, y))


def draw_health():
    """Tampilkan 3 slot hati: darah penuh untuk nyawa tersisa, kosong untuk hilang."""
    for i in range(MAX_HEALTH):
        x = HEART_X + i * (HEART_W + HEART_GAP)
        image = heart_full if i < health else heart_empty
        if image is not None:
            screen.blit(image, (x, HEART_Y))
        else:
            # Fallback sederhana jika file hati belum ditemukan.
            color = (220, 30, 60) if i < health else (90, 90, 90)
            pygame.draw.circle(screen, color, (x + 17, HEART_Y + 18), 14)
            pygame.draw.circle(screen, color, (x + 35, HEART_Y + 18), 14)
            pygame.draw.polygon(
                screen, color,
                [(x + 5, HEART_Y + 22), (x + 47, HEART_Y + 22), (x + 26, HEART_Y + 48)]
            )


def main():
    global player_x, player_y, jump_origin_y, facing
    global current_animation, frame_index, animation_timer, jump_timer
    global was_in_jump_zone, level, message, message_timer
    global health, hurt_timer, hurt_animation_timer, hurt_frame_index
    global hit_cooldown, boss_phase, boss_state_timer
    global boss_frame_index, boss_frame_timer, game_over

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
        elif keys[pygame.K_z]:
            direction = "INTERAKSI"
        else:
            direction = read_hand_direction()

        # Siklus boss hanya aktif pada Background 2: semi (1 dtk) -> buka (2 dtk) -> tutup (2 dtk).
        if level == 1:
            boss_state_timer -= dt
            boss_frame_timer += dt
            if boss_frame_timer >= 1.0 / BOSS_GIF_FPS:
                boss_frame_timer = 0.0
                boss_frame_index = (boss_frame_index + 1) % len(boss_animations[boss_phase])

            if boss_state_timer <= 0:
                if boss_phase == "SEMI":
                    boss_phase = "OPEN"
                    boss_state_timer = BOSS_OPEN_SECONDS
                elif boss_phase == "OPEN":
                    boss_phase = "CLOSED"
                    boss_state_timer = BOSS_CLOSED_SECONDS
                else:
                    boss_phase = "SEMI"
                    boss_state_timer = BOSS_SEMI_SECONDS
                boss_frame_index = 0
                boss_frame_timer = 0.0

        boss_eye_open = (level == 1 and boss_phase in ("SEMI", "OPEN"))

        # Pemain tetap bebas bergerak pada semua fase boss.
        # Jika game over, permainan berakhir dan karakter berhenti.
        if game_over:
            direction = "TENGAH"

        dx = 0.0
        if not game_over:
            if direction == "KIRI":
                dx = -MOVE_SPEED * dt
                facing = "LEFT"
                if jump_timer <= 0 and hurt_timer <= 0:
                    set_animation("RUN_LEFT")
            elif direction == "KANAN":
                dx = MOVE_SPEED * dt
                facing = "RIGHT"
                if jump_timer <= 0 and hurt_timer <= 0:
                    set_animation("RUN_RIGHT")
            elif direction in ("TENGAH", "BAWAH", "INTERAKSI") and jump_timer <= 0:
                set_animation("IDLE_LEFT" if facing == "LEFT" else "IDLE_RIGHT")

        in_jump_zone = direction == "ATAS" and not game_over
        if in_jump_zone and not was_in_jump_zone and jump_timer <= 0 and not game_over:
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
        if animation_timer >= 0.08 and hurt_timer <= 0:
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

        if hit_cooldown > 0:
            hit_cooldown = max(0.0, hit_cooldown - dt)

        if hurt_timer > 0:
            hurt_timer = max(0.0, hurt_timer - dt)
            hurt_animation_timer += dt
            if hurt_animation_timer >= HURT_FRAME_INTERVAL and hurt_frames:
                hurt_animation_timer = 0.0
                hurt_frame_index = (hurt_frame_index + 1) % len(hurt_frames)

        # Ketika mata boss terbuka, zona TENGAH layar adalah zona aman.
        # Pemain tetap bisa bergerak; jika posisi karakter keluar dari zona aman,
        # nyawa berkurang satu kali setiap cooldown.
        # Tidak ada zona aman. Saat mata boss terbuka, pemain boleh bergerak,
        # tetapi setiap input gerak akan mengurangi satu nyawa sesuai cooldown.
        # Saat idle/TENGAH, nyawa tidak berkurang.
        if (
            level == 1
            and boss_phase == "OPEN"
            and hit_cooldown <= 0
            and not game_over
            and direction in ("KIRI", "KANAN", "ATAS", "BAWAH")
        ):
            health = max(0, health - 1)
            hit_cooldown = BOSS_HIT_COOLDOWN
            hurt_timer = HURT_DURATION
            hurt_animation_timer = 0.0
            hurt_frame_index = 0

            if health <= 0:
                game_over = True
                message = "GAME OVER - nyawa habis"
            else:
                message = "Terkena serangan! -1 nyawa"
            message_timer = 1.8

        screen.blit(backgrounds[level], (0, 0))

        # Monster hanya digambar di Background 2, memakai GIF sesuai fase.
        if level == 1:
            boss_frames = boss_animations[boss_phase]
            screen.blit(boss_frames[boss_frame_index], (BOSS_X, BOSS_Y))

        if hurt_timer > 0 and hurt_frames:
            screen.blit(hurt_frames[hurt_frame_index], (int(player_x), int(player_y)))
        else:
            screen.blit(
                animations[current_animation][frame_index],
                (int(player_x), int(player_y))
            )

        # Nuansa RED LIGHT saat mata terbuka, GREEN LIGHT saat mata tertutup.
        # Efek hanya menimpa area gameplay; tulisan HUD dan ikon nyawa tetap jelas.
        if level == 1 and boss_phase in ("OPEN", "CLOSED"):
            pulse = (math.sin(pygame.time.get_ticks() / 350.0) + 1.0) / 2.0
            alpha = int(28 + pulse * 30)  # intensitas warna berdenyut: 28-58
            if boss_phase == "OPEN":
                boss_color_overlay.fill((255, 0, 0, alpha))
            else:
                boss_color_overlay.fill((0, 255, 35, alpha))
            screen.blit(boss_color_overlay, (0, 0))

        draw_text(f"LEVEL {level + 1}/3", 24, 20, (255, 240, 190))
        draw_text(f"Kontrol: {direction}", 24, 60)
        draw_health()
        if level == 1:
            if boss_phase == "SEMI":
                eye_text = "MATA SEMI TERBUKA"
            elif boss_phase == "OPEN":
                eye_text = "MATA TERBUKA - BERTAHAN DI TENGAH"
            else:
                eye_text = "MATA TERTUTUP - BOLEH GERAK"
            draw_text(eye_text, 24, 170, (255, 220, 120), small_font)
        if game_over:
            draw_text("GAME OVER - tekan ESC untuk keluar", SCREEN_W // 2 - 240, SCREEN_H // 2,
                      (255, 80, 80), font)
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
