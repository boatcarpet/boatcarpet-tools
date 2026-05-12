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
