from fastapi import Depends, FastAPI, HTTPException, File, UploadFile, Response, Cookie
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel
import tempfile
import models
from typing import Annotated
from database import engine, SessionLocal
from sqlalchemy.orm import Session

from validation import ValidatePass,ValidateUser,ValidateRePass,Argon2id
from token_distributor import give_access_token,validate_access_token,give_token_payload
from myaes import encrypt_file,decrypt_file

from firebase_admin import credentials, initialize_app, storage
import os
import secrets

firebase_key = 
{

}


app = FastAPI()
models.Base.metadata.create_all(bind = engine)

class UserRegister(BaseModel):
    username: str
    password: str
    repassword:str

class UserLogin(BaseModel):
    username: str
    password: str

class UserBase(BaseModel):
    username: str
    password: bytes
    salt: bytes

class FileBase(BaseModel):
    filename: str
    user_id: int
    key: bytes

class CloudFile(BaseModel):
    filename: str
    user_id: int
    key: bytes
    backup_key: bytes

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_key)
initialize_app(cred, {"storageBucket": f"{firebase_key['project_id']}.appspot.com"})

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

app.mount("/static/css", StaticFiles(directory="public/css"), name="css")
app.mount("/static/javascript", StaticFiles(directory="public/javascript"), name="javascript")
app.mount("/static/assets", StaticFiles(directory="public/assets"), name="assets")

def validate_token(access_token: str = Cookie(None)):
    return access_token

@app.get("/homepage")
async def read_root(access_token: str = Depends(validate_token)):

    path = "public/html/homepage.html"

    if validate_access_token(access_token) == False:
        path = "public/html/login.html"

    try:
        # Ensure the file path is correct
        file_path = Path(path)  
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found")
        html_content = file_path.read_text()
        return HTMLResponse(content=html_content)
    except Exception as e:
        # Catch any other exceptions and raise a server error
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/deletebackup")
async def backup_upload(db: db_dependency, access_token: str = Depends(validate_token)):

    if validate_access_token(access_token) == False:
        raise HTTPException(status_code=500, detail=str(e))

    user_id = give_token_payload(access_token)['id']

    try:
        file_info = read_file(user_id, db)

        if file_info is None or file_info['backup_key'] is None:
            raise HTTPException(status_code=404, detail="User data not found")
   
        try:
            bucket = storage.bucket()
            blob = bucket.blob(f"{user_id}/backup")

            if not blob.exists():
                raise HTTPException(status_code=404, detail="Backup file not found")

            blob.delete()

            update_cloud_key(user_id, None, db)

            return {"info": "Backup file deleted successfully"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete from Firebase: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/getbackup")
async def backup_upload(db: db_dependency, access_token: str = Depends(validate_token)):

    if validate_access_token(access_token) == False:
        raise HTTPException(status_code=500, detail=str(e))

    user_id = give_token_payload(access_token)['id']

    try:
        file_info = read_file(user_id, db)

        if file_info is None or file_info['backup_key'] is None:
            raise HTTPException(status_code=404, detail="User data not found")

        backup_key = file_info['backup_key']
        
        try:
            bucket = storage.bucket()
            blob = bucket.blob(f"{user_id}/backup")

            # Create a temporary file to download the encrypted data
            temp_file_path = ''
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                blob.download_to_filename(temp_file.name)
                temp_file_path = temp_file.name

            # Read the encrypted data from the temporary file
            decrypted_file_path = ''
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                decrypted_file_path = temp_file.name

                with open(temp_file_path, 'rb') as encrypted_file:
                    chunk_size = 16 * 1024
                    chunk = encrypted_file.read(chunk_size)

                    while chunk:                
                        decrypted_chunk = decrypt_file(chunk, backup_key)
                        temp_file.write(decrypted_chunk)
                        chunk = encrypted_file.read(chunk_size)
            
            # Ensure the encrypted temporary file is deleted
            os.remove(temp_file_path)

            return FileResponse(decrypted_file_path, filename='backup.txt', media_type='application/octet-stream')

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download from Database: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/uploadbackup")
async def backup_upload(db: db_dependency, access_token: str = Depends(validate_token), file: UploadFile = File(...)):

    if validate_access_token(access_token) == False:
        raise HTTPException(status_code=500, detail=str(e))

    user_id = give_token_payload(access_token)['id']

    try:
        # Check if the uploaded file is a .zip file
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=422, detail="Only .zip files are allowed")
        
        user_data = read_file(user_id, db)
        backup_key = secrets.token_bytes(16)

        update_cloud_key(user_id, backup_key, db)
        
        # Create a temporary file for the encrypted data
        temp_file_path = ""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            chunk_size = 16 * 1024
            chunk = await file.read(chunk_size)
            while chunk:                
                encrypted_chunk = encrypt_file(chunk, backup_key)
                temp_file.write(encrypted_chunk)
                chunk = await file.read(chunk_size)

        # Upload the encrypted file to Firebase Storage
        try:
            bucket = storage.bucket()
            blob = bucket.blob(f"{user_id}/backup")
            blob.upload_from_filename(temp_file_path)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload to Database: {str(e)}")
        
        finally:
            os.remove(temp_file_path)

        return {"info": f"Encrypted file '{file.filename}' uploaded to Database"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/encrypt")
async def encrypt_upload(db: db_dependency, access_token: str = Depends(validate_token), file: UploadFile = File(...)):

    if validate_access_token(access_token) == False:
        raise HTTPException(status_code=500, detail=str(e))

    user_id = give_token_payload(access_token)['id']
    try:
        # Check if the uploaded file is a .zip file
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=422, detail="Only .zip files are allowed")

        user_data = read_file(user_id, db)
        key = secrets.token_bytes(16)
        file_name = file.filename

        if user_data is None:
            file_instance = FileBase(filename=file_name, user_id=user_id, key=key)
            create_file(file_instance, db)
        else:
            file_instance = FileBase(filename=file_name, user_id=user_id, key=key)
            update_file(file_instance, db)

        user_data = read_file(user_id, db)

        # Encrypt file data
        key = user_data['key']

        # Create a temporary file for the encrypted data
        temp_file_path = ""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            chunk_size = 16 * 1024
            chunk = await file.read(chunk_size)
            while chunk:                
                encrypted_chunk = encrypt_file(chunk, key)
                temp_file.write(encrypted_chunk)
                chunk = await file.read(chunk_size)

        returned_filename = file.filename.replace(".zip", "_encrypted.zip")
    
        return FileResponse(temp_file_path, filename=returned_filename , media_type='application/octet-stream')
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decrypt")
async def encrypt_upload(db: db_dependency, access_token: str = Depends(validate_token), file: UploadFile = File(...)):

    if validate_access_token(access_token) == False:
        raise HTTPException(status_code=500, detail=str(e))

    user_id = give_token_payload(access_token)['id']
    try:
        # Check if the uploaded file is a .zip file
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=422, detail="Only .zip files are allowed")
        
        user_data = read_file(user_id, db)
        if user_data is None:
            raise HTTPException(status_code=500, detail=str(e))
        

        key = user_data['key']

        # Create a temporary file for the encrypted data
        temp_file_path = ""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            chunk_size = 16 * 1024
            chunk = await file.read(chunk_size)
            while chunk:                
                decrypted_chunk = decrypt_file(chunk, key)
                temp_file.write(decrypted_chunk)
                chunk = await file.read(chunk_size)

        returned_filename = user_data['filename'].replace(".zip", "_decrypted.zip")

        return FileResponse(temp_file_path, filename=returned_filename, media_type='application/octet-stream')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/login")
