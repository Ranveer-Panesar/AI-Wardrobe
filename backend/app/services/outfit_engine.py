"""
Rule-based outfit combination engine (Phase 3 & Occasion-Aware AI Stylist).

Pure Python — no DB imports, no FastAPI — directly unit-testable.

Architecture
────────────
1.  Category taxonomy: map raw CLIP labels → 5 abstract types
    (TOP / BOTTOM / OUTERWEAR / FOOTWEAR / DRESS).

2.  Occasion & Context Scoring (0–1 float):
    • occasion_affinity_score — evaluates alignment with target event
      (sport, casual, business, formal, evening, wedding) and applies
      strict conflict penalties for inappropriate items (e.g. blazers in sport,
      gym shorts in formal).
    • season_affinity_score   — checks thermal comfort and seasonal layering.
    • style_affinity_score    — matches style aesthetics (Athleisure, Streetwear, etc.).

3.  Aesthetic Scoring:
    • color_harmony_score     — HSL hue-distance & wheel harmony.
    • formality_score         — standard deviation across pieces.
    • pattern_clash_penalty   — busy vs solid pattern clash.
    • category_structure_score — rewards complete looks (top + bottom ± layers).

4.  Composite Scorer:
    Weighted sum multiplied by occasion conflict penalty.

5.  Curated Presentation:
    • Dynamic naming: e.g. "Athletic Motion Set", "Polished Business Casual".
    • Smart reasoning: clear justification of why the look works for the occasion.
    • Style tag assignment: heuristic probability breakdown.
"""
from __future__ import annotations

import colorsys
import itertools
import math
from dataclasses import dataclass, field
from enum import Enum


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
_CATEGORY_MAP: dict[str, CategoryType] = {
    "t-shirt": CategoryType.TOP,
    "tshirt": CategoryType.TOP,
    "tee": CategoryType.TOP,
    "tank top": CategoryType.TOP,
    "casual shirt": CategoryType.TOP,
    "formal shirt": CategoryType.TOP,
    "shirt": CategoryType.TOP,
    "polo shirt": CategoryType.TOP,
    "polo": CategoryType.TOP,
    "sweater": CategoryType.TOP,
    "sweatshirt": CategoryType.TOP,
    "jeans": CategoryType.BOTTOM,
    "formal trousers": CategoryType.BOTTOM,
    "trousers": CategoryType.BOTTOM,
    "chinos": CategoryType.BOTTOM,
    "pants": CategoryType.BOTTOM,
    "shorts": CategoryType.BOTTOM,
    "joggers": CategoryType.BOTTOM,
    "sweatpants": CategoryType.BOTTOM,
    "skirt": CategoryType.BOTTOM,
    "jacket": CategoryType.OUTERWEAR,
    "hoodie": CategoryType.OUTERWEAR,
    "blazer": CategoryType.OUTERWEAR,
    "coat": CategoryType.OUTERWEAR,
    "cardigan": CategoryType.OUTERWEAR,
    "dress": CategoryType.DRESS,
    "suit": CategoryType.OUTERWEAR,
    "sneakers": CategoryType.FOOTWEAR,
    "shoes": CategoryType.FOOTWEAR,
    "boots": CategoryType.FOOTWEAR,
}


def get_category_type(category: str) -> CategoryType:
    """Map a raw label (case-insensitive) to an abstract CategoryType."""
    cat = category.lower().strip()
    for key, val in _CATEGORY_MAP.items():
        if key in cat or cat in key:
            return val
    return CategoryType.UNKNOWN


# ---------------------------------------------------------------------------
# 2. Color harmony scoring
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
    """
    if not colors_a or not colors_b:
        return 0.5

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
        return 0.90   # true complementary
    if 110 <= d <= 150 or 210 <= d <= 250:
        return 0.60   # triadic
    return 0.35       # clashing zone


def color_harmony_score_for_outfit(garments: list["GarmentData"]) -> float:
    """
    Average pairwise colour harmony across all garments in the outfit.
    """
    if len(garments) <= 1:
        return 1.0
    scores = []
    for i in range(len(garments) - 1):
        s = color_harmony_score(garments[i].dominant_colors, garments[i + 1].dominant_colors)
        scores.append(s)
    return sum(scores) / len(scores)


# ---------------------------------------------------------------------------
# 3. Formality coherence scoring
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
    Low std-dev → near 1. High std-dev → near 0.
    """
    levels = [_FORMALITY_LEVEL.get(f.lower().strip(), 1) for f in formalities]
    if len(levels) <= 1:
        return 1.0

    mean = sum(levels) / len(levels)
    variance = sum((x - mean) ** 2 for x in levels) / len(levels)
    std_dev = math.sqrt(variance)

    return max(0.0, 1.0 - (std_dev / 1.5))


