from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from config.db import Session
from schemas.profile import ProfileSchema, ServiceTypeSchema, LocationSchema, ScheduleWork
from routes.user import get_current_user, get_user
from models.profile import Profile
from fastapi.responses import FileResponse
import os
import time
import shutil
from typing import List
from models.user import User
import uuid


ProfileAPI = APIRouter()

@ProfileAPI.get('/profile-image/{user_id}', tags=["Profile Sector 1"]) ## FUNCIONA ##
def get_profile_image(user_id: int):
    # Obtener la ruta de la imagen de perfil de la base de datos
    with Session() as session:
        profile = session.query(Profile).filter_by(user_id=user_id).first()
        if profile and profile.profile_image_path:
            return FileResponse(profile.profile_image_path, media_type="image/jpeg")
        raise HTTPException(status_code=404, detail="Profile image not found")


UPLOAD_DIR = "./uploads"
PROFILE_IMAGES_DIR = os.path.join(UPLOAD_DIR, "profile_images") # Ruta absoluta donde se guardarán las imágenes
    
@ProfileAPI.post('/upload-profile-image', tags=["Profile Sector 1"])
def upload_profile_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    # Asegúrate de que el directorio de carga exista para el usuario actual
    user_folder = str(current_user['id'])
    os.makedirs(PROFILE_IMAGES_DIR, exist_ok=True)
    user_upload_dir = os.path.join(PROFILE_IMAGES_DIR, user_folder)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Genera un nombre único para la imagen basado en un timestamp
    unique_filename = f"{int(time.time())}_{file.filename}"
    new_image_path = os.path.join(user_upload_dir, unique_filename)
    
    # Guarda la nueva imagen en el sistema de archivos
    with open(new_image_path, "wb") as image_file:
        image_file.write(file.file.read())
    
    # Actualiza la ruta de la imagen de perfil en la base de datos
    with Session() as session:
        existing_profile = session.query(Profile).filter_by(user_id=current_user['id']).first()
        if existing_profile:
            # Eliminar la imagen anterior si existe
            if existing_profile.profile_image_path:
                try:
                    os.remove(existing_profile.profile_image_path)
                except FileNotFoundError:
                    pass  # Si el archivo no existe, continúa sin error
            
            existing_profile.profile_image_path = new_image_path
            session.commit()
            return {"message": "Profile image updated successfully"}

        raise HTTPException(status_code=404, detail="Profile not found")

### GET PROFILE OF CURRENT USER ###
@ProfileAPI.get('/profile/me', tags=["Profile Sector 2"])
def get_own_profile(current_user: dict = Depends(get_current_user)):
    """ Get logged-in user's profile """
    with Session() as session:
        # Obtener el usuario actual
        user = get_user(session, current_user["email"])
        if user is None or user.profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Verificar el estado is_paid del usuario
        if not user.is_paid:
            raise HTTPException(status_code=403, detail="User is not paid")

        profile = user.profile

        profile_data = {
            "id": user.id,
            "name": user.name,
            "rating": profile.rating,
            "phone": profile.phone,
            "description": profile.description,
            "service_type": profile.service_type.split(',') if profile.service_type else [],
            "location": profile.location.split(',') if profile.location else [],
            "schedule_work": profile.schedule_work,
        }

        return profile_data

def get_user_by_id(session: Session, user_id: int):
    return session.query(User).filter(User.id == user_id).first()

@ProfileAPI.get('/profile/{user_id}', tags=["Profile Sector 2"])
def get_user_profile(user_id: int, current_user: dict = Depends(get_current_user)):
    """ Get profile of a user by user ID """
    with Session() as session:
        # Obtener el usuario por ID
        user_profile = get_user_by_id(session, user_id)
        
        if user_profile is None or user_profile.profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Verificar el estado is_paid del usuario
        if not user_profile.is_paid:
            raise HTTPException(status_code=403, detail="User is not paid")

        # Obtener el perfil del usuario
        profile = user_profile.profile

        profile_data = {
            "id": user_profile.id,
            "name": user_profile.name,
            "phone": profile.phone,
            "description": profile.description,
            "service_type": profile.service_type.split(',') if profile.service_type else [],
            "location": profile.location.split(',') if profile.location else [],
            "schedule_work": profile.schedule_work,
        }

        return profile_data

    

