## v9.62.2 — Bugfix: berber/vinyl color not filling the pattern

- FIX: selecting a color (e.g. Oatmeal berber) left the pattern as a plain
  white outline - no texture, no color fill. Cause: v9.62 derived the swatch
  image path from the color NAME ("Oatmeal" -> "oatmeal" -> look up key
  "oatmeal-berber"). The color card name, the VINYL_COLORS id, and the swatch
  filename did not all agree, so the lookup missed and returned null.
- FIX approach: the swatch image path is now passed EXPLICITLY. Each color
  card / vinyl grid cell passes its own swatch path into selMat(), which
  stores it in new state field S.swatchSrc. The renderer reads S.swatchSrc
  directly. No name->id->path derivation, so there is no map to keep in sync
  and nothing to mismatch.
- selMat() / selVinyl() gained a swatchSrc parameter. Berber cards updated to
  pass their path; buildVinylGrid() emits a data-sw attribute the onclick
  reads. New state field: S.swatchSrc.
- Removed now-dead SWATCH_TEXTURES map and swatchTextureFor() (replaced with
  an explanatory note - nothing referenced them after this change).

## v9.62.1 — Bugfix: pattern images not loading from file://

- FIX: pattern images showed "Pattern image not found" when the builder was
  opened directly from disk (file://). Cause: v9.62's new _loadPatternImage()
  set img.crossOrigin="anonymous" unconditionally. On file:// Chrome treats a
  crossOrigin <img> as a blocked cross-origin request and refuses to load it,
  even though the file exists at the right path.
- crossOrigin is now set ONLY when the page is served over http(s) - it's
  needed there so canvas getImageData() works (e.g. on GitHub Pages), but on
  file:// the image is same-origin and getImageData works without it.
- Also removed the now-unused crossorigin attribute from the hidden
  #sb-pattern-img element (dead leftover; nothing loads through it).
- No functional change to the per-piece renderer itself - this only fixes
  image loading on local file:// testing.

## v9.62 — Per-piece pattern coloring (Option C renderer)

- NEW: `renderPatternColored()` replaces `renderTintedPattern()` as the pattern
  color entry point. Two automatic paths:
  - PER-PIECE: boats with an entry in the new `PATTERN_PIECES` config have
    each selected piece filled (texture or color) and each unselected piece
    drawn as outline-only. Every piece keeps its visible outline.
  - WHOLE-PATTERN FALLBACK: boats not in `PATTERN_PIECES` color the whole
    pattern interior — today's behavior. Nothing breaks; the per-piece
    feature "lights up" per-boat as piece files are added.
- NEW: `PATTERN_PIECES` config object (currently EMPTY — no boats split yet).
  Maps "Make|Model" -> [{id,img}] of per-piece image files. Piece ids must
  match SVG_DEFS piece ids. Pieces share the whole-pattern 1400px canvas.
- NEW: `SWATCH_TEXTURES` map + `swatchTextureFor()` — pieces/patterns can now
  be filled with the actual swatch TEXTURE (tiled), not just a flat color.
  Berber swatches mapped here; vinyl reuses VINYL_PHOTOS.
- NEW: shared helpers `_computeInterior()`, `_fillInterior()`,
  `_loadPatternImage()` (image-load retry + readable error box).
- CHANGE: outline detection threshold 150 -> 180. Many CMC patterns have
  faint thin lines; at 150 the flood-fill leaked through and the interior
  under-colored (the Sea Ray 320 was a clear case). 180 seals reliably.
- Back-compat shim: `renderTintedPattern()` still exists and routes to
  `renderPatternColored()`. Call site in `updSidebar` updated to call the
  new entry point directly.
- Build order from here: (1) this renderer [DONE], (2) piece-splitter tool,
  (3) split boats one at a time — Sea Ray 320 first as the proven template.

# v9.60 → v9.61 — Clean Pattern Merge (restandardized images)

## What changed
The builder's `patterns/` folder previously held a mix of low-resolution,
inconsistent images (some as small as 242×400px, formats split across
.png / .jpg / .webp). All 57 main patterns were replaced with the
restandardized set: uniformly 1400px-wide, clean, all `.webp`.

## How it was done
1. Copied 56 clean `.webp` files from `restandardized_full/` into
   `builder_v9_60/patterns/`, overwriting the old mixed-format files.
2. Deleted the 49 now-orphaned old `.png` / `.jpg` files.
3. Updated all 49 affected `PATTERN_IMGS` entries in `index.html` so every
   path ends in `.webp` (the 8 already-`.webp` entries needed no path change).
4. `patterns/variants/` (17 variant images) left completely untouched —
   variants use a separate naming scheme and are not part of the
   restandardized set.

## The 330 Sundancer exception — IMPORTANT
`sea-ray-330-sundancer.webp` was the ONE file NOT copied from
`restandardized_full/`. The restandardized 330 is the **stale pre-split
image** — it still has the "08-10" and "12 +-" labels baked in and shows
both pattern halves together. That image predates the v9.x 330-split work.
The builder's existing 330 (the clean "12 +-" half, with `sr330da-gen2`
as the "08-10" variant) was kept as-is. Do not let a future bulk-copy
overwrite it with the restandardized version.

