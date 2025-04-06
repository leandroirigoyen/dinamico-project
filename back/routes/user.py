from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy import select, update
from config.db import conn, Session
from models.user import User
from models.profile import Profile
from schemas.user import UserSchemaCreation, UserEmail, UserName
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT
import secrets
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

UserAPI = APIRouter()

SECRET_KEY = "96cb7f04c156382c151fdd1ba870fec774cdc051047e7a410eb50c060761a75c"  # Cambia esto con tu propia clave secreta
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 ## COMENTAR

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Función para verificar las contraseñas
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Función para obtener el hash de una contraseña
def get_password_hash(password):
    return pwd_context.hash(password)

# Función para generar el token de acceso
def create_access_token(data: dict, expires_delta: timedelta): ## ELIMINAR expires_delta: timedelta ##
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta ## COMENTAR
    to_encode.update({"exp": expire}) ## COMENTAR
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

### OBTENER USUARIO POR MAIL ### SE UTILIZA EN TOKEN Y CURRENT_USER
def get_user(session: Session, email: str):
    return session.execute(select(User).where(User.email == email)).first()


### USUARIO ACTUAL ###
@UserAPI.get("/current_user", tags=["Validation"])
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Refrescar la sesión de la base de datos para obtener el último usuario creado
    with Session() as session:
        session.expire_all()
        
        user = get_user(session, email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        # Crear un diccionario con los campos específicos que deseas devolver
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "verification_code": user.verification_code,
            "is_verified": user.is_verified, 
            "expiration_date":user.expiration_date
            # Agrega otros campos aquí
        }

        return user_data

### TOKEN CREATION ACCESS ### Manda a la base de datos directamente el access_token

def get_user(session: Session, email: str):
    return session.query(User).filter(User.email == email).first()

