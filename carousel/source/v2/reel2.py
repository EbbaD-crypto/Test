import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import cv2, numpy as np, subprocess
from mock import scaled
from bird import bird
from final import close_bird
FPS, W, H = 30, 1080, 1920
D = '/home/user/Test/carousel/'
pages = [cv2.imread(D + f + '.png').astype(np.float32) / 255 for f in ['01_omslag','02_Alessio','03_August','04_Amir','05_Atlas','06_Arthur']]
PW, PH = 1000, 1250
pages = [cv2.resize(p, (PW, PH), interpolation=cv2.INTER_AREA) for p in pages]
PX, PY = (W - PW) // 2 + 20, (H - PH) // 2
# table: kraft/linen under the book, darker
from mock import background
bgp = background()[..., ::-1].astype(np.float32)
tab = cv2.resize(bgp, (W, H)) * np.array([0.62, 0.68, 0.74], np.float32)  # darker, warm desk tone (BGR)
# book block: page edges stacked on the right/bottom
def base():
    c = tab.copy()
    sh = np.zeros((H, W), np.float32); cv2.rectangle(sh, (PX - 6, PY - 4), (PX + PW + 14, PY + PH + 16), 1, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 14) * 0.35; c *= (1 - sh[..., None])
    for i in range(8, 0, -1):  # page edges
        col = np.array([0.86, 0.9, 0.93]) * (0.92 + 0.01 * i)
        cv2.rectangle(c, (PX + i, PY + i), (PX + PW + i, PY + PH + i), col.tolist(), -1)
    cv2.line(c, (PX - 2, PY), (PX - 2, PY + PH), (0.2, 0.25, 0.3), 3)  # spine
    return c
BASE = base()
gx, gy = np.meshgrid(np.arange(PW, dtype=np.float32), np.arange(PH, dtype=np.float32))
def turned(page, t):
    """page rotating about its left edge (spine); t 0..1 -> 0..180deg. returns rgb, alpha in page box (may extend)"""
    th = t * np.pi
    c = np.cos(th)
    if abs(c) < 0.02: return None, None, 0
    # destination x' = x*cos, with perspective: far edge grows vertically as it lifts
    lift = np.sin(th)
    xs = gx / max(abs(c), 1e-3)                     # source x for dest x
    k = 1 + 0.10 * lift * (gx / PW)                 # vertical stretch towards the free edge
    ys = (gy - PH / 2) / k + PH / 2
    src = page if c > 0 else np.full_like(page, 0.0) + np.array([0.80, 0.86, 0.90])  # back of page: plain paper
    if c < 0: src = cv2.flip(page, 1) * 0.15 + src * 0.85  # faint show-through
    xs = xs.astype(np.float32); ys = ys.astype(np.float32); src = src.astype(np.float32)
    rgb = cv2.remap(src, xs, ys, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    a = cv2.remap(np.ones((PH, PW), np.float32), xs, ys, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    shade = 1 - 0.35 * lift * (gx / (PW * abs(c) + 1))[..., None].clip(0, 1)
    rgb = rgb * shade
    if c < 0:  # mirrored to the left of the spine
        rgb, a = cv2.flip(rgb, 1), cv2.flip(a, 1)
        return rgb, a, -1
    return rgb, a, 1
def compose(c, rgb, a, x0):
    x1 = max(x0, 0); x2 = min(x0 + PW, W)
    if x2 <= x1: return
    sl = slice(x1 - x0, x2 - x0)
    A = a[:, sl][..., None]
    c[PY:PY + PH, x1:x2] = c[PY:PY + PH, x1:x2] * (1 - A) + rgb[:, sl] * A
# stop-motion birds
birds = []
for i, bid in enumerate([7, 10, 9, 8]):
    rgb, a = close_bird(bid, 260, seed=i)
    birds.append((np.ascontiguousarray(rgb[..., ::-1]).astype(np.float32), a.astype(np.float32)))
def put_bird(c, rgb, a, cx, cy, rot, sq):
    h, w = a.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1); M[1] *= sq; M[1, 2] += h * (1 - sq) / 2
    M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    r = cv2.warpAffine(rgb * a[..., None], M, (W, H)); aa = cv2.warpAffine(a, M, (W, H))
    sh = cv2.GaussianBlur(np.roll(aa, (14, 10), (0, 1)), (0, 0), 4) * 0.25
    c *= (1 - sh[..., None])
    c[:] = c * (1 - aa[..., None]) + r
HOLD, TURN = 1.6, 0.9
flights = [  # (start time, bird, path start, path end, dur)
    (0.6, 0, (-150, 1500), (1250, 250), 3.0),
    (4.2, 1, (1250, 1700), (-150, 500), 3.2),
    (8.0, 2, (-150, 300), (1250, 1300), 3.0),
    (11.6, 3, (1250, 400), (-150, 1600), 3.0),
]
n = len(pages); total = int((n * HOLD + (n - 1) * TURN + 1.0) * FPS)
proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', D + 'reel_5_boy_names.mp4'],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
rng = np.random.default_rng(3)
for f in range(total):
    t = f / FPS
    c = BASE.copy()
    seg = HOLD + TURN; k = int(t // seg); local = t - k * seg
    k = min(k, n - 1)
    if k < n - 1 and local > HOLD:
        p = (local - HOLD) / TURN; p = p * p * (3 - 2 * p)
        compose(c, pages[k + 1], np.ones((PH, PW), np.float32), PX)   # next page underneath
        if k > 0: pass
        r = turned(pages[k], p)
        if r[0] is not None:
            rgb, a, side = r
            if side == 1: compose(c, rgb, a, PX)
            else: compose(c, rgb, a, PX - PW)
    else:
        compose(c, pages[k], np.ones((PH, PW), np.float32), PX)
    # birds at 10 fps "on twos/threes" with hand-placed jitter
    ts = np.floor(t * 10) / 10
    for st, b, p0, p1, dur in flights:
        if st <= ts <= st + dur:
            u = (ts - st) / dur
            r2 = np.random.default_rng(int(ts * 10) + b * 100)
            cx = p0[0] + (p1[0] - p0[0]) * u + r2.normal(0, 6)
            cy = p0[1] + (p1[1] - p0[1]) * u - 120 * np.sin(np.pi * u) + r2.normal(0, 6)
            flap = 1.0 if int(ts * 10) % 2 == 0 else 0.82
            rot = (-8 if p1[0] > p0[0] else 8) + r2.normal(0, 3)
            rgb, a = birds[b]
            if p1[0] < p0[0]: rgb, a = cv2.flip(rgb, 1), cv2.flip(a, 1)
            put_bird(c, rgb, a, cx, cy, rot, flap)
    proc.stdin.write((np.clip(c, 0, 1)[..., ::-1] * 255).astype(np.uint8).tobytes() if False else (np.clip(c, 0, 1) * 255).astype(np.uint8).tobytes())
proc.stdin.close(); proc.wait(); print(total / FPS)
