from pydantic import BaseModel, Field


class ClassificationResponse(BaseModel):
    category: str
    category_confidence: float = Field(..., ge=0, le=1)
    pattern: str
    formality: str
    dominant_colors: list[str]
    # Only populated if the caller asks for it (?include_embedding=true) —
    # it's a 512-float vector, no point sending it over the wire by default
    # when the frontend just wants to show the user what was detected.
    embedding: list[float] | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "casual shirt",
                "category_confidence": 0.87,
                "pattern": "striped",
                "formality": "smart casual",
                "dominant_colors": ["#1a3c5e", "#f2f2f2"],
                "embedding": None,
            }
        }
    }
