from fastapi import APIRouter, Depends, HTTPException
from config.db import Session
from models.profile import Profile
from models.reports import Report
from routes.user import get_current_user
from schemas.reports import ReportCreate, ReportBase, ReportList
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException, APIRouter
from models.recommendations import Recommendation
from schemas.recommendations import RecommendationCreate


RecommendationsAPI = APIRouter()

# Define la función para enviar el correo electrónico de recomendación
def send_recommendation_email(user_id, user_name, recommendation_text):
    # Detalles del servidor SMTP
    smtp_server = 'smtp-relay.brevo.com'
    smtp_port = 587
    smtp_username = 'info.dinamicouy@gmail.com'
    smtp_password = 'bpqtnD29HxjJ4G3v'

    # Crear el mensaje de correo electrónico
    msg = MIMEMultipart()
    msg['From'] = 'info.dinamicouy@gmail.com'
    msg['To'] = 'info.dinamicouy@gmail.com'  # Cambia esto a la dirección de correo donde deseas enviar las recomendaciones
    msg['Subject'] = 'Nueva recomendación'

    # Adjuntar los detalles de la recomendación al cuerpo del correo electrónico, incluyendo el ID y el nombre del usuario
    message = f"ID de usuario: {user_id}\nNombre de usuario: {user_name}\n\nRecomendación:\n{recommendation_text}"
    msg.attach(MIMEText(message, 'plain'))

    try:
        # Iniciar la conexión SMTP y enviar el correo electrónico
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        print("Correo electrónico de recomendación enviado con éxito")
    except Exception as e:
        print(f"Error al enviar el correo electrónico: {e}")
        raise HTTPException(status_code=500, detail="Error al enviar el correo electrónico")

@RecommendationsAPI.post("/recommendations", response_model=None, tags=["Recommendations"])
def create_recommendation(
    recommendation: RecommendationCreate,
    current_user: dict = Depends(get_current_user)
):
    with Session() as session:
        # Crea una instancia de Recommendation con los datos proporcionados
        recommendation_db = Recommendation(
            user_id=current_user["id"],
            user_name=current_user.get("name", "Nombre de usuario no especificado"),
            recommendation_text=recommendation.recommendation_text
        )

        # Guarda la recomendación en la base de datos
        session.add(recommendation_db)
        session.commit()
        session.refresh(recommendation_db)

        # Llama a la función para enviar el correo electrónico con ID y nombre de usuario
        send_recommendation_email(current_user["id"], current_user.get("name", "Nombre de usuario no especificado"), recommendation.recommendation_text)


        return "Recomendación enviada con éxito"  # No se necesita un modelo de respuesta en este caso
