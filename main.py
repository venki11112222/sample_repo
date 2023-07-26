from fastapi import FastAPI, Query, Depends, Response, status, HTTPException
from typing import Optional,List 
from pydantic import BaseModel
from datetime import datetime,timedelta
from jose import JWTError,jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from schemas import BossSchema
# from models import Boss
from sqlalchemy import Column,String,Integer,Boolean,ForeignKey
from sqlalchemy.orm import Session
from uvicorn.config import Config
from passlib.context import CryptContext
from sqlalchemy.orm import relationship

from database import Base,SessionLocal,engine

##Models to create database tables
class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True,index=True)
    email = Column(String,unique=True,index=True)
    is_active = Column(Boolean,default=True)

    # user_id = Column(Integer,ForeignKey("boss.id"))

    # creator = relationship("Boss",back_populates="boss")

class Boss(Base):
    __tablename__ = "boss"
    id = Column(Integer, primary_key=True)
    name=Column(String, unique=True,index=True)
    email = Column(String, unique=True,index=True)
    password=Column(String, unique=True,index=True)

    # boss = relationship("User",back_populates="creator")

class Student(Base):
    __tablename__="student"
    rollno = Column(Integer,primary_key= True,nullable=False)
    name = Column(String,nullable =False)
    company = Column(String,nullable = False)
    attendance = Column(Boolean,default= False)

## to create tables based on models given.It executes only once to create tables.
Base.metadata.create_all(bind=engine)

app=FastAPI()
## Schema to provide the column and datatype info to database while inserting/putting data to db.
class UserSchema(BaseModel):
    id:int
    email:str
    is_active:bool

    class Config:
        orm_mode=True

class StudentSchema(BaseModel):
    rollno : int
    name : str
    company : str
    attendance : bool

    class Config:
        orm_mode=True

class BossSchema(BaseModel):
    id:int
    name:str
    email:str
    password:str

    class Config:
        orm_mode=True

class Login(BaseModel):
    username:str
    password:str

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None

#To_show the boss id,name and email and hide the password we use this schema
class show_bossschema(BaseModel):
    id:int
    name:str
    email:str

    class Config:
        orm_mode=True

#password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
class Hash():
    def bcrypt(password:str):
        return pwd_context.hash(password)
    
    def verify(plain_password,hashed_password):
        return pwd_context.verify(plain_password,hashed_password)
    
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#Create token based on login user. If logined user is available in database then goahead with
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(data: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials raised while verifying bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(data, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    # user = get_user(fake_users_db, username=token_data.username)
    # if user is None:
    #     raise credentials_exception
    # return user

    
#database session creation and using in all routes whenever db requires.
def get_db():
    db=SessionLocal()
    print("The db is following: ")
    print(db)
    try:
        yield db
    finally:
        db.close()

@app.post("/users",response_model=UserSchema,tags=['users'])
def index(user:UserSchema,db:Session=Depends(get_db),current_user:UserSchema=Depends(get_current_user)):
    u=User(id=user.id,email=user.email,is_active=user.is_active)
    # u=User(**user)
    print("THe data of u is: ",u)
    db.add(u)
    db.commit()
    return u

@app.get("/users",response_model=List[UserSchema],tags=['users'])
def data_get(db:Session=Depends(get_db),current_user:UserSchema=Depends(get_current_user)):
    data=db.query(User).all()
    print(data)
    return data

@app.get("/users/{id}",status_code=status.HTTP_200_OK,tags=['users'])
def data_geton_id(id,response:Response,db:Session=Depends(get_db),current_user:UserSchema=Depends(get_current_user)):
    data_id=db.query(User).filter(User.id == id).first()
    if not data_id:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail":f"The user data with id {id} is not found in database"}
    return data_id

@app.delete("/users/{id}",status_code=status.HTTP_200_OK,tags=['users'])
def data_delete(id, response:Response, db:Session=Depends(get_db),current_user:UserSchema=Depends(get_current_user)):
    # db.query(User).filter(User.id == id).delete(synchronize_session=False)
    data_to_delete=db.query(User).filter(User.id == id)
    print("The data_to_delete is following: ")
    print(data_to_delete)
    if not data_to_delete.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User id is not found in database")
    data_to_delete.delete(synchronize_session=False)
    db.commit()
    return {"details":f"record with id {id} is sucessfully deleted"}

@app.put("/users/{id}",status_code=status.HTTP_202_ACCEPTED,tags=['users'])
def put_data(id,user:UserSchema, db:Session=Depends(get_db),current_user:UserSchema=Depends(get_current_user)):
    data_tobe_updated=db.query(User).filter(User.id == id)
    if not data_tobe_updated.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"user with id {id} not found in database")
    # data_tobe_updated.update({'email':"zulia@gmail.com"}, synchronize_session=False)
    data_tobe_updated.update({"email":"gimmy@gmail.com"}, synchronize_session=False)
    db.commit()
    return "data is successfully updated."


@app.post("/boss",response_model=show_bossschema,tags=['Boss'])
def create_boss(request:BossSchema,db:Session=Depends(get_db),current_user:UserSchema=Depends(get_current_user)):
    # new_boss=Boss(request)
    hashed_password=pwd_context.hash(request.password)
    new_boss=Boss(id=request.id,name=request.name,email=request.email,password=hashed_password)
    print("The new boss is following: ")
    print(new_boss)
    db.add(new_boss)
    db.commit()
    db.refresh(new_boss)
    return new_boss

@app.get("/boss",tags=['Boss'])
def data_get(db:Session=Depends(get_db),current_user:UserSchema=Depends(get_current_user)):
    data_boss=db.query(Boss).all()
    print(data_boss)
    print("================================Venkatesh-----1111=====================================")
    return data_boss


@app.get("/boss/{id}",response_model=show_bossschema,tags=['Boss'])
def data_get_id(id:int,db:Session=Depends(get_db),current_user:UserSchema=Depends(get_current_user)):
    user=db.query(Boss).filter(Boss.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"user with id {id} is not available")
    return user


@app.post("/login",tags=['Authentication'])
# def login(request:Login,db:Session=Depends(get_db)):
def login(request:OAuth2PasswordRequestForm = Depends(),db:Session=Depends(get_db)):
    user = db.query(Boss).filter(Boss.email == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No user found with the given username{request.username}")
    if not Hash.verify(request.password,user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Incorrect Password")
    #generate a jwt token and return
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
    # return user
