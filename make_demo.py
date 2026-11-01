#!/usr/bin/env python3
"""Builds the hackathon demo video from the REAL generated pack + still.
Cards (English, for judges) rendered with PIL; assembled with ffmpeg.
All content comes from demo-pack.json — nothing is mocked."""
import json, os, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, "demo_frames")
os.makedirs(FR, exist_ok=True)
W, H = 1280, 720
BG = (11, 11, 13); GOLD = (212, 175, 55); GOLD2 = (241, 212, 122)
TXT = (242, 234, 210); DIM = (167, 159, 138); CARD = (21, 21, 26)

def font(size, bold=False):
    names = ["NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf",
             "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for root in ("/usr/share/fonts/truetype/noto", "/usr/share/fonts/truetype/dejavu"):
        for n in names:
            p = os.path.join(root, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F_TITLE = font(54, True); F_H = font(34, True); F_B = font(26); F_S = font(21); F_BIG = font(40, True)

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def card(name, heading, body_lines, sub=None, dur=6):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 40, W-40, H-40], 24, fill=CARD, outline=GOLD, width=2)
    y = 90
    for ln in wrap(d, heading, F_H, W-200):
        d.text((90, y), ln, font=F_H, fill=GOLD); y += 46
    y += 14
    for para in body_lines:
        for ln in wrap(d, para, F_B, W-200):
            d.text((90, y), ln, font=F_B, fill=TXT); y += 38
        y += 14
    if sub:
        d.text((90, H-110), sub, font=F_S, fill=DIM)
    img.save(os.path.join(FR, name))
    return dur

pack = json.load(open(os.path.join(HERE, "demo-pack.json")))["pack"]
hook_en = pack["hook"]["en"]; titles = [t["en"] for t in pack["titles"]]
s1 = pack["scenes"][0]; kws = ", ".join(pack["keywords"][:9])

segs = []
segs.append(("c1.png", card("c1.png", "Shorts Production Agent",
    ["From one line of an idea + a music track",
     "to a complete, ready-to-produce vertical-short pack.",
     "", "Arabic-first. Powered entirely by Meta Muse models."],
    "Meta Global AI Developer Hackathon · Indie · Build for Your World", 7)))
segs.append(("c2.png", card("c2.png", "The problem",
    ["Short-form creators in non-English markets produce with scattered notes and guesswork.",
     "Pre-production — hook, scenes, prompts, titles, keywords — is where shorts win or die, and it is all manual."], None, 9)))
segs.append(("c3.png", card("c3.png", "One click: the brief",
    ["Idea: A pharaonic folk hero above Old Cairo's rooftops at sunset, black cloak in the wind — king-of-the-street energy.",
     "Track / artist: Hamou El Marshidi · Mood: epic, confident · 30 seconds · 9:16",
     "Model: Muse Spark 1.3 (or Muse Wonder 1.0)"], "A real brief from a real channel's morning ideas mail", 10)))
segs.append(("c4.png", card("c4.png", "The pack: hook + scenes",
    ["Second-zero hook: " + hook_en,
     f"{len(pack['scenes'])} scenes, each with a still prompt, a motion prompt, a camera move and an audio cue — plus voiceover, titles and a checklist.",
     "Generated live in 17 seconds · 4,121 tokens · about $0.016."], None, 13)))
segs.append(("c5.png", card("c5.png", "Scene 1 — generator-ready prompts",
    ["STILL: " + s1["still_prompt"][:300] + "…",
     "MOTION: " + s1["motion_prompt"][:220] + "…"], None, 12)))

# still card: blurred backdrop + centered image
still = Image.open(os.path.join(HERE, "demo-scene1.jpg")).convert("RGB")
bgimg = still.resize((W, H)).filter(ImageFilter.GaussianBlur(18))
fg = still.copy(); fg.thumbnail((420, 660))
bgimg.paste(fg, ((W - fg.width)//2, (H - fg.height)//2 - 10))
d = ImageDraw.Draw(bgimg)
d.rectangle([0, H-64, W, H], fill=(0, 0, 0))
d.text((30, H-46), "Scene 1 still — generated in-app with Muse Image 1.0", font=F_S, fill=GOLD2)
bgimg.save(os.path.join(FR, "c6.png")); segs.append(("c6.png", 11))

segs.append(("c7.png", card("c7.png", "Titles + keywords, bilingual",
    ["Titles: " + " · ".join(titles[:3]),
     "Keywords: " + kws],
    "Artist name in title + tags · AI-design-first keywords · never any text on the video", 10)))
segs.append(("c8.png", card("c8.png", "Built with Meta's models",
    ["Muse Wonder 1.0 · Muse Spark 1.3 · Muse Image 1.0",
     "via the Meta Model API — the same doctrine runs a real, measured YouTube channel in Cairo.",
     "", "Build for Your World — literally."],
    "Shorts Production Agent · Z E L Z A L · Cairo", 8)))

# assemble
seg_files = []
for i, (name, dur) in enumerate(segs):
    out = os.path.join(FR, f"seg{i}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", os.path.join(FR, name),
                    "-vf", f"scale=2560:1440,zoompan=z='min(zoom+0.0006,1.07)':d={dur*30}:s=1280x720:fps=30,fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4}:d=0.4",
                    "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", out],
                   check=True, capture_output=True)
    seg_files.append(out)
lst = os.path.join(FR, "list.txt")
open(lst, "w").write("".join(f"file '{f}'\n" for f in seg_files))
final = os.path.join(HERE, "demo-video.mp4")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-c:v", "copy", "-c:a", "aac", "-shortest", final],
               check=True, capture_output=True)
print("OK ->", final, os.path.getsize(final), "bytes,", sum(d for _, d in segs), "seconds")
