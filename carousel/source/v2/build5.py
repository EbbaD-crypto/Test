"""Desk stop-motion reel: a hand lays papers down (they simply appear), then clears them off frame in jerky steps."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
import numpy as np, cv2, subprocess
import build3 as B
from build3 import L, render, W
from build4 import scene, end_scene, FNS
from comp import finish, paper
from aged import age
H, FPS = 1920, 12
# constant desk: darker kraft tabletop
desk = B.scan('src/crumple.jpg', H, 0.3) * np.array([0.72, 0.62, 0.50], np.float32)
def sheetify(bg, seed):
    s = 0.86; sh = cv2.resize(bg, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
    a = np.ones(sh.shape[:2], np.float32); a[:2] = a[-2:] = 0; a[:, :2] = a[:, -2:] = 0
    return age(sh, a, 300 + seed, 0.5), a
def exit_vec(l):
    dx, dy = l.dx, l.dy
    if abs(dx) < 1 and abs(dy) < 1: dx, dy = (1, 0.3) if l.g % 2 else (-1, 0.4)
    v = np.array([dx, dy], np.float32); v = v / np.linalg.norm(v)
    return (float(v[0] * 1900), float(v[1] * 1900))
proc = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '21', '-preset', 'slow', '-r', '24', '-movflags', '+faststart',
    '/home/user/Test/carousel/reel_5_boy_names.mp4'], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
n = [0]
def out(img, hold):
    b = (np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes()
    for _ in range(hold): proc.stdin.write(b); n[0] += 1
out(finish(desk.copy(), 0), 6)                       # empty desk first
scenes = FNS + [end_scene]
for si, fn in enumerate(scenes):
    bg, layers, ex = scene(fn, H) if fn is not end_scene else end_scene(H)
    s_rgb, s_a = sheetify(bg, si)
    rot = [-1.5, 1.2, -0.8, 1.6, -1.2, 0.9, 0][si]
    for l in layers: l.g += 1
    layers.insert(0, L(s_rgb, s_a, 0, 0, rot, g=0, frm=(0, 0)))
    def ex2(cv, H_, ex=ex, show=[True]):
        if show[0]: ex(cv, H_)
    G = max(l.g for l in layers)
    last = fn is end_scene
    # lay down: each group simply appears
    for g in range(G + 1):
        img = finish(render(desk, layers, g, 0.0, H, ex2 if g >= 1 else None), si)
        out(img, 3 if g < G else (18 if not last else 30))
    if last: break
    # clear away in three waves: small things, the main pieces, the sheet
    for l in layers:
        if l.g >= 3: l.g = 3
    G = min(G, 3)
    for g in range(G, -1, -1):
        for l in layers:
            if l.g == g: l.frm = exit_vec(l)
        out(finish(render(desk, layers, g, 0.35, H, ex2 if g >= 1 else None), si), 2)
        out(finish(render(desk, layers, g - 1, 0.0, H, ex2 if g - 1 >= 1 else None), si) if g > 0 else finish(desk.copy(), si), 2)
proc.stdin.close(); proc.wait(); print('reel s', n[0] / FPS)
