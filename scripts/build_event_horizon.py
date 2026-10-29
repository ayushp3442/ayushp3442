#!/usr/bin/env python3
"""Event Horizon: animated profile header + contribution calendar built from REAL public
contribution data. Standard library only (works in GitHub Actions with no pip install).

  python scripts/build_event_horizon.py --user ayushp3442 --out assets
  python scripts/build_event_horizon.py --html saved_contributions.html --out assets   # offline test
"""
import argparse, math, os, random, re, urllib.request
from xml.sax.saxutils import escape as esc
from datetime import date, timedelta

# ---- edit these ---------------------------------------------------------------
NAME = "Ayush Pandey"
SUBTITLE = "AI · FULL-STACK · FLUTTER · SPRING BOOT"
PHRASES = ["Building AI agents & LLM apps",
           "Building full-stack apps with Flutter & Spring Boot",
           "Full-stack with Next.js, Express & TypeScript"]
# -------------------------------------------------------------------------------

T = 12.0
FONT = "Inter,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'Fira Code','JetBrains Mono',Consolas,'Liberation Mono',monospace"
CYAN, AMBER, ORANGE = "#7DE3FF", "#ffb347", "#ffab4a"
# contribution tiles: dark ember -> white-hot, same family as the accretion disk
LV = ["#1b120e", "#6b2d0d", "#b8420f", "#ff7a1a", "#ffc46b"]


# ------------------------------- data ------------------------------------------
def fetch(user=None, html_path=None):
    if html_path:
        html = open(html_path, encoding="utf-8").read()
    else:
        req = urllib.request.Request("https://github.com/users/%s/contributions" % user,
                                     headers={"User-Agent": "Mozilla/5.0 (event-horizon-bot)"})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    cells = re.findall(r'<td[^>]*data-date="([\d-]+)"[^>]*id="([^"]+)"[^>]*data-level="(\d)"', html)
    tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html))
    if not cells:
        raise RuntimeError("no contribution cells found (GitHub markup changed?)")
    out = []
    for d, i, l in cells:
        m = re.match(r"(\d+)", tips.get(i, ""))
        out.append((d, int(m.group(1)) if m else 0, int(l)))
    return sorted(out)


def stats(days):
    counts = [c for _, c, _ in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur, i = 0, len(counts) - 1
    if counts and counts[i] == 0:
        i -= 1  # today may not have commits yet
    while i >= 0 and counts[i] > 0:
        cur += 1
        i -= 1
    return sum(counts), cur, longest, max(counts)


# ------------------------------- helpers ---------------------------------------
def pc(t): return "%.2f%%" % max(0.0, min(100.0, t / T * 100))


def kf(name, frames):
    g = {}
    for t, d in frames:
        g[round(t, 3)] = g.get(round(t, 3), "") + d.rstrip(";") + ";"
    if 0.0 not in g:
        g[0.0] = g[min(g)]
    if T not in g:
        g[T] = g[0.0]
    return "@keyframes %s{%s}" % (name, "".join("%s{%s}" % (pc(t), g[t]) for t in sorted(g)))


def mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(pa, pb))


def wrap(W, H, title, desc, defs, css, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">'
            "<title>%s</title><desc>%s</desc><defs>%s</defs><style>%s@media (prefers-reduced-motion:reduce){svg *{animation:none!important}}</style>%s</svg>"
            % (W, H, W, H, title, title, desc, defs, css, body))