# ---------------------------------------------------------------------------
# 4. Pattern clash penalty
# ---------------------------------------------------------------------------

_BUSY_PATTERNS = {"striped", "checked", "floral", "polka dot", "graphic print"}


def pattern_clash_penalty(patterns: list[str]) -> float:
    """
    Returns penalty in [0, 1]; apply as: (1 - penalty).
    """
    busy = [p.lower().strip() for p in patterns if p.lower().strip() in _BUSY_PATTERNS]
    if len(busy) < 2:
        return 0.0
    if len(set(busy)) == 1:
        return 0.15
    return 0.35


# ---------------------------------------------------------------------------
# 5. Category structure scoring
# ---------------------------------------------------------------------------

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
    types = frozenset(get_category_type(c) for c in categories) - {CategoryType.UNKNOWN}

    for look in _COMPLETE_LOOKS:
        if look.issubset(types):
            return 1.0

    for look in _PARTIAL_LOOKS:
        if look.issubset(types):
            return 0.5

    return 0.1


# ---------------------------------------------------------------------------
# 6. Occasion Affinity & Conflict Penalties
# ---------------------------------------------------------------------------

# Per-occasion category affinity weights (0.0 to 1.0).
# Items below 0.10 are treated as hard conflicts that destroy the outfit's suitability.
_OCCASION_AFFINITY: dict[str, dict[str, float]] = {
    "sport": {
        "shorts": 1.0,
        "joggers": 1.0,
        "sweatpants": 1.0,
        "t-shirt": 0.95,
        "tank top": 0.95,
        "hoodie": 0.85,
        "sweatshirt": 0.80,
        "sneakers": 1.0,
        "jacket": 0.50,          # Windbreaker/track jacket
        "polo shirt": 0.35,      # Tennis/golf acceptable but penalized vs active tees
        "jeans": 0.005,          # HEAVILY PENALIZED: Denim is strictly prohibited in sport
        "casual shirt": 0.005,   # HEAVILY PENALIZED: Button-up shirts are strictly prohibited in sport
        "formal shirt": 0.001,   # HEAVILY PENALIZED: Dress shirts are strictly prohibited in sport
        "shirt": 0.005,          # HEAVILY PENALIZED
        "button-down": 0.005,    # HEAVILY PENALIZED
        "sweater": 0.02,         # Heavy penalty
        "cardigan": 0.005,       # HEAVILY PENALIZED
        "skirt": 0.20,           # Tennis skirt only
        "dress": 0.005,          # STRICT CONFLICT
        "formal trousers": 0.001,# STRICT CONFLICT: No suit pants in sport!
        "trousers": 0.005,       # STRICT CONFLICT
        "chinos": 0.005,         # STRICT CONFLICT
        "blazer": 0.001,         # STRICT CONFLICT: Absolutely NO blazers in sport!
        "coat": 0.001,
        "suit": 0.001,
    },
    "casual": {
        "t-shirt": 1.0,
        "jeans": 1.0,
        "casual shirt": 0.95,
        "polo shirt": 0.90,
        "shorts": 0.90,
        "jacket": 0.85,
        "hoodie": 0.90,
        "sweater": 0.85,
        "sweatshirt": 0.85,
        "joggers": 0.80,
        "sneakers": 1.0,
        "skirt": 0.80,
        "dress": 0.80,
        "formal trousers": 0.45,
        "formal shirt": 0.45,
        "blazer": 0.40,
        "coat": 0.50,
        "suit": 0.15,
    },
    "business": {
        "formal trousers": 1.0,
        "formal shirt": 1.0,
        "blazer": 1.0,
        "suit": 1.0,
        "chinos": 0.95,
        "polo shirt": 0.80,
        "casual shirt": 0.85,
        "sweater": 0.80,
        "cardigan": 0.80,
        "skirt": 0.90,
        "dress": 0.85,
        "coat": 0.90,
        "jacket": 0.50,
        "jeans": 0.40,
        "t-shirt": 0.20,
        "hoodie": 0.01,         # STRICT CONFLICT
        "shorts": 0.005,        # STRICT CONFLICT: No shorts in business!
        "joggers": 0.005,       # STRICT CONFLICT: No joggers in business!
        "sweatpants": 0.005,
    },
    "formal": {
        "formal trousers": 1.0,
        "formal shirt": 1.0,
        "blazer": 1.0,
        "suit": 1.0,
        "dress": 1.0,
        "coat": 0.90,
        "skirt": 0.85,
        "sweater": 0.35,
        "polo shirt": 0.20,
        "casual shirt": 0.25,
        "jeans": 0.01,          # STRICT CONFLICT: No jeans in formal!
        "t-shirt": 0.01,        # STRICT CONFLICT: No tees in formal!
        "hoodie": 0.001,        # STRICT CONFLICT
        "shorts": 0.001,        # STRICT CONFLICT
        "joggers": 0.001,       # STRICT CONFLICT
        "sweatpants": 0.001,
    },
    "evening": {
        "blazer": 1.0,
        "formal trousers": 0.95,
        "dress": 1.0,
        "formal shirt": 0.90,
        "casual shirt": 0.85,
        "jeans": 0.65,
        "polo shirt": 0.65,
        "sweater": 0.70,
        "jacket": 0.75,
        "coat": 0.85,
        "t-shirt": 0.45,
        "skirt": 0.85,
        "shorts": 0.05,
        "joggers": 0.01,
        "hoodie": 0.10,
    },
    "wedding": {
        "suit": 1.0,
        "blazer": 1.0,
        "formal shirt": 1.0,
        "formal trousers": 1.0,
        "dress": 1.0,
        "coat": 0.85,
        "skirt": 0.80,
        "polo shirt": 0.15,
        "casual shirt": 0.20,
        "sweater": 0.20,
        "jeans": 0.005,         # STRICT CONFLICT
        "t-shirt": 0.001,       # STRICT CONFLICT
        "hoodie": 0.001,        # STRICT CONFLICT
        "shorts": 0.001,        # STRICT CONFLICT
        "joggers": 0.001,       # STRICT CONFLICT
        "sweatpants": 0.001,
    },
}


