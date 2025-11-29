from pydantic import BaseModel, ConfigDict


class ReviewDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    guten_id: int
    username: str
    rating: int
    text: str
    created_at: str | None = None


class ReviewCreate(BaseModel):
    """Modelo usado al crear una nueva reseña (input del usuario)."""
    model_config = ConfigDict(from_attributes=True)

    username: str
    rating: int
    text: str
