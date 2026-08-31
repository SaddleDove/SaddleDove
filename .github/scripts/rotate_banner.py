#!/usr/bin/env python3
"""Pick today's profile banner (seasonal rules + weighted pool) and update README if changed.

Runs daily via GitHub Actions (UTC 16:00 = 00:00 Asia/Shanghai). The image URL changes
with the filename, which busts GitHub's camo image cache on every switch.
"""
import datetime
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
README = ROOT / "README.md"

# Seasonal overrides win over the pool.
SEASONAL = [
    (lambda d: d.month == 6, "neon-pride.png"),                                   # June — pride
    (lambda d: d.month == 10 and d.day >= 25, "pumpkin-duel.png"),                # Oct 25–31 — halloween week
    (lambda d: d.month == 12 and 21 <= d.day <= 27, "aurora-duel.png"),           # Dec 21–27 — winter solstice week
    (lambda d: d.month == 4 and d.day == 22, "watch-over-earth.png"),             # Apr 22 — earth day
]
# Default pool; star-chart is the hidden rare one (5%).
POOL = [
    ("red-sun-duel.png", 40),
    ("space-cowboy.png", 40),
    ("watch-over-earth.png", 15),
    ("star-chart-duel.png", 5),
]


def fnv1a(text):
    h = 2166136261
    for ch in text.encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def pick(day):
    for test, filename in SEASONAL:
        if test(day):
            return filename
    seed = fnv1a(f"{day.year}-{day.month}-{day.day}")
    total = sum(weight for _, weight in POOL)
    r = seed % total
    acc = 0
    for filename, weight in POOL:
        acc += weight
        if r < acc:
            return filename
    return POOL[0][0]


def main():
    # Asia/Shanghai (UTC+8, no DST)
    day = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date()
    chosen = pick(day)
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(r'src="(?:banners?/)?[^"]+\.png"')
    new_text, n = pattern.subn(f'src="banners/{chosen}"', text)
    if n == 0:
        raise SystemExit("banner <img> line not found in README")
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        print(f"banner -> {chosen}")
    else:
        print(f"banner unchanged ({chosen})")


if __name__ == "__main__":
    main()
