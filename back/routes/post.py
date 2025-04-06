from fastapi import Depends, HTTPException, APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import select, and_, or_, func
from models.post import Post, PostImage
from schemas.post import PostSchemaCreation
from config.db import Session
from routes.user import get_current_user
from models.user import User
from models.profile import Profile
from models.notifications import Notification
from routes.notifications import send_notification
import time
from typing import List
import os
from sqlalchemy.orm import joinedload

PostAPI = APIRouter()



@PostAPI.get("/post-images/{post_id}/{image_id}", tags=["Post Images"])
def get_post_image(post_id: int, image_id: int):
    with Session() as session:
        post = session.query(Post).filter_by(id=post_id).first()
        if post:
            image = session.query(PostImage).filter_by(post_id=post_id, id=image_id).first()
            if image:
                media_type = "image/jpeg" if image.image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                return FileResponse(image.image_path, media_type=media_type)
            else:
                raise HTTPException(status_code=404, detail="Image not found for this post")
        else:
            raise HTTPException(status_code=404, detail="Post not found")

@PostAPI.delete("/post-images/{post_id}/{image_id}", tags=["Post Images"])
def delete_post_image(
    post_id: int, image_id: int, current_user: dict = Depends(get_current_user)
):
    with Session() as session:
        # Buscar el post correspondiente al post_id
        post = session.query(Post).filter_by(id=post_id).first()
        if post:
            # Verificar si el usuario actual es el creador del post
            if post.user_id != current_user["id"]:
                raise HTTPException(
                    status_code=403, detail="You don't have permission to delete this image"
                )
            # Buscar la imagen correspondiente al image_id y al post_id
            image = session.query(PostImage).filter_by(post_id=post_id, id=image_id).first()
            if image:
                # Eliminar la imagen de la base de datos y del sistema de archivos
                session.delete(image)
                session.commit()
                return {"message": "Image deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Image not found for this post")
        else:
            raise HTTPException(status_code=404, detail="Post not found")

@PostAPI.get('/posts', tags=["Post"])
def list_posts():
    """ List all posts with associated images """
    with Session() as session:
        # Obtener todos los posts con las imágenes asociadas
        posts = session.query(Post).options(joinedload(Post.images)).all()

        # Construir la respuesta final como una lista de resultados
        response = [
            {
                "Post": {
                    "post": post,
                    "images": [{"id": image.id, "image_path": image.image_path} for image in post.images]
                }
            }
            for post in posts
        ]

        return response
    
@PostAPI.get('/my-posts', tags=["Post"])
def list_user_posts(current_user: dict = Depends(get_current_user)):
    """ List posts created by the logged-in user """
    with Session() as session:
        user_id = current_user["id"]
        user_posts_data = (
            session.query(Post, PostImage)
            .outerjoin(PostImage, Post.id == PostImage.post_id)  # LEFT JOIN to include all posts
            .filter(Post.user_id == user_id)
            .all()
        )
        
        user_posts_dict = {}
        for post, post_image in user_posts_data:
            if post.id not in user_posts_dict:
                user_posts_dict[post.id] = {
                    "Post": post,
                    "images": []
                }
            if post_image:  # Check if there is an associated image
                user_posts_dict[post.id]["images"].append(post_image)
        
        response = list(user_posts_dict.values())  # Convert the dictionary values to a list
        
        return response



@PostAPI.get('/posts/{post_id}', tags=["Post"])
def get_post(post_id: int):
    """ Get a specific post """
    with Session() as session:
        post_data = (
            session.query(Post, PostImage)
            .filter(Post.id == post_id, Post.id == PostImage.post_id)
            .first()
        )
        if post_data is None:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post, post_images = post_data
        response = {
            "Post": post,
            "images": post_images
        }
        
        return response


UPLOAD_DIR = "./uploads"
POST_IMAGES_DIR = os.path.join(UPLOAD_DIR, "post_images")