## Integrity check
- 74 unique pattern references in `index.html` (57 main + 17 variant)
- 74 files exist on disk, 0 missing, 0 orphans
- All 58 `.webp` images served HTTP 200 in a local render test

## Still flagged (separate future task)
The CMC re-source list now stands at 12 patterns — see CMC_RESOURCE_LIST.md
for the full structured list with a per-pattern reason for each.
Session 2 flagged 8 (photos / baked-in text): bryant-236, cobalt-a25,
four-winns-190-horizon, rinker-232-captiva-br, wellcraft-2600-martinique,
bayliner-225, baja-202-islander, cruisers-yachts-375-aft-cabin.
Session 3 added the rest of the Rinker line — rinker-270-fv, rinker-282-br,
rinker-350-fv — after a visual audit showed the whole Rinker batch fails
the clean-line-art rule (measurements baked in, a solid-black silhouette,
and one washed-out near-invisible image). All were still merged in (better
than what was there before) but remain on the re-source list.

---

# v9.59 → v9.60 — Real Color Preview

## What changed
The sidebar pattern preview now shows the carpet **actually filled with the selected color** instead of just a tinted background.

## How it works
1. Pattern image is drawn onto an HTML5 canvas
2. JavaScript scans every pixel to identify:
   - **Outline pixels** (dark lines) → kept as-is
   - **Background pixels** (white area outside the carpet shape) → kept white
   - **Interior pixels** (inside the carpet shape) → replaced with the selected color
3. To handle gaps in CMC line drawings, the outline is dilated by 2 pixels before flood-fill so small breaks in lines don't cause color to leak out
4. Re-color is instant when customer changes color (image cached after first load)

## Technical details
- Replaced `<img>` in sidebar pattern preview with `<canvas>`
- Added `renderTintedPattern(imgSrc, canvas, colorHex)` function
- Uses `Uint8Array` flood-fill from corners — O(width × height), runs in <50ms for typical patterns
- Performance cap: images larger than 500px wide are downscaled before processing

## Known limitations
- Patterns that don't have a clean line-art format (Bryant 236 hand-drawn scan, Cobalt A25 CAD screenshot, etc.) will look weird — those need clean replacement images from CMC first
- Berber colors (Oatmeal, Gray) show as solid color — no texture overlay yet
- Vinyl colors show as solid color — vinyl swatches not yet used

## Future improvements (deferred)
- Composite actual berber/vinyl swatch texture into the interior instead of solid color
- Handle the 7 non-clean patterns (replace with CMC clean versions)

---

# v9.58 → v9.59 — CMC Patterns Batch 1

## New patterns added (4 new models)
- **Chris-Craft 200** (2000-2010) — `patterns/chris-craft-200.webp`
- **Chaparral 200** (2001-2003) — `patterns/chaparral-200.webp`
- **Chaparral 243 Sunesta** (2002) — `patterns/chaparral-243-sunesta.jpg`
- **Chaparral 285 SSi** (2004-2009) — `patterns/chaparral-285-ssi.webp` (previously fell back to 230 SSi)

## Pattern upgrade (1 file replaced)
- **Ebbtide 200 Campione** — replaced handwritten engineering print (`.png`) with clean CMC line drawing (`.jpg`)

