import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import cv2, numpy as np, subprocess
from mock import background
FPS, W, H = 30, 1080, 1920
D = '/home/user/Test/carousel/'
slides = [cv2.imread(D + f + '.png') for f in ['01_omslag','02_Alessio','03_August','04_Amir','05_Atlas','06_Arthur']]
# table under the cards: same album paper, slightly darker
bgp = (background() * 255).astype(np.uint8)[..., ::-1]
table = cv2.resize(bgp, (W, int(bgp.shape[0] * W / bgp.shape[1]) * 2))[:H]
table = cv2.resize(bgp, (int(1350 * H / 1350 * 1080 / 1350 * 1350 / 1080), H))
table = cv2.resize(bgp, (W, H)).astype(np.float32) * 0.88
def ease(t): return 1 - (1 - t) ** 3
def card(img, scale, rot, cx, cy, canvas, shadow=True):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    warped = cv2.warpAffine(img.astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
    mask = cv2.warpAffine(np.ones((h, w), np.float32), M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
    if shadow:
        sh = cv2.GaussianBlur(np.roll(mask, (6, 3), (0, 1)), (0, 0), 7)[..., None] * 0.3
        canvas *= (1 - sh)
    return canvas * (1 - mask) + warped * mask
HOLD, IN = 2.0, 0.55
frames = []
total = int((len(slides) * (HOLD + IN) + 0.8) * FPS)
rng = np.random.default_rng(1); rots = rng.uniform(-2.5, 2.5, len(slides)); rots[0] = 0
proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', D + 'reel_5_boy_names.mp4'],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
for f in range(total):
    t = f / FPS
    cv = table.copy()
    seg = HOLD + IN
    k = min(int(t // seg), len(slides) - 1)
    for i in range(k + 1):
        local = t - i * seg
        p = ease(min(max(local / IN, 0), 1)) if i > 0 else 1
        # slow push-in while the top card is held
        zoom = 0.96 + 0.025 * min(max((local - IN) / HOLD, 0), 1) if i == k else 0.96
        cy = H / 2 + (1 - p) * H * 0.9
        rot = rots[i] + (1 - p) * 6
        cv = card(slides[i], zoom, rot, W / 2, cy, cv)
    proc.stdin.write(np.clip(cv, 0, 255).astype(np.uint8).tobytes())
proc.stdin.close(); proc.wait()
print('frames', total)
