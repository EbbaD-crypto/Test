import cv2, numpy as np
from pencil import pencilize
f = cv2.imread('ill/globe_fill.png', cv2.IMREAD_UNCHANGED); l = cv2.imread('ill/globe_line.png', cv2.IMREAD_UNCHANGED)
f = cv2.cvtColor(f, cv2.COLOR_BGRA2RGBA); l = cv2.cvtColor(l, cv2.COLOR_BGRA2RGBA)
o = pencilize(f, l)
bg = cv2.cvtColor(cv2.imread('base_names.png'), cv2.COLOR_BGR2RGB)[300:300+o.shape[0]//1, 300:300+o.shape[1]].astype(np.float32)/255
bg = cv2.resize(cv2.cvtColor(cv2.imread('base_names.png'), cv2.COLOR_BGR2RGB), (o.shape[1], o.shape[0])).astype(np.float32)/255
# multiply-ish blend: pigment over paper
res = bg * (1 - o[...,3:]) + (o[...,:3] * bg ** 0.3) * o[...,3:]
cv2.imwrite('test_pencil.png', cv2.cvtColor((cv2.resize(res,(o.shape[1]//2,o.shape[0]//2),interpolation=cv2.INTER_AREA)*255).astype(np.uint8), cv2.COLOR_RGB2BGR))
