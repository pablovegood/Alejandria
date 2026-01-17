# src/loan/router.py
from fastapi import APIRouter, HTTPException, Query
from src.loan.schemas import LoanRequest
from src.loan.service import LoanService, MAX_LOANS_PER_USER
import logging

logger = logging.getLogger("alejandria_api")

router = APIRouter(prefix="/loans", tags=["loans"])
service = LoanService()

# -------------------------------------------------------------------------
# CREAR PRÉSTAMO
# -------------------------------------------------------------------------
@router.post("/")
def create_loan(req: LoanRequest):
    try:
        result = service.create_loan(req.username, req.guten_id, req.title, req.author)

        if not result.get("ok", True):
            code = result.get("code", "")
            detail = result.get("detail", "Error al crear préstamo.")

            # 403 = límite alcanzado
            if code == "LIMIT_REACHED":
                raise HTTPException(status_code=403, detail=detail)

            # 409 = conflicto (ya prestado / no disponible)
            if code in ("ALREADY_BORROWED", "NOT_AVAILABLE"):
                raise HTTPException(status_code=409, detail=detail)

            raise HTTPException(status_code=400, detail=detail)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Error al crear préstamo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------------------------------------------------
# LISTAR PRÉSTAMOS (+ meta para el frontend)
# -------------------------------------------------------------------------
@router.get("/")
def list_loans(username: str = Query(...)):
    try:
        loans = service.list_loans(username)
        return {
            "loans": loans,
            "active": len(loans),
            "max": MAX_LOANS_PER_USER
        }
    except Exception as e:
        logger.exception(f"❌ Error al listar préstamos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------------------------------------------------
# DEVOLVER LIBRO
# -------------------------------------------------------------------------
@router.delete("/{username}/{guten_id}")
def delete_loan(username: str, guten_id: int):
    try:
        result = service.delete_loan(username, guten_id)
        if not result.get("ok", True):
            raise HTTPException(status_code=404, detail=result.get("detail", "No encontrado"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Error al eliminar préstamo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
