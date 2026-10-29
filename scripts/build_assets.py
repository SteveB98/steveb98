#!/usr/bin/env python3
"""Build the animated SVGs used by the profile README.

Writes assets/header-{dark,light}.svg, assets/levels-{dark,light}.svg and
assets/divider.svg.
DM Sans is pinned to fixed weights, subset to the glyphs used, and embedded
as base64 WOFF2 so the banner renders on-brand without any network fetch
(GitHub serves README images through camo, which blocks external fonts).

Needs fonttools + brotli:  python -m venv .venv && .venv/bin/pip install fonttools brotli
Run:                       .venv/bin/python scripts/build_assets.py
"""
import base64
import io
import random
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONT = Path.home() / ".local/share/fonts/edgecraft/DMSans.ttf"
OUT = ROOT / "assets"

W, H = 1200, 320
X0 = 64

TITLE = "steve berg"
KICKER = "SIDE A: CODE  /  SIDE B: SOUND"
PROMPT = "›"  # single right angle quote, used as a prompt glyph
PHRASES = [
    "building fast websites at EdgeCraft Digital",
    "producing music between commits",
    "automating the boring parts",
    "mixing code and sound since UVic",
    "ricing Arch + Hyprland for fun",
]
REGIONS = [  # timeline lane: (label, x, width, kind)
    ("react.tsx", 64, 150, "code"),
    ("kick.wav", 222, 110, "sound"),
    ("workers.js", 340, 160, "code"),
    ("bass.mid", 508, 120, "sound"),
    ("astro.config", 636, 170, "code"),
    ("vox_take3.wav", 814, 180, "sound"),
    ("deploy.sh", 1002, 134, "code"),
]

LEVELS = [  # (value, label, meter level 0..1); numbers match edgecraftdigital.com
    ("30+", "WEBSITES CRAFTED", 0.82),
    ("5.0", "AVERAGE STAR RATING", 1.0),
    ("8+", "YEARS EXPERIENCE", 0.64),
]
LEVELS_H = 200

THEMES = {
    "dark": dict(bg="#161826", surface="#232532", ink="#e9e9ed", accent="#9184d9",
                 accent_text="#b5abfc", region_sound="#2c2a45"),
    "light": dict(bg="#f3f5fe", surface="#e3e6f6", ink="#161826", accent="#9184d9",
                  accent_text="#5d5294", region_sound="#dcd8f5"),
}

TYPE_SIZE = 26
STEP = 4.0  # seconds each phrase owns in the cycle
CYCLE = STEP * len(PHRASES)


def font_face(weight, opsz, text):
    font = instancer.instantiateVariableFont(TTFont(FONT), {"wght": weight, "opsz": opsz})
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'DM Sans {weight}';"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


def advance(font, text, size):
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in text) * size / upm


def eq_bars(t):
    rnd = random.Random(7)
    out, css = [], []
    n, bw, gap, base, x = 26, 10, 5, 238, 744
    for i in range(n):
        h = rnd.randint(40, 150)
        dur = round(rnd.uniform(0.9, 1.8), 2)
        delay = round(-rnd.uniform(0, 2), 2)
        lo = round(rnd.uniform(0.15, 0.45), 2)
        accent = i % 5 == 2
        fill = t["accent"] if accent else t["ink"]
        op = 0.95 if accent else round(0.18 + 0.5 * (i / n), 2)
        out.append(f'<rect class="eq b{i}" x="{x}" y="{base - h}" width="{bw}" height="{h}" '
                   f'rx="2" fill="{fill}" fill-opacity="{op}"/>')
        css.append(f".b{i}{{animation:eq{i} {dur}s ease-in-out {delay}s infinite alternate}}"
                   f"@keyframes eq{i}{{from{{transform:scaleY({lo})}}to{{transform:scaleY(1)}}}}")
        x += bw + gap
    return "\n  ".join(out), "".join(css)


