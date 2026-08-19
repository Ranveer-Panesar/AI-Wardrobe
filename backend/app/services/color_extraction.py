"""
Dominant color extraction via PIL's built-in median-cut color quantization —
no ML/extra heavy dependencies needed for this one, it's a solved problem
with classical image processing.
"""
from PIL import Image


def extract_dominant_colors(image: Image.Image, num_colors: int = 3) -> list[str]:
    """Returns the top `num_colors` dominant colors in the image as hex strings,
    ordered most-to-least dominant by pixel count."""
    # Downscale first — color quantization on a huge image is slow and the
    # dominant colors don't change meaningfully at lower resolution.
    small = image.convert("RGB").resize((150, 150))

    quantized = small.quantize(colors=num_colors, method=Image.MEDIANCUT)
    palette = quantized.getpalette()

    # getcolors() returns [(pixel_count, palette_index), ...]
    color_counts = sorted(quantized.getcolors(), reverse=True)

    hex_colors = []
    for _count, palette_idx in color_counts[:num_colors]:
        r, g, b = palette[palette_idx * 3 : palette_idx * 3 + 3]
        hex_colors.append(f"#{r:02x}{g:02x}{b:02x}")

    return hex_colors
