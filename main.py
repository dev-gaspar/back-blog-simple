from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde un archivo .env
load_dotenv()

# Configuración de la base de datos utilizando la variable de entorno
DATABASE_URL = os.getenv("DATABASE_URL")  # Recupera la variable de entorno

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está definida en las variables de entorno")

# Crear la conexión a la base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear la base de datos si no existe
Base = declarative_base()

# Modelo de la tabla de posts
class PostModel(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)

# Crear la tabla en la base de datos si no existe
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configuración de CORS para permitir solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de datos para los posts
class Post(BaseModel):
    title: str
    content: str

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas de la API

@app.get("/", response_class=JSONResponse)
async def read_root():
    return {"message": "Bienvenido a la API de Articulos"}

@app.get("/posts", response_class=JSONResponse)
async def get_posts(db: Session = Depends(get_db)):
    try:
        posts = db.query(PostModel).all()
        return posts
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/{post_id}", response_class=JSONResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    try:
        post = db.query(PostModel).filter(PostModel.id == post_id).first()
        if post:
            return post
        raise HTTPException(status_code=404, detail="Post no encontrado")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts", response_class=JSONResponse)
async def create_post(post: Post, db: Session = Depends(get_db)):
    try:
        post_data = PostModel(title=post.title, content=post.content)
        db.add(post_data)
        db.commit()
        db.refresh(post_data)
        return post_data
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/posts/{post_id}", response_class=JSONResponse)
async def update_post(post_id: int, post: Post, db: Session = Depends(get_db)):
    try:
        db_post = db.query(PostModel).filter(PostModel.id == post_id).first()
        if db_post:
            db_post.title = post.title
            db_post.content = post.content
            db.commit()
            db.refresh(db_post)
            return db_post
        raise HTTPException(status_code=404, detail="Post no encontrado")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/posts/{post_id}", response_class=JSONResponse)
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    try:
        db_post = db.query(PostModel).filter(PostModel.id == post_id).first()
        if db_post:
            db.delete(db_post)
            db.commit()
            return db_post
        raise HTTPException(status_code=404, detail="Post no encontrado")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