def typed_lines(t, font):
    prompt_w = advance(font, PROMPT + " ", TYPE_SIZE)
    tx, y = X0 + prompt_w, 222
    out, css = [], []
    for i, phrase in enumerate(PHRASES):
        w = advance(font, phrase, TYPE_SIZE)
        n = len(phrase)
        start = i * STEP
        # percentages of the full cycle for: type in, hold, delete
        p0 = start / CYCLE * 100
        p1 = (start + 1.4) / CYCLE * 100
        p2 = (start + 3.3) / CYCLE * 100
        p3 = (start + 3.7) / CYCLE * 100
        ease_in = f"steps({n},end)"
        ease_out = f"steps({max(4, n // 3)},end)"
        kf = (f"@keyframes w{i}{{0%,{p0:.3f}%{{transform:translateX(0);animation-timing-function:{ease_in}}}"
              f"{p1:.3f}%,{p2:.3f}%{{transform:translateX({w:.1f}px);animation-timing-function:{ease_out}}}"
              f"{p3:.3f}%,100%{{transform:translateX(0)}}}}")
        vis = (f"@keyframes v{i}{{0%,{p0 - 0.001 if p0 else 0:.3f}%{{opacity:0}}"
               f"{p0:.3f}%,{p3:.3f}%{{opacity:1}}{p3 + 0.001:.3f}%,100%{{opacity:0}}}}")
        css.append(kf + vis)
        css.append(f".ph{i}{{animation:v{i} {CYCLE}s linear infinite}}"
                   f".ph{i} .wipe,.ph{i} .caret{{animation:w{i} {CYCLE}s infinite}}")
        out.append(
            f'<g class="ph ph{i}">'
            f'<text x="{tx:.1f}" y="{y}" class="type">{phrase}</text>'
            f'<rect class="wipe" x="{tx:.1f}" y="{y - 26}" width="{w + 4:.1f}" height="36" fill="{t["bg"]}"/>'
            f'<rect class="caret" x="{tx + 2:.1f}" y="{y - 21}" width="3" height="27" fill="{t["accent"]}"/>'
            f'</g>')
    return "\n  ".join(out), "".join(css)


def ruler(t):
    ticks = []
    span = (W - 2 * X0) / 16
    for i in range(17):
        x = X0 + i * span
        major = i % 4 == 0
        ticks.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{30 if major else 36}" y2="44" '
                     f'stroke="{t["ink"]}" stroke-opacity="{0.35 if major else 0.16}"/>')
        if major and i < 16:
            ticks.append(f'<text x="{x + 6:.1f}" y="38" class="tiny">{i // 4 + 1}.1</text>')
    return "\n  ".join(ticks)


