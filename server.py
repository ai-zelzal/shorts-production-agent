#!/usr/bin/env python3
"""Shorts Production Agent — Meta Global AI Developer Hackathon (Indie track).

Turns a one-line idea + a music track into a complete, ready-to-produce
vertical-short production pack, using Meta Muse models via the Meta Model API:
  - muse-wonder-1.0 / muse-spark-1.3 / muse-spark-1.3-contributor (pack reasoning)
  - muse-image-1.0 (scene still generation)

Stdlib only. The API key is read from the Muse credential store
(~/.config/muse/auth.json) or from META_API_KEY; it is never sent to the browser.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_BASE = "https://api.meta.ai/v1"
HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8791"))

MODELS = ["muse-wonder-1.0", "muse-spark-1.3", "muse-spark-1.3-contributor"]


def load_key():
    if os.environ.get("META_API_KEY"):
        return os.environ["META_API_KEY"]
    p = os.path.expanduser("~/.config/muse/auth.json")
    with open(p) as f:
        return json.load(f)["providers"]["meta"]["api_key"]


API_KEY = load_key()


def api_call(path, payload, timeout=240):
    req = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Meta API {e.code}: {e.read().decode()[:300]}")


SYSTEM_PROMPT = """You are the Shorts Production Agent: a professional production director for vertical AI music shorts (YouTube Shorts / Reels / TikTok), built on a real, measured production practice from Cairo, Egypt.

Given an idea, a music track/artist, a mood and a duration, produce a COMPLETE production pack a creator can execute immediately. Binding production doctrine:
- Format is always vertical 9:16.
- The hook lives at second zero: the strongest visual AND the strongest audio moment open the video. No slow intros.
- NEVER any text on the video itself. Titles and tags live only in the upload metadata.
- Scenes: 4 to 6 scenes that fit the duration. Every scene gets (a) an English still-image prompt (rich, cinematic, generator-ready) and (b) an English motion prompt for animating that still in a video generator, plus a camera move and the audio cue it syncs to.
- If a hero character is described, keep one consistent character description repeated inside every still prompt (identity consistency across scenes).
- Titles: exactly 4 bilingual options (Arabic + English). If an artist is named, the artist's name appears in every title and in the tags.
- Keywords lead with AI design ("AI design", "تصميم ذكاء اصطناعي") and are bilingual.
- Voiceover: one short, punchy Egyptian-Arabic line set (with English translation) that fits the duration, or empty if the track carries the video alone.
- Checklist: the concrete next production steps, in order.

Return ONLY valid JSON (no markdown fences, no commentary) with exactly this shape:
{"hook":{"ar":"","en":"","visual":""},
 "concept":"",
 "scenes":[{"n":1,"seconds":"0-5","still_prompt":"","motion_prompt":"","camera":"","audio_cue":""}],
 "voiceover":{"ar":"","en":""},
 "titles":[{"ar":"","en":""}],
 "keywords":[""],
 "hashtags":[""],
 "checklist":[""]}"""


def build_pack(body):
    model = body.get("model") or "muse-spark-1.3"
    if model not in MODELS:
        model = "muse-spark-1.3"
    user = (
        f"Idea: {body.get('idea','')}\n"
        f"Track / artist: {body.get('track','') or 'not specified'}\n"
        f"Mood: {body.get('mood','') or 'powerful'}\n"
        f"Duration: {body.get('duration','30')} seconds\n"
        f"Hero character (optional): {body.get('hero','') or 'none'}\n"
        "Produce the production pack JSON now."
    )
    res = api_call("/chat/completions", {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "max_tokens": 6000,
    })
    text = res["choices"][0]["message"].get("content") or ""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].lstrip("json").strip() if "```" in text[3:] else text
    start, end = text.find("{"), text.rfind("}")
    pack = json.loads(text[start:end + 1])
    return {"model": model, "usage": res.get("usage"), "pack": pack}


def gen_image(body):
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("empty prompt")
    res = api_call("/images/generations", {
        "model": "muse-image-1.0",
        "prompt": prompt + ", vertical 9:16 composition, cinematic lighting, no text, no watermark",
        "size": "1024x1536",
    }, timeout=300)
    b64 = res["data"][0]["b64_json"]
    return {"image": "data:image/jpeg;base64," + b64}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/api/health":
            self.send_json({"ok": True, "models": MODELS, "image_model": "muse-image-1.0"})
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/pack":
                self.send_json(build_pack(body))
            elif self.path == "/api/image":
                self.send_json(gen_image(body))
            else:
                self.send_json({"error": "not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)[:400]}, 500)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
