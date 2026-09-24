# Stream Deck+ button font sizing

## Key bitmap size

Companion maps Plus LCD keys as **120×120 px** each
(`generateButtonsGrid(4, 2, { width: 120, height: 120 })`).

Touch-strip segment canvas is separate (**800×100** px across the strip).

## How `fontsize` maps to pixels

In Companion layered text drawing:

```text
font_px = fontsize% × element_height_px / 100 / 1.2
```

`fontsize` is **percent of the text element height** (UI range 3–200).
Default when “auto” was used historically is **100**.

With a full-key text layer on a 120 px key:

| fontsize % | ≈ font_px |
|------------|-----------|
| 18 | 18 |
| 44 | 44 |
| 55 | 55 |
| 64 | 64 |
| 85 | 85 |
| 100 | 100 |

There is also ~**1.5%** padding inside the text box.

## Why 85% showed only two letters

With **Shrink to fit = off**, Companion:

1. Estimates a max character count from aspect ratio and font size.
2. **Truncates** the string to that count before drawing.
3. Does not scale the glyph down if it is too wide.

Large `%` + no shrink ⇒ huge glyphs and/or hard truncation. That is why
labels like `WORK` / `POINT` collapsed to about two letters.

## Practical rule for this demo

| Setting | Value | Why |
|---------|-------|-----|
| LCD `fontsize` | **42** | Fits 5-letter `POINT` on one line on 120 px keys |
| Strip `fontsize` | **70** | Strip is short; still readable |
| Knob `fontsize` | **50** | Smaller faces |
| `fontsizeAllowShrink` | **on** | Extra safety if labels grow |

Rough no-shrink fill for caps (width-limited, ~0.55×em):

- 3 letters → ~71%
- 4 letters → ~53%
- 5 letters (`POINT`) → ~42%

**58% still wrapped `WORK` / `POINT` in practice.** Use **42%** for LCD action labels.