def occasion_affinity_score(garments: list["GarmentData"], target_occasion: str = "casual") -> tuple[float, float]:
    """
    Calculate occasion alignment score and hard conflict multiplier.
    Returns: (affinity_score [0..1], conflict_multiplier [0..1]).
    If any piece is severely clashing with the occasion (e.g. shirt or jeans in sport),
    conflict_multiplier drops drastically to heavily penalize and disqualify the combination.
    """
    occ = target_occasion.lower().strip()
    if occ not in _OCCASION_AFFINITY:
        occ = "casual"

    affinity_table = _OCCASION_AFFINITY[occ]

    affinities = []
    conflict_mult = 1.0

    for g in garments:
        cat = g.category.lower().strip()
        # Find best matching category in table
        aff = 0.5
        for k, v in affinity_table.items():
            if k in cat or cat in k:
                aff = v
                break

        affinities.append(aff)

        # Apply hard conflict if item affinity is below threshold
        if aff <= 0.10:
            conflict_mult *= aff

        # Occasion vs formality mismatch
        formality = g.formality.lower().strip()
        if occ in ("sport",) and formality in ("formal", "smart casual"):
            conflict_mult *= 0.10
        elif occ in ("formal", "wedding") and formality in ("very casual",):
            conflict_mult *= 0.01

        # Direct explicit conflict penalties
        if occ == "sport":
            # Heavily penalize any jeans / denim
            if any(term in cat for term in ("jean", "denim")):
                conflict_mult *= 0.02
            # Heavily penalize button-down, formal, casual, or dress shirts
            if "shirt" in cat and "t-shirt" not in cat and "sweatshirt" not in cat:
                if "polo" in cat:
                    conflict_mult *= 0.40  # Polo is demoted in active sportswear
                else:
                    conflict_mult *= 0.02  # Shirts heavily penalized in sport
            # Strictly disqualify blazers, suits, formal trousers, chinos, coats
            if any(term in cat for term in ("trouser", "chino", "blazer", "suit", "coat", "slacks")):
                conflict_mult *= 0.001

        elif occ in ("formal", "wedding"):
            if any(term in cat for term in ("jean", "denim", "short", "jogger", "sweatpant", "hoodie", "tee", "t-shirt")):
                conflict_mult *= 0.02

        elif occ == "business":
            if any(term in cat for term in ("short", "jogger", "sweatpant", "hoodie")):
                conflict_mult *= 0.01

    base_affinity = sum(affinities) / max(len(affinities), 1)
    return base_affinity, max(0.0001, conflict_mult)


