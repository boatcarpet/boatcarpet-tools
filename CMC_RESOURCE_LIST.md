# CMC Re-Source List (Pattern Quality Audit)

Status of every pattern currently in `builder_v9_60/patterns/`. Tracks which
need clean CMC re-source.

**Standard:** clean line art, single carpet shape, make + model caption only,
no measurements, no baked-in text, no photos, no solid silhouettes.

**Acceptance criteria when CMC sends a new image:**
- clean exact outlines (line art, not a photo)
- pieces numbered and labeled on the right side if multi-piece
- make and model written cleanly at the bottom — nothing else
- if it meets standard AND is cleaner than what we have, replace it

When you have a clean CMC source: run it through `standardize.py`, drop the
result into `builder_v9_60/patterns/`, done. The PATTERN_IMGS path is already
`.webp` so no `index.html` edit is needed.

Last updated: 2026-05-15 (session 4 — full live-site audit)

---

## Headline

Audited all 57 patterns on the live https deploy with Oatmeal berber. The
overall finding: **most makes need rework. Only Chris-Craft and Sea Ray came
through the audit clean. Everything else needs varying degrees of attention.**

The bad patterns still *function* (renderer fills them, customer can complete
an order) — they just look ugly because the source image has measurement
lines, baked-in text, photo artifacts, or other contamination. This is a
credibility/presentation issue, not a functional one.

---

## Audit results by make

Legend:
- ✅ verified clean (renders cleanly with berber fill)
- 🚫 flagged for re-source (renders but looks bad)
- ⚠️ partial — see notes
- ❓ not tested individually
- ➖ no pattern image (model exists in dropdown but no underlying image)

### Baja (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| baja-202-islander | 🚫 | photo / baked-in text |

### Bayliner (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| bayliner-225 | 🚫 | photo / baked-in text |

### Bryant (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| bryant-236 | 🚫 | photo, not line art |

### Caravelle (2 patterns)
| Slug | Status | Notes |
|------|--------|-------|
| caravelle-192-interceptor | 🚫 | flagged in audit |
| caravelle-212-interceptor | 🚫 | flagged in audit |

### Chaparral (7 patterns)
**Overall:** "they all need looking at." Treat the whole brand as needing
re-source. Most have baked-in text / measurements / photo artifacts.
| Slug | Status | Notes |
|------|--------|-------|
| chaparral-200 | 🚫 | brand-wide rework |
| chaparral-230-ssi | ✅ | clean — verified during audit |
| chaparral-236-ssi | 🚫 | flagged in audit |
| chaparral-243-sunesta | 🚫 | flagged (236 Sunesta uses this image) |
| chaparral-285-ssi | 🚫 | brand-wide rework |
| chaparral-290-signature | 🚫 | flagged (270 Signature, 276 use this; 290 Signature itself flagged bad) |
| chaparral-h2o-21-sport | 🚫 | brand-wide rework |

### Chris-Craft (2 patterns)
| Slug | Status | Notes |
|------|--------|-------|
| chris-craft-200 | ✅ | clean |
| chris-craft-launch-22 | ✅ | clean |

### Cobalt (2 patterns)
| Slug | Status | Notes |
|------|--------|-------|
| cobalt-292 | ❓ | not individually verified — assume needs check |
| cobalt-a25 | 🚫 | photo, not line art |

### Crownline (0 patterns)
**No pattern images exist for any Crownline model.** Models appear in dropdown
but show no underlying pattern. Whole make needs sourcing from scratch.

### Cruisers Yachts (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| cruisers-yachts-375-aft-cabin | 🚫 | photo / baked-in text |

### Doral (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| doral-boca-grande-36 | ❓ | not individually verified |

### Ebbtide (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| ebbtide-200-campione | ⚠️ | image exists for 220, all other Ebbtide models show no pattern |

### Four Winns (3 patterns)
| Slug | Status | Notes |
|------|--------|-------|
| four-winns-190-horizon | 🚫 | photo / baked-in text |
| four-winns-210-horizon | ❓ | not individually flagged but make is suspect |
| four-winns-260-horizon | 🚫 | measurement lines and dimension marks baked into the image |

### Hurricane (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| hurricane-gs-170 | ⚠️ | base model has an image, all "likely compatible" Hurricane models show no image at all |