## Data table changes
- `MD`: added "200" and "243 Sunesta" to Chaparral models list (285 SSi was already present)
- `MD`: added "200" to Chris-Craft models, expanded year range to 2000-2010
- `CMC_YEARS`: added year ranges for all 4 new patterns
- `VENDOR_SOURCE`: added "CMC" attribution for all 4 new patterns
- `PATTERN_FALLBACK`: removed obsolete "Chaparral|285 SSi" → "Chaparral|230 SSi" entry

## Stats
- Patterns folder: 53 → 57 files (4 new, 1 replaced)
- Models with exact pattern match: was 53, now 57
- Total models in builder dropdown: was 106, now 109

---

# v9.55 → v9.56 Refactor — CHANGELOG

## What stayed exactly the same
- All 80 pattern/swatch/illustration **images** (byte-identical — same JPEGs and PNGs from v9.55, just on disk instead of inlined as base64)
- All 18 makes, 106 model entries, year ranges in `MD`
- `CMC_SET` (which boats have a pattern)
- `CMC_YEARS` (confirmed year ranges per pattern)
- `PATTERN_VARIANTS` (probable-pattern gallery)
- `PIECES` definitions and per-boat piece layouts
- The Sea Ray piece-selection SVG visualization
- Step flow (Model → Pieces → Color → Pricing → Order)
- Color picker UI (berber + vinyl)
- Custom binding picker
- Quote/order email workflow
- UPS zip-table shipping estimator (`estUPS`) — unchanged on purpose; will be replaced when UPS API integration lands

## What changed

### File structure
- `BoatCarpet_v9_55_2.html` (3.4 MB single file)
  - became
- `index.html` (164 KB) + `patterns/` + `patterns/variants/` + `assets/` + `assets/swatches/`

### Pricing formula
- **Before** (v9.55): `Math.round((sy × pricePerSY + 250) / 0.70 / 0.65) + ups + binding`
- **After** (v9.56): `Math.round((sy × pricePerSY + sy × 50) × 1.30 × 1.30) + ups + binding`
- Constants line changed from:
  ```js
  const S_BERBER=17.50,S_VINYL=27.50,S_CUT=250,S_MFG=0.70,S_RET=0.65,S_CMC_H=75;
  ```
  to:
  ```js
  const S_BERBER=17.50,S_VINYL=27.50,S_LABOR_SY=50,S_CMC_MULT=1.30,S_RET_MULT=1.30;
  ```

#### Worked example for a 10 sy boat (test UPS = $120)
| Component | v9.55 result | v9.56 result |
|---|---|---|
| Materials (sy × $17.50) | $175 | $175 |
| Labor | $250 flat | $500 (10 × $50) |
| Base | $425 | $675 |
| After CMC markup | $607 (÷ 0.70) | $878 (× 1.30) |
| After retail markup | **$934** (÷ 0.65) | **$1,141** (× 1.30) |
| + UPS | $1,054 | $1,261 |

### Cleanup
- Removed dead `CMC_PRICES` table (defined in v9.55 but never read anywhere)
- Removed `S_CUT`, `S_MFG`, `S_RET`, `S_CMC_H` constants (no longer used)

## What's deferred
- UPS API integration (will need credentials, serverless proxy function — separate work)
- Loading state / preload behavior (kept v9.55's behavior: no skeleton, browser-native image loading)
- Migration to folder-based catalog (`patterns.json`) — current `MD` / `CMC_SET` / `CMC_YEARS` structure preserved; can be unified later when CMC bulk-sync is built

## How to deploy
1. Drop `index.html` + `patterns/` + `assets/` into your GitHub Pages repo
2. Push → site goes live
3. Test a quote on any boat — pricing should match the v9.56 column above

## How to add new patterns going forward
Two paths until the unified `patterns.json` exists:
1. **Image**: drop `make-model-slug.jpg` (or `.png`) into `patterns/`
2. **Catalog entry**: add to `MD`, `CMC_SET`, and (if confirmed) `CMC_YEARS` in `index.html`

After CMC bulk-sync ships, this becomes "drop file in `inbox/` → run `organize_patterns.py` → push." That's the work for v9.57+.
