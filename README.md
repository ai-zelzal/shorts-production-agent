# Shorts Production Agent — وكيل إنتاج الشورتات

**Meta Global AI Developer Hackathon · Indie track · Theme: Build for Your World**

One line of an idea + a music track in → a complete, ready-to-execute production
pack for a vertical AI music short out. Built on a real production practice:
an Egyptian creator's channel where every short is produced exactly this way —
second-zero hook, scene stills, motion prompts, bilingual titles, keyword bank.

## What it produces
- **Second-zero hook** (Arabic + English + the opening visual)
- **4–6 scenes**, each with an English still-image prompt, an English motion
  prompt (for animating the still in a video generator), a camera move and an
  audio cue synced to the track
- **Scene stills generated in-app** with Muse Image 1.0
- **4 bilingual titles** (artist name included), a bilingual keyword bank led by
  "AI design", hashtags, an optional Egyptian-Arabic voiceover, and an ordered
  production checklist

## Meta models used (Meta Model API, https://api.meta.ai/v1)
| Role | Model |
|---|---|
| Pack reasoning (choice) | `muse-wonder-1.0` / `muse-spark-1.3` / `muse-spark-1.3-contributor` |
| Scene stills | `muse-image-1.0` |

## Run it
```bash
META_API_KEY=<your key> python3 server.py   # or keep the key in ~/.config/muse/auth.json
# open http://127.0.0.1:8791
```
Python 3 standard library only — no dependencies. The key stays server-side;
the browser never sees it.

## Files
- `server.py` — API proxy + production-doctrine system prompt
- `index.html` — Arabic RTL interface (black/gold), model picker, per-scene still generation
- `demo-pack.json` — a real generated pack (Muse Spark 1.3, 4,121 tokens, ~$0.016); its scene-1 still, generated via Muse Image 1.0, is shown in the demo video

## Why it matters
Short-form creators outside the English-speaking core markets produce with
scattered notes and guesswork. This agent compresses a professional director's
whole pre-production into one click — in Arabic first — using only Meta models.
