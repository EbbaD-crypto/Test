import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
from final import *
from comp import paper
opts = [('A', 'SpecialElite', 92), ('B', 'CutiveMono', 100), ('C', 'IMFellEnglishSC', 100), ('D', 'PlayfairDisplaySC', 92), ('E', 'OldStandardTT', 100), ('F', 'LibreCaslonText', 96)]
W, H = 1080, 1350
img = paper('cream', H, W, '#efe4cc', 3)
a = np.ones((H, W), np.float32); a[:4] = a[-4:] = 0; a[:, :4] = a[:, -4:] = 0
img = age(img, a, 5, 0.6)
for i, (k, f, s) in enumerate(opts):
    y = 130 + i * 205
    type_in(img, k, 'CourierPrime', 30, 90, y, seed=i)
    type_in(img, 'Atlas', f, s, 560, y, seed=i + 3, depth=1.2)
    type_in(img, f, 'CourierPrime', 18, 560, y + 75, seed=i + 9)
save(finish(img, 1), '/home/user/Test/brand/typsnitt_namn_val.png')