### EDIT PROFILE FROM CURRENT USER ###
@ProfileAPI.put('/profile/me', tags=["Profile Sector 2"])
def update_own_profile(this_profile: ProfileSchema, current_user: dict = Depends(get_current_user)):
    """ Update logged-in user's profile """
    with Session() as session:
        # Obtener el usuario actual
        user = get_user(session, current_user["email"])
        if user is None or user.profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Verificar el estado is_paid del usuario
        if not user.is_paid:
            raise HTTPException(status_code=403, detail="User is not paid")

        profile = user.profile

        # Actualizar solo los campos que se proporcionan
        if this_profile.description is not None:
            profile.description = this_profile.description
        if this_profile.phone is not None:
            profile.phone = this_profile.phone
        if this_profile.service_type is not None:
            profile.service_type = ','.join(this_profile.service_type)
        if this_profile.location is not None:
            profile.location = ','.join(this_profile.location)

        # Confirmar los cambios en la base de datos
        session.commit()

        profile_data = {
            "name": user.name,
            "rating": profile.rating,
            "phone": profile.phone,
            "description": profile.description,
            "service_type": profile.service_type,
            "location": profile.location,
        }

        return profile_data

### EDITAR HORARIO ###
# @ProfileAPI.put('/profile/schedule-work', tags=["Schedule Work"])
# def update_schedule_work(schedule: ScheduleWork, current_user: dict = Depends(get_current_user)):
#     """Update schedule_work for the logged-in user"""
#     with Session() as session:
#         user = get_user(session, current_user["email"])
#         if user is None or user.profile is None:
#             raise HTTPException(status_code=404, detail="Profile not found")

#         # Verificar el estado is_paid del usuario
#         if not user.is_paid:
#             raise HTTPException(status_code=403, detail="User is not paid")

#         profile = user.profile

#         # Actualizar schedule_work según los datos proporcionados
#         if schedule.is_24_hours:
#             profile.schedule_work = "24 horas"
#         else:
#             if schedule.start_time and schedule.end_time:
#                 start_time_str = schedule.start_time.strftime('%H:%M')
#                 end_time_str = schedule.end_time.strftime('%H:%M')
#                 profile.schedule_work = f"{start_time_str} - {end_time_str}"

#         # Confirmar los cambios en la base de datos
#         session.commit()

#         return {"message": "Schedule work updated successfully"}

#VARIABLE SCHEDULE WORK    
@ProfileAPI.put('/profile/schedule-work', tags=["Schedule Work"])
def update_schedule_work(schedule: ScheduleWork, current_user: dict = Depends(get_current_user)):
    """Update schedule_work for the logged-in user"""
    with Session() as session:
        user = get_user(session, current_user["email"])
        if user is None or user.profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Verificar el estado is_paid del usuario
        if not user.is_paid:
            raise HTTPException(status_code=403, detail="User is not paid")

        profile = user.profile

        # Verificar si is_24_hours es True
        if schedule.is_24_hours:
            # Si is_24_hours es True, establecer el horario como una cadena vacía
            profile.schedule_work = "24 horas"
        else:
            # Si is_24_hours es False, asegurarse de que se proporcionen start_time y end_time
            if not schedule.start_time or not schedule.end_time:
                raise HTTPException(status_code=400, detail="Both start_time and end_time are required when is_24_hours is False")

            # Procesar start_time y end_time si se proporcionan
            profile.schedule_work = f"{schedule.start_time} - {schedule.end_time}"  # Formato "09:00 AM - 05:00 PM"

        # Confirmar los cambios en la base de datos
        session.commit()

        return {"message": "Schedule work updated successfully"}


@ProfileAPI.get('/profile/schedule-work/{user_id}', tags=["Schedule Work"], response_model=ScheduleWork)
def get_schedule_work(current_user: dict = Depends(get_current_user)):
    """Obtener el horario de trabajo para el usuario registrado"""
    with Session() as session:
        user = get_user(session, current_user["email"])
        if user is None or user.profile is None:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")

        profile = user.profile

        # Asegúrate de que todos los campos requeridos tengan valores válidos
        is_24_hours = False
        start_time = ""
        end_time = ""

        if profile.schedule_work == "24 horas":
            is_24_hours = True
        else:
            # Descomponer el horario de trabajo en start_time y end_time si es necesario
            if profile.schedule_work and "-" in profile.schedule_work:
                start_time, end_time = map(str.strip, profile.schedule_work.split("-"))

        return ScheduleWork(is_24_hours=is_24_hours, start_time=start_time, end_time=end_time)
    
