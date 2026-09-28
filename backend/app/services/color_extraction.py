"""
Dominant color extraction with background filtering.

Strategy: instead of rembg (which conflicts with torch's numpy<2 requirement),
we use a two-step approach:
  1. Filter out near-white and near-grey background pixels using HSV saturation
     and value thresholds — clothing items are almost always more saturated than
     a white/grey/beige photo background.
  2. Run PIL's median-cut quantisation on the *remaining* pixels, so only the
     garment's actual colours are considered.

This catches the vast majority of studio/product-photo backgrounds (white, off-
white, light grey, light beige) without any ML model or extra deps.
"""
from PIL import Image
import numpy as np


# Pixels with saturation below this threshold (0-255) are treated as
# "washed out" / background. Adjust up if too many garment colours are
# being stripped; adjust down if backgrounds still leak through.
_MIN_SATURATION = 30   # out of 255
_MIN_VALUE = 30        # ignore near-black shadows (also not garment colour)
_MAX_VALUE = 248       # ignore near-white background


def _make_garment_mask(rgb_arr: np.ndarray) -> np.ndarray:
    """
    Return a boolean mask (H, W) that is True for pixels that look like
    actual garment colours (sufficiently saturated, not near-white/black).

    Works on the HSV representation: background whites/greys have very low
    saturation; garment colours almost always have meaningful saturation.
    """
    # PIL HSV conversion gives H in [0,255], S in [0,255], V in [0,255]
    pil_img = Image.fromarray(rgb_arr, "RGB")
    hsv_arr = np.array(pil_img.convert("HSV"))
    s = hsv_arr[:, :, 1]
    v = hsv_arr[:, :, 2]
    return (s >= _MIN_SATURATION) & (v >= _MIN_VALUE) & (v <= _MAX_VALUE)


def extract_dominant_colors(image: Image.Image, num_colors: int = 3) -> list[str]:
    """
    Returns the top `num_colors` dominant garment colors as hex strings,
    ordered most-to-least dominant by pixel count.

    Background pixels (near-white, near-grey) are excluded before
    quantisation so they don't pollute the result.
    """
    # 1. Downscale — quantisation doesn't need full resolution
    small = image.convert("RGB").resize((150, 150), Image.LANCZOS)
    rgb_arr = np.array(small)

    # 2. Build background mask
    garment_mask = _make_garment_mask(rgb_arr)
    garment_pixels = rgb_arr[garment_mask]  # shape (N, 3)

    # 3. Fall back to full image if mask is too aggressive (< 5% pixels left)
    min_pixels = int(0.05 * rgb_arr.shape[0] * rgb_arr.shape[1])
    if len(garment_pixels) < min_pixels:
        # Image may be very light-coloured — skip masking
        quantized = small.quantize(colors=num_colors, method=Image.MEDIANCUT)
    else:
        # Rebuild a small PIL image from only the garment pixels and quantise
        n = len(garment_pixels)
        side = int(n ** 0.5) + 1
        padded = np.zeros((side * side, 3), dtype=np.uint8)
        padded[:n] = garment_pixels
        garment_img = Image.fromarray(padded.reshape(side, side, 3), "RGB")
        quantized = garment_img.quantize(colors=num_colors, method=Image.MEDIANCUT)

    # 4. Extract top colours from quantisation palette
    palette = quantized.getpalette()
    color_counts = sorted(quantized.getcolors() or [], reverse=True)

    hex_colors = []
    for _count, palette_idx in color_counts[:num_colors]:
        r, g, b = palette[palette_idx * 3: palette_idx * 3 + 3]
        hex_colors.append(f"#{r:02x}{g:02x}{b:02x}")

    # Pad to num_colors if quantisation returned fewer (shouldn't happen, but safe)
    while len(hex_colors) < num_colors:
        hex_colors.append("#000000")

    return hex_colors