# ---------------------------------------------------------------------------
# 7. Season & Style Affinity
# ---------------------------------------------------------------------------

def season_affinity_score(garments: list["GarmentData"], season: str | None = None) -> float:
    if not season:
        return 1.0

    s = season.lower().strip()
    has_outerwear = any(g.category_type == CategoryType.OUTERWEAR for g in garments)
    has_shorts = any("short" in g.category.lower() for g in garments)
    has_sweater = any("sweater" in g.category.lower() or "hoodie" in g.category.lower() for g in garments)

    if "summer" in s:
        score = 0.95
        if has_shorts:
            score += 0.05
        if has_outerwear:
            score -= 0.35  # heavy blazers in hot summer
        if has_sweater:
            score -= 0.40
        return max(0.2, min(score, 1.0))

    if "winter" in s:
        score = 0.70
        if has_outerwear or has_sweater:
            score += 0.30
        if has_shorts:
            score -= 0.60  # shorts in winter
        return max(0.1, min(score, 1.0))

    if "autumn" in s or "spring" in s:
        return 0.95

    return 1.0


_STYLE_CATEGORY_AFFINITY: dict[str, dict[str, float]] = {
    "athleisure": {
        "joggers": 1.0, "shorts": 0.95, "t-shirt": 0.95, "hoodie": 0.95,
        "polo shirt": 0.85, "sneakers": 1.0, "blazer": 0.05, "formal trousers": 0.05
    },
    "streetwear": {
        "hoodie": 1.0, "t-shirt": 0.95, "jeans": 0.95, "joggers": 0.85,
        "jacket": 0.90, "blazer": 0.20, "formal trousers": 0.20
    },
    "classic": {
        "polo shirt": 0.95, "casual shirt": 0.95, "formal shirt": 0.90,
        "jeans": 0.90, "formal trousers": 0.90, "blazer": 0.90, "sweater": 0.90
    },
    "minimalist": {
        "polo shirt": 0.95, "t-shirt": 0.95, "formal trousers": 0.90,
        "jeans": 0.90, "blazer": 0.90
    },
    "vintage": {
        "casual shirt": 0.95, "jacket": 0.90, "jeans": 0.90, "sweater": 0.90
    },
    "bohemian": {
        "casual shirt": 0.95, "skirt": 0.95, "dress": 0.95
    },
}


def style_affinity_score(garments: list["GarmentData"], style: str | None = None) -> float:
    if not style:
        return 1.0

    st = style.lower().strip()
    table = _STYLE_CATEGORY_AFFINITY.get(st)
    if not table:
        return 1.0

    scores = []
    for g in garments:
        cat = g.category.lower().strip()
        score = 0.5
        for k, v in table.items():
            if k in cat or cat in k:
                score = v
                break
        scores.append(score)

    return sum(scores) / max(len(scores), 1)


# ---------------------------------------------------------------------------
# 8. Composite outfit scoring
# ---------------------------------------------------------------------------

@dataclass
class GarmentData:
    """Lightweight in-memory representation of a garment used by the engine."""
    id: str
    category: str
    pattern: str
    formality: str
    dominant_colors: list[str] = field(default_factory=list)

    @property
    def category_type(self) -> CategoryType:
        return get_category_type(self.category)


