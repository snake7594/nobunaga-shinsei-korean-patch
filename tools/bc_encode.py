"""Vectorized BC3 (DXT5) encoder — range-fit, good quality for UI/text graphics."""
import numpy as np

def _to565(c):
    r = (c[:, 0].astype(np.uint16) >> 3) << 11
    g = (c[:, 1].astype(np.uint16) >> 2) << 5
    b = c[:, 2].astype(np.uint16) >> 3
    return r | g | b

def _from565(v):
    r = ((v >> 11) & 31).astype(np.float32) * (255 / 31)
    g = ((v >> 5) & 63).astype(np.float32) * (255 / 63)
    b = (v & 31).astype(np.float32) * (255 / 31)
    return np.stack([r, g, b], axis=1)

def encode_bc3(rgba):
    """rgba: (H, W, 4) uint8, H/W multiples of 4. Returns bytes."""
    H, W, _ = rgba.shape
    nby, nbx = H // 4, W // 4
    blocks = rgba.reshape(nby, 4, nbx, 4, 4).transpose(0, 2, 1, 3, 4).reshape(-1, 16, 4)
    n = blocks.shape[0]
    px_rgb = blocks[:, :, :3].astype(np.float32)
    px_a = blocks[:, :, 3].astype(np.float32)

    # ---- alpha part (BC4): a0 > a1 -> 8-value mode ----
    a0 = px_a.max(1)
    a1 = px_a.min(1)
    flat = a0 == a1
    a0f = np.where(flat, np.minimum(a0 + 1, 255), a0)  # avoid degenerate palette
    pal = np.empty((n, 8), np.float32)
    pal[:, 0] = a0f
    pal[:, 1] = a1
    for k in range(1, 7):
        pal[:, k + 1] = ((7 - k) * a0f + k * a1) / 7
    d = np.abs(px_a[:, :, None] - pal[:, None, :])
    aidx = d.argmin(2).astype(np.uint64)              # (n,16) 3-bit
    abits = np.zeros(n, np.uint64)
    for k in range(16):
        abits |= aidx[:, k] << np.uint64(3 * k)
    alpha_bytes = np.empty((n, 8), np.uint8)
    alpha_bytes[:, 0] = a0f.astype(np.uint8)
    alpha_bytes[:, 1] = a1.astype(np.uint8)
    ab = abits[:, None] >> (np.arange(6, dtype=np.uint64)[None, :] * np.uint64(8))
    alpha_bytes[:, 2:8] = (ab & np.uint64(0xFF)).astype(np.uint8)

    # ---- color part (BC1-style, always 4-color in BC3) ----
    lum = px_rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    imax = lum.argmax(1)
    imin = lum.argmin(1)
    cmax = px_rgb[np.arange(n), imax]
    cmin = px_rgb[np.arange(n), imin]
    c0 = _to565(cmax.astype(np.uint8))
    c1 = _to565(cmin.astype(np.uint8))
    swap = c0 < c1
    c0s = np.where(swap, c1, c0)
    c1s = np.where(swap, c0, c1)
    eq = c0s == c1s
    p0 = _from565(c0s)
    p1 = _from565(c1s)
    cpal = np.stack([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3], axis=1)  # (n,4,3)
    dc = ((px_rgb[:, :, None, :] - cpal[:, None, :, :]) ** 2).sum(3)
    cidx = dc.argmin(2).astype(np.uint32)
    cidx[eq] = 0
    cbits = np.zeros(n, np.uint32)
    for k in range(16):
        cbits |= cidx[:, k] << np.uint32(2 * k)
    color_bytes = np.empty((n, 8), np.uint8)
    color_bytes[:, 0] = (c0s & 0xFF).astype(np.uint8)
    color_bytes[:, 1] = (c0s >> 8).astype(np.uint8)
    color_bytes[:, 2] = (c1s & 0xFF).astype(np.uint8)
    color_bytes[:, 3] = (c1s >> 8).astype(np.uint8)
    for k in range(4):
        color_bytes[:, 4 + k] = ((cbits >> np.uint32(8 * k)) & np.uint32(0xFF)).astype(np.uint8)

    out = np.concatenate([alpha_bytes, color_bytes], axis=1)  # (n,16)
    return out.tobytes()
