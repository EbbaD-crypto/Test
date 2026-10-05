import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import cv2, numpy as np, subprocess
from archive import *
W, H, FPS = 1080, 1920, 24
S = 0.9
bgr = lambda im: np.ascontiguousarray(im[..., ::-1]).astype(np.float32)
desk = cv2.resize(bgr(background()), (W, H)) * np.array([0.58, 0.64, 0.72], np.float32)
def M_page(cx, cy, rot):
    M = cv2.getRotationMatrix2D((540, 675), rot, S); M[0, 2] += cx - 540; M[1, 2] += cy - 675; return M
ONE = np.ones((1350, 1080), np.float32)
def lay(c, img, M, shadow=0.22):
    wa = cv2.warpAffine(ONE, M, (W, H)); wi = cv2.warpAffine(img, M, (W, H))
    sh = cv2.GaussianBlur(np.roll(wa, (3, 2), (0, 1)), (0, 0), 2.0) * shadow
    c *= (1 - sh[..., None]); c[:] = c * (1 - wa[..., None]) + wi
# pull sequence: tugs of uneven length, a tiny sideways wiggle, like a hand pulling
PULLS = [0, 0, 40, 95, 120, 190, 250, 265, 330, 380]
WIG = [0, 0, 0.6, -0.4, 0.3, -0.5, 0.4, 0, -0.2, 0]
rng = np.random.default_rng(7)
seqs = [[bgr(cover2())]]
for i, t in enumerate(NAMES):
    n = i + 1
    card = make_card(n, *t[:5]); front = decorate_front(make_front(n), n)
    base_rot = 2.5 if n % 2 else 1.5
    seqs.append([bgr(name_card2(n, *t, pull=p, card=card, front=front, rot=base_rot + w)) for p, w in zip(PULLS, WIG)])
    print('rendered', t[0], flush=True)
poses = [(W / 2 + rng.normal(0, 8), H / 2 + rng.normal(0, 8), rng.normal(0, 1.3)) for _ in seqs]; poses[0] = (W / 2, H / 2, 0)
frames = []
def emit(c, k=2):
    for _ in range(k): frames.append(c)
placed = []
for k, seq in enumerate(seqs):
    cx, cy, rot = poses[k]
    under = desk.copy()
    for img, PM in placed: lay(under, img, PM)
    if k:  # new spread slid onto the pile by hand
        for d, rj in [(1.0, 9), (0.55, 5), (0.22, 2.5), (0.06, 0.8)]:
            c = under.copy(); lay(c, seq[0], M_page(cx + d * 1150, cy + d * 160, rot + rj)); emit(c)
    M = M_page(cx, cy, rot)
    for j, img in enumerate(seq):
        c = under.copy(); lay(c, img, M); emit(c, 2 if j else 6)
    emit(c, int(FPS * (1.6 if k else 1.3)))
    placed.append((seq[-1], M))
emit(frames[-1], 12)
proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', '/home/user/Test/carousel/reel_5_boy_names.mp4'],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
fr = np.random.default_rng(11)
for i, c in enumerate(frames):
    if i % 2 == 0: j = fr.normal(0, 1.3, 2); g = 1 + fr.normal(0, 0.018)
    out = cv2.warpAffine(c, np.float32([[1, 0, j[0]], [0, 1, j[1]]]), (W, H), borderMode=cv2.BORDER_REFLECT) * g
    proc.stdin.write((np.clip(out, 0, 1) * 255).astype(np.uint8).tobytes())
proc.stdin.close(); proc.wait(); print(len(frames) / FPS)
