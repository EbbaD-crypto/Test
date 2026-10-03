import sys; sys.path.insert(0,'.'); sys.path.insert(0,'v3')
from mock import *
def bird(i, width, mute=0.3):
    rgb, a = scaled(i, width)
    g = rgb.mean(-1, keepdims=True)
    rgb = rgb * (1 - mute) + g * mute                      # desaturate
    rgb = rgb * np.array([1.0, 0.96, 0.88]) * 0.97          # age / warm like old print
    return np.clip(rgb, 0, 1), a
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
    b_rgb, b_a = bird(10, 330); place(cv, b_rgb, b_a, 70, 760, -8, shadow=0.22)
    postmark(cv, 190, 1210, 'ATHENS', '21.V.26', rot=-12, color='#4b3f3a', seed=7)
    save(finish(cv.img, 4), 'v3/mock_atlas_bird2.png')
atlas_bird()
