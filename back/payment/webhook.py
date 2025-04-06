import requests

# Define las credenciales y el access token del usuario
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwcnVlYmFAZ21haWwuY29tIiwiZXhwIjoxNzE2ODY2MDk4fQ.cSmM39jpSK4cJi-c_2_aViGEPGlSTm8R-dzToC9j1Wk"

# Define la URL del webhook
webhook_url = "https://00bf-186-53-38-154.ngrok-free.app/webhook/mercadopago"

# Define los datos de la notificación de prueba
notification_data = {
    "action": "payment.created",
    "api_version": "v1",
    "application_id": "3427294086695156",
    "date_created": "2023-08-31T00:00:00Z",
    "id": "123456789",
    "live_mode": "false",
    "type": "payment",
    "user_id": access_token,
    "data": {
        "external_reference": access_token,
        "id": "payment_id_test",
        "status": "approved",
        "subscription_plan_id": "2c9380848100905c0181168fd259090a"
    }
}

# Enviar la solicitud POST al webhook
response = requests.post(webhook_url, json=notification_data)

# Imprimir la respuesta del servidor
print("Respuesta del servidor:", response.status_code, response.text)