def score_outfit(
    garments: list[GarmentData],
    occasion: str = "casual",
    style: str | None = None,
    season: str | None = None,
    fit: str | None = None,
) -> float:
    """
    Compute a 0–1 composite compatibility score for a set of garments.
    Factors in occasion affinity, color harmony, formality, seasonality, and structure.
    """
    categories = [g.category for g in garments]
    patterns = [g.pattern for g in garments]
    formalities = [g.formality for g in garments]

    color_h = color_harmony_score_for_outfit(garments)
    formality_h = formality_score(formalities)
    structure_h = category_structure_score(categories)
    pattern_pen = pattern_clash_penalty(patterns)

    occ_affinity, conflict_multiplier = occasion_affinity_score(garments, occasion)
    season_aff = season_affinity_score(garments, season)
    style_aff = style_affinity_score(garments, style)

    # Occasion is heavily weighted (0.40) to guarantee context appropriateness
    composite = (
        0.40 * occ_affinity
        + 0.20 * color_h
        + 0.15 * formality_h
        + 0.10 * structure_h
        + 0.10 * season_aff
        + 0.05 * style_aff
    ) * (1.0 - pattern_pen) * conflict_multiplier

    return round(min(max(composite, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# 9. Style Tag Assignment
# ---------------------------------------------------------------------------

def assign_style_tags(garments: list[GarmentData]) -> dict[str, float]:
    """Heuristic style breakdown over axes: casual, bold, formal, retro."""
    formalities = [g.formality.lower().strip() for g in garments]
    patterns = [g.pattern.lower().strip() for g in garments]

    avg_formality = sum(_FORMALITY_LEVEL.get(f, 1) for f in formalities) / max(len(formalities), 1)

    formal_score = round(min(avg_formality / 3.0, 1.0), 3)
    casual_score = round(1.0 - formal_score, 3)

    has_graphic = any(p in {"graphic print", "floral"} for p in patterns)
    bold_score = round(0.6 if has_graphic else 0.1, 3)

    has_retro_pattern = any(p in {"checked", "polka dot"} for p in patterns)
    retro_score = round(0.5 if (has_retro_pattern and 0.5 <= avg_formality <= 2.5) else 0.05, 3)

    return {
        "casual": casual_score,
        "bold": bold_score,
        "formal": formal_score,
        "retro": retro_score,
    }


# ---------------------------------------------------------------------------
# 10. Dynamic Naming and Explanations
# ---------------------------------------------------------------------------

def generate_outfit_title(combo: list[GarmentData], occasion: str, rank: int) -> str:
    occ = occasion.lower().strip()
    titles = {
        "sport": [
            "Athletic Motion Set",
            "Performance Sport Duo",
            "Active Training Fit",
            "Breathable Workout Look",
            "Agile Sport Track",
            "Dynamic Fitness Duo"
        ],
        "formal": [
            "Executive Tailored Suiting",
            "Sharp Black-Tie Elegance",
            "Sartorial Formal Ensemble",
            "Distinguished Classic Look",
            "Prestigious Suited Fit",
            "Refined Formal Coordination"
        ],
        "business": [
            "Polished Corporate Attire",
            "Modern Business Casual",
            "Executive Office Look",
            "Smart Workday Ensemble",
            "Sleek Professional Duo",
            "Boardroom Classic Set"
        ],
        "wedding": [
            "Refined Celebration Suiting",
            "Distinguished Guest Attire",
            "Elegant Nuptial Look",
            "Tailored Ceremony Ensemble",
            "Chic Wedding Guest Fit",
            "Festive Formal Duo"
        ],
        "evening": [
            "Night Out Tailored Duo",
            "Twilight Chic Ensemble",
            "After-Hours Sleek Look",
            "Midnight Smart Attire",
            "Sophisticated Evening Fit",
            "Dusk Modern Coordination"
        ],
        "casual": [
            "Weekend Relaxed Everyday",
            "Clean Laid-Back Classic",
            "Urban Street Casual",
            "Effortless Casual Pairing",
            "Versatile Everyday Fit",
            "Modern Leisure Ensemble"
        ]
    }.get(occ, [
        "Curated Wardrobe Look",
        "Balanced Style Ensemble",
        "Coordinated Outfit Pairing"
    ])

    return titles[(rank - 1) % len(titles)]


def generate_outfit_reasoning(
    combo: list[GarmentData],
    occasion: str,
    score: float,
    color_score: float,
    formality_score: float,
    season: str | None = None,
) -> str:
    categories = [g.category.lower() for g in combo]
    cats_str = " & ".join(c.capitalize() for c in categories[:2])
    occ = occasion.lower().strip()

    reasons = []

    if occ == "sport":
        reasons.append(f"Engineered for athletic movement with flexible, breathable {cats_str} delivering maximum range of motion without restrictive tailoring.")
    elif occ == "formal":
        reasons.append(f"Uncompromising formal sophistication: crisp tailored lines and dignified silhouette matching high-formality events.")
    elif occ == "business":
        reasons.append(f"Polished business profile balancing refined professional standards with day-long office comfort.")
    elif occ == "wedding":
        reasons.append(f"Celebratory ceremonial refinement with dignified tailoring suited for wedding and reception settings.")
    elif occ == "evening":
        reasons.append(f"Sleek after-dark aesthetic with elevated contrast and sharp styling for night events.")
    else:
        reasons.append(f"Effortless everyday coordination pairing versatile {cats_str} for a balanced, modern casual look.")

    if color_score >= 0.85:
        reasons.append("Exceptional palette harmony with balanced tones.")
    elif color_score >= 0.70:
        reasons.append("Clean complementary color pairing.")

    return " ".join(reasons)


# ---------------------------------------------------------------------------
# 11. Combination generator
# ---------------------------------------------------------------------------

@dataclass
class ScoredOutfit:
    garment_ids: list[str]
    score: float
    style_tags: dict[str, float]
    name: str = ""
    reasoning: str = ""
    occasion: str = ""


def _is_valid_combo(garments: list[GarmentData]) -> bool:
    types = [g.category_type for g in garments]
    type_set = set(types)

    has_dress = CategoryType.DRESS in type_set
    has_top = CategoryType.TOP in type_set
    has_bottom = CategoryType.BOTTOM in type_set

    if has_dress and (has_top or has_bottom):
        return False

    if has_dress:
        return True

    if has_top and has_bottom:
        return True

    return False


def generate_outfits(
    garments: list[GarmentData],
    count: int = 6,
    occasion: str = "casual",
    style: str | None = None,
    season: str | None = None,
    fit: str | None = None,
) -> list[ScoredOutfit]:
    """
    Generate and rank the top `count` outfit combinations from a user's wardrobe,
    strictly customized to the user's selected occasion, style, and season.
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

    footwear_options: list[list[GarmentData]] = [[]] + [[f] for f in footwear]
    candidates: list[list[GarmentData]] = []

    # TOP + BOTTOM (± OUTERWEAR) (± FOOTWEAR)
    for top, bottom in itertools.product(tops, bottoms):
        base = [top, bottom]
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

        s = score_outfit(combo, occasion=occasion, style=style, season=season, fit=fit)
        tags = assign_style_tags(combo)

        scored.append(ScoredOutfit(
            garment_ids=[g.id for g in combo],
            score=s,
            style_tags=tags,
            occasion=occasion,
        ))

    # Sort descending by score
    scored.sort(key=lambda o: o.score, reverse=True)

    # Attach dynamic titles and justifications to top outfits
    results: list[ScoredOutfit] = []
    top_combos = scored[:count]

    # Map ID -> GarmentData for quick lookup
    g_map = {g.id: g for g in garments}

    for rank, out in enumerate(top_combos, 1):
        combo_items = [g_map[gid] for gid in out.garment_ids if gid in g_map]
        c_score = color_harmony_score_for_outfit(combo_items)
        f_score = formality_score([g.formality for g in combo_items])
        title = generate_outfit_title(combo_items, occasion, rank)
        reasoning = generate_outfit_reasoning(combo_items, occasion, out.score, c_score, f_score, season)

        results.append(ScoredOutfit(
            garment_ids=out.garment_ids,
            score=out.score,
            style_tags=out.style_tags,
            name=title,
            reasoning=reasoning,
            occasion=occasion,
        ))

    return results
