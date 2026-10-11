"""Erzeugt ui/icon.ico (Programm- und Installer-Icon) passend zu ui/icon.svg."""
from pathlib import Path

from PIL import Image, ImageDraw

S = 1024
k = S / 64


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


grad = Image.new("RGB", (S, S))
px = grad.load()
c1, c2 = (0x6D, 0x5E, 0xFC), (0xB0, 0x5C, 0xF6)
for y in range(S):
    for x in range(S):
        px[x, y] = lerp(c1, c2, (x + y) / (2 * S))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(16 * k), fill=255)
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
img.paste(grad, (0, 0), mask)
d = ImageDraw.Draw(img)
for x, y, h in [(12, 27, 10), (20.5, 19, 26), (29.5, 12, 40), (38.5, 21, 22), (47, 26, 12)]:
    d.rounded_rectangle([x * k, y * k, (x + 5) * k, (y + h) * k], radius=int(2.5 * k), fill="white")
out = Path(__file__).resolve().parent.parent / "ui" / "icon.ico"
img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.resize((256, 256), Image.LANCZOS).save(out.with_suffix(".png"))
print("geschrieben:", out)
