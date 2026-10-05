import numpy as np, cv2
R = np.random.default_rng(7)

def noise(h, w, sigma, rng=R):
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), sigma)
    return (n - n.mean()) / (n.std() + 1e-6)

def hatch(h, w, angle, spacing=5.0, rng=R):
    """colored-pencil strokes: many short parallel strokes with random pressure"""
    img = np.zeros((h, w), np.float32)
    diag = int(np.hypot(h, w)) + 20
    big = np.zeros((diag, diag), np.float32)
    y = 0.0
    while y < diag:
        x = rng.uniform(-40, 0)
        while x < diag:
            L = rng.uniform(25, 90); p = rng.uniform(0.35, 1.0)
            cv2.line(big, (int(x), int(y + rng.normal(0, .8))), (int(x + L), int(y + rng.normal(0, 1.2))), p, int(rng.choice([1, 2, 2, 3])), cv2.LINE_AA)
            x += L + rng.uniform(-10, 8)
        y += spacing * rng.uniform(0.6, 1.3)
    M = cv2.getRotationMatrix2D((diag / 2, diag / 2), angle, 1)
    big = cv2.warpAffine(big, M, (diag, diag))
    oy, ox = (diag - h) // 2, (diag - w) // 2
    return big[oy:oy + h, ox:ox + w]

def tooth(h, w, rng=R):
    """paper tooth: pigment skips the valleys"""
    t = noise(h, w, 0.9, rng) * 0.6 + noise(h, w, 2.5, rng) * 0.4
    return np.clip(0.5 + 0.45 * t, 0, 1)

def wobble(img, amp=2.5, scale=18, rng=R):
    h, w = img.shape[:2]
    dx = noise(h, w, scale, rng) * amp; dy = noise(h, w, scale, rng) * amp
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(img, gx + dx, gy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

def pencilize(fill_rgba, line_rgba, graphite=(58, 52, 50), seed=0):
    """returns float RGBA (0..1) colored-pencil + graphite drawing"""
    rng = np.random.default_rng(seed)
    h, w = fill_rgba.shape[:2]
    fill = wobble(fill_rgba.astype(np.float32) / 255, 2.0, 22, rng)
    line = wobble(line_rgba.astype(np.float32) / 255, 2.2, 14, rng)
    a = fill[..., 3]
    # pencil coverage: hatching + tooth, denser near shape edges
    hz = np.maximum(hatch(h, w, rng.uniform(28, 42), 5.0, rng), hatch(h, w, rng.uniform(-60, -45), 7.0, rng) * 0.55)
    th = tooth(h, w, rng)
    dist = cv2.distanceTransform((a > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    edge = np.clip(1 - dist / 14, 0, 1)
    cov = np.clip(0.38 + 0.55 * hz + 0.35 * (th - 0.5) + 0.3 * edge, 0, 1)
    cov *= np.clip(0.8 + 0.25 * noise(h, w, 40, rng), 0.55, 1.05)   # uneven pressure across the shape
    fa = a * np.clip(cov, 0, 1) * 0.92
    # colors: slightly muted, darker where pressure is heavier
    col = fill[..., :3]
    col = col * (1 - 0.18 * (cov[..., None] - 0.5))
    # graphite lines: grainy, double-pass for sketchiness
    la = line[..., 3]
    la2 = wobble(line_rgba[..., 3].astype(np.float32) / 255, 3.0, 10, rng) * 0.4
    lgrain = np.clip(0.78 + 0.32 * noise(h, w, 0.7, rng) + 0.12 * noise(h, w, 6, rng), 0.2, 1)
    lalpha = np.clip(np.maximum(la, la2) * lgrain, 0, 1)
    lcol = line[..., :3].copy()
    dark = (lcol.mean(-1) < 0.35)[..., None]
    g = np.array(graphite, np.float32) / 255
    lcol = np.where(dark, g, lcol)
    # composite line over fill
    out_a = lalpha + fa * (1 - lalpha)
    out_c = (lcol * lalpha[..., None] + col * (fa * (1 - lalpha))[..., None]) / np.maximum(out_a, 1e-4)[..., None]
    return np.dstack([out_c, out_a])
