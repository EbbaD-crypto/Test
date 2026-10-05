import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import cv2, numpy as np, subprocess
import final
from mock import background
final.NOBIRD[0] = True
pages = [final.cover_card()] + [final.name_card(i + 1, *t) for i, t in enumerate(final.NAMES)]
pages = [p[..., ::-1].astype(np.float32).copy() for p in pages]         # BGR
birds = {k: (np.ascontiguousarray(v[0][..., ::-1]).astype(np.float32), v[1].astype(np.float32), v[2], v[3], v[4]) for k, v in final.BIRDS.items()}
W, H, FPS = 1080, 1920, 24
S = 0.9                                     # page scale on the desk
desk = cv2.resize(background()[..., ::-1].astype(np.float32), (W, H)) * np.array([0.58, 0.64, 0.72], np.float32)
def M_page(cx, cy, rot):
    M = cv2.getRotationMatrix2D((540, 675), rot, S); M[0, 2] += cx - 540; M[1, 2] += cy - 675; return M
def lay(c, img, a, M, shadow=0.22):
    wa = cv2.warpAffine(a, M, (W, H)); wi = cv2.warpAffine(img * a[..., None], M, (W, H))
    sh = cv2.GaussianBlur(np.roll(wa, (3, 2), (0, 1)), (0, 0), 2.0) * shadow
    c *= (1 - sh[..., None]); c[:] = c * (1 - wa[..., None]) + wi
ONE = np.ones((1350, 1080), np.float32)
rng = np.random.default_rng(7)
placed = []                                 # (page idx, M)
final_pose = [(W / 2 + rng.normal(0, 8), H / 2 + rng.normal(0, 8), rng.normal(0, 1.4)) for _ in pages]
final_pose[0] = (W / 2, H / 2, 0.0)
def bird_on(c, k, M, step, nsteps):
    """bird hops in on discrete stop-motion steps, then sits on its spot"""
    rgb, a, bx, by, brot = birds[k]
    tx, ty = M @ np.array([bx, by, 1.0])
    u = min(step / nsteps, 1.0)
    sx, sy = tx - 520 if k % 2 == 0 else tx + 560, ty - 420
    x = sx + (tx - sx) * u; y = sy + (ty - sy) * u - 90 * np.sin(np.pi * u)
    flap = 1.0 if (u >= 1 or step % 2 == 0) else 0.8
    rot = brot + np.degrees(np.arctan2(M[1, 0], M[0, 0])) * -1 + (0 if u >= 1 else (-14 if k % 2 == 0 else 14) * (1 - u))
    h, w = a.shape
    B = cv2.getRotationMatrix2D((w / 2, h / 2), rot, S); B[1] *= flap; B[1, 2] += h * S * (1 - flap) / 2
    B[0, 2] += x - w / 2; B[1, 2] += y - h / 2
    lay(c, rgb, a, B, shadow=0.18 if u >= 1 else 0.12)
frames = []
def emit(c, n=2):   # "on twos": every pose held for 2 frames at 24fps
    for _ in range(n): frames.append(c)
for k in range(len(pages)):
    cx, cy, rot = final_pose[k]
    # page slid in by hand in a few jerky steps
    steps = [(1.0, 9), (0.55, 5), (0.22, 2.5), (0.06, 0.8), (0, 0)] if k else [(0, 0)]
    for d, rj in steps:
        c = desk.copy()
        for pk, PM in placed: lay(c, pages[pk], ONE, PM)
        for pk, PM in placed[-1:]:
            if pk in birds: bird_on(c, pk, PM, 99, 1)
        M = M_page(cx + d * 1150, cy + d * 160, rot + rj)
        lay(c, pages[k], ONE, M)
        emit(c)
    M = M_page(cx, cy, rot); placed.append((k, M))
    base_c = desk.copy()
    for pk, PM in placed: lay(base_c, pages[pk], ONE, PM)
    # bird hops onto the page
    nsteps = 6
    for st in range(1, nsteps + 1):
        c = base_c.copy(); bird_on(c, k, M, st, nsteps); emit(c)
    # hold
    c = base_c.copy(); bird_on(c, k, M, 99, 1)
    emit(c, int(FPS * (1.5 if k else 1.2)))
emit(frames[-1], 12)
proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', '/home/user/Test/carousel/reel_5_boy_names.mp4'],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
fr = np.random.default_rng(11)
for i, c in enumerate(frames):
    if i % 2 == 0:  # camera nudge + exposure flicker change on each held pose
        j = fr.normal(0, 1.3, 2); g = 1 + fr.normal(0, 0.018)
    M = np.float32([[1, 0, j[0]], [0, 1, j[1]]])
    out = cv2.warpAffine(c, M, (W, H), borderMode=cv2.BORDER_REFLECT) * g
    proc.stdin.write((np.clip(out, 0, 1) * 255).astype(np.uint8).tobytes())
proc.stdin.close(); proc.wait(); print(len(frames) / FPS)