# ### CREATE FOLDERS AND FILES ###

# UPLOAD_DIR = "./uploads"
# CERTIFICATES_DIR = os.path.join(UPLOAD_DIR, "certificates")
# PAST_WORKS_DIR = os.path.join(UPLOAD_DIR, "past_works")

# ### GET FOLDER IMAGES BY FOLDER ID ###

# @ProfileAPI.get('/folder-images/{folder_id}', tags=["Profile Sector 3"])
# def get_folder_images(folder_id: int, current_user: dict = Depends(get_current_user)):
#     user_folder = str(current_user['id'])

#     # Verificar si el usuario actual tiene acceso a la carpeta
#     folder_type = None
#     if folder_exists("certificates", user_folder, folder_id):
#         folder_type = "certificates"
#     elif folder_exists("past_works", user_folder, folder_id):
#         folder_type = "past_works"
#     else:
#         raise HTTPException(status_code=404, detail="Folder not found")

#     # Ahora tienes el tipo de carpeta y puedes continuar como antes
#     folder_path = os.path.join(UPLOAD_DIR, folder_type, user_folder, str(folder_id))

#     image_paths = []
#     for file_name in os.listdir(folder_path):
#         file_path = os.path.join(folder_path, file_name)
#         if os.path.isfile(file_path):
#             media_type = "image/jpeg" if file_name.lower().endswith((".jpg", ".jpeg")) else "image/png"
#             image_paths.append((file_path, media_type))

#     if not image_paths:
#         raise HTTPException(status_code=404, detail="No images found in this folder")

#     # Devolver la primera imagen si hay más de una, o la única imagen si solo hay una
#     file_path, media_type = image_paths[0]

#     return FileResponse(file_path, media_type=media_type)

# # Función auxiliar para verificar si una carpeta existe
# def folder_exists(folder_type, user_folder, folder_id):
#     folder_path = os.path.join(UPLOAD_DIR, folder_type, user_folder, str(folder_id))
#     return os.path.exists(folder_path)


# ### GET IMAGE ID FROM FOLDER ID

# @ProfileAPI.get('/folder-images/{folder_id}/{image_id}', tags=["Profile Sector 3"])
# def get_folder_image(folder_id: int, image_id: int, current_user: dict = Depends(get_current_user)):
#     user_folder = str(current_user['id'])
    
#     # Intenta encontrar la carpeta en "certificates"
#     folder_path_certificates = os.path.join(UPLOAD_DIR, "certificates", user_folder, str(folder_id))
#     if os.path.exists(folder_path_certificates):
#         folder_type = "certificates"
#     else:
#         # Si no se encuentra en "certificates", busca en "past_works"
#         folder_path_past_works = os.path.join(UPLOAD_DIR, "past_works", user_folder, str(folder_id))
#         if os.path.exists(folder_path_past_works):
#             folder_type = "past_works"
#         else:
#             raise HTTPException(status_code=404, detail="Folder not found")

#     # Ahora tienes el tipo de carpeta y puedes continuar como antes
#     folder_path = os.path.join(UPLOAD_DIR, folder_type, user_folder, str(folder_id))
    
#     # Construye el nombre del archivo en función de image_id
#     file_name = f"{image_id}.jpg"  # Asegúrate de usar la extensión correcta

#     file_path = os.path.join(folder_path, file_name)

#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="Image not found")

#     # Devuelve la imagen
#     media_type = "image/jpeg" if file_name.lower().endswith((".jpg", ".jpeg")) else "image/png"
#     return FileResponse(file_path, media_type=media_type)


# ### GET FOLDER NAME FROM FOLDER ID ###


# @ProfileAPI.get('/get-folder-name/{folder_id}', tags=["Profile Sector 3"])
# def get_folder_name(folder_id: int):
#     if folder_id in folder_name_mapping:
#         folder_name = folder_name_mapping[folder_id]
#         return {"folder_name": folder_name}
#     else:
#         raise HTTPException(status_code=404, detail="Folder not found")
    
# ### GET ALL FOLDERS INFO FROM USER ###

# @ProfileAPI.get('/user-folders', tags=["Profile Sector 3"])
# def get_user_folders(current_user: dict = Depends(get_current_user)):
#     user_folder = str(current_user['id'])

