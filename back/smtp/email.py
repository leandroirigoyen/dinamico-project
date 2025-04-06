from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel as pyBaseModel
from routes.user import get_current_user
from config.db import Session
from  models.user import User

EmailAPI = APIRouter()



class VerificationCode(pyBaseModel):
    code: str


@EmailAPI.post("/verify-email", tags=["Validation"])
async def verify_email(code_data: VerificationCode, current_user: dict = Depends(get_current_user)):

    # Verificar si el código enviado coincide con el código almacenado en la base de datos
    stored_code = current_user.get("verification_code")

    if not stored_code:
        raise HTTPException(status_code=400, detail="Verification code not found")

    if code_data.code == stored_code:
        if current_user.get("is_verified"):
            # Si el usuario ya está verificado, no necesitas hacer nada más
            return {"message": "User is already verified"}

        # Si coinciden, actualizar el estado 'is_verified' en el usuario
        update_user_verification_status(current_user['id'], is_verified=True)

        # Eliminar el código de verificación de la base de datos
        update_user_verification_code(current_user['id'], verification_code=None)

        return {"message": "Email verification successful"}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification code")

def update_user_verification_code(user_id, verification_code):
    try:
        with Session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.verification_code = verification_code
                session.commit()
                return True
            else:
                return False
    except Exception as e:
        print(f"Error updating user verification code: {e}")
        return False



def update_user_verification_status(user_id, is_verified):
    try:
        with Session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.is_verified = is_verified
                session.commit()
                return True
            else:
                return False
    except Exception as e:
        print(f"Error updating user verification status: {e}")
        return False


