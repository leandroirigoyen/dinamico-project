from fastapi import Depends, HTTPException, APIRouter
from models.notifications import Notification
from routes.user import get_current_user
from typing import List
from models.user import User
from models.post import Post
from config.db import Session
from sqlalchemy.orm import aliased
from models.profile import Comment
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel


NotificationAPI = APIRouter()

class NotificationUpdate(BaseModel):
    notification_id: int

# Modificar función send_notification para crear una notificación
def send_notification(session, sender_id, receiver_id, content, post_id, comment_id=None):
    notification = Notification(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        post_id=post_id,
        comment_id=comment_id
    )

    session.add(notification)
    session.commit()

    
 

# Endpoint para obtener notificaciones del usuario actual
@NotificationAPI.get("/notifications", tags=["Notifications"])
def get_notifications_with_info(current_user: dict = Depends(get_current_user)):
    with Session() as session:
        UserSender = aliased(User)
        UserReceiver = aliased(User)
        
        notifications = (
            session.query(Notification, Comment, UserSender, UserReceiver, Post)
            .outerjoin(Comment, Notification.comment_id == Comment.id)
            .join(UserSender, Notification.sender_id == UserSender.id)
            .join(UserReceiver, Notification.receiver_id == UserReceiver.id)
            .join(Post, Notification.post_id == Post.id, isouter=True)
            .filter(Notification.receiver_id == current_user["id"])
            .all()
        )

        notification_info = []
        for notification, comment, sender_user, receiver_user, post in notifications:
            info = {
                "notification_id": notification.id,
                "sender_id": notification.sender_id,
                "receiver_id": notification.receiver_id,
                "post_id": post.id if post else None,
                "comment_id": comment.id if comment else None,
                "content": notification.content,
                "read": notification.read,
                "created_at": notification.created_at,
                "sender_name": sender_user.name,
                "receiver_name": receiver_user.name,
                "location": post.location if post else None,  # Agregar la ubicación del post
                "service_type": post.service_type if post else None,
                "urgent": post.urgent if post else None  # Agregar el tipo de servicio del post
            }
            
            notification_info.append(info)

        return notification_info


















# Endpoint para marcar notificaciones como leídas
@NotificationAPI.post("/notifications/mark-read/{notification_id}", tags=["Notifications"])
def mark_notification_read(notification_id: int, current_user_data: dict = Depends(get_current_user)):
    current_user = User(**current_user_data)
    
    try:
        with Session() as session:
            notification = session.query(Notification).filter_by(id=notification_id, receiver_id=current_user.id).first()
            if notification:
                notification.read = True
                session.commit()
                return {"message": "Notification marked as read"}
            else:
                return {"error": "Notification not found or not accessible for this user"}
    except SQLAlchemyError as e:
        return {"error": f"An error occurred: {str(e)}"}

    
@NotificationAPI.post("/notifications/{post_id}", tags=["Notifications"])
def send_availability_notification(post_id: int, current_user_data: dict = Depends(get_current_user)):
    current_user = User(**current_user_data)
    
    # Verificar si el post existe
    with Session() as session:
        post = session.query(Post).filter_by(id=post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Publicación no encontrada")

        # Crear una notificación de disponibilidad
        notification_content = f"está para trabajar en la publicación: {post.title}"
        send_notification(session, current_user.id, post.user_id, notification_content, post_id)  # Pasar la sesión y corregir el orden de los argumentos

    return {"message": "Notificación de disponibilidad enviada correctamente"}

@NotificationAPI.delete("/notifications/{notification_id}", tags=["Notifications"])
def delete_notification(notification_id: int, current_user: dict = Depends(get_current_user)):
    with Session() as session:
        notification = session.query(Notification).get(notification_id)
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Verificar que el usuario logueado sea el receptor de la notificación
        if notification.receiver_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="You are not authorized to delete this notification")

        # Actualizar los comentarios relacionados para que no estén vinculados a ninguna notificación
        session.query(Comment).filter(Comment.notification_id == notification.id).update({"notification_id": None})

        # Luego, elimina la notificación
        session.delete(notification)
        session.commit()

        return {"message": "Notification deleted successfully"}