#     certificates_folders = []
#     past_works_folders = []

#     # Función para obtener los image_id dentro de una carpeta
#     def get_image_ids(folder_type, folder_id):
#         image_ids = []
#         folder_path = os.path.join(UPLOAD_DIR, folder_type, user_folder, str(folder_id))
#         if os.path.exists(folder_path):
#             for file_name in os.listdir(folder_path):
#                 if file_name.lower().endswith((".jpg", ".jpeg")):
#                     image_id = int(os.path.splitext(file_name)[0])  # Obtiene el image_id del nombre del archivo
#                     image_ids.append(image_id)
#         return image_ids

#     # Buscar carpetas en "certificates"
#     certificates_folder_path = os.path.join(UPLOAD_DIR, "certificates", user_folder)
#     if os.path.exists(certificates_folder_path):
#         for folder_id in os.listdir(certificates_folder_path):
#             folder_path = os.path.join(certificates_folder_path, folder_id)
#             if os.path.isdir(folder_path):
#                 folder_id = int(folder_id)
#                 folder_name = folder_name_mapping.get(folder_id, "")
#                 image_ids = get_image_ids("certificates", folder_id)
#                 certificates_folders.append({"folder_id": folder_id, "folder_name": folder_name, "image_ids": image_ids})

#     # Buscar carpetas en "past_works"
#     past_works_folder_path = os.path.join(UPLOAD_DIR, "past_works", user_folder)
#     if os.path.exists(past_works_folder_path):
#         for folder_id in os.listdir(past_works_folder_path):
#             folder_path = os.path.join(past_works_folder_path, folder_id)
#             if os.path.isdir(folder_path):
#                 folder_id = int(folder_id)
#                 folder_name = folder_name_mapping.get(folder_id, "")
#                 image_ids = get_image_ids("past_works", folder_id)
#                 past_works_folders.append({"folder_id": folder_id, "folder_name": folder_name, "image_ids": image_ids})

#     return {"certificates_folders": certificates_folders, "past_works_folders": past_works_folders}


# @ProfileAPI.post('/upload-certificate/{folder_name}', tags=["Profile Sector 3"])
# def upload_certificate(folder_name: str, files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
#     return _upload_files(files, current_user, "certificates", folder_name)

# @ProfileAPI.post('/upload-past-work/{folder_name}', tags=["Profile Sector 3"])
# def upload_past_work(folder_name: str, files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
#     return _upload_files(files, current_user, "past_works", folder_name)

# # Variable global para rastrear el ID de la carpeta y el ID del archivo
# next_folder_id = 1
# next_file_id = 1

# def _upload_files(files: List[UploadFile], current_user: dict, folder_name: str, folder_title: str):
#     user_id = current_user['id']

#     global next_folder_id, next_file_id  # Usar las variables globales

#     # Generar el ID de la carpeta secuencialmente
#     folder_id = next_folder_id
#     next_folder_id += 1

#     # Agregar esta línea para mapear folder_id a folder_title
#     folder_name_mapping[folder_id] = folder_title

#     user_folder = str(current_user['id'])
#     os.makedirs(os.path.join(CERTIFICATES_DIR, user_folder), exist_ok=True)
#     os.makedirs(os.path.join(PAST_WORKS_DIR, user_folder), exist_ok=True)

#     # Utilizar el ID como nombre de la carpeta
#     folder_path = os.path.join(UPLOAD_DIR, folder_name, user_folder, str(folder_id))
#     os.makedirs(folder_path, exist_ok=True)

#     uploaded_file_ids = []  # Almacenar los IDs de los archivos subidos

#     for file in files:
#         # Generar un nombre de archivo único basado en el ID de la carpeta y un contador interno
#         file_id = next_file_id
#         next_file_id += 1

#         new_file_path = os.path.join(folder_path, f"{file_id}.jpg")  # Puedes utilizar ".jpg" o ".png" como extensión
#         with open(new_file_path, "wb") as new_file:
#             new_file.write(file.file.read())

#         uploaded_file_ids.append(file_id)

#     with Session() as session:
#         existing_profile = session.query(Profile).filter_by(user_id=current_user['id']).first()
#         if existing_profile:
#             folder_attribute = getattr(existing_profile, folder_name, {})
#             if folder_name not in folder_attribute:
#                 folder_attribute[folder_name] = {}
#             folder_attribute[folder_name][folder_id] = {"title": folder_title, "file_ids": uploaded_file_ids}

