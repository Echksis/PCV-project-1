import os
import sys
import math
import cv2
import numpy as np
import pygame
from PIL import Image, ImageSequence

BASE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(BASE, "ASSET")
GAMEOVER_FOLDER = os.path.join(ASSET, "GameOver")
GAMEOVER_FILE = os.path.join(GAMEOVER_FOLDER, "GameOver.png")

GAMEOVER_MAX_SIZE = (1320, 380)

GAMEOVER_PROMPT_Y = 930

WIN_FOLDER = os.path.join(ASSET, "Ending win")
WIN_FILE = os.path.join(WIN_FOLDER, "Win.png")
WIN_MAX_SIZE = (900, 760)
WIN_POPUP_X = 1250
WIN_POPUP_Y = 300
WIN_POPUP_SIZE = (280, 100)
WIN_TRIGGER_DISTANCE = 420

SCREEN_W, SCREEN_H = 1920, 1080
FPS = 60
CAMERA_INDEX = 0

HSV_LOWER = np.array([35, 50, 40], dtype=np.uint8)
HSV_UPPER = np.array([90, 255, 255], dtype=np.uint8)
MIN_AREA = 1500


X_LEFT = 1.0 / 3.0
X_RIGHT = 2.0 / 3.0
Y_SPLIT = 0.50

MOVE_SPEED = 360
PLAYER_SIZE = (200, 200)
PLAYER_START_X = 160
PLAYER_START_Y = SCREEN_H * 0.53


BOSS_FOLDER = os.path.join(ASSET, "MONSTER")
BOSS_SEMI_FILE = os.path.join(BOSS_FOLDER, "semi buka.gif")
BOSS_OPEN_FILE = os.path.join(BOSS_FOLDER, "mata buka.gif")
BOSS_CLOSED_FILE = os.path.join(BOSS_FOLDER, "mata tutup.gif")
BOSS_X = 1000             
BOSS_Y = 0              
BOSS_SIZE = (900, 720)   
BOSS_SEMI_SECONDS = 1.0   
BOSS_OPEN_SECONDS = 2.0   
BOSS_CLOSED_SECONDS = 2.0 
BOSS_GIF_FPS = 12         
BOSS_HIT_COOLDOWN = 1.0   


MAX_HEALTH = 3
HEART_SIZE = (52, 52)
HEART_X = 630             
HEART_Y = 100   
HEART_SCALE = 0.55       
HEART_GAP = 10           
HURT_DURATION = 0.45
HURT_FRAME_INTERVAL = 0.035  

JUMP_DURATION = 0.85
JUMP_HEIGHT = 200


OBSTACLE_FOLDER = os.path.join(ASSET, "obstacle")
BARREL_FILE = os.path.join(OBSTACLE_FOLDER, "barrel.gif")
BAT_FILE = os.path.join(OBSTACLE_FOLDER, "kelelawar.gif")
BARREL_Y = 675                 
BAT_Y = 525                    
BARREL_SIZE = (105, 105)
BAT_SIZE = (115, 95)
OBSTACLES_PER_TYPE = 5
OBSTACLE_GAP_MIN, OBSTACLE_GAP_MAX = 1.8, 2.7  
BARREL_SPEED_MIN, BARREL_SPEED_MAX = 430, 570
BAT_SPEED_MIN, BAT_SPEED_MAX = 470, 620
OBSTACLE_HIT_COOLDOWN = 1.0

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


boss_color_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
pygame.display.set_caption("Menyelamatkan Adik - Prototype Full HD")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)
small_font = pygame.font.SysFont("Arial", 22)



OPENING_FOLDER = os.path.join(ASSET, "opening")
DIALOGUE_TYPE_SPEED = 42  
DIALOGUE_AUTO_NEXT = False  

SCENE5_STOP_SECONDS = 4.2  
SCENE5_DIALOGUE_START_DELAY = 3.0  
SCENE5_KAKAK_DELAY = 0.8   


