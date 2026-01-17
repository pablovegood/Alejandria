from fastapi import APIRouter, HTTPException, Query

from .schemas import LoanRequest
from .service import LoanService

router = APIRouter(prefix="/loans", tags=["loans"])
service = LoanService()


@router.post("/", summary="Crear un préstamo")
def create_loan(payload: LoanRequest):
    """
    Crea un nuevo préstamo para un usuario.

    Reglas:
    - Máximo 4 préstamos activos por usuario.
    - Un mismo usuario no puede tener duplicado el mismo libro.
    """
    result = service.create_loan(
        username=payload.username,
        guten_id=payload.guten_id,
        title=payload.title,
        author=payload.author,
    )
    if not result.get("ok"):
        detail = result.get("detail", "No se pudo crear el préstamo.")
        # 409 = conflicto lógico (límite, duplicado, etc.)
        raise HTTPException(status_code=409, detail=detail)
    return result


@router.get("/", summary="Préstamos de un usuario")
def list_user_loans(
    username: str = Query(..., description="Nombre de usuario dueño de los préstamos"),
):
    """
    Respuesta:
    {
      "ok": true,
      "user": "pablo",
      "active_count": 2,
      "max_loans": 4,
      "loans": [ ... ]
    }
    """
    return service.get_user_loans(username=username)


@router.get("/{username}", summary="Préstamos de un usuario (alias por path)")
def list_user_loans_by_path(username: str):
    """Alias de GET /loans?username= para comodidad."""
    return service.get_user_loans(username=username)


@router.delete("/{username}/{guten_id}", summary="Devolver un libro")
def delete_loan(username: str, guten_id: int):
    result = service.delete_loan(username=username, guten_id=guten_id)
    if not result.get("ok"):
        raise HTTPException(
            status_code=404, detail=result.get("detail", "Préstamo no encontrado.")
        )
    return result
