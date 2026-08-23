"""
Rule-based outfit combination engine (Phase 3).

Pure Python — no DB imports, no FastAPI — so every function here is directly
unit-testable without any mocking or test-client overhead.

Architecture
────────────
1.  Category taxonomy: map raw CLIP labels → 5 abstract types
    (TOP / BOTTOM / OUTERWEAR / FOOTWEAR / DRESS).

2.  Scoring functions (each → 0–1 float):
    • color_harmony_score   — HSL hue-distance analysis
    • formality_score       — penalises mixed formality levels
    • pattern_clash_penalty — penalises clashing non-solid patterns
    • category_structure_score — rewards "complete" looks

3.  Composite scorer: weighted sum of the above.

4.  Style tag assignment: heuristic mapping → {"casual", "bold", "formal", "retro"}.

5.  Combination generator: enumerates valid combos from the user's wardrobe,
    scores each, deduplicates, and returns the top-N.
"""
from __future__ import annotations

import colorsys
import itertools
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple


# ---------------------------------------------------------------------------
# 1. Category taxonomy
# ---------------------------------------------------------------------------

class CategoryType(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    OUTERWEAR = "outerwear"
    FOOTWEAR = "footwear"
    DRESS = "dress"
    UNKNOWN = "unknown"


# Maps the free-text labels produced by Fashion-CLIP → abstract type.
# Extend this dict as new CATEGORY_LABELS are added to classification.py.
_CATEGORY_MAP: dict[str, CategoryType] = {
    "t-shirt": CategoryType.TOP,
    "casual shirt": CategoryType.TOP,
    "formal shirt": CategoryType.TOP,
    "polo shirt": CategoryType.TOP,
    "sweater": CategoryType.TOP,
    "jeans": CategoryType.BOTTOM,
    "formal trousers": CategoryType.BOTTOM,
    "shorts": CategoryType.BOTTOM,
    "joggers": CategoryType.BOTTOM,
    "skirt": CategoryType.BOTTOM,
    "jacket": CategoryType.OUTERWEAR,
    "hoodie": CategoryType.OUTERWEAR,
    "blazer": CategoryType.OUTERWEAR,
    "dress": CategoryType.DRESS,
}


def get_category_type(category: str) -> CategoryType:
    """Map a raw label (case-insensitive) to an abstract CategoryType."""
    return _CATEGORY_MAP.get(category.lower().strip(), CategoryType.UNKNOWN)


# ---------------------------------------------------------------------------
# 2a. Color harmony scoring
# ---------------------------------------------------------------------------

def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert '#rrggbb' to (H 0–360, S 0–1, L 0–1)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l


def _is_neutral(s: float, l: float) -> bool:
    """Low-saturation or very light/dark colours are neutral (black/white/grey/beige)."""
    return s < 0.15 or l < 0.12 or l > 0.88


def _hue_distance(h1: float, h2: float) -> float:
    """Shortest angular distance between two hues on the colour wheel (0–180)."""
    d = abs(h1 - h2) % 360
    return d if d <= 180 else 360 - d


def color_harmony_score(colors_a: list[str], colors_b: list[str]) -> float:
    """
    Score how well two garments' dominant colour palettes harmonise.

    Logic (applied to the *most dominant* colour of each garment):
    • Both neutral                → 0.90  (safe, classic, never clashes)
    • One neutral + one chromatic → 0.85  (neutral grounds any colour)
    • Analogous  (Δhue ≤ 30°)    → 1.00  (monochromatic / close-family)
    • Split-complementary (150–210°) → 0.75
    • Complementary (165–195°)   → 0.90  (intentional contrast)
    • Triadic / tetradic zone     → 0.60
    • Clashing (everything else)  → 0.35
    """
    if not colors_a or not colors_b:
        return 0.5  # no colour info — neutral assumption

    try:
        h_a, s_a, l_a = _hex_to_hsl(colors_a[0])
        h_b, s_b, l_b = _hex_to_hsl(colors_b[0])
    except (ValueError, IndexError):
        return 0.5

    neutral_a = _is_neutral(s_a, l_a)
    neutral_b = _is_neutral(s_b, l_b)

    if neutral_a and neutral_b:
        return 0.90
    if neutral_a or neutral_b:
        return 0.85

    d = _hue_distance(h_a, h_b)

    if d <= 30:
        return 1.00   # analogous
    if d <= 60:
        return 0.80   # close analogous
    if 150 <= d <= 210:
        return 0.75   # split-complementary / complementary
    if 165 <= d <= 195:
        return 0.90   # true complementary (sub-range override handled via check order)
    if 110 <= d <= 150 or 210 <= d <= 250:
        return 0.60   # triadic
    return 0.35       # clashing zone


def color_harmony_score_for_outfit(garments: list["GarmentData"]) -> float:
    """
    Average pairwise colour harmony across all garments in the outfit.
    Uses only adjacent pairs in category order (top→bottom→outerwear) to
    avoid O(n²) explosion on large wardrobes.
    """
    if len(garments) <= 1:
        return 1.0
    scores = []
    for i in range(len(garments) - 1):
        s = color_harmony_score(garments[i].dominant_colors, garments[i + 1].dominant_colors)
        scores.append(s)
    return sum(scores) / len(scores)


# ---------------------------------------------------------------------------
# 2b. Formality coherence scoring
# ---------------------------------------------------------------------------

_FORMALITY_LEVEL: dict[str, int] = {
    "very casual": 0,
    "casual": 1,
    "smart casual": 2,
    "formal": 3,
}


def formality_score(formalities: list[str]) -> float:
    """
    Score how well garment formality levels match each other.
    Low std-dev (everyone at the same level) → score near 1.
    High std-dev (e.g. mixing very casual + formal) → score near 0.
    """
    levels = [_FORMALITY_LEVEL.get(f.lower().strip(), 1) for f in formalities]
    if len(levels) <= 1:
        return 1.0

    mean = sum(levels) / len(levels)
    variance = sum((x - mean) ** 2 for x in levels) / len(levels)
    std_dev = math.sqrt(variance)

    # Max possible std-dev for 4 levels (0–3) is ~1.5; normalise and invert.
    # Clamp to [0, 1] in case of degenerate inputs.
    return max(0.0, 1.0 - (std_dev / 1.5))


# ---------------------------------------------------------------------------
# 2c. Pattern clash penalty
# ---------------------------------------------------------------------------

# These patterns are "busy" — two busy patterns in the same outfit = clash.
_BUSY_PATTERNS = {"striped", "checked", "floral", "polka dot", "graphic print"}


def pattern_clash_penalty(patterns: list[str]) -> float:
    """
    Returns a penalty value in [0, 1]; apply as: score × (1 − penalty).

    Rules:
    • ≥ 2 distinct busy patterns            → 0.35 penalty
    • Same busy pattern repeated (e.g. two stripes) → 0.15 penalty
    • ≤ 1 busy pattern (solid + anything)   → 0.0  penalty
    """
    busy = [p.lower().strip() for p in patterns if p.lower().strip() in _BUSY_PATTERNS]
    if len(busy) < 2:
        return 0.0
    if len(set(busy)) == 1:
        # Same pattern repeated — slightly off but not a full clash.
        return 0.15
    return 0.35


# ---------------------------------------------------------------------------
# 2d. Category structure scoring
# ---------------------------------------------------------------------------

# Valid structural templates for a complete outfit, in order of desirability.
# Each entry is a frozenset of CategoryTypes that constitutes a "look".
_COMPLETE_LOOKS: list[frozenset[CategoryType]] = [
    frozenset({CategoryType.TOP, CategoryType.BOTTOM, CategoryType.OUTERWEAR, CategoryType.FOOTWEAR}),
    frozenset({CategoryType.DRESS, CategoryType.OUTERWEAR, CategoryType.FOOTWEAR}),
    frozenset({CategoryType.TOP, CategoryType.BOTTOM, CategoryType.OUTERWEAR}),
    frozenset({CategoryType.DRESS, CategoryType.OUTERWEAR}),
    frozenset({CategoryType.TOP, CategoryType.BOTTOM, CategoryType.FOOTWEAR}),
    frozenset({CategoryType.TOP, CategoryType.BOTTOM}),
    frozenset({CategoryType.DRESS, CategoryType.FOOTWEAR}),
    frozenset({CategoryType.DRESS}),
]

_PARTIAL_LOOKS: list[frozenset[CategoryType]] = [
    frozenset({CategoryType.TOP, CategoryType.OUTERWEAR}),
]


def category_structure_score(categories: list[str]) -> float:
    """
    Score how structurally complete an outfit is.
    1.0 → covers a recognised complete look template.
    0.5 → partial (e.g. top + outerwear, no bottom).
    0.1 → no recognisable structure.
    """
    types = frozenset(get_category_type(c) for c in categories) - {CategoryType.UNKNOWN}

    for look in _COMPLETE_LOOKS:
        if look.issubset(types):
            # Bonus for wearing footwear
            base = 1.0
            return base

    for look in _PARTIAL_LOOKS:
        if look.issubset(types):
            return 0.5

    return 0.1


# ---------------------------------------------------------------------------
# 3. Composite score
# ---------------------------------------------------------------------------

WEIGHT_COLOR = 0.35
WEIGHT_FORMALITY = 0.25
WEIGHT_STRUCTURE = 0.25
WEIGHT_PATTERN = 0.15


@dataclass
class GarmentData:
    """
    Lightweight in-memory representation of a garment used by the engine.
    Constructed from the ORM Garment objects by the outfit service — keeps
    the engine free of SQLAlchemy imports.
    """
    id: str
    category: str
    pattern: str
    formality: str
    dominant_colors: list[str] = field(default_factory=list)

    @property
    def category_type(self) -> CategoryType:
        return get_category_type(self.category)


def score_outfit(garments: list[GarmentData]) -> float:
    """
    Compute a 0–1 composite compatibility score for a set of garments.
    Higher is better.
    """
    categories = [g.category for g in garments]
    patterns = [g.pattern for g in garments]
    formalities = [g.formality for g in garments]

    color_h = color_harmony_score_for_outfit(garments)
    formality_h = formality_score(formalities)
    structure_h = category_structure_score(categories)
    pattern_pen = pattern_clash_penalty(patterns)

    composite = (
        WEIGHT_COLOR * color_h
        + WEIGHT_FORMALITY * formality_h
        + WEIGHT_STRUCTURE * structure_h
        + WEIGHT_PATTERN * (1.0 - pattern_pen)
    )
    return round(min(max(composite, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# 4. Style tag assignment
# ---------------------------------------------------------------------------

def assign_style_tags(garments: list[GarmentData]) -> dict[str, float]:
    """
    Heuristic style probability breakdown over four axes.
    Values are intentionally not a strict probability distribution —
    a single outfit can be partly casual and partly bold.

    Returns: {"casual": float, "bold": float, "formal": float, "retro": float}
    """
    formalities = [g.formality.lower().strip() for g in garments]
    patterns = [g.pattern.lower().strip() for g in garments]

    # --- Formality axis ---
    avg_formality = sum(_FORMALITY_LEVEL.get(f, 1) for f in formalities) / max(len(formalities), 1)

    formal_score = round(min(avg_formality / 3.0, 1.0), 3)
    casual_score = round(1.0 - formal_score, 3)

    # --- Bold axis — graphic prints or very high colour contrast ---
    has_graphic = any(p in {"graphic print", "floral"} for p in patterns)
    bold_score = round(0.6 if has_graphic else 0.1, 3)

    # --- Retro axis — checked / polka dot patterns at mid-formality ---
    has_retro_pattern = any(p in {"checked", "polka dot"} for p in patterns)
    retro_score = round(0.5 if (has_retro_pattern and 0.5 <= avg_formality <= 2.5) else 0.05, 3)

    # Normalise so values are bounded, even if they don't sum to 1.
    # Frontend can display these as independent "vibes" rather than a pie chart.
    return {
        "casual": casual_score,
        "bold": bold_score,
        "formal": formal_score,
        "retro": retro_score,
    }


# ---------------------------------------------------------------------------
# 5. Combination generator
# ---------------------------------------------------------------------------

class ScoredOutfit(NamedTuple):
    garment_ids: list[str]
    score: float
    style_tags: dict[str, float]


def _is_valid_combo(garments: list[GarmentData]) -> bool:
    """
    A combo is valid if it contains at least one structurally meaningful
    look: (TOP + BOTTOM) or (DRESS) — i.e. the wearer isn't just layering
    two jackets over nothing.
    Also rejects combos that mix a DRESS with a TOP or BOTTOM (dress replaces
    both, adding either makes no sense).
    """
    types = [g.category_type for g in garments]
    type_set = set(types)

    has_dress = CategoryType.DRESS in type_set
    has_top = CategoryType.TOP in type_set
    has_bottom = CategoryType.BOTTOM in type_set

    if has_dress and (has_top or has_bottom):
        return False  # DRESS + TOP or DRESS + BOTTOM doesn't make sense

    if has_dress:
        return True   # DRESS alone (+ optional OUTERWEAR/FOOTWEAR) is complete

    if has_top and has_bottom:
        return True   # classic TOP + BOTTOM (+ optional layers)

    return False  # incomplete — e.g. two jackets, or just a shirt alone


def generate_outfits(
    garments: list[GarmentData],
    count: int = 5,
) -> list[ScoredOutfit]:
    """
    Generate and rank the top `count` outfit combinations from a user's wardrobe.

    Strategy:
    ─────────
    1. Group garments by CategoryType bucket.
    2. Build candidate combos by exhaustively combining:
       • Every (top, bottom) pair  — the core of most outfits
       • Every (top, bottom, outerwear) triple
       • Every (dress,) singleton
       • Every (dress, outerwear) pair
       • Optionally append footwear to any of the above
    3. Filter invalid combos.
    4. Score each combo.
    5. Deduplicate (frozenset of IDs — order doesn't matter for a set of clothes).
    6. Sort descending, return top N.
    """
    if not garments:
        return []

    # Bucket garments by type
    buckets: dict[CategoryType, list[GarmentData]] = {t: [] for t in CategoryType}
    for g in garments:
        buckets[g.category_type].append(g)

    tops = buckets[CategoryType.TOP]
    bottoms = buckets[CategoryType.BOTTOM]
    outerwear = buckets[CategoryType.OUTERWEAR]
    footwear = buckets[CategoryType.FOOTWEAR]
    dresses = buckets[CategoryType.DRESS]

    # Footwear is optional; include "no footwear" as a candidate too.
    footwear_options: list[list[GarmentData]] = [[]] + [[f] for f in footwear]

    candidates: list[list[GarmentData]] = []

    # TOP + BOTTOM (± OUTERWEAR) (± FOOTWEAR)
    for top, bottom in itertools.product(tops, bottoms):
        base = [top, bottom]
        # With and without outerwear
        outerwear_options: list[list[GarmentData]] = [[]] + [[o] for o in outerwear]
        for ow, fw in itertools.product(outerwear_options, footwear_options):
            candidates.append(base + ow + fw)

    # DRESS (± OUTERWEAR) (± FOOTWEAR)
    for dress in dresses:
        base = [dress]
        outerwear_options_d: list[list[GarmentData]] = [[]] + [[o] for o in outerwear]
        for ow, fw in itertools.product(outerwear_options_d, footwear_options):
            candidates.append(base + ow + fw)

    seen: set[frozenset[str]] = set()
    scored: list[ScoredOutfit] = []

    for combo in candidates:
        if not _is_valid_combo(combo):
            continue

        key = frozenset(g.id for g in combo)
        if key in seen:
            continue
        seen.add(key)

        s = score_outfit(combo)
        tags = assign_style_tags(combo)
        scored.append(ScoredOutfit(
            garment_ids=[g.id for g in combo],
            score=s,
            style_tags=tags,
        ))

    scored.sort(key=lambda o: o.score, reverse=True)
    return scored[:count]
