import sys; sys.path.insert(0, '.')
from comp import *
P = PAL
base = rd('base_names.png')

def tag(cv, text, x, y, kind='kraft', color=None, seed=0, rot=-2):
    piece(cv, kind, [[x, y], [x + 175, y - 6], [x + 178, y + 52], [x + 2, y + 58]], color, seed=seed, edge='cut')
    write(cv, text, 'SpecialElite', 30, x + 89, y + 26, P['ink'], rot=rot, typewriter=True, seed=seed)

def name_slide(n, d):
    flip = d.get('flip', False)
    cv = Canvas(base[:, ::-1].copy() if flip else base)
    cx = 490 if flip else 590
    tag(cv, f'Nº {n} / 5', 860 if flip else 62, 64, seed=n)
    # the name, cut from coloured papers
    first, rest = d['papers']
    papers = [first] + [rest[0]] * (len(d['name']) - 1)
    cut_word(cv, d['name'], 'IMFellEnglish', d.get('size', 170), cx, 470, papers, seed=n * 3, track=6, rot_amp=2.5)
    # pronunciation typed on a torn slip
    sw = 540 if len(d['lang'] + d['ipa']) > 16 else 470
    piece(cv, 'cream', [[cx - sw / 2, 522], [cx + sw / 2, 507], [cx + sw / 2 + 6, 592], [cx - sw / 2 + 4, 606]], d['slip'], seed=8 + n)
    write(cv, f"{d['lang']}:  {d['ipa']}", 'Gentium-Italic', 44, cx + 2, 557, P['ink'], rot=-1.5, seed=2 + n, bleed=0.5, grain=0.18)
    # origin as typed paper strips
    y = 650
    for i, line in enumerate(d['origin']):
        f = ImageFont.truetype(F('SpecialElite'), 27); lw = f.getlength(line) + 46
        off = [-60, 50, -20][i % 3]
        x0 = cx + off - lw / 2
        piece(cv, 'cream', [[x0, y + 2], [x0 + lw, y - 3], [x0 + lw + 2, y + 52], [x0 + 1, y + 55]], '#f7f1e3', seed=20 + n * 5 + i, edge='cut')
        write(cv, line, 'SpecialElite', 27, cx + off, y + 26, P['ink'], rot=[-1.2, 0.7, -0.4][i % 3], typewriter=True, seed=30 + n * 5 + i)
        y += 64
    # meaning handwritten in ink, straight onto the old sheet
    paragraph(cv, d['meaning'], 'HomemadeApple', 29, cx + 10, y + 70, 690, 64, '#2f2a3a', rot=-2.5, seed=40 + n, bleed=0.45, grain=0.3)
    for fn in d['extras']: fn(cv)
    if n < 5:
        cutout(cv, 'src/d15.png', (840, 1210, 1045, 1325), 120 if flip else 960, 1280, 0.8, rot=-3)
    else:
        piece(cv, 'kraft', [[575, 1262], [780, 1254], [784, 1322], [578, 1328]], None, seed=77, edge='cut')
        write(cv, 'save ♡' if False else 'save for later', 'HomemadeApple', 24, 680, 1292, P['ink'], rot=-2, seed=78)
    save(finish(cv.img, n), f'out_{n + 1}.png')

