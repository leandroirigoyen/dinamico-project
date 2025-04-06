from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timedelta
import requests
from routes.user import get_current_user

PaymentAPI = APIRouter()

# Access token del vendedor de Mercado Pago
MERCADOPAGO_ACCESS_TOKEN = "APP_USR-4332466440353952-052720-a3432774308ab2458b3b4710a5e6f591-470216786"

# Datos de los planes de suscripción
PLANES = {
    "mensual": {"title": "Plan Mensual", "price": 200, "days": 30, "subscription_plan_id": "2c9380848115cdc701811680e8b40064"},
    "trimestral": {"title": "Plan Trimestral", "price": 510, "days": 90, "subscription_plan_id": "2c9380848100905c0181168fd259090a"},
    "anual": {"title": "Plan Anual", "price": 1680, "days": 365, "subscription_plan_id": "2c9380848115cdc7018116919cc4006b"}
}

# Endpoint para procesar la notificación de Mercado Pago
@PaymentAPI.post("/webhook/mercadopago")
async def receive_mercadopago_notification(request: Request):
    try:
        data = await request.json()
        print("Received Mercado Pago Notification:", data)
        # Aquí procesamos la notificación y actualizamos la suscripción del usuario
        if data.get("type") == "payment" and data.get("action") == "payment.created":
            user_id = data.get("user_id")
            if user_id:
                plan_id = data["data"].get("subscription_plan_id")
                if plan_id:
                    plan = next((p for p in PLANES.values() if p["subscription_plan_id"] == plan_id), None)
                    if plan:
                        # Verificar si el pago fue exitoso
                        if data["data"].get("status") == "approved":
                            expiration_date = datetime.utcnow() + timedelta(days=plan["days"])
                            # Aquí debes actualizar la suscripción del usuario en la base de datos
                            print(f"Updating subscription for user {user_id} with expiration date {expiration_date}")
                        else:
                            # Manejar caso de pago no aprobado
                            print("Payment not approved")
        return {"message": "Notification received successfully"}
    except Exception as e:
        print("Error processing notification:", e)
        raise HTTPException(status_code=500, detail="Error processing notification")

class PaymentRedirect(BaseModel):
    redirect_url: str
    
# Endpoint para redirigir al usuario a la página de pago de Mercado Pago
@PaymentAPI.get("/subscribe/{plan}", response_model=PaymentRedirect)
async def subscribe_to_plan(plan: str, current_user: Dict = Depends(get_current_user)):
    # Verificar si el plan de suscripción es válido
    if plan not in PLANES:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    # Aquí debes redirigir al usuario a la página de pago de Mercado Pago correspondiente al plan seleccionado
    mp_checkout_url = f"https://www.mercadopago.com.uy/subscriptions/checkout?preapproval_plan_id={PLANES[plan]['subscription_plan_id']}"
    return PaymentRedirect(redirect_url=mp_checkout_url)