def _draw_pixel_dialogue(surface, speaker, text, visible_chars):
    """Kotak dialog putih pixel-art, nameplate, dan efek typewriter."""
    box_w, box_h = 1510, 188
    box_x = (SCREEN_W - box_w) // 2
    box_y = SCREEN_H - box_h - 62
    name_w, name_h = 230, 56
    name_x, name_y = box_x + 42, box_y - name_h + 4

    
    pygame.draw.rect(surface, (0, 0, 0), (box_x + 13, box_y + 13, box_w, box_h))
    pygame.draw.rect(surface, (0, 0, 0), (box_x + 7, box_y + 7, box_w, box_h))
    pygame.draw.rect(surface, (0, 0, 0), (box_x, box_y, box_w, box_h))
    pygame.draw.rect(surface, (255, 255, 255),
                     (box_x + 8, box_y + 8, box_w - 16, box_h - 16))

    
    pygame.draw.rect(surface, (0, 0, 0), (name_x + 6, name_y + 6, name_w, name_h))
    pygame.draw.rect(surface, (0, 0, 0), (name_x, name_y, name_w, name_h))
    pygame.draw.rect(surface, (255, 255, 255),
                     (name_x + 6, name_y + 6, name_w - 12, name_h - 12))

    
    name_font = pygame.font.SysFont("monospace", 29, bold=True)
    dialogue_font = pygame.font.SysFont("monospace", 35, bold=True)
    name_img = name_font.render(speaker, False, (0, 0, 0))
    surface.blit(name_img, name_img.get_rect(center=(name_x + name_w // 2,
                                                     name_y + name_h // 2)))

    shown = text[:visible_chars]
    
    words = shown.split(" ")
    lines, current = [], ""
    max_width = box_w - 110
    for word in words:
        candidate = word if not current else current + " " + word
        if dialogue_font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = 46
    total_h = len(lines) * line_h
    start_y = box_y + max(16, (box_h - total_h) // 2)
    for idx, line in enumerate(lines):
        line_img = dialogue_font.render(line, False, (0, 0, 0))
        surface.blit(line_img, line_img.get_rect(
            center=(SCREEN_W // 2, start_y + idx * line_h + line_h // 2)
        ))

    
    if visible_chars >= len(text) and (pygame.time.get_ticks() // 350) % 2 == 0:
        px, py = box_x + box_w - 64, box_y + box_h - 42
        pygame.draw.polygon(surface, (0, 0, 0),
                            [(px, py), (px + 27, py), (px + 13, py + 18)])


def _open_cutscene_video(filename):
    path = os.path.join(OPENING_FOLDER, filename)
    if not os.path.isfile(path):
        print(f"[CUTSCENE] Video tidak ditemukan: {path}")
        return None, None
    cap_video = cv2.VideoCapture(path)
    if not cap_video.isOpened():
        print(f"[CUTSCENE] Video tidak dapat dibuka: {path}")
        cap_video.release()
        return None, None
    fps_video = cap_video.get(cv2.CAP_PROP_FPS)
    if not fps_video or fps_video < 1 or fps_video > 120:
        fps_video = 30.0
    return cap_video, fps_video


def play_opening_cutscene(surface, game_clock):
    """
    Scene 1/3/5 diputar sekali. Bila Scene 1 atau 3 habis sebelum dialog selesai,
    Scene 2/4 akan diloop sebagai latar. Scene 5 menahan frame terakhir.
    SPACE: selesaikan teks yang sedang diketik, lalu SPACE lagi untuk dialog berikutnya.
    """
    scenes = [
        {
            "main": "scene1.mp4", "loop": "scene2.mp4",
            "dialogues": [
                ("Adik", "Kak! Aku sudah menemukan herbal yang kita cari!"),
                ("Kakak", "Bagus. Ini cukup untuk obat Ibu."),
                ("Adik", "Kalau begitu, setelah ini kita bisa langsung pulang, kan?"),
                ("Kakak", "Iya. Ayo, hari sudah mulai gelap."),
            ],
            "loop_after_main": True,
        },
        {
            "main": "scene3.mp4", "loop": "scene4.mp4",
            "dialogues": [
                ("Adik", "Kak... itu kerajaan kita, kan?"),
                ("Kakak", "Apa yang terjadi di sana...?"),
                ("Adik", "Kenapa ada api di mana-mana? Apa semua orang baik-baik saja?"),
                ("Kakak", "Aku tidak tahu. Kita harus segera ke sana!"),
            ],
            "loop_after_main": True,
        },
        {
            "main": "scene5.mp4", "loop": None,
            "dialogues": [
                ("Adik", "KAKAAAK!! TOLONG AKU!!"),
                ("Kakak", "ADIK!! PEGANG TANGANKU!!"),
                ("Adik", "KAKAAAK!!"),
                ("Kakak", "TIDAAAK!!"),
            ],
            "loop_after_main": False,
        },
    ]

    for scene_index, scene in enumerate(scenes):
        if not os.path.isfile(os.path.join(OPENING_FOLDER, scene["main"])):
            print("[CUTSCENE] Folder/video opening tidak lengkap. Cutscene dilewati.")
            return

        main_cap, main_fps = _open_cutscene_video(scene["main"])
        loop_cap, loop_fps = (None, 30.0)
        if scene["loop"]:
            loop_cap, loop_fps = _open_cutscene_video(scene["loop"])

        current_cap = main_cap
        current_fps = main_fps or 30.0
        main_finished = False
        loop_started = False
        last_frame = None
        frame_elapsed = 0.0
        dialogue_index = 0
        char_count = 0.0
        line_complete = False
        scene_done = False
        scene_start_ticks = pygame.time.get_ticks()
        scene5_kakak_delay_until = None
        scene5_auto_advance_at = None

        while not scene_done:
            dt = min(game_clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if main_cap: main_cap.release()
                    if loop_cap: loop_cap.release()
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        if main_cap: main_cap.release()
                        if loop_cap: loop_cap.release()
                        return
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z):
                        dialogue = scene["dialogues"][dialogue_index][1]
                        if char_count < len(dialogue):
                            char_count = float(len(dialogue))  
                            if scene_index == 2 and dialogue_index == 0:
                                scene5_auto_advance_at = pygame.time.get_ticks() + int(SCENE5_KAKAK_DELAY * 1000)
                        else:
                            
                            if not (scene_index == 2 and dialogue_index == 0):
                                dialogue_index += 1
                                if dialogue_index >= len(scene["dialogues"]):
                                    scene_done = True
                                else:
                                    char_count = 0.0

            
            frame_elapsed += dt
            frame_interval = 1.0 / max(1.0, current_fps)
            
            if scene_index == 2 and current_cap is main_cap and main_cap is not None:
                current_pos_ms = main_cap.get(cv2.CAP_PROP_POS_MSEC)
                if current_pos_ms >= SCENE5_STOP_SECONDS * 1000:
                    current_cap = None  
            if frame_elapsed >= frame_interval and current_cap is not None:
                frame_elapsed %= frame_interval
                ok, frame = current_cap.read()
                if ok:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (SCREEN_W, SCREEN_H), interpolation=cv2.INTER_AREA)
                    last_frame = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
                else:
                    if current_cap is main_cap and not main_finished:
                        main_finished = True
                        if scene["loop_after_main"] and loop_cap is not None:
                            current_cap = loop_cap
                            current_fps = loop_fps
                            loop_started = True
                        else:
                            
                            current_cap = None
                    elif current_cap is loop_cap and loop_cap is not None:
                        loop_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            if last_frame is not None:
                surface.blit(last_frame, (0, 0))
            else:
                surface.fill((0, 0, 0))

            if dialogue_index < len(scene["dialogues"]):
                
                if (scene_index == 2 and dialogue_index == 0
                        and char_count >= len(scene["dialogues"][0][1])
                        and scene5_auto_advance_at is None):
                    scene5_auto_advance_at = pygame.time.get_ticks() + int(SCENE5_KAKAK_DELAY * 1000)

                if (scene_index == 2 and dialogue_index == 0
                        and scene5_auto_advance_at is not None
                        and pygame.time.get_ticks() >= scene5_auto_advance_at):
                    dialogue_index = 1
                    char_count = 0.0
                    scene5_kakak_delay_until = None

                scene5_waiting_to_start = (
                    scene_index == 2
                    and (pygame.time.get_ticks() - scene_start_ticks) < int(SCENE5_DIALOGUE_START_DELAY * 1000)
                )
                if not scene5_waiting_to_start:
                    speaker, dialogue = scene["dialogues"][dialogue_index]
                    char_count = min(float(len(dialogue)), char_count + DIALOGUE_TYPE_SPEED * dt)
                    _draw_pixel_dialogue(surface, speaker, dialogue, int(char_count))

            pygame.display.flip()

        if main_cap:
            main_cap.release()
        if loop_cap:
            loop_cap.release()

    
    start_ticks = pygame.time.get_ticks()
    title_font = pygame.font.SysFont("monospace", 76, bold=True)
    while pygame.time.get_ticks() - start_ticks < 2200:
        game_clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
        surface.fill((8, 6, 16))
        title = title_font.render("I WILL FIND YOU", False, (245, 235, 220))
        surface.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
        pygame.display.flip()



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
        
        white = (
            (bgr[:, :, 0] >= 220) &
            (bgr[:, :, 1] >= 220) &
            (bgr[:, :, 2] >= 220)
        ).astype(np.uint8)

        
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



backgrounds = [load_background(path) for path in BG_FILES]
if os.path.isfile(GAMEOVER_FILE):
    gameover_image = pygame.image.load(GAMEOVER_FILE).convert_alpha()
    gw, gh = gameover_image.get_size()
    scale = min(GAMEOVER_MAX_SIZE[0] / gw, GAMEOVER_MAX_SIZE[1] / gh, 1.0)
    gameover_image = pygame.transform.smoothscale(
        gameover_image, (max(1, int(gw * scale)), max(1, int(gh * scale)))
    )
else:
    gameover_image = None
    print(f"PERINGATAN: gambar GameOver tidak ditemukan: {GAMEOVER_FILE}")
win_image = None
if os.path.isfile(WIN_FILE):
    win_image = pygame.image.load(WIN_FILE).convert_alpha()
    ww, wh = win_image.get_size()
    win_scale = min(WIN_MAX_SIZE[0] / ww, WIN_MAX_SIZE[1] / wh, 1.0)
    win_image = pygame.transform.smoothscale(
        win_image, (max(1, int(ww * win_scale)), max(1, int(wh * win_scale)))
    )
else:
    print(f"PERINGATAN: gambar ending win tidak ditemukan: {WIN_FILE}")

win_popup_font = pygame.font.SysFont("Arial", 22, bold=True)
win_key_font = pygame.font.SysFont("Arial", 30, bold=True)

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


def load_obstacle_gif(path, size):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Obstacle tidak ditemukan: {path}")
    frames = []
    with Image.open(path) as gif:
        for frame in ImageSequence.Iterator(gif):
            rgba = frame.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            frames.append(pygame.image.frombytes(
                rgba.tobytes(), rgba.size, "RGBA"
            ).convert_alpha())
    return frames



boss_animations = {
    "SEMI": load_transparent_gif_frames(BOSS_SEMI_FILE, BOSS_SIZE),
    "OPEN": load_transparent_gif_frames(BOSS_OPEN_FILE, BOSS_SIZE),
    "CLOSED": load_transparent_gif_frames(BOSS_CLOSED_FILE, BOSS_SIZE),
}

barrel_frames = load_obstacle_gif(BARREL_FILE, BARREL_SIZE)
bat_frames = load_obstacle_gif(BAT_FILE, BAT_SIZE)


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


hurt_path = os.path.join(ASSET, "kakak", "hurt.gif")
if not os.path.isfile(hurt_path):
    hurt_path = os.path.join(BASE, "hurt.gif")
hurt_frames = load_gif_frames(hurt_path, PLAYER_SIZE) if os.path.isfile(hurt_path) else []


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

    
    x_left_px = int(X_LEFT * 640)
    x_right_px = int(X_RIGHT * 640)
    y_split_px = int(Y_SPLIT * 480)

    
    cv2.line(frame, (x_right_px, 0), (x_right_px, 480), (255, 255, 0), 2)
    cv2.line(frame, (x_left_px, y_split_px), (x_left_px, 480), (255, 255, 0), 2)
    cv2.line(frame, (0, y_split_px), (640, y_split_px), (255, 255, 0), 2)

    
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
obstacles = []
obstacle_spawn_timer = 1.0
obstacle_spawn_kind = "BARREL"
spawned_counts = {"BARREL": 0, "BAT": 0}
obstacle_hit_cooldown = 0.0


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


def reset_game():
    """Reset semua state permainan agar tombol R benar-benar mengulang level 1."""
    global player_x, player_y, jump_origin_y, facing
    global current_animation, frame_index, animation_timer, jump_timer, was_in_jump_zone
    global level, message, message_timer, health, hurt_timer, hurt_animation_timer, hurt_frame_index
    global hit_cooldown, boss_phase, boss_state_timer, boss_frame_index, boss_frame_timer, game_over
    global obstacles, obstacle_spawn_timer, obstacle_spawn_kind, spawned_counts, obstacle_hit_cooldown

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
    obstacles = []
    obstacle_spawn_timer = 1.0
    obstacle_spawn_kind = "BARREL"
    spawned_counts = {"BARREL": 0, "BAT": 0}
    obstacle_hit_cooldown = 0.0


def main():
    global player_x, player_y, jump_origin_y, facing
    global current_animation, frame_index, animation_timer, jump_timer
    global was_in_jump_zone, level, message, message_timer
    global health, hurt_timer, hurt_animation_timer, hurt_frame_index
    global hit_cooldown, boss_phase, boss_state_timer
    global boss_frame_index, boss_frame_timer, game_over
    global obstacles, obstacle_spawn_timer, obstacle_spawn_kind
    global spawned_counts, obstacle_hit_cooldown
    global win_ending, win_popup_active

    
    play_opening_cutscene(screen, clock)

    win_ending = False
    win_popup_active = False
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.04)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_over and event.key == pygame.K_r:
                    reset_game()
                elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

        keys = pygame.key.get_pressed()

        
        if keys[pygame.K_LEFT]:
            direction = "KIRI"
        elif keys[pygame.K_RIGHT]:
            direction = "KANAN"
        elif keys[pygame.K_UP]:
            direction = "ATAS"
        else:
            direction = read_hand_direction()

        
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

        
        # Ending diaktifkan oleh zona Z pada webcam (kanan atas), bukan keyboard.
        if win_popup_active and direction == "INTERAKSI" and not game_over:
            win_ending = True

        if game_over or win_ending:
            direction = "TENGAH"

        dx = 0.0
        if not game_over and not win_ending:
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
                
                frame_index = min(frame_index + 1, len(frames) - 1)
            else:
                
                frame_index = (frame_index + 1) % len(frames)

        
        if player_x > SCREEN_W - PLAYER_SIZE[0] - 5 and level < 2:
            level += 1
            obstacles.clear()
            spawned_counts = {"BARREL": 0, "BAT": 0}
            obstacle_spawn_timer = 1.0
            obstacle_spawn_kind = "BARREL"
            player_x = 40
            message = f"Level {level + 1}"
            message_timer = 2.0
        elif player_x < 5 and level > 0:
            level -= 1
            obstacles.clear()
            spawned_counts = {"BARREL": 0, "BAT": 0}
            obstacle_spawn_timer = 1.0
            obstacle_spawn_kind = "BARREL"
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

        
        obstacle_hit_cooldown = max(0.0, obstacle_hit_cooldown - dt)
        if level == 0 and not game_over:
            obstacle_spawn_timer -= dt
            if obstacle_spawn_timer <= 0:
                kind = obstacle_spawn_kind
                if spawned_counts[kind] < OBSTACLES_PER_TYPE:
                    if kind == "BARREL":
                        y = BARREL_Y
                        speed = np.random.uniform(BARREL_SPEED_MIN, BARREL_SPEED_MAX)
                        frames = barrel_frames
                    else:
                        y = BAT_Y
                        speed = np.random.uniform(BAT_SPEED_MIN, BAT_SPEED_MAX)
                        frames = bat_frames
                    obstacles.append({"kind": kind, "x": float(SCREEN_W + 20),
                                      "y": float(y), "speed": float(speed),
                                      "frames": frames, "frame": 0, "anim_t": 0.0})
                    spawned_counts[kind] += 1
                obstacle_spawn_kind = "BAT" if kind == "BARREL" else "BARREL"
                if all(spawned_counts[k] >= OBSTACLES_PER_TYPE for k in spawned_counts):
                    obstacle_spawn_timer = 999999
                else:
                    obstacle_spawn_timer = np.random.uniform(OBSTACLE_GAP_MIN, OBSTACLE_GAP_MAX)

            
            player_rect = pygame.Rect(int(player_x + PLAYER_SIZE[0] * 0.22),
                                      int(player_y + PLAYER_SIZE[1] * 0.18),
                                      int(PLAYER_SIZE[0] * 0.56),
                                      int(PLAYER_SIZE[1] * 0.64))
            for obs in obstacles:
                obs["x"] -= obs["speed"] * dt
                obs["anim_t"] += dt
                if obs["anim_t"] >= 0.16:
                    obs["anim_t"] = 0.0
                    obs["frame"] = (obs["frame"] + 1) % len(obs["frames"])
                spr = obs["frames"][obs["frame"]]
                ix, iy = int(spr.get_width() * 0.18), int(spr.get_height() * 0.18)
                rect = pygame.Rect(int(obs["x"] + ix), int(obs["y"] + iy),
                                   max(1, spr.get_width() - 2 * ix),
                                   max(1, spr.get_height() - 2 * iy))
                if player_rect.colliderect(rect) and obstacle_hit_cooldown <= 0:
                    health = max(0, health - 1)
                    obstacle_hit_cooldown = OBSTACLE_HIT_COOLDOWN
                    hurt_timer, hurt_animation_timer, hurt_frame_index = HURT_DURATION, 0.0, 0
                    message = "Terkena obstacle! -1 nyawa"
                    message_timer = 1.5
                    if health <= 0:
                        game_over = True
                        message = "GAME OVER - nyawa habis"
            obstacles = [o for o in obstacles if o["x"] + o["frames"][0].get_width() > 0]
        else:
            obstacles.clear()
            obstacle_spawn_timer = 1.0
            spawned_counts = {"BARREL": 0, "BAT": 0}
            obstacle_spawn_kind = "BARREL"

        
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

        
        if level == 0:
            for obs in obstacles:
                screen.blit(obs["frames"][obs["frame"]], (int(obs["x"]), int(obs["y"])))

        
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

        
        win_popup_cx = WIN_POPUP_X + WIN_POPUP_SIZE[0] // 2
        win_popup_cy = WIN_POPUP_Y + WIN_POPUP_SIZE[1] // 2
        player_cx = player_x + PLAYER_SIZE[0] // 2
        player_cy = player_y + PLAYER_SIZE[1] // 2
        win_distance = math.hypot(player_cx - win_popup_cx, player_cy - win_popup_cy)
        win_popup_active = (
            level == 2 and not game_over and not win_ending
            and win_distance <= WIN_TRIGGER_DISTANCE
        )

        if win_popup_active:
            popup_rect = pygame.Rect(WIN_POPUP_X, WIN_POPUP_Y, *WIN_POPUP_SIZE)
            pygame.draw.rect(screen, (0, 0, 0), popup_rect.move(7, 7))
            pygame.draw.rect(screen, (255, 255, 255), popup_rect)
            pygame.draw.rect(screen, (20, 20, 20), popup_rect, 5)
            key_box = pygame.Rect(WIN_POPUP_X + 10, WIN_POPUP_Y + 10, 52, WIN_POPUP_SIZE[1] - 20)
            pygame.draw.rect(screen, (30, 30, 30), key_box)
            z_label = win_key_font.render("Z", True, (255, 255, 255))
            screen.blit(z_label, z_label.get_rect(center=key_box.center))
            prompt = win_popup_font.render("Selamatkan adikmu", True, (20, 20, 20))
            screen.blit(prompt, (WIN_POPUP_X + 72, WIN_POPUP_Y + (WIN_POPUP_SIZE[1] - prompt.get_height()) // 2))

        if win_ending:
            shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 190))
            screen.blit(shade, (0, 0))
            if win_image is not None:
                screen.blit(win_image, win_image.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
            else:
                win_text = font.render("SELAMAT! ADIK BERHASIL DISELAMATKAN", True, (255, 255, 255))
                screen.blit(win_text, win_text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))

        if level == 1 and boss_phase in ("OPEN", "CLOSED"):
            pulse = (math.sin(pygame.time.get_ticks() / 350.0) + 1.0) / 2.0
            alpha = int(28 + pulse * 30)  
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
            
            shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 175))
            screen.blit(shade, (0, 0))

            if gameover_image is not None:
                
                                screen.blit(
                    gameover_image,
                    gameover_image.get_rect(
                        center=(SCREEN_W // 2, SCREEN_H // 2)
                    )
                )
            else:
                title = font.render("GAME OVER", True, (255, 50, 50))
                screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 70)))

            
            blink_on = (pygame.time.get_ticks() // 450) % 2 == 0
            prompt_color = (255, 35, 35) if blink_on else (150, 0, 0)
            prompt = pygame.font.SysFont("Arial", 38, bold=True).render(
                "Menu - ESC     /     Replay - R", True, prompt_color
            )
            screen.blit(prompt, prompt.get_rect(center=(SCREEN_W // 2, GAMEOVER_PROMPT_Y)))
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
