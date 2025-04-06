from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
import os
from models.profile import Profile, CertificateImage, Certificate, PastWork, PastWorkImage
from schemas.shared_images import CertificateResponse, CertificateImageResponse, CertificateUpdate, EmptyCertificateImageResponse
from schemas.shared_images import PastWorkCreate, PastWorkImageResponse, PastWorkResponse, PastWorkUpdate, EmptyPastWorkImageResponse
from config.db import Session
import time
from typing import List
from routes.user import get_current_user
from fastapi.responses import FileResponse
import shutil

CPwAPI = APIRouter()



@CPwAPI.get("/certificate-images/{certificate_id}/{image_id}", tags=["Certificates"])
def get_certificate_image(certificate_id: int, image_id: int):
    with Session() as session:
        certificate = session.query(Certificate).filter_by(id=certificate_id).first()
        if certificate:
            image = session.query(CertificateImage).filter_by(certificate_id=certificate_id, id=image_id).first()
            if image:
                media_type = "image/jpeg" if image.image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                return FileResponse(image.image_path, media_type=media_type)
            else:
                raise HTTPException(status_code=404, detail="Image not found for this certificate")
        else:
            raise HTTPException(status_code=404, detail="Certificate not found")

@CPwAPI.get("/certificate/{certificate_id}", tags=["Certificates"])
def get_certificate(certificate_id: int):
    with Session() as session:
        certificate = session.query(Certificate).filter_by(id=certificate_id).first()
        if certificate:
            # Recupera las imágenes asociadas al certificado
            images = session.query(CertificateImage).filter_by(certificate_id=certificate_id).all()

            # Crea una lista de objetos CertificateImageResponse
            image_responses = []
            for image in images:
                image_response = CertificateImageResponse(id=image.id, image_path=image.image_path)
                image_responses.append(image_response)

            # Crea el objeto CertificateResponse con las imágenes
            certificate_response = CertificateResponse(
                id=certificate.id,
                user_id=certificate.user_id,
                folder_name=certificate.folder_name,
                images=image_responses
            )

            return certificate_response
        else:
            raise HTTPException(status_code=404, detail="Certificate not found")
        

        
@CPwAPI.get("/certificates", response_model=List[CertificateResponse], tags=["Certificates"])
def get_certificates(current_user: dict = Depends(get_current_user)):
    with Session() as session:
        certificates = session.query(Certificate).filter_by(user_id=current_user['id']).all()

        certificate_responses = []
        for certificate in certificates:
            # Recupera las imágenes asociadas al certificado
            images = session.query(CertificateImage).filter_by(certificate_id=certificate.id).all()

            # Crea una lista de objetos CertificateImageResponse
            image_responses = []
            for image in images:
                image_response = CertificateImageResponse(id=image.id, image_path=image.image_path)
                image_responses.append(image_response)

            # Crea el objeto CertificateResponse con las imágenes
            certificate_response = CertificateResponse(
                id=certificate.id,
                user_id=certificate.user_id,
                folder_name=certificate.folder_name,
                images=image_responses
            )

            certificate_responses.append(certificate_response)

        return certificate_responses
    
@CPwAPI.get("/certificates/{user_id}", response_model=List[CertificateResponse], tags=["Certificates"])
def get_certificates(user_id: int):
    with Session() as session:
        certificates = session.query(Certificate).filter_by(user_id=user_id).all()

        certificate_responses = []
        for certificate in certificates:
            # Recupera las imágenes asociadas al certificado
            images = session.query(CertificateImage).filter_by(certificate_id=certificate.id).all()

            # Crea una lista de objetos CertificateImageResponse
            image_responses = []
            for image in images:
                image_response = CertificateImageResponse(id=image.id, image_path=image.image_path)
                image_responses.append(image_response)

            # Crea el objeto CertificateResponse con las imágenes
            certificate_response = CertificateResponse(
                id=certificate.id,
                user_id=certificate.user_id,
                folder_name=certificate.folder_name,
                images=image_responses
            )

            certificate_responses.append(certificate_response)

        return certificate_responses