async def read_root():
    try:
        # Ensure the file path is correct
        file_path = Path("public/html/login.html")  
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found")
        html_content = file_path.read_text()
        return HTMLResponse(content=html_content)
    except Exception as e:
        # Catch any other exceptions and raise a server error
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/login")
async def login_user(userdata: UserLogin, db: db_dependency, response: Response):

    username = userdata.username
    userpass = userdata.password
    my_data = read_user(username, db)

    if my_data is None:
        return {"error": True, "yaping": "Username or Password dont match"}

    hashpass = Argon2id(userpass,my_data['salt'])

    if my_data['password'] != hashpass:
        return {"error": True, "yaping": "Username or Password dont match"}

    id_str = str(my_data['id'])
    access_token = give_access_token({'user': username, 'id': id_str})
    response.set_cookie(key="access_token",value = access_token , httponly=True)

    return {"error": False, "validate": True}


@app.get("/register")
async def read_root():
    try:
        # Ensure the file path is correct
        file_path = Path("public/html/register.html")  
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found")
        html_content = file_path.read_text()
        return HTMLResponse(content=html_content)
    except Exception as e:
        # Catch any other exceptions and raise a server error
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/register")
async def register_user(userdata: UserRegister, db: db_dependency, response: Response):
    
    if not ValidateUser(userdata.username):
        return {"error": True, "unvalid": "username", "yaping": "Username must include 3 to 12 charcters with only letters and digits"}
    if not ValidatePass(userdata.password):
        return {"error": True, "unvalid": "password", "yaping": "Password must include 6 to 25 charcters, no space and a digit"}
    if not ValidateRePass(userdata.password, userdata.repassword):
        return {"error": True, "unvalid": "repassword", "yaping": "passwords not matching"}
    if read_user(userdata.username, db) != None:
        return {"error": True, "unvalid": "username", "yaping": "Username already in use"}


    username = userdata.username
    hashpass,salt = Argon2id(userdata.password)

    user = UserBase(username=username, password=hashpass, salt=salt)
    create_user(user, db)

    id_str = str(read_user(username, db)['id'])
    access_token = give_access_token({'user': username, 'id': id_str})
    response.set_cookie(key="access_token",value = access_token , httponly=True)

    return {"message": "User registered successfully"}


def create_user(user: UserBase, db: db_dependency):
    user_dic = user.model_dump()
    db_user = models.User(**user_dic)
    db.add(db_user)
    db.commit()

def create_file(file_data: FileBase, db: db_dependency):
    file_dic = file_data.model_dump()
    db_file = models.File(**file_dic)
    db.add(db_file)
    db.commit()

def read_user(username: str, db: Session):
    db_user = db.query(models.User).filter(models.User.username == username).first()

    if db_user is None:
        return None
    
    user_dict = {
        "id": db_user.id,
        "username": db_user.username,
        "password": db_user.password,
        "salt": db_user.salt
    }
    return user_dict

def read_file(user_id: str, db: Session):
    db_file = db.query(models.File).filter(models.File.user_id == user_id).first()

    if db_file is None:
        return None

    file_dict = {
        "user_id": db_file.user_id,
        "filename": db_file.filename,
        "key": db_file.key,
        "backup_key": db_file.backup_key
    }
    return file_dict

def update_file(file_data: FileBase, db: Session):
    db_file = db.query(models.File).filter(models.File.user_id == file_data.user_id).first()
    
    if db_file is None:
        return None
    
    file_dic = file_data.model_dump().items()
    for key, value in file_dic:
        setattr(db_file, key, value)

    db.commit()

def update_cloud_key(user_id: str, backup_key: bytes, db: Session):
    db_file = db.query(models.File).filter(models.File.user_id == user_id).first()
    
    if db_file is None:
        return None

    setattr(db_file, 'backup_key', backup_key)

    db.commit()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
