from fastapi import APIRouter, Depends, HTTPException
from config.db import Session
from models.profile import Profile
from models.reports import Report
from routes.user import get_current_user
from schemas.reports import ReportCreate, ReportBase, ReportList
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException

ReportsAPI = APIRouter()



# Define la función para enviar el correo electrónico de informe
def send_report_email(report_details):
    # Detalles del servidor SMTP
    smtp_server = 'smtp-relay.brevo.com'
    smtp_port = 587
    smtp_username = 'info.dinamicouy@gmail.com'
    smtp_password = 'bpqtnD29HxjJ4G3v'

    # Crear el mensaje de correo electrónico
    msg = MIMEMultipart()
    msg['From'] = 'info.dinamicouy@gmail.com'
    msg['To'] = 'info.dinamicouy@gmail.com'  # Cambia esto a la dirección de correo donde deseas enviar los informes
    msg['Subject'] = 'Nuevo informe creado'

    # Adjuntar los detalles del informe al cuerpo del correo electrónico
    msg.attach(MIMEText(report_details, 'plain'))

    try:
        # Iniciar la conexión SMTP y enviar el correo electrónico
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        print("Correo electrónico de informe enviado con éxito")
    except Exception as e:
        print(f"Error al enviar el correo electrónico: {e}")
        raise HTTPException(status_code=500, detail="Error al enviar el correo electrónico")

# Definir tu endpoint para crear informes
@ReportsAPI.post("/profiles/{profile_id}/report", response_model=None, tags=["Reports"])
def create_report(
    profile_id: int,
    report: ReportCreate,
    current_user: dict = Depends(get_current_user)
):
    with Session() as session:
        # Verificar si el perfil que se está denunciando existe
        profile = session.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Crea una instancia de Report con los datos proporcionados
        report_db = Report(
            profile_id=profile_id,
            reported_by_user_id=current_user["id"],
            unfinished_work=report.unfinished_work,
            missed_completion_time=report.missed_completion_time,
            low_work_quality=report.low_work_quality,
            delayed_responses=report.delayed_responses,
            incorrect_profile_info=report.incorrect_profile_info,
            unauthorized_images=report.unauthorized_images,
            message=report.message
        )

        # Guarda la denuncia en la base de datos
        session.add(report_db)
        session.commit()
        session.refresh(report_db)

        # Obtener los detalles del informe
        report_details = """
        Detalles del informe:
        - Perfil ID: {}
        - Reportado por el usuario ID: {}
        - Trabajo no terminado: {}
        - Tiempo de finalización perdido: {}
        - Baja calidad del trabajo: {}
        - Respuestas retrasadas: {}
        - Información de perfil incorrecta: {}
        - Imágenes no autorizadas: {}
        - Mensaje: {}
        """.format(profile_id, current_user["id"], report.unfinished_work, report.missed_completion_time,
                   report.low_work_quality, report.delayed_responses, report.incorrect_profile_info,
                   report.unauthorized_images, report.message)

        # Llama a la función para enviar el correo electrónico
        send_report_email(report_details)

        return report_db
    
@ReportsAPI.get("/profiles/{profile_id}/reports", response_model=ReportList, tags=["Reports"])
def get_reports_for_profile(
    profile_id: int,
    current_user: dict = Depends(get_current_user)
):
    with Session() as session:
        # Verifica si el perfil que se está consultando existe
        profile = session.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Verifica si el usuario actual tiene permiso para acceder a los informes de este perfil
        # Esto puede requerir lógica adicional dependiendo de tus requerimientos de autorización

        # Recupera los informes relacionados con el perfil
        reports = (
            session.query(Report)
            .filter(Report.profile_id == profile_id)
            .all()
        )

        # Convierte los informes en una lista de ReportBase
        report_base_list = [
            ReportBase(
                id=report.id,
                profile_id=report.profile_id,
                reported_by_user_id=report.reported_by_user_id,
                unfinished_work=report.unfinished_work,
                missed_completion_time=report.missed_completion_time,
                low_work_quality=report.low_work_quality,
                delayed_responses=report.delayed_responses,
                incorrect_profile_info=report.incorrect_profile_info,
                unauthorized_images=report.unauthorized_images,
                message=report.message
            )
            for report in reports
        ]

        return ReportList(reports=report_base_list)