#             # Agrega la carpeta y los IDs de los archivos al campo "folders"
#             existing_profile.folders.update(folder_attribute)
#             session.commit()
#             return {"message": f"{folder_name.capitalize()} updated successfully"}
        

# folder_name_mapping = {}

# ### AGREGAR IMAGEN POR FOLDER_ID ###

# @ProfileAPI.post('/add-image/{folder_id}', tags=["Profile Sector 3"])
# def add_image_to_folder(folder_id: int, files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
#     global next_file_id
#     # Verifica si el usuario tiene acceso a esta carpeta
#     user_id = current_user['id']
    
#     # Comprueba si la carpeta existe en "certificates" o "past_works"
#     folder_path_certificates = os.path.join(UPLOAD_DIR, "certificates", str(user_id), str(folder_id))
#     folder_path_past_works = os.path.join(UPLOAD_DIR, "past_works", str(user_id), str(folder_id))
    
#     if os.path.exists(folder_path_certificates):
#         folder_type = "certificates"
#     elif os.path.exists(folder_path_past_works):
#         folder_type = "past_works"
#     else:
#         raise HTTPException(status_code=404, detail="Folder not found")

#     # Verifica si la carpeta existe en el mapeo de nombres
#     if folder_id not in folder_name_mapping:
#         raise HTTPException(status_code=404, detail="Folder not found")

#     user_folder = str(user_id)
#     folder_path = os.path.join(UPLOAD_DIR, folder_type, user_folder, str(folder_id))

#     # Asegúrate de que la carpeta exista
#     if not os.path.exists(folder_path):
#         raise HTTPException(status_code=404, detail="Folder not found")

#     uploaded_file_ids = []  # Almacenar los IDs de los archivos subidos

#     for file in files:
#         # Generar un ID de archivo único basado en un contador interno
#         file_id = next_file_id
#         next_file_id += 1

#         # Utiliza un nombre de archivo basado en el ID del archivo
#         file_name = f"{file_id}.jpg"  # Puedes utilizar ".jpg" o ".png" como extensión
#         new_file_path = os.path.join(folder_path, file_name)

#         with open(new_file_path, "wb") as new_file:
#             new_file.write(file.file.read())

#         uploaded_file_ids.append(file_id)

#     return {"message": f"Images added to folder with ID {folder_id}"}


# ### EDITAR NOMBRE DE CARPETA ###

# @ProfileAPI.put('/update-folder-name/{folder_id}', tags=["Profile Sector 3"])
# def update_folder_name(folder_id: int, new_folder_name: str, current_user: dict = Depends(get_current_user)):
#     # Verificar que el usuario tenga acceso a esta carpeta
#     user_id = current_user['id']
    
#     # Comprueba si la carpeta existe en "certificates" o "past_works"
#     folder_path_certificates = os.path.join(UPLOAD_DIR, "certificates", str(user_id), str(folder_id))
#     folder_path_past_works = os.path.join(UPLOAD_DIR, "past_works", str(user_id), str(folder_id))

#     with Session() as session:
#         if os.path.exists(folder_path_certificates):
#             folder_type = "certificates"
#         elif os.path.exists(folder_path_past_works):
#             folder_type = "past_works"
#         else:
#          raise HTTPException(status_code=404, detail="Folder not found")

#     # Obtén el nombre actual de la carpeta a través del mapeo de nombres
#     if folder_id in folder_name_mapping:
#         current_folder_name = folder_name_mapping[folder_id]
#     else:
#         raise HTTPException(status_code=404, detail="Folder not found")

#     # Actualiza el nombre de la carpeta en el mapeo de nombres
#     folder_name_mapping[folder_id] = new_folder_name

#     # Confirma los cambios en el mapeo de nombres
#     session.commit()

#     return {"message": f"Folder name updated successfully from '{current_folder_name}' to '{new_folder_name}'"}

# ### ELIMINA LA CARPETA POR FOLDER ID CON SU CONTENIDO ###

# @ProfileAPI.delete('/delete-folder/{folder_id}', tags=["Profile Sector 3"])
# def delete_folder(folder_id: int, current_user: dict = Depends(get_current_user)):
#     user_folder = str(current_user['id'])
    