### Lund (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| lund-1775-adventure | ❓ | not individually verified |

### Maxum (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| maxum-2400-scr | ⚠️ | same pattern as Hurricane — base has image, "likely compatible" models show nothing |

### Rinker (4 patterns)
**Whole make needs re-source.**
| Slug | Status | Notes |
|------|--------|-------|
| rinker-232-captiva-br | 🚫 | solid black silhouette + blue measurement callouts — unusable |
| rinker-270-fv | 🚫 | line art covered in measurement text |
| rinker-282-br | 🚫 | mostly clean but has a faint baked-in caption to crop — lightest case |
| rinker-350-fv | 🚫 | washed out to near-invisible, "2007 Rinker 350 SP" ghosted across it |

### Sea Ray (27 patterns)
**Looks pretty good — should be verified individually.** This is the
strongest make in the builder. Sea Ray 260 Sundeck is the proven reference
(used to validate the per-piece renderer Wednesday night).
| Slug | Status |
|------|--------|
| sea-ray-175-sport | ❓ |
| sea-ray-180-sport | ❓ |
| sea-ray-185-sport | ❓ |
| sea-ray-190-sport | ❓ |
| sea-ray-190-spx | ❓ |
| sea-ray-195-sport | ❓ |
| sea-ray-200-select | ❓ |
| sea-ray-220-sundeck | ❓ |
| sea-ray-240-sundancer | ❓ |
| sea-ray-240-sundeck | ❓ |
| sea-ray-250-slx | ❓ |
| sea-ray-260-sundancer | ❓ |
| sea-ray-260-sundeck | ✅ proven reference |
| sea-ray-270-sundeck | ❓ |
| sea-ray-320-sundancer | ❓ |
| sea-ray-330-sundancer | ❓ |
| sea-ray-340-sundancer | ❓ |
| sea-ray-350-sundancer | ❓ |
| sea-ray-360-sundancer | ❓ |
| sea-ray-370-sundancer | ❓ |
| sea-ray-380-sundancer | ❓ |
| sea-ray-390-sundancer | ❓ |
| sea-ray-400-sundancer | ❓ |
| sea-ray-410-sundancer | ❓ |
| sea-ray-420-ac | ❓ |
| sea-ray-searayder-f-14 | ❓ |
| sea-ray-searayder-f-16 | ❓ |

### Wellcraft (1 pattern)
| Slug | Status | Notes |
|------|--------|-------|
| wellcraft-2600-martinique | 🚫 | photo / baked-in text |

---

## Tally

| Status | Count |
|--------|-------|
| ✅ verified clean | 4 (chaparral-230-ssi, chris-craft-200, chris-craft-launch-22, sea-ray-260-sundeck) |
| 🚫 flagged for re-source | 17 |
| ⚠️ partial / "likely compatible" gaps | 3 makes (Ebbtide, Hurricane, Maxum) |
| ❓ not individually tested | ~33 |
| ➖ no images at all | Crownline (entire make) |

---

## CMC source format observations (session 4)

CMC's uploads on Google Drive vary by brand:
- **Sea Ray** — 134 timestamped screenshot PNGs (no model info in filenames; would need to open each image to identify the model from its caption)
- **Ranger** — 19 FlexiSign `.FS` proprietary CAD files (Composite Document Format from 2012; not directly usable as images — would need FlexiSign software or a converter)

Action: emailed CMC to ask if they can provide the other brands in the
Sea Ray-style screenshot format (since FS files aren't directly usable).
Awaiting their response.

---

## Strategy going forward

1. **Don't tear down current images.** They function. Customers can complete orders. Bad-looking images are an aesthetic problem, not a blocker.
2. **Verify functionality on every pattern** — make sure renderer, color fill, and piece selection behave consistently for all 57 patterns. (This is the "make everything function like the Sea Ray 260" workstream.)
3. **Replace patterns brand-by-brand** as clean CMC sources arrive, prioritizing the worst-flagged first (Rinker, Bayliner, Wellcraft, Chaparral).
4. **Crownline and the "likely compatible" gaps** (Ebbtide, Hurricane, Maxum sub-models) need NEW sourcing — they have no images today.
