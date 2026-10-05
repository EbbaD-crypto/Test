import cv2, numpy as np, sys
def cut_white(path, out, thr=238):
    im = cv2.imread(path); h, w = im.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flood = im.copy()
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if im[seed[1], seed[0]].min() > thr:
            cv2.floodFill(flood, mask, seed, (0, 0, 0), (12, 12, 12), (12, 12, 12), cv2.FLOODFILL_MASK_ONLY | (255 << 8) | 8)
    bg = mask[1:-1, 1:-1] > 0
    a = (~bg).astype(np.uint8) * 255
    a = cv2.erode(a, np.ones((3, 3), np.uint8)); a = cv2.GaussianBlur(a, (0, 0), 0.8)
    cv2.imwrite(out, np.dstack([im, a]))
for i in [2, 5]:
    cut_white(f'../../images/{i}.jpg', f'v3/a{i}.png')
