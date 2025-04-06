from fastapi import Depends, HTTPException, APIRouter
from config.db import Session, sess
from models.profile import Profile, Comment
from models.user import User
from routes.user import get_current_user
from schemas.comments import CommentInDB, CommentCreate
from routes.notifications import send_notification
from typing import List
from models.notifications import Notification
from sqlalchemy.orm import subqueryload

CommentAPI = APIRouter()

@CommentAPI.get("/pending-comments/", response_model=List[CommentInDB], tags=["Comments"])
def get_pending_comments_for_logged_user(
    current_user: dict = Depends(get_current_user),
):
    # Obtiene el perfil asociado al usuario actual
    session = Session()
    profile = session.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Modifica la consulta para cargar la relación 'notification' usando outerjoin
    pending_comments = (
        session.query(Comment)
        .filter(Comment.profile_id == profile.id, Comment.approved == False)
        .outerjoin(Notification, Comment.notification_id == Notification.id)  # Carga la relación 'notification'
        .all()
    )

    # Crea una lista de instancias de CommentInDB
    pending_comments_in_db = [
        CommentInDB(
            id=comment.id,
            timestamp=comment.timestamp,
            approved=comment.approved,
            user_id=comment.user_id,
            user_name=comment.user.name,
            profile_id=comment.profile_id,
            content=comment.content,
            notification_id=comment.notification_id
        )
        for comment in pending_comments
    ]

    return pending_comments_in_db


@CommentAPI.get("/approved-comments/", response_model=List[CommentInDB], tags=["Comments"])
def get_approved_comments(
    current_user: dict = Depends(get_current_user),
):
    # Obtén el perfil asociado al usuario actual
    session = Session()
    profile = session.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Obtén los comentarios aprobados para el perfil
    approved_comments = session.query(Comment).filter(Comment.profile_id == profile.id, Comment.approved == True).all()

    # Crea una lista de instancias de CommentInDB
    approved_comments_in_db = [
        CommentInDB(
            id=comment.id,
            timestamp=comment.timestamp,
            approved=comment.approved,
            user_id=comment.user_id,
            user_name=comment.user.name,
            profile_id=comment.profile_id,
            content=comment.content,
            notification_id=comment.notification_id
        )
        for comment in approved_comments
    ]

    return approved_comments_in_db

@CommentAPI.get("/approved-comments/{user_id}", response_model=List[CommentInDB], tags=["Comments"])
def get_approved_comments_by_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    with Session() as session:
        # Verifica si el usuario actual tiene acceso a ver los comentarios aprobados de otro usuario
        if current_user["id"] == user_id:
            raise HTTPException(status_code=400, detail="You cannot view your own approved comments.")

        # Obtén los comentarios aprobados del usuario especificado por su ID
        approved_comments = (
            session.query(Comment)
            .join(Profile)
            .filter(Profile.user_id == user_id, Comment.approved == True)
            .all()
        )

        # Crea una lista de instancias de CommentInDB
        approved_comments_in_db = [
            CommentInDB(
                id=comment.id,
                timestamp=comment.timestamp,
                approved=comment.approved,
                user_id=comment.user_id,
                user_name=comment.user.name,
                profile_id=comment.profile_id,
                content=comment.content,
                notification_id=comment.notification_id
            )
            for comment in approved_comments
        ]

        return approved_comments_in_db




@CommentAPI.get("/approved-comments/{comment_id}", response_model=CommentInDB, tags=["Comments"])
def get_approved_comment_by_id(
    comment_id: int,
    current_user: dict = Depends(get_current_user),
):
    # Obtén el perfil asociado al usuario actual
    session = Session()
    profile = session.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Obtén el comentario aprobado por su ID y que pertenezca al perfil
    approved_comment = session.query(Comment).filter(
        Comment.id == comment_id,
        Comment.profile_id == profile.id,
        Comment.approved == True
    ).first()

    if not approved_comment:
        raise HTTPException(status_code=404, detail="Approved comment not found")

    # Crea una instancia de CommentInDB
    approved_comment_in_db = CommentInDB(
        id=approved_comment.id,
        timestamp=approved_comment.timestamp,
        approved=approved_comment.approved,
        user_id=approved_comment.user_id,
        user_name=approved_comment.name,
        profile_id=approved_comment.profile_id,
        content=approved_comment.content,
        notification_id=approved_comment.notification_id
    )

    return approved_comment_in_db


@CommentAPI.get("/rejected-comments/", response_model=List[CommentInDB], tags=["Comments"])
def get_rejected_comments(
    current_user: dict = Depends(get_current_user),
):
    # Obtén el perfil asociado al usuario actual
    session = Session()
    profile = session.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Obtén los comentarios rechazados para el perfil
    rejected_comments = session.query(Comment).filter(Comment.profile_id == profile.id, Comment.approved == False).all()

    # Crea una lista de instancias de CommentInDB
    rejected_comments_in_db = [
        CommentInDB(
            id=comment.id,
            timestamp=comment.timestamp,
            approved=comment.approved,
            user_id=comment.user_id,
            user_name=comment.user.name,
            profile_id=comment.profile_id,
            content=comment.content,
            notification_id=comment.notification_id
        )
        for comment in rejected_comments
    ]

    return rejected_comments_in_db