@UserAPI.post("/token", tags=["Validation"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Refrescar la sesión de la base de datos para obtener el último usuario creado
    with Session() as session:
        session.expire_all()

        # Obtener el usuario de la base de datos
        user = get_user(session, form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid username or password")

        # Generar el token de acceso
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) ## COMENTAR PARA BORRAR TIEMPO DE EXPIRACION
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires ## COMENTAR PARA BORRAR TIEMPO DE EXPIRACION
        )

        # Actualizar el campo access_token en la base de datos usando una consulta de actualización
        stmt = update(User).where(User.id == user.id).values(access_token=access_token)
        session.execute(stmt)
        session.commit()

    # Retornar solo el token de acceso
    return {"access_token": access_token}



@UserAPI.post("/logout", tags=["Validation"])
async def logout(current_user: dict = Depends(get_current_user)):
    # Refrescar la sesión de la base de datos para obtener el último usuario creado
    with Session() as session:
        session.expire_all()

        # Obtener el usuario de la base de datos
        user = get_user(session, current_user["email"])
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        # Invalidar el token de acceso en la base de datos
        stmt = update(User).where(User.id == user.id).values(access_token=None)
        session.execute(stmt)
        session.commit()

    return {"message": "Logout successful"}



### OBTENER TODOS LOS USUARIOS ###
def get_session() -> Session:
    session = Session()
    try:
        yield session
    finally:
        session.close()


### GET ALL USERS ###
@UserAPI.get('/users', tags=["Users"])
def get_all_users(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):

    users = session.query(User).all()

    return users


### GET USER BY ID ###
@UserAPI.get('/users/{user_id}', tags=["Users"])
def get_user_by_id(user_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

def send_verification_email(user_email, verification_code):
    # Configura los detalles del servidor SMTP
    smtp_server = 'smtp-relay.brevo.com'
    smtp_port = 587
    smtp_username = 'info.dinamicouy@gmail.com'
    smtp_password = 'bpqtnD29HxjJ4G3v'

    # Crea el mensaje de correo electrónico
    msg = MIMEMultipart()
    msg['From'] = 'info.dinamicouy@gmail.com'
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


@UserAPI.post('/users', tags=["User"])
def create_user_with_profile(this_user: UserSchemaCreation):
    """Create user with profile"""
    new_user = this_user.dict()
    new_user["hashed_password"] = get_password_hash(new_user["password"])
    del new_user["password"]

    # Calcular la fecha de expiración inicial (30 días después de la fecha actual)
    expiration_date = datetime.utcnow() + timedelta(days=30)

    with Session() as session:
        # Genera un código de verificación de 6 caracteres numéricos
        verification_code = ''.join(random.choice('0123456789') for _ in range(6))

        # Crea el usuario con el código de verificación
        user = User(**new_user, is_paid=True, expiration_date=expiration_date, verification_code=verification_code)  # Estado is_paid en True
        profile = Profile(user=user)
        user.profile = profile
        session.add(user)
        session.commit()

        # Envía el correo electrónico de verificación
        if send_verification_email(user.email, verification_code):
            return {"message": "User registered successfully. Verification email sent."}
        else:
            return {"message": "User registered successfully, but verification email could not be sent."}

### CHANGE USER PASSWORD ###
@UserAPI.put('/users/change-password', tags=["User"])
def change_password(new_password: str, current_user: dict = Depends(get_current_user)):
    """Change user password"""

    # Obtener el usuario existente
    with Session() as session:
        existing_user = session.query(User).filter(User.id == current_user["id"]).first()
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Hashear la nueva contraseña
        hashed_new_password = get_password_hash(new_password)

        # Actualizar la contraseña hasheada en la base de datos
        existing_user.hashed_password = hashed_new_password

        # Confirmar los cambios en la base de datos
        session.commit()

        return {"message": "Password updated successfully"}


### CHANGE EMAIL ###
@UserAPI.put('/user_email', status_code=HTTP_200_OK, tags=["User"])
def update_user_email(this_user: UserEmail, current_user: dict = Depends(get_current_user)):
    """ Update Email """
    
    # Establecer la conexión a la base de datos
    with Session() as session:
        # Obtener el usuario existente
        existing_user = session.query(User).filter(User.id == current_user["id"]).first()
        if existing_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Actualizar solo los campos que se proporcionan
        if this_user.email:
            existing_user.email = this_user.email
        
        # Actualizar la marca de tiempo
        existing_user.updated_at = datetime.now()
        
        print("Updated email:", existing_user.email)

        # Confirmar los cambios en la base de datos
        session.commit()
        return {"message": "User updated successfully"}

### CHANGE NAME ###
@UserAPI.put('/users/{user_id}', status_code=HTTP_200_OK, tags=["User"])
def update_user_name(this_user: UserName, current_user: dict = Depends(get_current_user)):
    """ Update Name """
    
    # Establecer la conexión a la base de datos
    with Session() as session:
        # Obtener el usuario existente
        existing_user = session.query(User).filter(User.id == current_user["id"]).first()
        if existing_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Actualizar solo los campos que se proporcionan
        if this_user.name:
            existing_user.name = this_user.name
        
        # Actualizar la marca de tiempo
        existing_user.updated_at = datetime.now()
        
        print("Updated name:", existing_user.name)

        # Confirmar los cambios en la base de datos
        session.commit()
        return {"message": "User updated successfully"}

### GET INACTIVE USERS ###
@UserAPI.get('/users/{}/inactive', tags=["Inactive"])
def get_inactive_users():
    """ All inactive """
    with Session() as session:
        return session.query(User).filter(User.status != True).all()  # Todos los elementos inactivos

### INACTIVE USER ###
@UserAPI.delete('/users/{id}', status_code=HTTP_204_NO_CONTENT, tags=["Inactive"])
def deactivate_user(id: int):
    """ Delete (deactivate) product """

    with Session() as session:
        session.execute(update(User).values(
            status=False,
            updated_at=datetime.now()).where(User.id == id))   # check THIS
        session.commit()

    return Response(status_code=HTTP_204_NO_CONTENT) # Delete successful, no redirection needed


### GET ACTIVE USERS ###
@UserAPI.get('/users/{}/active', tags=["Active"])
def get_active_users():
    """ Get all active Users """
    conn.execute(select(User).where(User.status == True)).fetchall()  # Todos los elementos activos
    with Session() as session:
        return session.query(User).filter(User.status == True).all()  # Todos los elementos activos


### REACTIVATE USER ###
@UserAPI.put('/users/{id}/reactivate', status_code=HTTP_204_NO_CONTENT, tags=["Active"])
def reactivate_user(id: int):
    """ Reactivate user """
    try:
        with Session() as session:
            user = session.query(User).filter(User.id == id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user.status = True
            user.updated_at = datetime.now()

            session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(status_code=HTTP_204_NO_CONTENT)




        