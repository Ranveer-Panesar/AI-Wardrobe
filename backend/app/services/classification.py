"""
Garment classification using Fashion-CLIP (patrickjohncyh/fashion-clip).

Fashion-CLIP is CLIP fine-tuned on fashion product data — it gives us:
  1. Zero-shot classification: score an image against a list of candidate
     text labels, no training needed. Used here for category/pattern/formality.
  2. Image embeddings: a 512-dim vector per garment, reused later for the
     outfit-compatibility model (Phase 4) and similarity search.

Loaded as a lazy singleton so the model (a few hundred MB) is loaded once
per process, not once per request.
"""
from __future__ import annotations

from PIL import Image

MODEL_ID = "patrickjohncyh/fashion-clip"

# --- Label taxonomies ---
# These are the candidate labels Fashion-CLIP scores each image against.
# Tune/expand these based on what's actually in your users' wardrobes —
# it's much cheaper to edit a list than to retrain anything.
CATEGORY_LABELS = [
    "t-shirt", "casual shirt", "formal shirt", "polo shirt",
    "jeans", "formal trousers", "shorts", "joggers",
    "jacket", "hoodie", "sweater", "blazer",
    "dress", "skirt",
]

PATTERN_LABELS = ["solid", "striped", "checked", "floral", "graphic print", "polka dot"]

FORMALITY_LABELS = ["very casual", "casual", "smart casual", "formal"]


class FashionClassifier:
    """Wraps Fashion-CLIP for zero-shot classification + embeddings."""

    _instance: "FashionClassifier | None" = None

    def __init__(self):
        # Imported here (not top-of-file) so importing this module doesn't
        # force-load torch/transformers before they're actually needed —
        # keeps FastAPI startup fast and keeps these heavy deps out of the
        # way for anyone just running tests against a mocked classifier.
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained(MODEL_ID).to(self.device).eval()
        self.processor = CLIPProcessor.from_pretrained(MODEL_ID)
        self._torch = torch

    @classmethod
    def get_instance(cls) -> "FashionClassifier":
        """Lazy singleton — first call loads the model, later calls reuse it."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _zero_shot(
        self, image: Image.Image, candidate_labels: list[str], template: str = "a photo of a {}"
    ) -> tuple[str, float]:
        prompts = [template.format(label) for label in candidate_labels]
        inputs = self.processor(
            text=prompts, images=image, return_tensors="pt", padding=True
        ).to(self.device)

        with self._torch.no_grad():
            outputs = self.model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)[0]

        best_idx = int(probs.argmax())
        return candidate_labels[best_idx], float(probs[best_idx])

    def classify_category(self, image: Image.Image) -> tuple[str, float]:
        return self._zero_shot(image, CATEGORY_LABELS)

    def classify_pattern(self, image: Image.Image) -> tuple[str, float]:
        return self._zero_shot(image, PATTERN_LABELS, template="a {} pattern")

    def classify_formality(self, image: Image.Image) -> tuple[str, float]:
        return self._zero_shot(image, FORMALITY_LABELS, template="a {} garment")

    def get_embedding(self, image: Image.Image) -> list[float]:
        """L2-normalized 512-dim embedding — cosine similarity between two
        of these is a meaningful "how visually/stylistically similar" score,
        which is what Phase 4's compatibility head will be built on."""
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)

        with self._torch.no_grad():
            features = self.model.get_image_features(**inputs)
            features = features / features.norm(p=2, dim=-1, keepdim=True)

        return features[0].cpu().tolist()
