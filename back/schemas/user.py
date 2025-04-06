from pydantic import BaseModel as pyBaseModel

class UserSchemaCreation(pyBaseModel):
    
    name: str = ""
    email: str = ""
    password: str = ""

class UserSchema(pyBaseModel):
    id: int
    name: str = ""
    email: str = ""

class UserEmail(pyBaseModel):
    id: int
    email: str = ""

class UserName(pyBaseModel):
    id: int
    name: str = ""
    

class UserLogin(pyBaseModel):
    email: str = ""
    password: str = ""
    