@CommentAPI.get("/rejected-comments/{comment_id}", response_model=CommentInDB, tags=["Comments"])
def get_rejected_comment_by_id(
    comment_id: int,
    current_user: dict = Depends(get_current_user),
):
    # Obtén el perfil asociado al usuario actual
    session = Session()
    profile = session.query(Profile).filter(Profile.user_id == current_user["id"]).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Obtén el comentario rechazado por su ID y que pertenezca al perfil
    rejected_comment = session.query(Comment).filter(
        Comment.id == comment_id,
        Comment.profile_id == profile.id,
        Comment.approved == False
    ).first()

    if not rejected_comment:
        raise HTTPException(status_code=404, detail="Rejected comment not found")

    # Crea una instancia de CommentInDB
    rejected_comment_in_db = CommentInDB(
        id=rejected_comment.id,
        timestamp=rejected_comment.timestamp,
        approved=rejected_comment.approved,
        user_id=rejected_comment.user_id,
        user_name=rejected_comment.user.name,
        profile_id=rejected_comment.profile_id,
        content=rejected_comment.content,
        notification_id=rejected_comment.notification_id
    )

    return rejected_comment_in_db




@CommentAPI.post("/profiles/{profile_id}/comments/", response_model=CommentInDB, tags=["Comments"])
def create_comment_for_profile(
    profile_id: int,
    comment: CommentCreate,
    current_user: dict = Depends(get_current_user),
):
    profile = sess.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    with Session() as session:
        # Crea la instancia de comentario sin asignar notification_id
        comment_db = Comment(content=comment.content, user_id=current_user["id"], profile_id=profile_id)

        # Ahora crea una notificación relacionada con el comentario
        receiver_id = profile.user_id
        sender_id = current_user["id"]
        notification_text = f"ha dejado un comentario en tu perfil"
        
        notification = Notification(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=notification_text
        )

        # Almacena la notificación en la base de datos
        session.add(notification)
        session.commit()

        # Asigna el ID de la notificación al comentario
        comment_db.notification_id = notification.id

        # Almacena el comentario en la base de datos
        session.add(comment_db)
        session.commit()

        # Asegúrate de que el comentario se actualice con el notification_id
        session.refresh(comment_db)

        created_comment = session.query(Comment).filter(Comment.id == comment_db.id).first()

        # Crea una instancia de CommentInDB y devuelve su versión serializada
        comment_in_db_instance = CommentInDB(
            id=created_comment.id,
            timestamp=created_comment.timestamp,
            user_name=created_comment.user.name,
            approved=created_comment.approved,
            user_id=created_comment.user_id,
            profile_id=created_comment.profile_id,
            content=created_comment.content,
            notification_id=created_comment.notification_id
        )
        
        return comment_in_db_instance.dict()



    


@CommentAPI.post("/approve-comment/{comment_id}", response_model=CommentInDB, tags=["Comments"])
def approve_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user),
):
    # Obtén el comentario por su ID
    session = Session()
    comment = session.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Verifica si el comentario pertenece al perfil del usuario actual
    if comment.profile.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Cambia el estado "approved" a True
    comment.approved = True
    session.commit()

  

    # Crea una instancia de CommentInDB y devuelve su versión serializada
    comment_in_db_instance = CommentInDB(
        id=comment.id,
        timestamp=comment.timestamp,
        approved=comment.approved,
        user_id=comment.user_id,
        user_name=comment.user.name,
        profile_id=comment.profile_id,
        content=comment.content,
        notification_id=comment.notification_id  # Incluir el notification_id si está disponible
    )

    return comment_in_db_instance

@CommentAPI.post("/reject-comment/{comment_id}", response_model=CommentInDB, tags=["Comments"])
def reject_comment(
    comment_id: int,
    current_user: dict = Depends(get_current_user),
):
    # Obtén el comentario por su ID
    session = Session()
    comment = session.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Verifica si el comentario pertenece al perfil del usuario actual
    if comment.profile.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Cambia el estado "approved" a False
    comment.approved = False
    session.commit()

    # Crea una instancia de CommentInDB y devuelve su versión serializada
    comment_in_db_instance = CommentInDB(
        id=comment.id,
        timestamp=comment.timestamp,
        approved=comment.approved,
        user_id=comment.user_id,
        user_name=comment.user.name,
        profile_id=comment.profile_id,
        content=comment.content,
        notification_id=comment.notification_id
    )

    return comment_in_db_instance

