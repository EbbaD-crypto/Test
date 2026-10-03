import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
from archive import *
import cv2, numpy as np
R = '/home/user/Test/brand/referenser/'
def scan(name):
    im = cv2.imread(R + name)[..., ::-1].astype(np.float32) / 255
    h, w = im.shape[:2]; th = int(w * 1350 / 1080)       # crop to 4:5
    y0 = (h - th) // 2
    return cv2.resize(im[y0:y0 + th], (1080, 1350), interpolation=cv2.INTER_AREA)
# A: folder + card on the torn pink/grey/kraft collage
a = name_card2(4, *NAMES[3], bg=scan('rivet_papper_1.jpg'), divider=False)
save(a, '/home/user/Test/carousel/test_rivet_A_Atlas.png')
# B: loose card lying on the confetti tracing paper, pattern paper strip tucked under
bg = scan('rivet_papper_3_konfetti.jpg'); cv = Canvas(bg)
pat = scan('monster_blomkors.jpg')[200:1150, 150:930]; pa = np.ones(pat.shape[:2], np.float32)
from comp import torn as torn_edge
pa = torn_edge(np.pad(pa[6:-6, 6:-6], 6), 6, 2.0, 4)
flatplace(cv, pat, pa, 140, 160, -5)
card = make_card(4, *NAMES[3][:5], color='#e7b6a8')
flatplace(cv, card, CARD_A, 240, 300, 3)
save(finish(cv.img, 4), '/home/user/Test/carousel/test_rivet_B_Atlas.png')
