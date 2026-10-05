import numpy as np, cv2
def patch(img, box, dx, dy, feather=25):
    """copy region box shifted by (dx,dy) source offset onto box with feathered edges"""
    x0,y0,x1,y1 = box
    H,W = img.shape[:2]
    m = np.zeros((H,W),np.float32); cv2.rectangle(m,(x0,y0),(x1,y1),1,-1)
    m = cv2.GaussianBlur(m,(0,0),feather/2.5)
    M = np.float32([[1,0,dx],[0,1,dy]])
    src = cv2.warpAffine(img, M, (W,H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # src(x,y) = img(x-dx... ) -> we want img(x+dx,y+dy)
    src = cv2.warpAffine(img, np.float32([[1,0,-dx],[0,1,-dy]]), (W,H), borderMode=cv2.BORDER_REFLECT)
    return (img*(1-m[...,None]) + src*m[...,None]).astype(np.uint8)

d16 = cv2.imread('src/d16.png')
a = d16.copy()
a = patch(a,(300,290,770,430),0,250)      # Atlas -> copy from below on same sheet
a = patch(a,(500,460,660,515),0,200)      # Someone
a = patch(a,(70,345,205,462),36,150,14)   # cyan heart (left margin strip)
a = patch(a,(80,660,190,775),0,200,18)    # yellow star
a = patch(a,(830,1200,1080,1335),-300,0,20)  # arrow
cv2.imwrite('base_names.png', a)

d15 = cv2.imread('src/d15.png')
b = d15.copy()
cv2.imwrite('tmp.png', b)

def restore_grain(orig, filled, mask, ref_box):
    # add high-frequency grain sampled from a reference area to the inpainted zone
    x0,y0,x1,y1 = ref_box
    ref = orig[y0:y1, x0:x1].astype(np.float32)
    hf = ref - cv2.GaussianBlur(ref,(0,0),3)
    H,W = filled.shape[:2]
    reps = (H//hf.shape[0]+2, W//hf.shape[1]+2, 1)
    tile = np.tile(hf, reps)[:H,:W]
    m = cv2.GaussianBlur(mask.astype(np.float32)/255,(0,0),2)[...,None]
    return np.clip(filled.astype(np.float32) + tile*m, 0, 255).astype(np.uint8)

b = d15.copy()
gray = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
mask = np.zeros(gray.shape, np.uint8)
# title script (dark strokes)
reg = np.zeros_like(mask); cv2.rectangle(reg,(495,465),(905,875),255,-1)
mask |= ((gray < 150) & (reg > 0)).astype(np.uint8)*255
# big white A
reg2 = np.zeros_like(mask); cv2.rectangle(reg2,(335,915),(645,1210),255,-1)
mask |= ((gray > 228) & (reg2 > 0)).astype(np.uint8)*255
mask = cv2.dilate(mask, np.ones((5,5),np.uint8), iterations=2)
filled = cv2.inpaint(b, mask, 7, cv2.INPAINT_TELEA)
filled = restore_grain(b, filled, mask, (560,300,760,460))
# cyan sticker border -> cream paper
hsv = cv2.cvtColor(filled, cv2.COLOR_BGR2HSV)
cy = ((hsv[...,0] > 75) & (hsv[...,0] < 100) & (hsv[...,1] > 120) & (hsv[...,2] > 150)).astype(np.uint8)
cy = cv2.morphologyEx(cy, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
cream = np.array([226,236,242], np.float32)  # BGR off-white
noise = np.random.default_rng(1).normal(0, 3, filled.shape)
f2 = filled.astype(np.float32)
f2[cy>0] = cream + noise[cy>0]
filled = np.clip(f2,0,255).astype(np.uint8)
cv2.imwrite('base_cover.png', filled)