UPLOAD_DIR = "./uploads"
CERTIFICATES_IMAGES_DIR = os.path.join(UPLOAD_DIR, "certificates")

@CPwAPI.post('/upload-certificate', response_model=CertificateResponse, tags=["Certificates"])
def upload_certificate(
    folder_name: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Asegúrate de que el directorio de carga exista para el usuario actual
    user_folder = str(current_user['id'])
    os.makedirs(CERTIFICATES_IMAGES_DIR, exist_ok=True)
    user_upload_dir = os.path.join(CERTIFICATES_IMAGES_DIR, user_folder)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Crear una carpeta única para el folder name
    folder_dir = os.path.join(user_upload_dir, folder_name)
    os.makedirs(folder_dir, exist_ok=True)

    # Obtener el último número de archivo utilizado
    last_file_number = get_last_file_number(folder_dir)

    # Crear una nueva entrada de Certificate en la base de datos
    with Session() as session:
        existing_profile = session.query(Profile).filter_by(user_id=current_user['id']).first()
        if not existing_profile:
            raise HTTPException(status_code=404, detail="User not found")
        
        new_certificate = Certificate(
            user_id=current_user['id'],
            folder_name=folder_name
        )
        session.add(new_certificate)
        session.commit()
        
        # Crear registros para las imágenes de certificados
        for file in files:
            # Incrementar el contador de archivo y crear el nombre de archivo
            last_file_number += 1
            unique_filename = f"{last_file_number}.jpeg"  # Cambia la extensión según corresponda
            
            new_image_path = os.path.join(folder_dir, unique_filename)
            
            # Guarda el archivo en el sistema de archivos
            with open(new_image_path, "wb") as image_file:
                image_file.write(file.file.read())
            
            # Crea un registro en la tabla CertificateImage
            certificate_image = CertificateImage(
                certificate_id=new_certificate.id,
                image_path=new_image_path
            )
            session.add(certificate_image)
        
        session.commit()
        
        # Crear una instancia de CertificateResponse con el id de la carpeta, el nombre de la carpeta y la lista de imágenes
        certificate_response = CertificateResponse(
            id=new_certificate.id,
            user_id=new_certificate.user_id,
            folder_name=folder_name,
            images=[CertificateImageResponse(id=image.id, image_path=image.image_path) for image in new_certificate.images]
        )

        return certificate_response

def sqlalchemy_to_pydantic(certificate):
    return CertificateResponse(
        id=certificate.id,
        user_id=certificate.user_id,
        folder_name=certificate.folder_name,
        images=[CertificateImageResponse(id=image.id, image_path=image.image_path) for image in certificate.images]
    )


@CPwAPI.post("/certificate/{certificate_id}/add-images", response_model=CertificateResponse, tags=["Certificates"])
def add_images_to_certificate(
    certificate_id: int,
    certificate_images: List[UploadFile],
    current_user: dict = Depends(get_current_user)
):
    # Verifica si el certificado existe
    with Session() as session:
        certificate = session.query(Certificate).filter_by(id=certificate_id, user_id=current_user['id']).first()
        if certificate:
            # Obtén el directorio de la carpeta del certificado
            folder_dir = os.path.join(CERTIFICATES_IMAGES_DIR, str(current_user['id']), certificate.folder_name)

            # Obtener el último número de archivo utilizado
            last_file_number = get_last_file_number(folder_dir)

            # Crear registros para las imágenes de certificados
            for file in certificate_images:
                # Incrementar el contador de archivo y crear el nombre de archivo
                last_file_number += 1
                unique_filename = f"{last_file_number}.jpeg"  # Cambia la extensión según corresponda
                
                new_image_path = os.path.join(folder_dir, unique_filename)
                
                # Guarda el archivo en el sistema de archivos
                with open(new_image_path, "wb") as image_file:
                    image_file.write(file.file.read())
                
                # Crea un registro en la tabla CertificateImage
                certificate_image = CertificateImage(
                    certificate_id=certificate.id,
                    image_path=new_image_path
                )
                session.add(certificate_image)

            session.commit()

            # Convierte el objeto SQLAlchemy en un objeto Pydantic antes de devolverlo como respuesta
            return sqlalchemy_to_pydantic(certificate)
        else:
            raise HTTPException(status_code=404, detail="Certificate not found")
        

@CPwAPI.put("/certificate/{certificate_id}", response_model=CertificateResponse, tags=["Certificates"])
def update_certificate(
    certificate_id: int,
    certificate_update: CertificateUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Verifica si el certificado existe y pertenece al usuario actual
    with Session() as session:
        certificate = session.query(Certificate).filter_by(id=certificate_id, user_id=current_user['id']).first()
        if certificate:
            # Obtiene el directorio actual de la carpeta
            current_folder_dir = os.path.join(CERTIFICATES_IMAGES_DIR, str(current_user['id']), certificate.folder_name)

            # Actualiza el folder_name con el nuevo valor en la base de datos
            certificate.folder_name = certificate_update.folder_name

            # Calcula la nueva ruta completa de la carpeta en el sistema de archivos
            new_folder_dir = os.path.join(CERTIFICATES_IMAGES_DIR, str(current_user['id']), certificate.folder_name)

            # Renombra la carpeta en el sistema de archivos
            os.rename(current_folder_dir, new_folder_dir)

            # Guarda los cambios en la base de datos
            session.commit()

            # Convierte el objeto SQLAlchemy en un objeto Pydantic antes de devolverlo como respuesta
            return sqlalchemy_to_pydantic(certificate)
        else:
            raise HTTPException(status_code=404, detail="Certificate not found")

        
@CPwAPI.delete("/certificate/{certificate_id}", response_model=CertificateResponse, tags=["Certificates"])
def delete_certificate(
    certificate_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Verifica si el certificado existe y pertenece al usuario actual
    with Session() as session:
        certificate = session.query(Certificate).filter_by(id=certificate_id, user_id=current_user['id']).first()
        if certificate:
            # Elimina la carpeta y su contenido del sistema de archivos
            folder_dir = os.path.join(CERTIFICATES_IMAGES_DIR, str(current_user['id']), certificate.folder_name)
            shutil.rmtree(folder_dir)

            # Elimina el certificado de la base de datos
            session.delete(certificate)
            session.commit()

            # Convierte el objeto SQLAlchemy en un objeto Pydantic antes de devolverlo como respuesta
            return sqlalchemy_to_pydantic(certificate)
        else:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
@CPwAPI.delete("/certificate/{certificate_id}/image/{image_id}", response_model=EmptyCertificateImageResponse, tags=["Certificates"])
def delete_certificate_image(
    certificate_id: int,
    image_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Verifica si el certificado existe y pertenece al usuario actual
    with Session() as session:
        certificate = session.query(Certificate).filter_by(id=certificate_id, user_id=current_user['id']).first()
        if certificate:
            # Busca la imagen dentro del certificado
            certificate_image = session.query(CertificateImage).filter_by(certificate_id=certificate_id, id=image_id).first()
            if certificate_image:
                try:
                    # Elimina el archivo del sistema de archivos
                    os.remove(certificate_image.image_path)

                    # Elimina el registro de la imagen de la base de datos
                    session.delete(certificate_image)
                    session.commit()

                    # Devuelve una instancia vacía de EmptyCertificateImageResponse
                    return EmptyCertificateImageResponse()
                except Exception as e:
                    # Maneja cualquier error que pueda ocurrir durante la eliminación del archivo
                    raise HTTPException(status_code=500, detail="Error deleting certificate image")
            else:
                raise HTTPException(status_code=404, detail="Certificate image not found")
        else:
            raise HTTPException(status_code=404, detail="Certificate not found")
        

########################## PAST WORKS #############################

@CPwAPI.get("/pastwork-images/{past_work_id}/{image_id}", tags=["Past Works"])
def get_past_work_image(past_work_id: int, image_id: int):
    with Session() as session:
        past_work = session.query(PastWork).filter_by(id=past_work_id).first()
        if past_work:
            image = session.query(PastWorkImage).filter_by(past_work_id=past_work_id, id=image_id).first()
            if image:
                media_type = "image/jpeg" if image.image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                return FileResponse(image.image_path, media_type=media_type)
            else:
                raise HTTPException(status_code=404, detail="Image not found for this past work")
        else:
            raise HTTPException(status_code=404, detail="Past Work not found")

@CPwAPI.get("/past_work/{past_work_id}", response_model=PastWorkResponse, tags=["Past Works"])
def get_past_work(past_work_id: int):
    with Session() as session:
        past_work = session.query(PastWork).filter_by(id=past_work_id).first()
        if past_work:
            # Recupera las imágenes asociadas a trabajos pasados
            images = session.query(PastWorkImage).filter_by(past_work_id=past_work_id).all()

            # Crea una lista de objetos PastWorkImageResponse
            image_responses = []
            for image in images:
                image_response = PastWorkImageResponse(id=image.id, image_path=image.image_path)
                image_responses.append(image_response)

            # Crea el objeto PastWorkResponse con las imágenes
            past_work_response = PastWorkResponse(
                id=past_work.id,
                user_id=past_work.user_id,
                folder_name=past_work.folder_name,
                images=image_responses
            )

            return past_work_response
        else:
            raise HTTPException(status_code=404, detail="Past Work not found")
        
@CPwAPI.get("/past_works", response_model=List[PastWorkResponse], tags=["Past Works"])
def get_past_works(current_user: dict = Depends(get_current_user)):
    with Session() as session:
        past_works = session.query(PastWork).filter_by(user_id=current_user['id']).all()

        past_work_responses = []
        for past_work in past_works:
            # Recupera las imágenes asociadas al trabajo pasado
            images = session.query(PastWorkImage).filter_by(past_work_id=past_work.id).all()

            # Crea una lista de objetos PastWorkImageResponse
            image_responses = []
            for image in images:
                image_response = PastWorkImageResponse(id=image.id, image_path=image.image_path)
                image_responses.append(image_response)

            # Crea el objeto PastWorkResponse con las imágenes
            past_work_response = PastWorkResponse(
                id=past_work.id,
                user_id=past_work.user_id,
                folder_name=past_work.folder_name,
                images=image_responses
            )

            past_work_responses.append(past_work_response)

        return past_work_responses

@CPwAPI.get("/past_works/{user_id}", response_model=List[PastWorkResponse], tags=["Past Works"])
def get_past_works(user_id: int):
    with Session() as session:
        # Modifica la consulta para filtrar los trabajos pasados por el ID del usuario
        past_works = session.query(PastWork).filter_by(user_id=user_id).all()

        past_work_responses = []
        for past_work in past_works:
            # Recupera las imágenes asociadas al trabajo pasado
            images = session.query(PastWorkImage).filter_by(past_work_id=past_work.id).all()

            # Crea una lista de objetos PastWorkImageResponse
            image_responses = []
            for image in images:
                image_response = PastWorkImageResponse(id=image.id, image_path=image.image_path)
                image_responses.append(image_response)

            # Crea el objeto PastWorkResponse con las imágenes
            past_work_response = PastWorkResponse(
                id=past_work.id,
                user_id=past_work.user_id,
                folder_name=past_work.folder_name,
                images=image_responses
            )

            past_work_responses.append(past_work_response)

        return past_work_responses

UPLOAD_DIR = "./uploads"
PASTWORK_IMAGES_DIR = os.path.join(UPLOAD_DIR, "past_works")

@CPwAPI.post('/upload-past-work', tags=["Past Works"])
def upload_past_work(
    folder_name: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Asegúrate de que el directorio de carga exista para el usuario actual
        user_folder = str(current_user['id'])
        os.makedirs(PASTWORK_IMAGES_DIR, exist_ok=True)
        user_upload_dir = os.path.join(PASTWORK_IMAGES_DIR, user_folder)
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Crear una carpeta única para el folder name
        folder_dir = os.path.join(user_upload_dir, folder_name)
        os.makedirs(folder_dir, exist_ok=True)

        # Obtener el último número de archivo utilizado
        last_file_number = get_last_file_number(folder_dir)

        # Crear una nueva entrada de Past Work en la base de datos
        with Session() as session:
            existing_profile = session.query(Profile).filter_by(user_id=current_user['id']).first()
            if not existing_profile:
                raise HTTPException(status_code=404, detail="User not found")
            
            new_past_work = PastWork(
                user_id=current_user['id'],
                folder_name=folder_name
            )
            session.add(new_past_work)
            session.commit()
            
            # Crear registros para las imágenes de certificados
            for file in files:
                # Incrementar el contador de archivo y crear el nombre de archivo
                last_file_number += 1
                unique_filename = f"{last_file_number}.jpeg"  # Cambia la extensión según corresponda
                
                new_image_path = os.path.join(folder_dir, unique_filename)
                
                # Guarda el archivo en el sistema de archivos
                with open(new_image_path, "wb") as image_file:
                    image_file.write(file.file.read())
                
                # Crea un registro en la tabla PastWorkImage
                past_work_image = PastWorkImage(
                    past_work_id=new_past_work.id,
                    image_path=new_image_path
                )
                session.add(past_work_image)
            
            session.commit()
            
            # Crear una instancia de PastWorkResponse con el id de la carpeta, el nombre de la carpeta y la lista de imágenes
            past_work_response = PastWorkResponse(
                id=new_past_work.id,
                user_id=new_past_work.user_id,
                folder_name=folder_name,
                images=[PastWorkImageResponse(id=image.id, image_path=image.image_path) for image in new_past_work.images]
            )

            return past_work_response
    except Exception as e:
        # Manejar cualquier error y devolver una respuesta de error adecuada
        return {"error": str(e)}, 500
    
def sqlalchemy_to_pydantic(past_work):
    return PastWorkResponse(
        id=past_work.id,
        user_id=past_work.user_id,
        folder_name=past_work.folder_name,
        images=[PastWorkImageResponse(id=image.id, image_path=image.image_path) for image in past_work.images]
    )    

def get_last_file_number(folder_dir):
    # Obtener la lista de archivos en la carpeta
    files = os.listdir(folder_dir)
    
    # Filtrar solo los archivos con la extensión deseada (ejemplo: .jpeg)
    image_files = [file for file in files if file.endswith(".jpeg")]
    
    # Si no hay archivos, comenzar desde 1; de lo contrario, obtener el número más alto
    if not image_files:
        return 0
    else:
        # Ordenar la lista de archivos para encontrar el número más alto
        image_files.sort()
        last_file = image_files[-1]
        last_file_number = int(os.path.splitext(last_file)[0])
        return last_file_number
    




@CPwAPI.post("/past_work/{past_work_id}/add-images", tags=["Past Works"])
def add_images_to_past_work(
    past_work_id: int,
    past_work_images: List[UploadFile],
    current_user: dict = Depends(get_current_user)
):
    # Verifica si el trabajo pasado existe
    with Session() as session:
        past_work = session.query(PastWork).filter_by(id=past_work_id, user_id=current_user['id']).first()
        if past_work:
            # Obtén el directorio de la carpeta del trabajo pasado
            folder_dir = os.path.join(PASTWORK_IMAGES_DIR, str(current_user['id']), past_work.folder_name)

            # Obtener el último número de archivo utilizado
            last_file_number = get_last_file_number(folder_dir)

            # Crear registros para las imágenes de trabajos pasados
            for file in past_work_images:
                # Incrementar el contador de archivo y crear el nombre de archivo
                last_file_number += 1
                unique_filename = f"{last_file_number}.jpeg"  # Cambia la extensión según corresponda
                
                new_image_path = os.path.join(folder_dir, unique_filename)
                
                # Guarda el archivo en el sistema de archivos
                with open(new_image_path, "wb") as image_file:
                    image_file.write(file.file.read())
                
                # Crea un registro en la tabla PastWorkImage
                past_work_image = PastWorkImage(
                    past_work_id=past_work.id,
                    image_path=new_image_path
                )
                session.add(past_work_image)

            session.commit()

            # Convierte el objeto SQLAlchemy en un objeto Pydantic antes de devolverlo como respuesta
            return sqlalchemy_to_pydantic(past_work)
        else:
            raise HTTPException(status_code=404, detail="Past Work not found")
        

@CPwAPI.put("/past_work/{past_work_id}", tags=["Past Works"])
def update_past_work(
    past_work_id: int,
    past_work_update: PastWorkUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Verifica si el certificado existe y pertenece al usuario actual
    with Session() as session:
        past_work = session.query(PastWork).filter_by(id=past_work_id, user_id=current_user['id']).first()
        if past_work:
            # Obtiene el directorio actual de la carpeta
            current_folder_dir = os.path.join(PASTWORK_IMAGES_DIR, str(current_user['id']), past_work.folder_name)

            # Actualiza el folder_name con el nuevo valor en la base de datos
            past_work.folder_name = past_work_update.folder_name

            # Calcula la nueva ruta completa de la carpeta en el sistema de archivos
            new_folder_dir = os.path.join(PASTWORK_IMAGES_DIR, str(current_user['id']), past_work.folder_name)

            # Renombra la carpeta en el sistema de archivos
            os.rename(current_folder_dir, new_folder_dir)

            # Guarda los cambios en la base de datos
            session.commit()

            # Convierte el objeto SQLAlchemy en un objeto Pydantic antes de devolverlo como respuesta
            return sqlalchemy_to_pydantic(past_work)
        else:
            raise HTTPException(status_code=404, detail="Past Work not found")

        
@CPwAPI.delete("/past_work/{past_work_id}", response_model=PastWorkResponse, tags=["Past Works"])
def delete_past_work(
    past_work_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Verifica si el trabajo pasado existe y pertenece al usuario actual
    with Session() as session:
        past_work = session.query(PastWork).filter_by(id=past_work_id, user_id=current_user['id']).first()
        if past_work:
            # Elimina la carpeta y su contenido del sistema de archivos
            folder_dir = os.path.join(PASTWORK_IMAGES_DIR, str(current_user['id']), past_work.folder_name)
            shutil.rmtree(folder_dir)

            # Elimina el certificado de la base de datos
            session.delete(past_work)
            session.commit()

            # Convierte el objeto SQLAlchemy en un objeto Pydantic antes de devolverlo como respuesta
            return sqlalchemy_to_pydantic(past_work)
        else:
            raise HTTPException(status_code=404, detail="Past Work not found")
        
@CPwAPI.delete("/past_work/{past_work_id}/image/{image_id}", response_model=EmptyPastWorkImageResponse, tags=["Past Works"])
def delete_past_work_image(
    past_work_id: int,
    image_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Verifica si el trabajo pasado existe y pertenece al usuario actual
    with Session() as session:
        past_work = session.query(PastWork).filter_by(id=past_work_id, user_id=current_user['id']).first()
        if past_work:
            # Busca la imagen dentro del trabajo pasado
            past_work_image = session.query(PastWorkImage).filter_by(past_work_id=past_work_id, id=image_id).first()
            if past_work_image:
                try:
                    # Elimina el archivo del sistema de archivos
                    os.remove(past_work_image.image_path)

                    # Elimina el registro de la imagen de la base de datos
                    session.delete(past_work_image)
                    session.commit()

                    # Devuelve una instancia vacía de EmptyPastWorkImageResponse
                    return EmptyPastWorkImageResponse()
                except Exception as e:
                    # Maneja cualquier error que pueda ocurrir durante la eliminación del archivo
                    raise HTTPException(status_code=500, detail="Error deleting past work image")
            else:
                raise HTTPException(status_code=404, detail="Past Work image not found")
        else:
            raise HTTPException(status_code=404, detail="Past Work not found")
        