@PostAPI.post('/posts', tags=["Post"])
def create_post_with_images(
    title: str = Form(...),
    description: str = Form(...),
    service_type: str = Form(...),
    location: str = Form(...),
    urgent: bool = Form(...),
    images: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    with Session() as session:
        user = session.query(User).filter_by(id=current_user["id"]).first()

        new_post = Post(
            title=title,
            description=description,
            service_type=service_type,
            location=location,
            urgent=urgent,
            user_id=user.id
        )
        
        session.add(new_post)
        session.commit()
        
        # Obtener los usuarios con perfiles que coincidan con el tipo de servicio y la ubicación del post
        matching_users = session.execute(
            select(User).join(Profile).filter(
                and_(
                    Profile.service_type.contains(service_type),
                    Profile.location.contains(location)
                )
            )
        ).scalars().all()
        
        # Crear un conjunto para evitar duplicados
        notified_users = set()
        
        # Crear el mensaje de notificación base
        notification_text = ""
        if service_type and location:
            notification_text = f"ha creado un nuevo post en"
            
            # Enviar notificaciones a los usuarios coincidentes
            for user in matching_users:
                if user.id not in notified_users:
                    send_notification(session, current_user["id"], user.id, notification_text, new_post.id)

                    notified_users.add(user.id)
        
        # Si el post es urgente y el usuario está disponible las 24 horas
        if urgent and user.profile.schedule_work == "24 horas":
            # Solo envía la notificación urgente si aún no ha sido notificado
            if user.id not in notified_users:
                send_notification(session, current_user["id"], user.id, notification_text, new_post.id)

                notified_users.add(user.id)
        
        # Guardar el nuevo post en la base de datos
        session.commit()

        # Código para manejar la carga de imágenes
        os.makedirs(POST_IMAGES_DIR, exist_ok=True)
        post_folder = str(new_post.id)
        post_upload_dir = os.path.join(POST_IMAGES_DIR, post_folder)
        os.makedirs(post_upload_dir, exist_ok=True)
        
        image_paths = []
        for image in images:
            unique_filename = f"{int(time.time())}_{image.filename}"
            new_image_path = os.path.join(post_upload_dir, unique_filename)
            image_paths.append(new_image_path)
            
            with open(new_image_path, "wb") as image_file:
                image_file.write(image.file.read())
        
        # Crear registros de imágenes en la base de datos
        for image_path in image_paths:
            # Reemplazar las barras inversas por barras inclinadas en el path
            normalized_image_path = image_path.replace('\\', '/')
            post_image = PostImage(post_id=new_post.id, image_path=normalized_image_path)
            session.add(post_image)
        
        session.commit()
        
        return new_post


@PostAPI.put('/posts/{post_id}', tags=["Post"])
def update_post_with_images(
    post_id: int, title: str, description: str, service_type: str, location: str, urgent: bool, images: List[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    """ Update a specific post """
    with Session() as session:
        existing_post = session.query(Post).filter_by(id=post_id).first()
        if existing_post is None:
            raise HTTPException(status_code=404, detail="Post not found")

        # Verifica si el usuario logueado es el creador del post
        if existing_post.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="You don't have permission to update this post")

        existing_post.title = title
        existing_post.description = description
        existing_post.service_type = service_type
        existing_post.location = location
        existing_post.urgent = urgent

        # Código para manejar la carga de imágenes nuevas y existentes
        if images:
            os.makedirs(POST_IMAGES_DIR, exist_ok=True)
            post_folder = str(existing_post.id)
            post_upload_dir = os.path.join(POST_IMAGES_DIR, post_folder)
            os.makedirs(post_upload_dir, exist_ok=True)
            
            image_paths = []
            for image in images:
                unique_filename = f"{int(time.time())}_{image.filename}"
                new_image_path = os.path.join(post_upload_dir, unique_filename)
                image_paths.append(new_image_path)
                
                with open(new_image_path, "wb") as image_file:
                    image_file.write(image.file.read())
            
            # Crear registros de imágenes en la base de datos
            for image_path in image_paths:
                post_image = PostImage(post_id=existing_post.id, image_path=image_path)
                session.add(post_image)

        session.commit()

        return {"message": "Post updated successfully"}



@PostAPI.delete("/posts/{post_id}", tags=["Post"])
def delete_post(post_id: int, current_user: dict = Depends(get_current_user)):
    with Session() as session:
        post = session.query(Post).filter_by(id=post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Publicación no encontrada")

        # Verificar si el usuario actual es el creador del post
        if post.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta publicación")

        # Eliminar notificaciones relacionadas con el post
        session.query(Notification).filter_by(post_id=post_id).delete()

        # Eliminar el post
        session.delete(post)
        session.commit()

        return {"message": "Publicación eliminada correctamente"}