#     # Intenta encontrar la carpeta en "certificates"
#     folder_path_certificates = os.path.join(UPLOAD_DIR, "certificates", user_folder, str(folder_id))
#     if os.path.exists(folder_path_certificates):
#         folder_type = "certificates"
#     else:
#         # Si no se encuentra en "certificates", busca en "past_works"
#         folder_path_past_works = os.path.join(UPLOAD_DIR, "past_works", user_folder, str(folder_id))
#         if os.path.exists(folder_path_past_works):
#             folder_type = "past_works"
#         else:
#             raise HTTPException(status_code=404, detail="Folder not found")
    
#     # Ahora tienes el tipo de carpeta y la ruta, puedes eliminar la carpeta
#     folder_path = os.path.join(UPLOAD_DIR, folder_type, user_folder, str(folder_id))
#     shutil.rmtree(folder_path, ignore_errors=True)  # Esto eliminará la carpeta y su contenido

#     # Elimina la carpeta del mapeo de nombres si existe
#     if folder_id in folder_name_mapping:
#         del folder_name_mapping[folder_id]

#     # También elimina la carpeta del perfil del usuario si existe
#     with Session() as session:
#         existing_profile = session.query(Profile).filter_by(user_id=current_user['id']).first()
#         if existing_profile:
#             if folder_type in existing_profile.folders and folder_id in existing_profile.folders[folder_type]:
#                 del existing_profile.folders[folder_type][folder_id]
#                 session.commit()

#     return {"message": f"Folder with ID {folder_id} has been deleted"}


# ### ELIMINA IMAGEN FOR FOLDER ID Y IMAGE ID ###
# @ProfileAPI.delete('/delete-image/{folder_id}/{image_id}', tags=["Profile Sector 3"])
# def delete_folder_image(folder_id: int, image_id: int, current_user: dict = Depends(get_current_user)):
#     user_folder = str(current_user['id'])
    
#     # Intenta encontrar la carpeta en "certificates"
#     folder_path_certificates = os.path.join(UPLOAD_DIR, "certificates", user_folder, str(folder_id))
#     if os.path.exists(folder_path_certificates):
#         folder_type = "certificates"
#     else:
#         # Si no se encuentra en "certificates", busca en "past_works"
#         folder_path_past_works = os.path.join(UPLOAD_DIR, "past_works", user_folder, str(folder_id))
#         if os.path.exists(folder_path_past_works):
#             folder_type = "past_works"
#         else:
#             raise HTTPException(status_code=404, detail="Folder not found")

#     # Ahora tienes el tipo de carpeta y puedes continuar como antes
#     folder_path = os.path.join(UPLOAD_DIR, folder_type, user_folder, str(folder_id))
    
#     # Construye el nombre del archivo en función de image_id
#     file_name = f"{image_id}.jpg"  # Asegúrate de usar la extensión correcta

#     file_path = os.path.join(folder_path, file_name)

#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="Image not found")

#     # Elimina el archivo
#     os.remove(file_path)

#     return {"message": "Image deleted successfully"}



    


# Actualización del endpoint para obtener perfiles por tipo de servicio
@ProfileAPI.get('/profiles/service_type', response_model=List[ServiceTypeSchema], tags=["Filters"])
def get_profiles_by_service_type(
    service_type: str = Query(default=None, description="Filter profiles by service type"),
    session: Session = Depends(lambda: Session())
):
    """ Get profiles by service type """
    if service_type is None:
        profiles = session.query(Profile).all()
    else:
        profiles = session.query(Profile).filter(Profile.service_type.like(f'%{service_type}%')).all()

    profiles_data = [
        {
            "id": profile.id,
            "name": profile.user.name,
            "service_type": profile.service_type,
        }
        for profile in profiles
    ]

    return profiles_data

# Actualización del endpoint para obtener perfiles por tipo de servicio
@ProfileAPI.get('/profiles/location', response_model=List[LocationSchema], tags=["Filters"])
def get_profiles_by_location(
    location: str = Query(default=None, description="Filter profiles by service type"),
    session: Session = Depends(lambda: Session())
):
    """ Get profiles by service type """
    if location is None:
        profiles = session.query(Profile).all()
    else:
        profiles = session.query(Profile).filter(Profile.location.like(f'%{location}%')).all()

    profiles_data = [
        {
            "id": profile.id,
            "name": profile.user.name,
            "location": profile.location,
        }
        for profile in profiles
    ]

    return profiles_data