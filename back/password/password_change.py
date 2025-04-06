# Importa los módulos necesarios
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from config.db import Session
from models.user import User
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from routes.user import get_password_hash
import random

# Crea un enrutador para las rutas relacionadas con el cambio de contraseña
PasswordChangeAPI = APIRouter()

# Define un modelo para los datos de solicitud de cambio de contraseña
class PasswordChangeRequest(BaseModel):
    new_password: str

# Ruta para solicitar un cambio de contraseña
@PasswordChangeAPI.post("/request-change-password", tags=["User"])
async def request_password_change(email: str):
    # Busca al usuario por su dirección de correo electrónico
    with Session() as session:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Genera un código de verificación y envíalo por correo electrónico
        verification_code = ''.join(random.choice('0123456789') for _ in range(6))
        send_verification_email(user.email, verification_code)

        # Almacena el código de verificación en el usuario
        user.verification_code = verification_code
        session.commit()

        return {"message": "Verification code sent successfully"}

# Ruta para cambiar la contraseña después de verificar el código
@PasswordChangeAPI.post("/change-password", tags=["User"])
async def change_password(password_change: PasswordChangeRequest, verification_code: str):
    # Busca al usuario por el código de verificación
    with Session() as session:
        user = session.query(User).filter(User.verification_code == verification_code).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        # Hashea la nueva contraseña
        hashed_new_password = get_password_hash(password_change.new_password)

        # Actualiza la contraseña del usuario y elimina el código de verificación
        user.hashed_password = hashed_new_password
        user.verification_code = None
        session.commit()

        return {"message": "Password updated successfully"}

# Función para enviar correo electrónico de verificación
def send_verification_email(user_email, verification_code):
    # Configura los detalles del servidor SMTP y correo electrónico de origen
    smtp_server = 'smtp-relay.brevo.com'
    smtp_port = 587
    smtp_username = 'info.dinamicouy@gmail.com'
    smtp_password = 'bpqtnD29HxjJ4G3v'
    sender_email = 'info.dinamicouy@gmail.com'

    # Crea el mensaje de correo electrónico
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user_email
    msg['Subject'] = 'Verification Code'

    # Cuerpo del mensaje de correo electrónico
    message = f'Your verification code is: {verification_code}'
    msg.attach(MIMEText(message, 'plain'))

    # Inicia la conexión SMTP y envía el correo electrónico
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