R = lambda c: ('cream', c)
slides = [
 dict(name='Alessio', lang='Italian', ipa='[aˈlɛssjo]', slip=P['butter'],
      papers=(('stripes', (P['blush'], P['roseDeep'])), [R(P['dove']), R(P['rose'])]),
      origin=['From Greek alexō, meaning', '“to defend or help.”'],
      meaning='Someone whose quiet strength makes others feel safe enough to be themselves.',
      extras=[lambda cv: sticker(cv, 'lemons', 905, 205, 230, rot=-8, seed=1),
              lambda cv: sticker(cv, 'train', 210, 1210, 270, rot=5, seed=2),
              lambda cv: stamp(cv, 900, 1135, 140, 172, 'plane', P['roseDeep'], 'POSTE ITALIANE', '5', rot=7, seed=3),
              lambda cv: postmark(cv, 880, 1060, 'ROMA', '12.IV.26', rot=-12, seed=4),
              lambda cv: cutout(cv, 'src/d15.png', (140, 95, 385, 410), 120, 360, 0.55, rot=-14)]),
 dict(name='August', lang='English', ipa='[ˈɔːɡəst]', slip=P['blush'], flip=True,
      papers=(('stripes', (P['butter'], P['chestnut'])), [R(P['rose']), R(P['butter'])]),
      origin=['From Latin Augustus, meaning', '“venerable” or “exalted.”'],
      meaning='Someone who sees the good in others and gives it room to grow.',
      extras=[lambda cv: sticker(cv, 'balloon', 180, 230, 190, rot=-6, seed=5),
              lambda cv: sticker(cv, 'suitcase', 870, 1215, 250, rot=-5, seed=6),
              lambda cv: stamp(cv, 175, 1120, 140, 172, 'compass', P['doveDeep'], 'POSTAGE', '2d', rot=-6, seed=7),
              lambda cv: postmark(cv, 230, 1050, 'LONDON', '03.VIII.26', rot=8, seed=8),
              lambda cv: cutout(cv, 'src/d15.png', (880, 670, 1040, 800), 950, 330, 0.75, rot=10)]),
 dict(name='Amir', lang='Arabic', ipa='[ʔaˈmiːr]', slip=P['dove'], 
      papers=(('stripes', (P['blush'], P['chestnut'])), [R(P['butter']), R(P['dove'])]),
      origin=['From Arabic amīr, meaning', '“prince” or “commander.”'],
      meaning='Someone who makes others feel they belong, wherever they come from.',
      extras=[lambda cv: sticker(cv, 'crown', 900, 215, 210, rot=9, seed=9),
              lambda cv: sticker(cv, 'compass', 200, 1200, 200, rot=-10, seed=10),
              lambda cv: sticker(cv, 'map', 900, 1150, 230, rot=6, seed=11),
              lambda cv: cutout(cv, 'src/d15.png', (310, 490, 410, 590), 130, 365, 0.9, rot=-8),
              lambda cv: cutout(cv, 'src/d15.png', (830, 285, 930, 380), 1010, 980, 0.7, rot=12)]),
 dict(name='Atlas', lang='English', ipa='[ˈætləs]', slip=P['butter'], flip=True, 
      papers=(('stripes', (P['dove'], P['doveDeep'])), [R(P['rose']), R(P['cream'])]),
      origin=['A name from Greek mythology,', 'possibly meaning “to endure.”'],
      meaning='Someone with the courage to meet the unfamiliar and the tenderness to understand it.',
      extras=[lambda cv: sticker(cv, 'globe', 175, 245, 200, rot=-7, seed=12),
              lambda cv: sticker(cv, 'plane', 860, 1210, 250, rot=-12, seed=13),
              lambda cv: stamp(cv, 185, 1135, 140, 172, 'sailboat', P['chestnut'], 'HELLAS', '10', rot=-5, seed=14),
              lambda cv: postmark(cv, 245, 1060, 'ATHENS', '21.V.26', rot=10, seed=15),
              lambda cv: cutout(cv, 'src/d13.png', (148, 165, 292, 310), 960, 330, 0.6, rot=8)]),
 dict(name='Arthur', lang='British English', ipa='[ˈɑːθə]', slip=P['blush'],
      papers=(('stripes', (P['blush'], P['roseDeep'])), [R(P['dove']), R(P['butter'])]),
      origin=['A name of debated origin, possibly', 'connected with the Celtic', 'word for “bear.”'],
      meaning='Someone who notices what others feel, even when they cannot find the words.',
      extras=[lambda cv: sticker(cv, 'bear', 905, 215, 180, rot=7, seed=16),
              lambda cv: sticker(cv, 'sailboat', 205, 1205, 230, rot=-5, seed=17),
              lambda cv: stamp(cv, 910, 1185, 140, 172, 'train', P['doveDeep'], 'POSTAGE', '1d', rot=6, seed=18),
              lambda cv: postmark(cv, 870, 1120, 'LONDON', '09.IX.26', rot=-10, seed=19),
              lambda cv: cutout(cv, 'src/d13.png', (195, 985, 295, 1080), 120, 370, 0.8, rot=-10)]),
]

def cover():
    cv = Canvas(rd('base_cover.png'))
    # handwritten title on the tracing paper
    write(cv, '5', 'IMFellEnglish', 120, 700, 435, P['ink'], rot=-3, seed=1, bleed=0.5, grain=0.2)
    for i, l in enumerate(['Boy Names', 'for Little', 'Globetrotters']):
        write(cv, l, 'HomemadeApple', 46, 705 - i * 4, 560 + i * 80, '#2f2a3a', rot=-4, seed=2 + i, bleed=0.45, grain=0.28)
    # folklore initial: cut striped paper + colored-pencil wreath drawn round it
    sticker(cv, 'wreath', 480, 1040, 480, rot=0, seed=3, border=False)
    cut_word(cv, 'A', 'IMFellEnglish', 420, 480, 1215, [('stripes', (P['blush'], P['roseDeep']))], seed=5, rot_amp=2)
    # travel ephemera
    sticker(cv, 'globe', 905, 1000, 190, rot=8, seed=7)
    sticker(cv, 'train', 560, 105, 220, rot=-4, seed=8)
    stamp(cv, 925, 505, 120, 148, 'balloon', P['roseDeep'], 'PAR AVION', '5', rot=8, seed=9)
    postmark(cv, 900, 400, 'PARIS', '2026', rot=-14, seed=10, r=54)
    save(finish(cv.img, 0), 'out_1.png')

if __name__ == '__main__':
    which = sys.argv[1:] or ['c', '1', '2', '3', '4', '5']
    for w in which:
        if w == 'c': cover()
        else: name_slide(int(w), slides[int(w) - 1])
