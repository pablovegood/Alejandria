# src/auth/router.py
from fastapi import APIRouter, Depends, HTTPException
from src.auth.service import AuthService
from src.auth.schemas import SignupReq, LoginReq
import logging

logger = logging.getLogger("alejandria_api")

router = APIRouter(prefix="/auth", tags=["auth"])

service = AuthService()  # Instancia global del servicio


@router.post("/signup")
def signup(req: SignupReq):
    try:
        return service.signup(req)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"❌ Error en signup: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/login")
def login(req: LoginReq):
    try:
        return service.login(req)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"❌ Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
