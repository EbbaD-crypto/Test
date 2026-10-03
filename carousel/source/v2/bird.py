import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
from mock import *
def bird(i, width, mute=0.3):
    rgb, a = scaled(i, width)
    g = rgb.mean(-1, keepdims=True)
    rgb = rgb * (1 - mute) + g * mute                      # desaturate
    rgb = rgb * np.array([1.0, 0.96, 0.88]) * 0.97          # age / warm like old print
    return np.clip(rgb, 0, 1), a
def cut_bird(i, width, seed=3):
    rgb, a = bird(i, width)
    pad = 30
    rgb = np.pad(rgb, ((pad, pad), (pad, pad), (0, 0)), constant_values=1); a = np.pad(a, pad)
    h, w = a.shape
    # hand-cut paper margin: uneven width, straight scissor snips
    m = scissor(a, pad=11, eps=4.5, seed=seed)
    edge = paper('cream', h, w, '#f3ecdc', seed)
    # paper fibre: slightly darker rim where the scissors cut, faint grain on the print
    rim = np.clip(m - cv2.erode(m, np.ones((3, 3), np.uint8)), 0, 1)[..., None]
    edge = edge * (1 - 0.12 * rim)
    grain = paper('cream', h, w, None, seed + 1).mean(-1, keepdims=True)
    pig = rgb * np.clip(grain / grain.mean(), 0.9, 1.08)
    out = edge * (1 - a[..., None]) + pig * a[..., None]
    # slight curl: one side lifts a little lighter
    yy, xx = np.mgrid[0:h, 0:w]
    out = out * (0.97 + 0.04 * (xx / w))[..., None]
    return np.clip(out, 0, 1), np.maximum(m, a)

def atlas_bird():
    cv = Canvas(background())
    d_rgb, d_a = scaled(1, 700); place(cv, d_rgb, d_a, 30, 70, -4)
    f_rgb, f_a = scaled(2, 690)
    ink_local(f_rgb, 'Nº 4 / 5', 'SpecialElite', 34, 470, 110, INK, 1, bleed=0.3, grain=0.08)
    ink_local(f_rgb, 'Atlas', 'IMFellEnglish', 165, 345, 410, INK, 2, bleed=0.4, grain=0.08, op=1)
    ink_local(f_rgb, 'English:  [ˈætləs]', 'Gentium-Italic', 44, 345, 535, INK, 3, bleed=0.3, grain=0.06, op=1)
    ink_local(f_rgb, 'A name from Greek mythology,', 'SpecialElite', 29, 345, 635, INK, 4, bleed=0.3, grain=0.08, op=1)
    ink_local(f_rgb, 'possibly meaning “to endure.”', 'SpecialElite', 29, 345, 677, INK, 5, bleed=0.3, grain=0.08, op=1)
    para_local(f_rgb, 'Someone with the courage to meet the unfamiliar and the tenderness to understand it.',
               'IMFellEnglish-Italic', 40, 345, 775, 560, 52, '#4a3a32', 6, bleed=0.3, grain=0.06, op=1)
    place(cv, f_rgb, f_a, 290, 300, 3.5)
    b_rgb, b_a = cut_bird(10, 330); place(cv, b_rgb, b_a, 50, 740, -8, shadow=0.42)
    tape(cv, 300, 800, 80, 30, 38, '#e8dcc0', seed=9, alpha=0.55)
    postmark(cv, 190, 1210, 'ATHENS', '21.V.26', rot=-12, color='#4b3f3a', seed=7)
    save(finish(cv.img, 4), 'v3/mock_atlas_bird3.png')
atlas_bird()