def lane(t, font):
    out = [f'<line x1="{X0}" x2="{W - X0}" y1="291" y2="291" stroke="{t["ink"]}" stroke-opacity="0.12"/>']
    for label, x, w, kind in REGIONS:
        fill = t["region_sound"] if kind == "sound" else t["surface"]
        out.append(f'<rect x="{x}" y="262" width="{w}" height="26" rx="4" fill="{fill}"/>')
        if kind == "sound":  # little waveform squiggle inside audio regions
            rnd = random.Random(x)
            sx = x + 9 + advance(font, label, 11) + 0.04 * 11 * len(label) + 10
            pts = " ".join(f"{sx + j * 4:.1f},{275 + rnd.uniform(-7, 7):.1f}" for j in range(int((x + w - 8 - sx) // 4)))
            out.append(f'<polyline points="{pts}" fill="none" stroke="{t["accent"]}" '
                       f'stroke-opacity="0.8" stroke-width="1.2"/>')
        out.append(f'<text x="{x + 9}" y="279" class="tiny">{label}</text>')
    return "\n  ".join(out)


def header(name, t, faces, font500):
    bars, eq_css = eq_bars(t)
    lines, type_css = typed_lines(t, font500)
    reduce_css = (".eq,.ph,.wipe,.caret,.head{animation:none!important}"
                  ".ph{opacity:0}.ph0{opacity:1}.ph0 .wipe{opacity:0}.ph0 .caret{display:none}")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">Steve Berg</title>
<desc id="d">Developer and music producer. Building fast websites at EdgeCraft Digital, producing music between commits.</desc>
<style>
{faces}
.title{{font:600 104px 'DM Sans 600','DM Sans',Inter,'Segoe UI',Helvetica,Arial,sans-serif;letter-spacing:-0.035em;fill:{t["ink"]}}}
.kicker{{font:500 14px 'DM Sans 500','DM Sans',Inter,'Segoe UI',Helvetica,Arial,sans-serif;letter-spacing:0.22em;fill:{t["accent_text"]}}}
.type,.prompt{{font:500 {TYPE_SIZE}px 'DM Sans 500','DM Sans',Inter,'Segoe UI',Helvetica,Arial,sans-serif;font-kerning:none;fill:{t["ink"]};fill-opacity:.82}}
.prompt{{fill:{t["accent"]};fill-opacity:1}}
.tiny{{font:500 11px 'DM Sans 500','DM Sans',Inter,'Segoe UI',Helvetica,Arial,sans-serif;letter-spacing:0.04em;fill:{t["ink"]};fill-opacity:.55}}
.eq{{transform-box:fill-box;transform-origin:50% 100%}}
.caret{{opacity:1}}
.head{{animation:play 9s linear infinite}}
@keyframes play{{from{{transform:translateX(0)}}to{{transform:translateX({W - 2 * X0}px)}}}}
{eq_css}
{type_css}
@media (prefers-reduced-motion:reduce){{{reduce_css}}}
</style>
<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>
  {ruler(t)}
<text x="{X0}" y="96" class="kicker">{KICKER}</text>
<text x="{X0 - 4}" y="178" class="title">{TITLE}</text>
<text x="{X0}" y="222" class="prompt">{PROMPT}</text>
  {lines}
  {bars}
  {lane(t, font500)}
<g class="head">
  <line x1="{X0}" x2="{X0}" y1="26" y2="298" stroke="{t["accent"]}" stroke-width="2"/>
  <path d="M{X0 - 6} 24 h12 l-6 8 z" fill="{t["accent"]}"/>
</g>
</svg>
'''
    (OUT / f"header-{name}.svg").write_text(svg)


def star(x, y, r, fill):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f"{x + rr * math.cos(a):.1f},{y + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def levels(name, t, faces, font600):
    """Three channel strips: big number, label, and an LED meter that pumps."""
    col_w = (W - 2 * X0) / len(LEVELS)
    seg_n, seg_w, seg_gap = 28, 8, 3
    out, css = [], []
    for i, (value, label, level) in enumerate(LEVELS):
        x = X0 + i * col_w
        if i:
            out.append(f'<line x1="{x - 28:.1f}" x2="{x - 28:.1f}" y1="44" y2="{LEVELS_H - 40}" '
                       f'stroke="{t["ink"]}" stroke-opacity="0.12"/>')
        out.append(f'<text x="{x:.1f}" y="62" class="kicker">CH {i + 1:02d}  /  {label}</text>')
        out.append(f'<text x="{x - 3:.1f}" y="128" class="big">{value}</text>')
        if value == "5.0":
            out.append(star(x + advance(font600, value, 60) + 22, 108, 15, t["accent"]))
        lit = round(seg_n * level)
        segs = []
        for j in range(seg_n):
            hot = j >= seg_n - 6
            fill = t["accent"] if hot else t["ink"]
            op = (0.95 if hot else 0.6) if j < lit else 0.1
            segs.append(f'<rect x="{x + j * (seg_w + seg_gap):.1f}" y="152" width="{seg_w}" height="10" '
                        f'rx="1.5" fill="{fill}" fill-opacity="{op}"/>')
        meter_w = seg_n * (seg_w + seg_gap)
        # an opaque "shutter" slides over the unlit end so the meter breathes
        lo = 1 - (lit - 4) / seg_n
        css.append(f".m{i}{{animation:m{i} {1.3 + 0.35 * i:.2f}s ease-in-out {-0.4 * i:.1f}s infinite alternate}}"
                   f"@keyframes m{i}{{from{{transform:scaleX({max(lo, 0.02):.3f})}}"
                   f"to{{transform:scaleX({max(1 - lit / seg_n, 0.001):.3f})}}}}")
        out.append("".join(segs))
        out.append(f'<rect class="sh m{i}" x="{x - 1:.1f}" y="150" width="{meter_w + 2:.1f}" height="14" '
                   f'fill="{t["bg"]}" fill-opacity="0.82"/>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{LEVELS_H}" viewBox="0 0 {W} {LEVELS_H}" role="img" aria-labelledby="t">
<title id="t">30+ websites crafted, 5.0 average star rating, 8+ years experience</title>
<style>
{faces}
.big{{font:600 60px 'DM Sans 600','DM Sans',Inter,'Segoe UI',Helvetica,Arial,sans-serif;letter-spacing:-0.035em;fill:{t["ink"]}}}
.kicker{{font:500 12px 'DM Sans 500','DM Sans',Inter,'Segoe UI',Helvetica,Arial,sans-serif;letter-spacing:0.22em;fill:{t["accent_text"]}}}
.sh{{transform-box:fill-box;transform-origin:100% 50%}}
{"".join(css)}
@media (prefers-reduced-motion:reduce){{.sh{{animation:none!important;opacity:0}}}}
</style>
<rect width="{W}" height="{LEVELS_H}" rx="18" fill="{t["bg"]}"/>
  {chr(10).join("  " + o for o in out)}
</svg>
'''
    (OUT / f"levels-{name}.svg").write_text(svg)


def divider():
    rnd = random.Random(3)
    bars, css = [], []
    n, bw, gap = 75, 4, 12
    x = (W - (n * bw + (n - 1) * gap)) / 2
    for i in range(n):
        # envelope swells in the middle so it reads as a waveform, not a barcode
        env = 1 - abs(i - n / 2) / (n / 2)
        h = 6 + env * rnd.uniform(10, 34)
        dur = round(rnd.uniform(1.1, 2.2), 2)
        css.append(f".d{i}{{animation:dv {dur}s ease-in-out {-rnd.uniform(0, 2):.2f}s infinite alternate}}")
        bars.append(f'<rect class="d d{i}" x="{x:.1f}" y="{24 - h / 2:.1f}" width="{bw}" height="{h:.1f}" '
                    f'rx="2" fill="#9184d9" fill-opacity="{0.35 + 0.6 * env:.2f}"/>')
        x += bw + gap
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="48" viewBox="0 0 {W} 48" role="img" aria-label="">
<style>
.d{{transform-box:fill-box;transform-origin:50% 50%}}
@keyframes dv{{from{{transform:scaleY(.35)}}to{{transform:scaleY(1)}}}}
{"".join(css)}
@media (prefers-reduced-motion:reduce){{.d{{animation:none!important}}}}
</style>
  {chr(10).join("  " + b for b in bars)}
</svg>
'''
    (OUT / "divider.svg").write_text(svg)


def main():
    OUT.mkdir(exist_ok=True)
    small_text = KICKER + PROMPT + " " + "".join(PHRASES) + "".join(r[0] for r in REGIONS) + "0123456789."
    faces = font_face(600, 40, TITLE) + font_face(500, 14, small_text)
    font500 = instancer.instantiateVariableFont(TTFont(FONT), {"wght": 500, "opsz": 14})
    font600 = instancer.instantiateVariableFont(TTFont(FONT), {"wght": 600, "opsz": 40})
    level_text = "".join(v + l for v, l, _ in LEVELS) + "CH /0123456789"
    level_faces = font_face(600, 40, "".join(v for v, _, _ in LEVELS)) + font_face(500, 14, level_text)
    for name, t in THEMES.items():
        header(name, t, faces, font500)
        levels(name, t, level_faces, font600)
    divider()
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