# ------------------------------- black hole ------------------------------------
def black_hole(cx, cy, s, tilt, wide, W, H):
    """Returns (defs, css, back_layers, front_layers). Draw particles between back and front."""
    rs = 46 * s
    radii = [78, 100, 128, 160, 196]
    cols = ["#fff3d6", "#ffd28a", "#ffab4a", "#ff7a1a", "#b8420f"]
    sw = [5, 5, 4, 3, 2]
    dash = ["8 2", "5 5", "12 8", "3 7", "14 6"]
    dur = [4, 5.5, 7, 9, 12]
    rx = [r * s * wide for r in radii]
    ry = [r * s * 0.2 for r in radii]
    css = "".join("@keyframes df%d{to{stroke-dashoffset:-100}}" % i for i in range(5))
    css += "@keyframes gp{0%,100%{opacity:.5}50%{opacity:.85}}.bhg{animation:gp 8s ease-in-out infinite}"

    def disk():
        o = ""
        for i in range(5):
            w = max(1.2, sw[i] * math.sqrt(s))
            e = 'cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="none" stroke="%s" stroke-width="%.1f"' % (cx, cy, rx[i], ry[i], cols[i], w)
            o += "<ellipse %s opacity=\".28\"/>" % e
            o += '<ellipse %s pathLength="100" stroke-dasharray="%s" style="animation:df%d %ss linear infinite"/>' % (e, dash[i], i, dur[i])
        return o

    defs = (
        '<mask id="dm" maskUnits="userSpaceOnUse" x="0" y="0" width="%d" height="%d"><rect width="%d" height="%d" fill="url(#dg)"/></mask>'
        '<linearGradient id="dg" gradientUnits="userSpaceOnUse" x1="%.1f" y1="0" x2="%.1f" y2="0"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#6a6a6a"/></linearGradient>'
        '<clipPath id="fc"><rect x="0" y="%.1f" width="%d" height="%d"/></clipPath>'
        '<linearGradient id="lg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff3d6"/><stop offset=".5" stop-color="#ff9d3a"/><stop offset="1" stop-color="#3a1a08"/></linearGradient>'
        '<radialGradient id="bg"><stop offset="0" stop-color="#ff8a2a" stop-opacity=".55"/><stop offset=".35" stop-color="#b8420f" stop-opacity=".22"/><stop offset="1" stop-color="#05070f" stop-opacity="0"/></radialGradient>'
        '<filter id="bl" filterUnits="userSpaceOnUse" x="0" y="0" width="%d" height="%d"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    ) % (W, H, W, H, cx - rx[-1], cx + rx[-1], cy, W, H, W, H)
    lw = max(3.0, 6 * math.sqrt(s))
    back = (
        '<circle class="bhg" cx="%.1f" cy="%.1f" r="%.1f" fill="url(#bg)"/>'
        '<g mask="url(#dm)"><g transform="rotate(%s %.1f %.1f)">%s</g></g>'
        '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="url(#lg)" stroke-width="%.1f" filter="url(#bl)"/>'
    ) % (cx, cy, rs * 7, tilt, cx, cy, disk(), cx, cy, rs * 1.22, lw)
    front = (
        '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#000"/>'
        '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#ffe9bf" stroke-width="1.4" opacity=".9"/>'
        '<g mask="url(#dm)"><g transform="rotate(%s %.1f %.1f)"><g clip-path="url(#fc)">%s</g></g></g>'
    ) % (cx, cy, rs, cx, cy, rs * 1.04, tilt, cx, cy, disk())
    return defs, css, back, front


# ------------------------------- header ----------------------------------------
def header():
    W, H, BX, BY = 1200, 300, 930, 150
    rnd = random.Random(42)
    defs, css, back, front = black_hole(BX, BY, 1.0, -12, 1.0, W, H)
    css += ("@keyframes inf{0%{opacity:0;transform:rotate(0) scale(1)}10%{opacity:.95}80%{opacity:.9}100%{opacity:0;transform:rotate(-640deg) scale(.14)}}"
            "@keyframes tw{0%,100%{opacity:.25}50%{opacity:.9}}@keyframes bl{50%{opacity:0}}")
    stars = ""
    for k in range(60):
        x, y, r = rnd.uniform(20, 1180), rnd.uniform(10, 290), rnd.choice([.6, .8, 1.0, 1.3])
        tw = ' style="animation:tw %.1fs ease-in-out infinite;animation-delay:-%.1fs"' % (rnd.uniform(3, 7), rnd.uniform(0, 6)) if k % 5 == 0 else ""
        stars += '<circle cx="%.0f" cy="%.0f" r="%s" fill="#cfe0ff" opacity="%.2f"%s/>' % (x, y, r, rnd.uniform(.25, .7), tw)
    infall = ""
    for k in range(14):
        R, ang, d = rnd.uniform(170, 330), rnd.uniform(0, 6.283), rnd.uniform(8, 12)
        infall += ('<g style="transform-origin:%dpx %dpx;animation:inf %.1fs cubic-bezier(.45,0,.85,.55) -%.1fs infinite" opacity="0">'
                   '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/></g>') % (
            BX, BY, d, rnd.uniform(0, d), BX + R * math.cos(ang), BY + R * math.sin(ang), rnd.choice([1.4, 1.8, 2.2]), rnd.choice(["#ffd28a", ORANGE, "#fff3d6"]))
    infall = '<g transform="translate(%d %d) rotate(-12) scale(1 .38) translate(%d %d)">%s</g>' % (BX, BY, -BX, -BY, infall)
    # typewriter (pure CSS: stepped clip + caret), 4 s per phrase
    clips, texts, caret = "", "", []
    for i, p in enumerate(PHRASES):
        n = len(p)
        Wd = n * 12.0
        ts = 4.0 * i + 0.1
        td = min(2.2, 0.045 * n)
        css += kf("tc%d" % i, [(0, "transform:scaleX(0)"), (ts, "transform:scaleX(0);animation-timing-function:steps(%d,end)" % n),
                               (ts + td, "transform:scaleX(1)"), (4.0 * i + 3.3, "transform:scaleX(1);animation-timing-function:steps(8,end)"),
                               (4.0 * i + 3.7, "transform:scaleX(0)")])
        caret += [(ts, "transform:translateX(0);animation-timing-function:steps(%d,end)" % n), (ts + td, "transform:translateX(%.0fpx)" % Wd),
                  (4.0 * i + 3.3, "transform:translateX(%.0fpx);animation-timing-function:steps(8,end)" % Wd), (4.0 * i + 3.7, "transform:translateX(0)")]
        clips += '<clipPath id="tc%d"><rect x="72" y="204" width="%.0f" height="30" style="transform-origin:72px 0px;animation:tc%d 12s linear infinite"/></clipPath>' % (i, Wd, i)
        texts += '<text x="72" y="226" font-family="%s" font-size="20" fill="%s" textLength="%.0f" lengthAdjust="spacing" clip-path="url(#tc%d)">%s</text>' % (MONO, ORANGE, Wd, i, esc(p))
    css += kf("cr", caret)
    defs += clips + ('<linearGradient id="nm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#b9d8ff"/></linearGradient>'
                     '<linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>') % (AMBER, "#ff7a1a")
    body = (
        '<rect width="1200" height="300" rx="14" fill="#04060d"/>' + stars + back + infall + front +
        '<rect x="70" y="92" width="64" height="4" rx="2" fill="url(#ac)"/>'
        '<text x="70" y="150" font-family="%s" font-size="54" font-weight="800" fill="url(#nm)" letter-spacing="-1">%s</text>'
        '<text x="72" y="182" font-family="%s" font-size="14" letter-spacing="4" fill="#7f93c4">%s</text>%s'
        '<g style="animation:cr 12s linear infinite"><rect x="73" y="206" width="2" height="22" fill="%s" style="animation:bl 1s steps(1) infinite"/></g>'
    ) % (FONT, esc(NAME), FONT, esc(SUBTITLE), texts, ORANGE)
    return wrap(W, H, esc(NAME) + " header", "Black hole with accretion disk and a typewriter tagline.", defs, css, body)


# ------------------------------- calendar --------------------------------------
START = {1: "#ff9d3a", 2: "#ffab4a", 3: "#ffc46b", 4: "#fff3d6"}  # infalling matter colour by level
HOT = "#fff3d6"                                                    # everything heats up to white-hot


def calendar(days):
    W, H, pitch, cs = 1200, 350, 19, 15
    x0, y0 = 98, 84
    BX, BY, S = 600, 296, 0.62
    RS = 46 * S
    total, cur, longest, best = stats(days)
    first = date.fromisoformat(days[0][0])
    sun = first - timedelta(days=(first.weekday() + 1) % 7)
    cols = (date.fromisoformat(days[-1][0]) - sun).days // 7 + 1
    defs, css, back, front = black_hole(BX, BY, S, -2, 1.45, W, H)
    css += ".t{font-family:%s}.ax{font-size:11px;fill:#8f7258}.c{transform-box:fill-box;transform-origin:center}" % FONT
    css += "@keyframes tw{0%,100%{opacity:.25}50%{opacity:.9}}"

    # space background: same starfield recipe as the header
    rnd, stars = random.Random(7), ""
    for k in range(90):
        x, y, r = rnd.uniform(14, 1186), rnd.uniform(8, 342), rnd.choice([.6, .8, 1.0, 1.3])
        tw = ' style="animation:tw %.1fs ease-in-out infinite;animation-delay:-%.1fs"' % (rnd.uniform(3, 7), rnd.uniform(0, 6)) if k % 5 == 0 else ""
        stars += '<circle cx="%.0f" cy="%.0f" r="%s" fill="#cfe0ff" opacity="%.2f"%s/>' % (x, y, r, rnd.uniform(.25, .7), tw)

    # tiles (positions come straight from GitHub's own week/day grid)
    cells, months, last_m, last_c, active = "", "", None, -9, []
    for d, cnt, lv in days:
        dd = date.fromisoformat(d)
        col, row = (dd - sun).days // 7, (dd.weekday() + 1) % 7
        x, y = x0 + col * pitch, y0 + row * pitch
        if row == 0 and dd.month != last_m and col - last_c >= 3:
            months += '<text class="t ax" x="%d" y="%d">%s</text>' % (x, y0 - 10, dd.strftime("%b"))
            last_m, last_c = dd.month, col
        if lv:
            active.append((d, lv, x + cs / 2, y + cs / 2))
        cells += '<rect x="%d" y="%d" width="%d" height="%d" rx="3" fill="%s"%s/>' % (x, y, cs, cs, LV[lv], "@@%s@@" % d if lv else "")

    # active days that "fall in": spread evenly over the year, replayed in chronological order
    pick = active if len(active) <= 28 else [active[round(i * (len(active) - 1) / 27)] for i in range(28)]
    D, N, part, gulps = 3.0, 18, "", []
    css += kf("fl", [(0, "fill:#ffffff;transform:scale(1)"), (0.12, "fill:#fff3d6;transform:scale(1.4)"),
                     (0.5, "fill:#ffd28a;transform:scale(1.12)"), (1.4, "fill:var(--b);transform:scale(1)"), (T, "fill:var(--b);transform:scale(1)")])
    for k, (d, lv, sx, sy) in enumerate(pick):
        t0 = 0.3 + k * (10.0 / len(pick))
        r0, th0 = math.hypot(sx - BX, sy - BY), math.atan2(sy - BY, sx - BX)
        pts = []
        for j in range(N + 1):
            s_ = j / N
            u = s_ * s_
            r = 20 + (r0 - 20) * (1 - u) ** 1.5            # accelerates, ends inside the horizon
            th = th0 + 3.6 * s_ ** 2.2                     # tightening spiral
            pts.append((BX + r * math.cos(th), BY + r * math.sin(th) * (1 - 0.65 * u * u)))
        fr, prev = [], None
        for j, (x, y) in enumerate(pts):
            s_ = j / N
            nx, ny = pts[min(j + 1, N)]
            px, py = pts[max(j - 1, 0)]
            ang = math.degrees(math.atan2(ny - py, nx - px))
            while prev is not None and ang - prev > 180: ang -= 360
            while prev is not None and ang - prev < -180: ang += 360
            prev = ang
            o = min(1, s_ / 0.06) * max(0, min(1, (0.97 - s_) / 0.10))
            stretch, thin = 1 + 3.2 * s_ ** 2.5, 1 - 0.55 * s_ ** 2   # spaghettification
            fr.append((s_ * D, "opacity:%.2f;transform:translate(%.1fpx,%.1fpx) rotate(%.1fdeg) scale(%.2f,%.2f);fill:%s" % (
                o, x, y, ang, stretch, thin, mix(START[lv], HOT, s_ ** 1.4))))
        css += kf("p%d" % k, fr)
        # head + comet tail (same keyframes, delayed copies) + soft glow
        for op, rad, shift in ((.18, 6.0, 0.0), (1.0, 2.8, 0.0), (.55, 2.2, 0.10), (.32, 1.7, 0.20), (.16, 1.2, 0.30)):
            part += '<g opacity="%s"><circle r="%s" opacity="0" style="animation:p%d 12s linear infinite;animation-delay:%.2fs"/></g>' % (op, rad, k, t0 + shift)
        a_ = (t0 + D * 0.95) % T
        gulps += [(max(0.0, a_ - 0.02), "opacity:0;transform:scale(1)"), (a_, "opacity:.95;transform:scale(1.05)"), (a_ + 0.3, "opacity:0;transform:scale(1.3)")]
        cells = cells.replace("@@%s@@" % d, ' class="c" style="--b:%s;animation:fl 12s linear infinite;animation-delay:%.2fs"' % (LV[lv], t0))
    cells = re.sub(r"@@[\d-]+@@", "", cells)
    # the horizon flares every time something is swallowed
    gulp = ""
    if gulps:
        css += kf("gulp", sorted(gulps, key=lambda g: g[0]))
        gulp = ('<circle cx="%d" cy="%d" r="%.1f" fill="none" stroke="#ffe9bf" stroke-width="2.2" opacity="0" '
                'style="transform-origin:%dpx %dpx;animation:gulp 12s linear infinite"/>') % (BX, BY, RS * 1.08, BX, BY)

    labels = "".join('<text class="t ax" x="%d" y="%d" text-anchor="end">%s</text>' % (x0 - 10, y0 + r * pitch + 12, n) for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    legend = "".join('<rect x="%d" y="324" width="12" height="12" rx="2.5" fill="%s"/>' % (1048 + i * 16, c) for i, c in enumerate(LV))
    body = (
        '<rect x=".5" y=".5" width="1199" height="349" rx="14" fill="#04060d" stroke="#2b1a10"/>' + stars + back +
        '<text class="t" x="%d" y="38" font-size="19" font-weight="700" fill="#fff1dc">%s contributions in the last year</text>'
        '<text class="t" x="%d" y="38" font-size="13" fill="#b69272" text-anchor="end">Streak <tspan fill="%s" font-weight="700">%dd</tspan>  ·  Longest <tspan fill="%s" font-weight="700">%dd</tspan>  ·  Best day <tspan fill="%s" font-weight="700">%d</tspan></text>'
        % (x0, "{:,}".format(total), x0 + cols * pitch - 4, ORANGE, cur, ORANGE, longest, ORANGE, best) +
        months + labels + cells + part + front + gulp +
        '<text class="t" x="%d" y="334" font-size="11" letter-spacing="3" fill="#7a5636">NO COMMIT ESCAPES</text>'
        '<text class="t ax" x="1040" y="334" text-anchor="end">Less</text>%s<text class="t ax" x="1130" y="334">More</text>' % (x0, legend)
    )
    return wrap(W, H, "Contribution calendar: %d contributions in the last year" % total,
                "Real public contribution data. Active days fall into a black hole in a looping replay.", defs, css, body)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="ayushp3442")
    ap.add_argument("--html")
    ap.add_argument("--out", default="assets")
    a = ap.parse_args()
    days = fetch(a.user, a.html)
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, "event-horizon-header.svg"), "w", encoding="utf-8").write(header())
    open(os.path.join(a.out, "event-horizon-calendar.svg"), "w", encoding="utf-8").write(calendar(days))
    t, c, l, b = stats(days)
    print("ok: %d contributions, streak %d, longest %d, best day %d" % (t, c, l, b))
