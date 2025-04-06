# middlewares.py

from fastapi import Request
from fastapi.responses import JSONResponse
from config.db import Session

# Middleware para refrescar la sesión de la base de datos
async def refresh_db_session(request: Request, call_next):
    with Session() as session:
        session.expire_all()  # Refrescar la sesión antes de cada solicitud
        response = await call_next(request)
    return response

# Middleware para manejo de errores global
async def handle_errors(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        # Registrar la excepción o enviar una respuesta de error
        response = JSONResponse({"error": str(e)}, status_code=500)
    return response

# Middleware para registro de solicitudes y respuestas
async def log_requests_and_responses(request: Request, call_next):
    # Registro de solicitud
    print(f"Solicitud recibida: {request.method} {request.url}")

    response = await call_next(request)

    # Registro de respuesta
    print(f"Respuesta enviada: {response.status_code}")
    return response
