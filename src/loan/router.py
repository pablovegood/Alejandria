# src/loan/router.py
from fastapi import APIRouter, HTTPException, Query
from src.loan.schemas import LoanRequest
from src.loan.service import LoanService
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
            raise HTTPException(status_code=400, detail=result["detail"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Error al crear préstamo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------------------------------------------------
# LISTAR PRÉSTAMOS
# -------------------------------------------------------------------------
@router.get("/")
def list_loans(username: str = Query(...)):
    try:
        loans = service.list_loans(username)
        return {"loans": loans}
    except Exception as e:
        logger.exception(f"❌ Error al listar préstamos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# DEVOLVER LIBRO
# -------------------------------------------------------------------------
@router.delete("/{username}/{guten_id}")
def delete_loan(username: str, guten_id: int):
    try:
        result = service.delete_loan(username, guten_id)
        if not result.get("ok", True):
            raise HTTPException(status_code=404, detail=result["detail"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Error al eliminar préstamo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
