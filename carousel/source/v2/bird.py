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
    ink_local(f_rgb, 'Nº 4 / 5', 'SpecialElite', 30, 470, 110, BR, 1, typewriter=True)
    ink_local(f_rgb, 'Atlas', 'IMFellEnglish', 150, 345, 420, INK, 2, bleed=0.6, grain=0.2)
    ink_local(f_rgb, 'English:  [ˈætləs]', 'Gentium-Italic', 36, 345, 540, BR, 3, bleed=0.4, grain=0.15)
    ink_local(f_rgb, 'A name from Greek mythology,', 'SpecialElite', 24, 345, 650, BR, 4, typewriter=True)
    ink_local(f_rgb, 'possibly meaning “to endure.”', 'SpecialElite', 24, 345, 686, BR, 5, typewriter=True)
    para_local(f_rgb, 'Someone with the courage to meet the unfamiliar and the tenderness to understand it.',
               'HomemadeApple', 25, 345, 790, 520, 56, PEN, 6, bleed=0.4, grain=0.45, op=0.8)
    place(cv, f_rgb, f_a, 290, 300, 3.5)
    b_rgb, b_a = bird(10, 330); place(cv, b_rgb, b_a, 70, 760, -8, shadow=0.22)
    postmark(cv, 190, 1210, 'ATHENS', '21.V.26', rot=-12, color='#4b3f3a', seed=7)
    save(finish(cv.img, 4), 'v3/mock_atlas_bird.png')
atlas_bird()
