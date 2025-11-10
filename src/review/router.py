from fastapi import APIRouter, HTTPException
from src.review.service import ReviewService
from src.review.schemas import ReviewCreate
import logging

logger = logging.getLogger("alejandria_api")

router = APIRouter(prefix="/reviews", tags=["reviews"])
service = ReviewService()

@router.post("/{guten_id}")
def create_review(guten_id: int, review: ReviewCreate):
    try:
        result = service.create_review(guten_id, review.username, review.rating, review.text)
        return result
    except Exception as e:
        logger.exception(f"Error creando reseña: {e}")
        raise HTTPException(status_code=500, detail="Error al crear reseña")

@router.get("/{guten_id}")
def list_reviews(guten_id: int):
    try:
        return service.list_reviews(guten_id)
    except Exception as e:
        logger.exception(f"Error listando reseñas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener reseñas")
